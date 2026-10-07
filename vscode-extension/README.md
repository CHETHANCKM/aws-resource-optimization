# AWS Resource Optimization MCP

An MCP server and VS Code extension for AWS resource optimization.

Current extension version: v0.1.0

This extension is distributed as a VSIX on GitHub Releases and is not published to the Visual Studio Marketplace. Install it with VS Code's `Extensions: Install from VSIX...` command. To update, download the newer VSIX from a later release and install it manually; automatic extension updates are not available for this distribution method.

The Python MCP server is a separate component and must be installed from the wheel attached to the release, then configured in your MCP client. Use the `AWS Resource Optimization: Show Version` command to verify the server executable is available. The `aws_account_summary` tool currently returns a placeholder response and does not inspect AWS resources.

When this repository is open in VS Code, select **AWSRO** from the Chat Agent picker to use the repository's custom agent profile. You can also mention `@awsro` to use the extension's chat participant, which provides `/version`, `/account-summary`, `/report`, and `/help` slash commands. Slash-command suggestions are available when `@awsro` is selected. The account summary and report analyze data you include in chat; they do not connect to or query your AWS account. A compatible selected chat model is required for model-generated responses.

## Contributors

Contributions are welcome. Please open an issue or submit a pull request.