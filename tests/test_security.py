"""Security checks for the repository. Run before every push, from the project folder:

    python -m pytest tests          (or)          python tests/test_security.py

They replace checks that used to be done by hand:
- config/.env (API keys) is ignored by git;
- no key from config/.env appears in any file git tracks (notebook outputs included);
- saved notebook outputs show no local paths with a username;
- user input cannot change the URL of an Open Food Facts request;
- user data and logs (profiles, chat history, audit logs) are ignored by git and none is tracked.
A failing check names the file and the key's NAME, never the key itself.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.sources import off_get_by_barcode

NOTEBOOK_DIR = ROOT / "notebooks"
ENV_FILE = ROOT / "config" / ".env"
# Paths that would reveal a username: C:\Users\<name>, /Users/<name>, /home/<name>, AppData
LOCAL_PATH = re.compile(r"[A-Za-z]:\\\\?Users\\\\?|/Users/|/home/|AppData")


def git(*args):
    """Run a git command in the project folder; None if git is not available."""
    if shutil.which("git") is None:
        return None
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)


def secret_values():
    """{name: value} for the keys and tokens in config/.env (values are never printed)."""
    if not ENV_FILE.is_file():
        return {}
    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            name, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if len(value) >= 8 and re.search(r"KEY|TOKEN|SECRET|PASSWORD", name.upper()):
                values[name.strip()] = value
    return values


def test_env_file_is_ignored_by_git():
    result = git("check-ignore", "-q", "config/.env")
    if result is None:
        return   # no git here (for example Colab without a clone): nothing to check
    assert result.returncode == 0, "config/.env is NOT ignored by git: add '.env' to .gitignore before committing"


def test_no_key_in_tracked_files():
    secrets = secret_values()
    files = git("ls-files")
    if not secrets or files is None:
        return   # no keys on this computer, or no git
    leaks = []
    for name in files.stdout.splitlines():
        path = ROOT / name
        if not path.is_file() or path.stat().st_size > 50_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        leaks += [f"{name} contains {key}" for key, value in secrets.items() if value in text]
    assert not leaks, f"Secret found in tracked files: {leaks}"


def test_notebook_outputs_have_no_local_paths():
    found = []
    for notebook_path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"]):
            for output in cell.get("outputs", []):
                text = "".join(output.get("text") or output.get("data", {}).get("text/plain") or "")
                if LOCAL_PATH.search(text):
                    found.append(f"{notebook_path.name} cell {number}")
    assert not found, f"{found} show a local path with a username; clear or re-run them"


# Where the app keeps people's data (see docs/ethics_privacy.md, "User data"): never in git
USER_DATA_EXAMPLES = ["data/user/profiles.json", "logs/agent.audit.jsonl", "audit.jsonl", "user_profiles.db",
                      "chat_history.json", "app/user_profiles.json"]
USER_DATA = re.compile(r"(^|/)(data/user/|logs/)|\.audit\.jsonl$|(^|/)audit[^/]*\.jsonl$|(^|/)(user_profiles|chat_history)")


def test_user_data_is_ignored_and_never_tracked():
    for example in USER_DATA_EXAMPLES:
        result = git("check-ignore", "-q", "--no-index", example)
        if result is None:
            return   # no git here
        assert result.returncode == 0, f"{example} would be committed: add its folder or name to .gitignore"
    tracked = [name for name in git("ls-files").stdout.splitlines() if USER_DATA.search(name)]
    assert not tracked, f"user data is tracked by git (remove with git rm --cached): {tracked}"


def test_barcode_cannot_change_the_request_url():
    for bad in ["../search", "3036810201211/../../x", "abc", "", "1234567", "1" * 15]:
        try:
            off_get_by_barcode(bad)
        except ValueError:
            continue
        raise AssertionError(f"off_get_by_barcode accepted {bad!r}")


if __name__ == "__main__":
    tests = [(name, test) for name, test in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for name, test in tests:
        try:
            test()
            print(f"  pass  {name}")
        except Exception as e:  # noqa: BLE001 - report every failing check, then exit with an error
            failed += 1
            print(f"  FAIL  {name}: {e}")
    print(f"\n{len(tests) - failed} of {len(tests)} security checks passed")
    sys.exit(1 if failed else 0)
