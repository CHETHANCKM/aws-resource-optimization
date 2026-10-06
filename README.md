# AWS Resource Optimization MCP

This project is a minimal starter for an AWS Resource Optimization Model Context Protocol (MCP) server in Python.

It intentionally keeps the implementation simple and leaves real AWS analysis for future work. The current version is defined in the project root `VERSION` file so releases remain explicit and controlled.

## Current version

The application version is read from the repository root `VERSION` file.

Current value:

```text
0.1.0
```

Version format:

- Production: `v0.1.0`
- Development: `v0.1.0-<short-commit-sha>`

When the app runs in dev mode, the CLI prints the stable version plus the short commit SHA. Production installs print the stable tag only.

## What the MCP server provides

This starter exposes a minimal MCP server built with the official Python MCP SDK. It currently provides:

- a tool named `aws_account_summary`
- a prompt named `aws_report`

The tool returns:

```text
AWS Resource Optimization MCP is running.
```
The prompt returns a reusable AWS resource report template.

## Install and use as an MCP server

The VSIX adds VS Code commands, but it does not contain the Python MCP server. Download both the `.vsix` and `.whl` assets from the same GitHub Release. Users do not need to clone the repository.

1. In VS Code, open the Command Palette, run `Extensions: Install from VSIX...`, and select the downloaded VSIX.
2. Install the Python wheel in a virtual environment. Replace the wheel path with the file you downloaded:

```bash
python3 -m venv ~/.local/share/aws-resource-optimization/venv
~/.local/share/aws-resource-optimization/venv/bin/python -m pip install /path/to/downloaded/aws_resource_optimization_mcp-<version>-py3-none-any.whl
```

3. Add this server to your VS Code MCP configuration. Replace `your-name` with your macOS account name and adjust the executable path if you used another virtual environment location:

```json
{
  "servers": {
    "aws-resource-optimization": {
      "type": "stdio",
      "command": "/Users/your-name/.local/share/aws-resource-optimization/venv/bin/aws-resource-optimization-mcp",
      "args": [],
      "env": {
        "APP_ENV": "prod"
      }
    }
  }
}
```

4. Start the server from VS Code's MCP view. In Chat, select the `aws_account_summary` tool to test it. The current tool only returns a placeholder confirmation; it does not yet inspect AWS resources.

The VS Code command `AWS Resource Optimization: Show Version` is an additional executable check. If VS Code cannot find the binary, set `awsResourceOptimization.binaryPath` to its full path in VS Code Settings.
```bash
git clone https://github.com/CHETHANCKM/aws-resource-optimization.git
cd aws-resource-optimization
git checkout dev
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

To print the dev version format:

```bash
APP_ENV=dev GIT_COMMIT_SHA=$(git rev-parse --short HEAD) aws-resource-optimization-mcp /version
```

To print the production version format:

```bash
APP_ENV=prod aws-resource-optimization-mcp /version
```

## Run the MCP server

After installation, the project exposes the command:

```bash
aws-resource-optimization-mcp
```
This starts the MCP server using stdio transport, which is the common setup for MCP clients such as VS Code.

## Release process

The project uses GitHub Actions to validate and publish releases on pushes to either `main` or `dev`.

The workflow:

1. reads `VERSION`
2. validates it as `MAJOR.MINOR.PATCH`
3. runs tests
4. builds the Python package
5. builds the VSIX extension
6. creates a branch-specific tag
7. creates a GitHub Release with the release name
8. attaches the artifact files from `dist/` and `vscode-extension/*.vsix`

On `main`, the tag is a stable release such as:
```text
v0.1.0
```

On `dev`, the tag is versioned with the short commit SHA, for example:

```text
v0.1.0-abc123d
```

The runtime version output matches the release format:

```text
v0.1.0-abc123d
```

Production runs print only the stable version:

```text
v0.1.0
```
## MCP tool and prompt

Configure the server using the `servers` example in the installation steps above. Once it is started, the MCP client can call the `aws_account_summary` tool or use the `aws_report` prompt. The tool currently returns a placeholder and does not perform AWS account analysis.