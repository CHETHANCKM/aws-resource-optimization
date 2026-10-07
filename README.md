# AWS Resource Optimization MCP

A minimal AWS Resource Optimization Model Context Protocol (MCP) server in Python. Current production version: **v0.1.0**. Development releases use the version plus a short commit ID.

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
The VSIX adds VS Code commands, but it does not contain the Python MCP server. The Python wheel and VS Code extension are published separately.

### VS Code extension with automatic updates

For automatic extension updates, install **AWS Resource Optimization MCP** from the Visual Studio Marketplace. VS Code checks for Marketplace extension updates automatically. You can also download the `.vsix` from the GitHub Release and install it with `Extensions: Install from VSIX...`; Marketplace availability is required for native updates.

Stable releases are published to the Marketplace normally. Dev builds are published as prereleases; select the extension's prerelease version in VS Code to receive dev updates.

### Install the MCP server

Download the `.whl` asset from the same GitHub Release and install it in a virtual environment. Cloning the repository is not required:

```bash
python3 -m venv ~/.local/share/aws-resource-optimization/venv
~/.local/share/aws-resource-optimization/venv/bin/python -m pip install /path/to/downloaded/aws_resource_optimization_mcp-<version>-py3-none-any.whl
```

The extension and Python server are separate components. Updating the VS Code extension does not update the Python wheel; install a newer wheel separately when a new server release is available.

### Configure VS Code MCP

Add this server to your VS Code MCP configuration. Replace `your-name` with your macOS account name and adjust the path if you chose another virtual environment location:

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

Start the server from VS Code's MCP view. In Chat, select the `aws_account_summary` tool to test it. The current tool only returns a placeholder confirmation; it does not yet inspect AWS resources.

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

The project uses GitHub Actions to validate and publish releases on pushes to either `main` or `dev`. The workflow publishes the VS Code extension to the Visual Studio Marketplace, which enables VS Code's built-in extension update checks.

Before Marketplace publishing can work, create a Marketplace publisher whose ID matches the `publisher` field in `vscode-extension/package.json`, create a publishing token, and save it as the GitHub Actions repository secret `VSCE_PAT`.

The workflow:

1. reads `VERSION`
2. validates it as `MAJOR.MINOR.PATCH`
3. runs tests
4. builds the Python package
5. builds and publishes the VSIX to the Marketplace
6. creates a branch-specific version tag
7. creates a GitHub Release with the release name
8. attaches the artifacts from `dist/` and `vscode-extension/*.vsix`
9. moves the `latest` Git tag to the newly published commit
10. keeps only the two newest published releases total across `main` and `dev`, deleting older releases and their version tags

The `latest` Git tag is a movable alias for the newest release across both branches. Each release's version tag, such as `v0.1.0` or `v0.1.0-abc123d`, remains version-specific.
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

## Contributors

Contributions are welcome. Please open an issue to discuss a change or submit a pull request.