from __future__ import annotations

from functools import lru_cache
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

import tomllib


@lru_cache(maxsize=1)
def get_app_version() -> str:
    try:
        return importlib_metadata.version("snapnarrate")
    except importlib_metadata.PackageNotFoundError:
        pass
    except Exception:  # noqa: BLE001
        pass

    try:
        pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with pyproject.open("rb") as f:
            data: dict[str, Any] = tomllib.load(f)
        project = data.get("project", {})
        if isinstance(project, dict):
            version = project.get("version")
            if isinstance(version, str) and version.strip():
                return version.strip()
    except Exception:  # noqa: BLE001
        pass

    return "unknown"
