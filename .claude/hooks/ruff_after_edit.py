"""Claude Code PostToolUse hook: after Claude edits a Python file or notebook, run `ruff check --fix` on that one
file (the same rules as CI, from ruff.toml), so the fixable problems are gone before a commit. Problems ruff cannot
fix are sent back to Claude (exit code 2) to fix by hand. Only safe fixes, no reformatting.

A Python without ruff skips the check (CI still runs it). Registered in .claude/settings.json.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def edited_file() -> Path | None:
    try:
        data = json.loads(sys.stdin.read().lstrip("﻿"))
    except ValueError:
        return None
    tool_input = data.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not path or not path.endswith((".py", ".ipynb")):
        return None
    path = Path(path).resolve()
    project = Path(data.get("cwd") or ".").resolve()
    # Only the project's own files (not scratch scripts or other folders)
    return path if path.is_file() and path.is_relative_to(project) else None


def main() -> None:
    path = edited_file()
    if path is None or importlib.util.find_spec("ruff") is None:
        return
    # Fixed command; the path is a project file Claude just edited (checked above), passed as one argument
    out = subprocess.run([sys.executable, "-m", "ruff", "check", "--fix", "--quiet", str(path)],  # noqa: S603
                         capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if out.returncode != 0:
        print(f"ruff found problems it cannot fix in {path.name}:\n{out.stdout.strip()}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
