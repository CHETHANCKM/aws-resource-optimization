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

## Install for production

Install the stable release from the `main` branch:

```bash
git clone https://github.com/CHETHANCKM/aws-resource-optimization.git
cd aws-resource-optimization
git checkout main
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

If you want the package installed directly from GitHub:

```bash
pip install "git+https://github.com/CHETHANCKM/aws-resource-optimization.git@main"
```

## Install for development

Use the `dev` branch for the latest changes and commit-based versioning:

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

## Example VS Code MCP configuration

Use a configuration similar to this in VS Code:

```json
{
  "mcpServers": {
    "aws-resource-optimization": {
      "command": "aws-resource-optimization-mcp"
    }
  }
}
```

This is a starter configuration designed to be extended later with real AWS resource inspection logic.
