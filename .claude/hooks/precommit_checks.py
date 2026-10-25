"""Git pre-commit hook, after precommit_secrets.py: the same code checks as CI (ruff, then mypy), only when Python
files are staged, so a commit that would fail CI is stopped before it is made. A Python without ruff or mypy skips
that check with a note (CI still runs it); a failing check stops the commit (git commit --no-verify skips it, for
emergencies only).

Installed together with the secrets hook: python .claude/hooks/precommit_secrets.py --install
"""
import importlib.util
import subprocess
import sys


def staged_python() -> list[str]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"], capture_output=True,
                         check=False)
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p.endswith((".py", ".ipynb"))]


def run(name: str, args: list[str]) -> bool:
    if importlib.util.find_spec(name) is None:
        print(f"pre-commit: {name} is not installed in this Python; skipped (CI still runs it).")
        return True
    print(f"pre-commit: {name} ...")
    return subprocess.run([sys.executable, "-m", name, *args], check=False).returncode == 0


def main() -> None:
    files = staged_python()
    if not files:
        return
    ok = run("ruff", ["check", *files])
    ok = run("mypy", ["--config-file", "config/mypy.ini"]) and ok
    if not ok:
        sys.exit("pre-commit: fix the problems above (the same checks CI runs), then commit again.")


if __name__ == "__main__":
    main()
