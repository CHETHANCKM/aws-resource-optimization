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
const vscode = __importStar(require("vscode"));
const chatParticipantId = 'aws-resource-optimization-mcp-vsix.awsro';
function activate(context) {
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
        if (request.command === 'version' || request.command === 'about') {
            const bin = vscode.workspace.getConfiguration().get('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
            const result = cp.spawnSync(bin, [request.command === 'about' ? '--about' : '/version'], {
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
                ? `### About this Application\n\n\`\`\`text\n${(result.stdout || '').trim() || 'No application details returned.'}\n\`\`\``
                : `AWS Resource Optimization MCP version: ${(result.stdout || '').trim() || 'unknown'}`);
            return;
        }
        const prompt = request.command === 'help'
            ? 'Explain that this chat participant is @awsro and the custom agent is AWSRO. Document /version, /about, /account-summary, /report, and /help. Clarify that it can analyze AWS data supplied by the user but does not itself connect to an AWS account.'
            : request.command === 'account-summary'
                ? `Summarize only the AWS account and resource data included in the user's message. If no actual account data is present, say that explicitly and ask the user to provide it. Do not claim to have queried AWS.\n\n${request.prompt}`
                : request.command === 'report'
                    ? `Write an AWS resource optimization report using only the information included in the user's message. Separate observed facts from recommendations, and state clearly when the provided data is insufficient. Do not claim to have queried AWS.\n\n${request.prompt}`
                    : `You are the AWS Resource Optimization chat assistant. Help users analyze AWS resource and cost information they provide. You do not have direct access to AWS accounts; never claim to have queried AWS. State assumptions and distinguish evidence from recommendations.\n\n${request.prompt}`;
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
    context.subscriptions.push(showVersion, syncCommands, awsro);
}
function deactivate() { }
