from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = [
    ["poetry"],
    [str(ROOT / "RagBackend" / ".venv" / "Scripts" / "python.exe"), "-m", "poetry"],
    [str(ROOT / "RagBackend" / ".venv" / "bin" / "python"), "-m", "poetry"],
    [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "poetry"],
    [str(ROOT / ".venv" / "bin" / "python"), "-m", "poetry"],
    [sys.executable, "-m", "poetry"],
]


def main() -> int:
    args = sys.argv[1:]

    for command in CANDIDATES:
        executable = command[0]
        if executable == "poetry":
            if shutil.which("poetry") is None:
                continue
        elif not Path(executable).exists():
            continue

        try:
            completed = subprocess.run([*command, *args], check=False)
        except FileNotFoundError:
            continue
        return completed.returncode

    print(
        "Poetry is not available. Install it into RagBackend/.venv or your active Python environment first.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
