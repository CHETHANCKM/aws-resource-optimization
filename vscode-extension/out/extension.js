"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const cp = __importStar(require("child_process"));
const fs_1 = require("fs");
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const util_1 = require("util");
const url_1 = require("url");
const vscode = __importStar(require("vscode"));
const chatParticipantId = 'aws-resource-optimization-mcp-vsix.awsro';
const execFile = (0, util_1.promisify)(cp.execFile);
const githubReleasesUrl = 'https://api.github.com/repos/CHETHANCKM/aws-resource-optimization/releases?per_page=1';
const githubReleaseDownloadPrefix = 'https://github.com/CHETHANCKM/aws-resource-optimization/releases/download/';
const mcpPackageName = 'aws-resource-optimization-mcp';
const stopMcpServerCommand = 'workbench.mcp.stopServer';
const startMcpServerCommand = 'workbench.mcp.startServer';
async function resolveMcpPython(binaryPath) {
    const executablePath = path.isAbsolute(binaryPath) || binaryPath.includes(path.sep)
        ? path.resolve(binaryPath)
        : (await execFile(process.platform === 'win32' ? 'where.exe' : 'which', [binaryPath], {
            encoding: 'utf8',
            windowsHide: true,
        })).stdout.split(/\r?\n/)[0].trim();
    const candidates = [
        path.join(path.dirname(executablePath), process.platform === 'win32' ? 'python.exe' : 'python'),
    ];
    try {
        const firstLine = (await fs_1.promises.readFile(executablePath, 'utf8')).split(/\r?\n/, 1)[0];
        const shebang = /^#!\s*"?([^"\r\n]+)"?$/.exec(firstLine)?.[1];
        if (shebang && shebang !== '/usr/bin/env') {
            candidates.push(shebang);
        }
    }
    catch {
        // Binary launchers may not be readable as text; the adjacent interpreter remains the fallback.
    }
    for (const candidate of candidates) {
        try {
            await execFile(candidate, ['--version'], { encoding: 'utf8', windowsHide: true });
            return candidate;
        }
        catch {
            // Try the next interpreter candidate.
        }
    }
    throw new Error(`Could not locate the Python interpreter for MCP executable '${executablePath}'.`);
}
async function getInstalledMcpVersion(pythonPath) {
    const { stdout } = await execFile(pythonPath, ['-m', 'pip', 'show', mcpPackageName], {
        encoding: 'utf8',
        windowsHide: true,
    });
    const version = /^Version:\s*(.+)$/m.exec(stdout)?.[1]?.trim();
    if (!version) {
        throw new Error(`pip did not report an installed version of ${mcpPackageName}.`);
    }
    return version;
}
async function getLatestMcpWheel() {
    const response = await fetch(githubReleasesUrl, {
        headers: { Accept: 'application/vnd.github+json' },
        signal: AbortSignal.timeout(30_000),
    });
    if (!response.ok) {
        throw new Error(`GitHub returned ${response.status} while checking for the latest MCP release.`);
    }
    const releases = await response.json();
    const release = releases[0];
    if (!release?.tag_name || !Array.isArray(release.assets)) {
        throw new Error('GitHub did not return a published MCP release with downloadable assets.');
    }
    const wheel = release.assets.find(asset => typeof asset.name === 'string'
        && /^aws_resource_optimization_mcp-.+-py3-none-any\.whl$/.test(asset.name));
    const match = wheel?.name
        ? /^aws_resource_optimization_mcp-(\d+\.\d+\.\d+(?:\+dev\.[0-9a-f]{7})?)-py3-none-any\.whl$/.exec(wheel.name)
        : undefined;
    if (!wheel?.browser_download_url || !match) {
        throw new Error(`Release '${release.tag_name}' does not include a supported MCP wheel.`);
    }
    const url = new URL(wheel.browser_download_url);
    if (url.protocol !== 'https:' || !url.href.startsWith(githubReleaseDownloadPrefix)) {
        throw new Error('GitHub returned an unexpected MCP wheel download URL.');
    }
    return { version: match[1], url: url.href };
}
function activate(context) {
    const loginToAws = async () => {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceRoot) {
            vscode.window.showErrorMessage('Open the project folder in VS Code before logging in to AWS.');
            return undefined;
        }
        const selectedFiles = await vscode.window.showOpenDialog({
            canSelectFiles: true,
            canSelectFolders: false,
            canSelectMany: false,
            filters: { 'AWS credentials CSV': ['csv'] },
            defaultUri: workspaceRoot.uri,
            title: 'Select aws-credentials.csv',
        });
        if (!selectedFiles?.length) {
            return undefined;
        }
        const credentialsFile = selectedFiles[0];
        const expectedCredentialsPath = path.resolve(workspaceRoot.uri.fsPath, 'aws-credentials.csv');
        if (path.resolve(credentialsFile.fsPath) !== expectedCredentialsPath) {
            vscode.window.showErrorMessage(`Place the credentials file at '${expectedCredentialsPath}' and select it there. Other locations are not allowed.`);
            return undefined;
        }
        const confirmed = await vscode.window.showWarningMessage('AWS CLI will import these long-lived access keys into your local AWS credentials file. Continue?', { modal: true }, 'Import credentials');
        if (confirmed !== 'Import credentials') {
            return undefined;
        }
        const importResult = await runAwsCli(['configure', 'import', '--csv', (0, url_1.pathToFileURL)(credentialsFile.fsPath).href], 'import');
        if (importResult === undefined) {
            return undefined;
        }
        const profileOutput = await runAwsCli(['configure', 'list-profiles'], 'list profiles');
        if (profileOutput === undefined) {
            return undefined;
        }
        const profiles = profileOutput.split(/\r?\n/).map(profile => profile.trim()).filter(Boolean);
        if (profiles.length === 0) {
            vscode.window.showErrorMessage('AWS CLI did not report any profiles after importing the CSV.');
            return undefined;
        }
        const profile = await vscode.window.showQuickPick(profiles, {
            ignoreFocusOut: true,
            placeHolder: 'Choose the AWS profile created from the imported credentials',
        });
        if (!profile) {
            return undefined;
        }
        const identityOutput = await runAwsCli(['sts', 'get-caller-identity', '--profile', profile, '--output', 'json'], 'verify identity');
        if (identityOutput === undefined) {
            return undefined;
        }
        let identity;
        try {
            identity = JSON.parse(identityOutput);
        }
        catch {
            vscode.window.showErrorMessage('AWS CLI returned an invalid identity response.');
            return undefined;
        }
        if (typeof identity.Account !== 'string' || typeof identity.Arn !== 'string') {
            vscode.window.showErrorMessage('AWS CLI identity response did not include an account ID and ARN.');
            return undefined;
        }
        vscode.window.showInformationMessage(`Connected to AWS account ${identity.Account} with profile '${profile}'.`);
        return { profile, account: identity.Account, arn: identity.Arn };
    };
    const runAwsCli = async (args, operation) => {
        try {
            const result = await execFile('aws', args, { encoding: 'utf8', windowsHide: true });
            return result.stdout.trim();
        }
        catch (error) {
            if (typeof error === 'object' && error !== null && 'code' in error && error.code === 'ENOENT') {
                vscode.window.showErrorMessage('AWS CLI was not found. Install AWS CLI v2 and ensure `aws` is on VS Code’s PATH.');
            }
            else {
                vscode.window.showErrorMessage(`AWS CLI failed to ${operation}. Check the AWS CLI installation and CSV format.`);
            }
            return undefined;
        }
    };
    const loginToAwsCommand = vscode.commands.registerCommand('aws-resource-optimization.loginToAws', loginToAws);
    const logoutFromAws = async () => {
        const confirmed = await vscode.window.showWarningMessage('This signs out all AWS IAM Identity Center sessions and permanently deletes the shared AWS credentials file, which may contain credentials used by other applications. Environment-provided AWS credentials are not changed. Continue?', { modal: true }, 'Log out and delete credentials');
        if (confirmed !== 'Log out and delete credentials') {
            return false;
        }
        const logoutResult = await runAwsCli(['sso', 'logout'], 'sign out of AWS SSO sessions');
        if (logoutResult === undefined) {
            return false;
        }
        const credentialsFile = path.resolve(process.env.AWS_SHARED_CREDENTIALS_FILE || path.join(os.homedir(), '.aws', 'credentials'));
        try {
            await fs_1.promises.unlink(credentialsFile);
        }
        catch (error) {
            if (typeof error !== 'object' || error === null || !('code' in error) || error.code !== 'ENOENT') {
                vscode.window.showErrorMessage(`AWS SSO sessions were cleared, but the credentials file could not be deleted: ${String(error)}`);
                return false;
            }
        }
        vscode.window.showInformationMessage('Logged out of all AWS SSO sessions and removed the shared AWS credentials file. Environment-provided credentials, if any, are unchanged.');
        return true;
    };
    const logoutFromAwsCommand = vscode.commands.registerCommand('aws-resource-optimization.logoutFromAws', logoutFromAws);
    const configureAwsSso = async () => {
        const profile = await vscode.window.showInputBox({
            prompt: 'AWS CLI profile to configure for IAM Identity Center (SSO)',
            value: process.env.AWS_PROFILE || 'default',
            validateInput: value => /^[A-Za-z0-9._-]+$/.test(value.trim())
                ? undefined
                : 'Use letters, numbers, dots, underscores, or hyphens in the profile name.',
        });
        if (profile === undefined) {
            return false;
        }
        const selectedProfile = profile.trim();
        const terminal = vscode.window.createTerminal({ name: `AWS SSO: ${selectedProfile}` });
        terminal.show();
        terminal.sendText(`aws configure sso --profile ${selectedProfile} && aws sso login --profile ${selectedProfile}`);
        return selectedProfile;
    };
    const configureAwsSsoCommand = vscode.commands.registerCommand('aws-resource-optimization.configureAwsSso', configureAwsSso);
    const showVersion = vscode.commands.registerCommand('aws-resource-optimization.showVersion', () => {
        const bin = vscode.workspace.getConfiguration().get('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
        const result = cp.spawnSync(bin, ['/version'], {
            env: {
                ...process.env,
                APP_ENV: process.env.APP_ENV || 'dev',
            },
            encoding: 'utf-8',
        });
        if (result.error) {
            vscode.window.showErrorMessage(`AWS Resource Optimization MCP is not installed or not found at path '${bin}': ${String(result.error)}`);
            return;
        }
        const output = (result.stdout || '').trim() || (result.stderr || '').trim() || 'unknown';
        vscode.window.showInformationMessage(`AWS Resource Optimization MCP version: ${output}`);
    });
    const pullLatestMcp = async () => {
        const configuration = vscode.workspace.getConfiguration();
        const binaryPath = configuration.get('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
        const serverId = configuration.get('awsResourceOptimization.mcpServerId') || 'aws-resource-optimization';
        const commands = await vscode.commands.getCommands(true);
        if (!commands.includes(stopMcpServerCommand) || !commands.includes(startMcpServerCommand)) {
            throw new Error('This VS Code version does not expose MCP stop/start commands. Update VS Code, then retry.');
        }
        const pythonPath = await resolveMcpPython(binaryPath);
        const installedVersion = await getInstalledMcpVersion(pythonPath);
        const latest = await getLatestMcpWheel();
        const confirmation = await vscode.window.showWarningMessage(`Install MCP ${latest.version} from the AWS Resource Optimization GitHub release and restart server '${serverId}'? Current version: ${installedVersion}.`, { modal: true }, 'Update and Restart');
        if (confirmation !== 'Update and Restart') {
            return 'MCP update cancelled; no changes were made.';
        }
        let stopped = false;
        try {
            await vscode.commands.executeCommand(stopMcpServerCommand, serverId);
            stopped = true;
            if (installedVersion !== latest.version) {
                await execFile(pythonPath, ['-m', 'pip', 'install', '--upgrade', latest.url], {
                    encoding: 'utf8',
                    windowsHide: true,
                    timeout: 300_000,
                    maxBuffer: 10 * 1024 * 1024,
                });
            }
            await vscode.commands.executeCommand(startMcpServerCommand, serverId);
            stopped = false;
            const verifiedVersion = await getInstalledMcpVersion(pythonPath);
            if (verifiedVersion !== latest.version) {
                throw new Error(`The MCP restarted, but verification found ${verifiedVersion} instead of ${latest.version}.`);
            }
            return installedVersion === latest.version
                ? `Restarted MCP server '${serverId}'. Verified version ${verifiedVersion} is the latest GitHub release.`
                : `Installed and restarted MCP server '${serverId}'. Verified version ${verifiedVersion} is the latest GitHub release.`;
        }
        catch (error) {
            const detail = error instanceof Error ? error.message : String(error);
            if (stopped) {
                try {
                    await vscode.commands.executeCommand(startMcpServerCommand, serverId);
                    return `MCP update failed: ${detail}\nThe server was started again.`;
                }
                catch (restartError) {
                    const restartDetail = restartError instanceof Error ? restartError.message : String(restartError);
                    return `MCP update failed: ${detail}\nThe server could not be restarted: ${restartDetail}. Start '${serverId}' from the VS Code MCP view.`;
                }
            }
            return `MCP update failed: ${detail}`;
        }
    };
    const syncCommands = vscode.commands.registerCommand('aws-resource-optimization.syncCommands', async () => {
        const config = vscode.workspace.getConfiguration();
        const commandsFile = config.get('awsResourceOptimization.commandsFile') || 'vscode-extension/commands.json';
        // Try workspace root first
        const workspaceFolders = vscode.workspace.workspaceFolders;
        let fileUri;
        if (workspaceFolders && workspaceFolders.length > 0) {
            const candidate = vscode.Uri.joinPath(workspaceFolders[0].uri, commandsFile);
            try {
                await vscode.workspace.fs.stat(candidate);
                fileUri = candidate;
            }
            catch {
                // ignore
            }
        }
        // Fallback to extension-relative file
        if (!fileUri) {
            const extUri = vscode.Uri.joinPath(context.extensionUri, commandsFile.replace(/^\/+/, ''));
            try {
                await vscode.workspace.fs.stat(extUri);
                fileUri = extUri;
            }
            catch {
                // ignore
            }
        }
        if (!fileUri) {
            vscode.window.showErrorMessage(`Could not find commands file '${commandsFile}' in workspace or extension.`);
            return;
        }
        try {
            const raw = await vscode.workspace.fs.readFile(fileUri);
            const json = JSON.parse(Buffer.from(raw).toString('utf8'));
            // Register commands at runtime
            for (const cmd of json) {
                const id = cmd.command;
                const handler = async () => {
                    // If args present, execute the binary with provided args, otherwise open chat with the title as prompt
                    if (cmd.args && cmd.args.length > 0) {
                        const bin = config.get('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
                        const result = cp.spawnSync(bin, cmd.args, { encoding: 'utf-8', env: { ...process.env } });
                        if (result.error) {
                            vscode.window.showErrorMessage(`Failed to run '${bin}': ${String(result.error)}`);
                            return;
                        }
                        const out = (result.stdout || '').trim() || (result.stderr || '').trim() || 'unknown';
                        vscode.window.showInformationMessage(`${cmd.title}: ${out}`);
                        return;
                    }
                    // Open Chat view and insert the prompt (best-effort approach)
                    try {
                        await vscode.commands.executeCommand('workbench.action.chat.open');
                        // Paste text into the active chat input if possible (best-effort, may depend on VS Code API)
                        await vscode.env.clipboard.writeText(cmd.title || '');
                        await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
                        vscode.window.showInformationMessage(`Inserted command prompt into Chat: ${cmd.title}`);
                    }
                    catch (e) {
                        vscode.window.showInformationMessage(`Registered command '${id}'.`);
                    }
                };
                try {
                    const disposableCmd = vscode.commands.registerCommand(id, handler);
                    context.subscriptions.push(disposableCmd);
                }
                catch (e) {
                    // registration may fail for duplicate ids
                }
            }
            vscode.window.showInformationMessage(`Synced ${json.length} MCP commands from ${fileUri.path}.`);
        }
        catch (err) {
            vscode.window.showErrorMessage(`Failed to read/parse commands file: ${String(err)}`);
        }
    });
    const awsro = vscode.chat.createChatParticipant(chatParticipantId, async (request, _chatContext, stream, token) => {
        if (request.command === 'logout') {
            const loggedOut = await logoutFromAws();
            stream.markdown(loggedOut
                ? 'AWS logout completed. SSO sessions were cleared and the shared AWS credentials file was removed. Environment-provided credentials, if any, are unchanged.'
                : 'AWS logout was cancelled or could not be fully completed. Check the VS Code notification for details.');
            return;
        }
        if (request.command === 'login') {
            const result = await loginToAws();
            if (result) {
                stream.markdown(`Connected to AWS account \`${result.account}\` using profile \`${result.profile}\` ` +
                    `(ARN: \`${result.arn}\`). Pass profile \`${result.profile}\` to the MCP \`aws_account_summary\` tool.`);
            }
            else {
                stream.markdown('AWS CSV login was cancelled or could not be completed. Check the VS Code notification for details.');
            }
            return;
        }
        if (request.command === 'login-sso') {
            const profile = await configureAwsSso();
            if (profile) {
                stream.markdown(`AWS SSO setup for profile \`${profile}\` is running in the **AWS SSO: ${profile}** terminal. ` +
                    `Complete the prompts there. Then use the MCP \`aws_account_summary\` tool with profile \`${profile}\` ` +
                    `to verify the connection.`);
            }
            else {
                stream.markdown('AWS SSO setup was cancelled.');
            }
            return;
        }
        if (request.command === 'version' || request.command === 'about' || request.command === 'about-app') {
            const bin = vscode.workspace.getConfiguration().get('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
            const args = request.command === 'version'
                ? ['/version']
                : [request.command === 'about' ? '--about' : '--about-app'];
            const result = cp.spawnSync(bin, args, {
                env: {
                    ...process.env,
                    APP_ENV: process.env.APP_ENV || 'dev',
                },
                encoding: 'utf-8',
            });
            if (result.error) {
                stream.markdown(`Could not run \`${bin}\`: ${String(result.error)}`);
                return;
            }
            if (result.status !== 0) {
                stream.markdown(`The version command exited with status ${result.status}: ${(result.stderr || '').trim()}`);
                return;
            }
            stream.markdown(request.command === 'about'
                ? `### About this Application\n\n${(result.stdout || '').trim() || 'No application details returned.'}`
                : request.command === 'about-app'
                    ? `### Package Metadata\n\n\`\`\`text\n${(result.stdout || '').trim() || 'No package metadata returned.'}\n\`\`\``
                    : `AWS Resource Optimization MCP version: ${(result.stdout || '').trim() || 'unknown'}`);
            return;
        }
        if (request.command === 'pull-latest-mcp') {
            try {
                stream.markdown(await pullLatestMcp());
            }
            catch (error) {
                stream.markdown(`Could not update the AWS Resource Optimization MCP: ${error instanceof Error ? error.message : String(error)}`);
            }
            return;
        }
        const prompt = request.command === 'help'
            ? 'Explain that this chat participant is @awsro and the custom agent is AWSRO. Document /version, /about (application information), /about-app (detailed installed package metadata), /pull-latest-mcp (install the latest GitHub MCP wheel, restart the MCP server, and verify the installed version), /login (import aws-credentials.csv and verify AWS identity), /login-sso (configure IAM Identity Center), /logout (clear all cached SSO sessions and delete the shared AWS credentials file after confirmation; environment-provided credentials are unchanged), /account-summary, /report, and /help. Explain the logout confirmation warns that other applications may use the credentials file.'
            : request.command === 'account-summary'
                ? `Summarize only the AWS account and resource data included in the user's message. If no actual account data is present, say that explicitly and ask the user to provide it. Do not claim to have queried AWS.\n\n${request.prompt}`
                : request.command === 'report'
                    ? `Write an AWS resource optimization report using only the information included in the user's message. Separate observed facts from recommendations, and state clearly when the provided data is insufficient. Do not claim to have queried AWS.\n\n${request.prompt}`
                    : `You are the AWS Resource Optimization chat assistant. Help users analyze AWS resource and cost information they provide. You cannot directly invoke MCP tools from this chat participant; never claim to have queried AWS unless the user provides an aws_account_summary tool result. State assumptions and distinguish evidence from recommendations.\n\n${request.prompt}`;
        try {
            const response = await request.model.sendRequest([vscode.LanguageModelChatMessage.User(prompt)], {}, token);
            for await (const part of response.text) {
                stream.markdown(part);
            }
        }
        catch (error) {
            stream.markdown(`Unable to get a response from the selected chat model: ${error instanceof Error ? error.message : String(error)}`);
        }
    });
    context.subscriptions.push(loginToAwsCommand, logoutFromAwsCommand, configureAwsSsoCommand, showVersion, syncCommands, awsro);
}
function deactivate() { }
