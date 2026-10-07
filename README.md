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

The tool `aws_account_summary` verifies your AWS credentials by calling AWS STS and returns the connected account ID, ARN, and user ID. Pass the name of an AWS CLI profile to use an IAM Identity Center (SSO) profile; without one, it uses the standard boto3 credential chain.

The VSIX is distributed as a GitHub Release asset and is not published to the Visual Studio Marketplace. Download the `.vsix` and Python `.whl` assets from the same release. Cloning the repository is not required.

### Install the VS Code extension

1. Download the `.vsix` file from the GitHub Release.
2. In VS Code, open the Command Palette, run `Extensions: Install from VSIX...`, and select the downloaded file.
3. To update later, download the newer `.vsix` from its GitHub Release and install it the same way. VS Code will not auto-update this manually distributed extension.

When this repository is open in VS Code, select **AWSRO** from the Chat Agent picker for the repository custom agent, or mention `@awsro` for the extension chat participant and its `/version`, `/about`, `/about-app`, `/login`, `/account-summary`, `/report`, and `/help` commands. `/about` shows concise application information; `/about-app` shows detailed installed package metadata. The agent profile is workspace-scoped; `@awsro` is provided by the installed extension. Run `@awsro /login` or **AWS Resource Optimization: Configure AWS SSO** from the Command Palette to configure and sign in to an AWS CLI profile. Complete the prompts in the opened terminal. Then call the MCP `aws_account_summary` tool and provide the configured profile name to verify the AWS connection.

### Install the MCP server

Install the Python wheel in a virtual environment:

```bash
python3 -m venv ~/.local/share/aws-resource-optimization/venv
~/.local/share/aws-resource-optimization/venv/bin/python -m pip install /path/to/downloaded/aws_resource_optimization_mcp-<version>-py3-none-any.whl
```

The VSIX and Python MCP server are separate components. Updating the VSIX does not update the Python wheel; install a newer wheel separately when needed.

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

Start the server from VS Code's MCP view. Call `aws_account_summary` to verify the AWS account. For a named profile, pass its name as the `profile` argument. The tool checks identity only; it does not yet inspect resources.

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

The runtime version uses the repository's `VERSION` file when available and falls back to the installed package metadata, so wheels report their packaged version.

## Run the MCP server

After installation, the project exposes the command:

```bash
aws-resource-optimization-mcp
```
This starts the MCP server using stdio transport, which is the common setup for MCP clients such as VS Code.

## Release process

The project uses GitHub Actions to validate and publish releases on pushes to either `main` or `dev`. It packages the VSIX and attaches it to the GitHub Release; it does not publish to the Visual Studio Marketplace and requires no Marketplace publishing token.

The workflow:

1. reads `VERSION`
2. validates it as `MAJOR.MINOR.PATCH`
3. runs tests
4. builds the Python package
5. builds the VSIX
6. creates a branch-specific version tag
7. creates a GitHub Release with the release name
8. attaches the artifacts from `dist/` and `vscode-extension/*.vsix`
9. keeps only the newest published release across `main` and `dev`, deleting older releases and their version tags.
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
## Configure AWS SSO

Install AWS CLI v2 first. The VS Code extension's **AWS Resource Optimization: Configure AWS SSO** command and `@awsro /login` ask for an AWS CLI profile name, then run these AWS CLI steps in an integrated terminal:

```bash
aws configure sso --profile my-profile
aws sso login --profile my-profile
```

The AWS CLI opens the browser for the organization's IAM Identity Center login. The credentials are managed by the AWS CLI and boto3; the extension does not collect or store AWS credentials. After login, call `aws_account_summary` with `{"profile": "my-profile"}` to verify the connected account. The MCP server must be installed with the `boto3` dependency (included automatically when installing the wheel).

## Contributors

Contributions are welcome. Please open an issue to discuss a change or submit a pull request.