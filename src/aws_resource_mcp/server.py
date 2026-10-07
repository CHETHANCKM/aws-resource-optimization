from __future__ import annotations

import os
import re
import subprocess
import sys
from email.utils import parseaddr
from importlib.metadata import distribution, distributions

import boto3
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
    if "+dev." in __version__:
        base_version, short_sha = __version__.split("+dev.", 1)
        if short_sha:
            return f"v{base_version}-{short_sha}"

    version = f"v{__version__}"
    if get_current_env() == "dev":
        short_sha = get_short_commit_sha()
        if short_sha:
            return f"{version}-{short_sha}"
        return f"{version}-dev"
    return version


def get_application_info() -> str:
    package = distribution("aws-resource-optimization-mcp")
    metadata = package.metadata
    author = metadata.get("Author", "")
    if not author:
        author, _ = parseaddr(metadata.get("Author-email", ""))

    home_page = metadata.get("Home-page", "")
    if not home_page:
        for project_url in metadata.get_all("Project-URL", []):
            label, separator, url = project_url.partition(",")
            if separator and label.strip().lower() == "homepage":
                home_page = url.strip()
                break

    fields = [
        f"Name: {metadata.get('Name', 'aws-resource-optimization-mcp')}",
        f"Version: {package.version}",
        f"Summary: {metadata.get('Summary', '')}",
        f"Home-page: [{home_page}]({home_page})" if home_page else "Home-page: ",
        f"Author: {author}",
        f"License: {metadata.get('License') or metadata.get('License-Expression', '')}",
        f"Python: {sys.version.split()[0]}",
    ]
    return "\n".join(fields)


def get_package_metadata() -> str:
    package = distribution("aws-resource-optimization-mcp")
    metadata = package.metadata
    author = metadata.get("Author", "")
    author_email, parsed_email = parseaddr(metadata.get("Author-email", ""))
    if author_email and not author:
        author = author_email
    if parsed_email:
        author_email = parsed_email
    home_page = metadata.get("Home-page", "")
    if not home_page:
        for project_url in metadata.get_all("Project-URL", []):
            label, separator, url = project_url.partition(",")
            if separator and label.strip().lower() == "homepage":
                home_page = url.strip()
                break

    def dependency_name(requirement: str) -> str:
        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
        return match.group(1) if match else requirement

    package_name = metadata["Name"]
    normalized_package_name = re.sub(r"[-_.]+", "-", package_name).lower()
    required_by = sorted({
        installed.metadata["Name"]
        for installed in distributions()
        if installed.metadata.get("Name")
        and re.sub(r"[-_.]+", "-", installed.metadata["Name"]).lower() != normalized_package_name
        and any(
            re.sub(r"[-_.]+", "-", dependency_name(requirement)).lower() == normalized_package_name
            for requirement in (installed.requires or ())
        )
    })
    requirements = sorted({
        dependency_name(requirement)
        for requirement in (package.requires or ())
        if not re.search(r"\bextra\s*==\s*['\"]", requirement.partition(";")[2])
    })

    fields = [
        f"Python {sys.version.split()[0]}",
        f"Name: {package_name}",
        f"Version: {package.version}",
        f"Summary: {metadata.get('Summary', '')}",
        f"Home-page: {home_page}",
        f"Author: {author}",
        f"Author-email: {author_email}",
        f"License: {metadata.get('License') or metadata.get('License-Expression', '')}",
        f"Location: {package.locate_file('')}",
        f"Requires: {', '.join(requirements)}",
        f"Required-by: {', '.join(required_by)}",
    ]
    return "\n".join(fields)


@mcp.tool()
def aws_account_summary(profile: str | None = None) -> str:
    """Verify AWS credentials and return the connected account identity.

    Pass a named AWS CLI profile to use its credentials; otherwise the default
    boto3 credential chain is used.
    """
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    identity = session.client("sts").get_caller_identity()
    return (
        f"Connected to AWS account {identity['Account']}.\n"
        f"ARN: {identity['Arn']}\n"
        f"User ID: {identity['UserId']}"
    )


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
    if args and args[0] in {"/about", "--about"}:
        print(get_application_info())
        return
    if args and args[0] in {"/about-app", "--about-app"}:
        print(get_package_metadata())
        return
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
