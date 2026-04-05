"""Developer- and CI-friendly quality gate runner."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable


def _local_lint_imports_path() -> str | None:
    candidate_names = ["lint-imports", "lint-imports.exe"]
    scripts_directory = Path(PYTHON).resolve().parent
    for candidate_name in candidate_names:
        candidate = scripts_directory / candidate_name
        if candidate.exists():
            return str(candidate)
    return None


LINT_IMPORTS = shutil.which("lint-imports") or _local_lint_imports_path()


def _lint_imports_command() -> list[str]:
    if not LINT_IMPORTS:
        raise RuntimeError(
            "The 'lint-imports' executable was not found on PATH. "
            "Install requirements-dev.txt before running the architecture lint gate."
        )
    return [LINT_IMPORTS, "--config", ".importlinter"]


COMMANDS: dict[str, list[str]] = {
    "lint": [PYTHON, "-m", "ruff", "check", "application", "ui", "tests"],
    "arch-tests": [PYTHON, "-m", "unittest", "tests.architecture.test_hexagonal_imports"],
    "typecheck": [PYTHON, "-m", "mypy"],
    "test": [PYTHON, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
}
QUALITY_GATE_ORDER = ["lint", "arch-lint", "arch-tests", "typecheck", "test"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local and CI quality gates.")
    parser.add_argument(
        "command",
        nargs="?",
        default="quality",
        choices=["lint", "arch-lint", "arch-tests", "typecheck", "test", "quality"],
        help="The quality command to run.",
    )
    args = parser.parse_args()

    if args.command == "quality":
        for command_name in QUALITY_GATE_ORDER:
            _run_named_command(command_name)
        return 0

    _run_named_command(args.command)
    return 0


def _run_named_command(command_name: str) -> None:
    command = _command_for_name(command_name)
    print(f"[quality] Running {command_name}: {' '.join(command)}")
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _command_for_name(command_name: str) -> list[str]:
    if command_name == "arch-lint":
        return _lint_imports_command()
    return COMMANDS[command_name]


if __name__ == "__main__":
    raise SystemExit(main())
