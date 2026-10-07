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

When this repository is open in VS Code, select **AWSRO** from the Chat Agent picker for the repository custom agent, or mention `@awsro` for the extension chat participant and its `/version`, `/about`, `/about-app`, `/pull-latest-mcp`, `/login`, `/login-sso`, `/logout`, `/account-summary`, `/report`, and `/help` commands. `/about` shows concise application information; `/about-app` shows detailed installed package metadata. `/pull-latest-mcp` installs the latest published Python MCP wheel from GitHub Releases, restarts the configured MCP server, and verifies the installed version. The agent profile is workspace-scoped; `@awsro` is provided by the installed extension. Run `@awsro /login` or **AWS Resource Optimization: Login to AWS** to import `aws-credentials.csv` and verify the account. Run `@awsro /login-sso` or **AWS Resource Optimization: Configure AWS SSO** to use IAM Identity Center instead. Run **AWS Resource Optimization: Logout from AWS** or `@awsro /logout` to clear all cached SSO sessions and delete the shared AWS credentials file after confirming.

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

For instructions on publishing changes and installing updated release artifacts, see [How to Update](./HOW_TO_UPDATE.md).

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
## Log in with an AWS credentials CSV

Install AWS CLI v2 first. Place the IAM access-key CSV downloaded from AWS in the root of the project folder opened in VS Code, named exactly `aws-credentials.csv`. The login command rejects files from other directories or with other names. Run **AWS Resource Optimization: Login to AWS** from the Command Palette or use `@awsro /login`. Select the root-level file and confirm the import. The extension asks the AWS CLI to import the CSV, lets you choose a profile, and verifies the identity with AWS STS. The extension does not read or print the secret access key. AWS CLI imports profiles using the IAM user name from the downloaded CSV; credentials are saved in the standard AWS credentials file.

After login, call `aws_account_summary` with the selected profile, for example `{"profile": "my-profile"}`, to check the connection again.

To use IAM Identity Center instead, run **AWS Resource Optimization: Configure AWS SSO** or `@awsro /login-sso`. Complete the AWS CLI prompts and browser login in the terminal that opens. Credentials are managed by the AWS CLI and boto3; the extension does not collect or store AWS credentials. The MCP server must be installed with the `boto3` dependency (included automatically when installing the wheel).

## Contributors

- Chethan Sundar