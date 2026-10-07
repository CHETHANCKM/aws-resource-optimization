import asyncio

import aws_resource_mcp
from aws_resource_mcp import __version__, get_version, read_version
from aws_resource_mcp import server
from aws_resource_mcp.server import aws_account_summary, aws_report, get_version_with_env, mcp


def test_server_imports():
    assert mcp is not None


def test_version_can_be_read():
    assert read_version() == __version__
    assert get_version() == __version__
    assert isinstance(__version__, str)
    assert __version__


def test_version_uses_installed_metadata_when_version_file_is_missing(tmp_path, monkeypatch):
    module_path = tmp_path / "src" / "aws_resource_mcp" / "__init__.py"
    monkeypatch.setattr(aws_resource_mcp, "__file__", str(module_path))

    def installed_version(distribution):
        assert distribution == "aws-resource-optimization-mcp"
        return "0.1.0"

    monkeypatch.setattr(aws_resource_mcp, "version", installed_version)

    assert read_version() == "0.1.0"


def test_tool_exists():
    tool_names = asyncio.run(mcp.list_tools())
    assert "aws_account_summary" in {tool.name for tool in tool_names}


def test_prompt_exists():
    prompt_names = asyncio.run(mcp.list_prompts())
    assert "aws_report" in {prompt.name for prompt in prompt_names}


def test_tool_response():
    assert aws_account_summary() == "AWS Resource Optimization MCP is running."


def test_prompt_response():
    prompt_text = aws_report()
    assert "AWS resource report" in prompt_text


def test_version_command_output(monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("GIT_COMMIT_SHA", "abc123def456")
    assert get_version_with_env() == f"v{__version__}-abc123d"

    monkeypatch.setenv("APP_ENV", "prod")
    assert get_version_with_env() == f"v{__version__}"


def test_dev_wheel_version_uses_embedded_commit_sha(monkeypatch):
    monkeypatch.setattr(server, "__version__", "0.1.0+dev.abc123d")
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("GIT_COMMIT_SHA", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    assert get_version_with_env() == "v0.1.0-abc123d"
