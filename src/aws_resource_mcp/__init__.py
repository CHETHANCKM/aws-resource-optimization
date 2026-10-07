from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def read_version() -> str:
    version_path = Path(__file__).resolve().parents[2] / "VERSION"
    if version_path.exists():
        return version_path.read_text(encoding="utf-8").strip()
    try:
        return version("aws-resource-optimization-mcp")
    except PackageNotFoundError:
        return "0.0.0"


__version__ = read_version()


def get_version() -> str:
    return __version__
