# AWS Resource Optimization MCP

This project is a minimal, production-ready starter for an AWS Resource Optimization Model Context Protocol (MCP) server in Python.

It intentionally keeps the implementation simple and leaves real AWS analysis for future work. The current version is defined in the project root `VERSION` file so releases remain explicit and controlled.

## Current version

The application version is read from the `VERSION` file at the repository root.

Current value:

```text
0.1.0
```

## What the MCP server is

This starter exposes a minimal MCP server built with the official Python MCP SDK. It currently provides:

- a tool named `aws_account_summary`
- a prompt named `aws_report`

The tool returns a simple test response:

```text
AWS Resource Optimization MCP is running.
```

The prompt returns a basic instruction for generating an AWS resource report.

## Local development

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[test]
```

## Installation

```bash
pip install .
```

## How to run the MCP server

After installation, the project exposes the command:

```bash
aws-resource-optimization-mcp
```

This starts the MCP server using stdio transport, which is the usual setup for MCP clients such as VS Code.

## MCP tool

The tool is:

- `aws_account_summary`

It currently returns a simple confirmation string indicating the server is running.

## MCP prompt

The prompt is:

- `aws_report`

It returns a reusable prompt template describing the content of a basic AWS resource report.

## Version management through VERSION

The version is controlled from a single source of truth:

```text
VERSION
0.1.0
```

The project does not hardcode the version in multiple places. The Python package version is dynamically read from that file during packaging.

## Release process

The project uses GitHub Actions to validate and publish releases on pushes to either `main` or `dev`.

The workflow:

1. reads `VERSION`
2. validates it as `MAJOR.MINOR.PATCH`
3. runs tests
4. builds the package
5. creates a branch-specific tag
6. creates a GitHub Release with the release name
7. attaches the built artifacts from `dist/`

On `main`, the tag is a stable release such as:

```text
v0.1.0
```

On `dev`, the tag is a prerelease such as:

```text
v0.1.0-dev
```

The runtime version output also includes the environment suffix, for example:

```text
0.1.0-dev
```

The workflow is intentionally simple and does not auto-bump versions.

## GitHub Actions release behavior

The release job runs on pushes to `main` and `dev`.

If the tag already exists, the workflow fails with a clear message such as:

```text
Release v0.1.0-dev already exists. Update VERSION before pushing.
```

This prevents duplicate releases and ensures the developer updates `VERSION` before the next release.

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

This is a starter configuration. It is designed to be extended later with real AWS resource inspection logic.