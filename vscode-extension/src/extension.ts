import * as cp from 'child_process';
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const showVersion = vscode.commands.registerCommand('aws-resource-optimization.showVersion', () => {
    const bin = vscode.workspace.getConfiguration().get<string>('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
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
    const commandsFile = config.get<string>('awsResourceOptimization.commandsFile') || 'vscode-extension/commands.json';

    // Try workspace root first
    const workspaceFolders = vscode.workspace.workspaceFolders;
    let fileUri: vscode.Uri | undefined;
    if (workspaceFolders && workspaceFolders.length > 0) {
      const candidate = vscode.Uri.joinPath(workspaceFolders[0].uri, commandsFile);
      try {
        await vscode.workspace.fs.stat(candidate);
        fileUri = candidate;
      } catch {
        // ignore
      }
    }

    // Fallback to extension-relative file
    if (!fileUri) {
      const extUri = vscode.Uri.joinPath(context.extensionUri, commandsFile.replace(/^\/+/, ''));
      try {
        await vscode.workspace.fs.stat(extUri);
        fileUri = extUri;
      } catch {
        // ignore
      }
    }

    if (!fileUri) {
      vscode.window.showErrorMessage(`Could not find commands file '${commandsFile}' in workspace or extension.`);
      return;
    }

    try {
      const raw = await vscode.workspace.fs.readFile(fileUri);
      const json = JSON.parse(Buffer.from(raw).toString('utf8')) as Array<{ command: string; title: string; args?: string[] }>;

      // Register commands at runtime
      for (const cmd of json) {
        const id = cmd.command;
        const handler = async () => {
          // If args present, execute the binary with provided args, otherwise open chat with the title as prompt
          if (cmd.args && cmd.args.length > 0) {
            const bin = config.get<string>('awsResourceOptimization.binaryPath') || 'aws-resource-optimization-mcp';
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
          } catch (e) {
            vscode.window.showInformationMessage(`Registered command '${id}'.`);
          }
        };

        try {
          const disposableCmd = vscode.commands.registerCommand(id, handler);
          context.subscriptions.push(disposableCmd);
        } catch (e) {
          // registration may fail for duplicate ids
        }
      }

      vscode.window.showInformationMessage(`Synced ${json.length} MCP commands from ${fileUri.path}.`);
    } catch (err) {
      vscode.window.showErrorMessage(`Failed to read/parse commands file: ${String(err)}`);
    }
  });

  context.subscriptions.push(showVersion, syncCommands);
}

export function deactivate() {}
