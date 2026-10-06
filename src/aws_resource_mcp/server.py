from __future__ import annotations

import os
import sys

from mcp.server.fastmcp import FastMCP

from aws_resource_mcp import __version__

mcp = FastMCP("AWS Resource Optimization")


def get_current_env() -> str:
    return os.getenv("APP_ENV") or os.getenv("ENV") or "local"


def get_version_with_env() -> str:
    return f"{__version__}-{get_current_env()}"


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
