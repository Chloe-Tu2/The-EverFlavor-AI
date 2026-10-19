"""The guards that keep API keys and user data out of git (.claude/hooks/, adapted from the Kepler project).

guard_secrets.py runs before every shell command Claude Code runs; precommit_secrets.py runs on every git
commit once installed. These tests feed them sample commands and paths.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / ".claude" / "hooks"


def guard(command: str) -> str:
    """Run the Claude Code guard on one command; '' when it lets the command through, else its reason."""
    out = subprocess.run([sys.executable, str(HOOKS / "guard_secrets.py")], input=json.dumps({"tool_input": {"command": command}}),
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out.strip() else ""


@pytest.mark.parametrize("command", [
    "git add config/.env",
    "git add -f config/.env",
    'cd x && git add "config\\.env"',
    "git add data/user/profile.json",
    "git add logs/agent.audit.jsonl",
    "git add user_profiles.parquet chat_history.json",
    "git commit --no-verify -m wip",
    "git commit -nm wip",
    "git -c core.hooksPath=/dev/null commit -m wip",
])
def test_guard_refuses_keys_user_data_and_skipping_the_hook(command):
    assert "Blocked by" in guard(command)


@pytest.mark.parametrize("command", [
    "git add README.md app/app.py",
    "git add config/.env.example",
    "git status",
    'git commit -m "keep config/.env out of git"',   # a message is not a path
    "python -m pytest -q",
])
def test_guard_lets_ordinary_commands_through(command):
    assert guard(command) == ""


def test_precommit_hook_uses_the_same_rules():
    source = (HOOKS / "precommit_secrets.py").read_text(encoding="utf-8")
    pattern = re.search(r"SECRET = re.compile\((r'.*?'\s*\n\s*r'.*?')", source, re.DOTALL)
    assert pattern
    secret = re.compile("".join(re.findall(r"r'(.*?)'", pattern.group(1))), re.IGNORECASE)
    assert all(secret.search(p) for p in ["config/.env", "data/user/a.json", "logs/x.txt", "audit_2026.jsonl",
                                          "user_profiles.parquet", "chat_history.json", "certs/server.pem"])
    assert not any(secret.search(p) for p in ["config/.env.example", "src/everflavor/llm.py", "docs/ethics_privacy.md"])
