from __future__ import annotations

import os
import subprocess
import sys

from mcp.server.fastmcp import FastMCP

from aws_resource_mcp import __version__

mcp = FastMCP("AWS Resource Optimization")


def get_current_env() -> str:
    return (os.getenv("APP_ENV") or os.getenv("ENV") or "local").lower()


def get_short_commit_sha() -> str | None:
    sha = os.getenv("GIT_COMMIT_SHA") or os.getenv("GITHUB_SHA")
    if sha:
        return sha[:7]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    commit_sha = result.stdout.strip()
    return commit_sha[:7] if commit_sha else None


def get_version_with_env() -> str:
    version = f"v{__version__}"
    if get_current_env() == "dev":
        short_sha = get_short_commit_sha()
        if short_sha:
            return f"{version}-{short_sha}"
        return f"{version}-dev"
    return version


@mcp.tool()
def aws_account_summary() -> str:
    """Return a simple confirmation that the MCP server is running."""
    return "AWS Resource Optimization MCP is running."


@mcp.prompt()
def aws_report() -> str:
    """Provide a basic prompt template for an AWS resource report."""
    return (
        "Generate an AWS resource report for this account. "
        "Review compute, storage, networking, cost, and utilization details. "
        "Summarize the current state and provide actionable recommendations."
    )


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in {"/version", "--version", "-v"}:
        print(get_version_with_env())
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
