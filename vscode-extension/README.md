# AWS Resource Optimization MCP

An MCP server and VS Code extension for AWS resource optimization.

Current extension version: v0.1.0

This extension is distributed as a VSIX on GitHub Releases and is not published to the Visual Studio Marketplace. Install it with VS Code's `Extensions: Install from VSIX...` command. To update, download the newer VSIX from a later release and install it manually; automatic extension updates are not available for this distribution method.

The Python MCP server is a separate component and must be installed from the wheel attached to the release, then configured in your MCP client. Use the `AWS Resource Optimization: Show Version` command to verify the server executable is available. The `aws_account_summary` tool verifies AWS credentials and returns the connected account identity through AWS STS.

Each GitHub Release includes an `INSTALL.txt` asset with macOS `python3` and virtual-environment setup instructions, the exact pip install command for that release, and the executable path to use when configuring the MCP server. The wheel keeps its standard versioned filename so pip can install it directly.

When this repository is open in VS Code, select **AWSRO** from the Chat Agent picker to use the repository's custom agent profile. You can also mention `@awsro` to use the extension's chat participant, which provides `/version`, `/about`, `/login`, `/account-summary`, `/report`, and `/help` slash commands. Install AWS CLI v2 first. `/login` opens a terminal to configure and sign in to an AWS IAM Identity Center profile. Complete the AWS CLI prompts there, then use the MCP `aws_account_summary` tool with that profile name to verify the connection. The extension does not collect or store AWS credentials. `/about` shows the installed Python version, package metadata, and installation location. Slash-command suggestions are available when `@awsro` is selected. `/account-summary` and `/report` in chat analyze data you include in chat; use the MCP tool to query your AWS identity. A compatible selected chat model is required for model-generated responses.

## Contributors

Contributions are welcome. Please open an issue or submit a pull request.