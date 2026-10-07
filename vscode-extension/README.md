# AWS Resource Optimization MCP

An MCP server and VS Code extension for AWS resource optimization.

Current extension version: v0.1.0

This extension is distributed as a VSIX on GitHub Releases and is not published to the Visual Studio Marketplace. Install it with VS Code's `Extensions: Install from VSIX...` command. To update, download the newer VSIX from a later release and install it manually; automatic extension updates are not available for this distribution method.

The Python MCP server is a separate component and must be installed from the wheel attached to the release, then configured in your MCP client. Use the `AWS Resource Optimization: Show Version` command to verify the server executable is available. The `aws_account_summary` tool currently returns a placeholder response and does not inspect AWS resources.

In VS Code Chat, mention `@awsopt` to use the AWS Resource Optimization chat participant. It provides `/version`, `/account-summary`, `/report`, and `/help` slash commands. The account summary and report analyze data you include in chat; they do not connect to or query your AWS account. A compatible selected chat model is required for those responses.

## Contributors

Contributions are welcome. Please open an issue or submit a pull request.