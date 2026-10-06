import asyncio

from aws_resource_mcp import __version__, get_version, read_version
from aws_resource_mcp.server import aws_account_summary, aws_report, get_version_with_env, mcp


def test_server_imports():
    assert mcp is not None


def test_version_can_be_read():
    assert read_version() == __version__
    assert get_version() == __version__
    assert isinstance(__version__, str)
    assert __version__


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
