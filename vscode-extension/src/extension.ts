import * as cp from 'child_process';
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('aws-resource-optimization.showVersion', () => {
    const result = cp.spawnSync('aws-resource-optimization-mcp', ['/version'], {
      env: {
        ...process.env,
        APP_ENV: process.env.APP_ENV || 'dev',
      },
      encoding: 'utf-8',
    });

    if (result.error) {
      vscode.window.showErrorMessage(`AWS Resource Optimization MCP is not installed: ${String(result.error)}`);
      return;
    }

    const output = (result.stdout || '').trim() || (result.stderr || '').trim() || 'unknown';
    vscode.window.showInformationMessage(`AWS Resource Optimization MCP version: ${output}`);
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
