from __future__ import annotations

import argparse
from importlib.resources import files

from strands import Agent, tool

from aws_resource_mcp.server import (
    aws_account_summary as mcp_aws_account_summary,
    generate_report as mcp_generate_report,
)

SYSTEM_PROMPT = files("aws_resource_mcp").joinpath("system_prompt.md").read_text(encoding="utf-8")


@tool
def aws_account_summary(profile: str | None = None) -> str:
    """Verify AWS credentials and return the connected account identity."""
    return mcp_aws_account_summary(profile)


@tool
def generate_report(
    profile: str | None = None,
    regions: list[str] | None = None,
    output_path: str | None = None,
) -> str:
    """Generate a read-only HTML AWS resource optimization report."""
    return mcp_generate_report(profile, regions, output_path)


def create_agent() -> Agent:
    return Agent(
        tools=[aws_account_summary, generate_report],
        system_prompt=SYSTEM_PROMPT,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the AWS Strands optimization agent.")
    parser.add_argument("prompt", nargs="+", help="Question or task for the agent")
    args = parser.parse_args(argv)
    print(create_agent()(" ".join(args.prompt)))


if __name__ == "__main__":
    main()