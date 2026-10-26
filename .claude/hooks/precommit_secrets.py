"""Git pre-commit hook: refuse any commit whose staged files include an API key or user data (env, key or pem files,
data/user/, logs/, audit logs, user profiles, chat history; adapted from the Kepler project). Git runs it on every commit, however the command was written, and it sees the real index, so it is the lock
that cannot be talked around; guard_secrets.py (Claude Code) and .gitignore are the earlier layers.

Install (once per clone, from the project folder): python .claude/hooks/precommit_secrets.py --install
"""
import re
import subprocess
import sys
from pathlib import Path

SECRET = re.compile(r'(^|/)(\.secrets(/|$)|[^/]*\.(key|pem)$|\.env(?!\.example$)(\.[\w-]+)?$|data/user(/|$)|logs(/|$)'
                    r'|[^/]*audit[^/]*\.jsonl$|user_profiles[^/]*$|chat_history[^/]*$|kaggle\.json$)', re.IGNORECASE)   # Windows ignores case
HOOK = '#!/bin/sh\n# Installed by .claude/hooks/precommit_secrets.py --install\nroot="$(git rev-parse --show-toplevel)"\n' \
       'py="$(command -v python3 || command -v python)"\n"$py" "$root/.claude/hooks/precommit_secrets.py" || exit 1\n' \
       'exec "$py" "$root/.claude/hooks/precommit_checks.py"\n'   # then the code checks (precommit_checks.py)


def staged():
    out = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z'], capture_output=True, check=False)
    if out.returncode != 0:   # fail closed: if git can't say what's staged, don't commit
        sys.exit('pre-commit: could not list the staged files; refusing to commit.')
    return [p for p in out.stdout.decode('utf-8', 'replace').split('\0') if p]


def main():
    if '--install' in sys.argv:
        hooks = Path(subprocess.run(['git', 'rev-parse', '--git-path', 'hooks'], capture_output=True, text=True,
                                    check=True).stdout.strip())
        hooks.mkdir(parents=True, exist_ok=True)
        (hooks / 'pre-commit').write_text(HOOK, encoding='utf-8', newline='\n')
        print(f'installed {hooks / "pre-commit"}')
        return 0
    bad = [p for p in staged() if SECRET.search(p.replace('\\', '/'))]
    if bad:
        sys.exit('pre-commit: refusing to commit API keys or user data: ' + ', '.join(bad)
                 + '\nUnstage them with: git restore --staged <file>')
    return 0


if __name__ == '__main__':
    sys.exit(main())
