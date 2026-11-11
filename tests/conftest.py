import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: Path):
    """Import a script that lives outside a package (hooks, skill scripts)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """An empty vault with one project in the four-file layout."""
    p = tmp_path / "Alpha"
    p.mkdir()
    (p / "Workdoc - Alpha.md").write_text("# Alpha\n\n#### Log\n", encoding="utf-8")
    (p / "tasks.md").write_text("## Doing\n\n## Done\n", encoding="utf-8")
    (p / "session.md").write_text("# Session Alpha\n\n## Last done\n\n## Next step\n", encoding="utf-8")
    (tmp_path / "_system").mkdir()
    return tmp_path
