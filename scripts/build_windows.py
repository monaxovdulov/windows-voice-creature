from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    spec_path = project_root / "screen-creature.spec"
    command = [sys.executable, "-m", "PyInstaller", "--noconfirm", str(spec_path)]
    return subprocess.call(command, cwd=project_root)


if __name__ == "__main__":
    raise SystemExit(main())

