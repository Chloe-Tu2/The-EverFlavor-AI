"""PreToolUse hook (Bash and PowerShell): never let a git command stage or commit API keys or user data.

Adapted from the Kepler project's hook (same author). Protected here: config/.env and any .env, key or pem file
(.env.example is meant to be committed), and user data (docs/ethics_privacy.md): data/user/, logs/, audit logs,
user profiles and chat history.

The command is split the way a shell splits it (quotes removed, ; && || | as separators, heredoc bodies dropped), then
each git call is read past its global options (-C, -c, --git-dir...) to its real subcommand:
  add / stage / update-index  naming a key or user-data path (SECRET below)          -> refused
  commit with --no-verify (any abbreviation, --no-v...) or a short -n                 -> refused (skips the git hook)
  commit naming a secret path, or while a secret file is already staged               -> refused
  -c core.hooksPath=..., git config core.hooksPath <value>, GIT_CONFIG_* variables    -> refused (redirects the hook)
Commit messages are values, not paths: a message that mentions the key is fine.

This is one layer of four: .gitignore keeps these files out of `git add .`; the git pre-commit hook
(precommit_secrets.py) checks the real index on every commit; and CI fails if one is ever tracked
(tests/test_security.py).
"""
import json
import re
import shlex
import subprocess
import sys

SECRET = re.compile(r'(^|[/\\])(\.secrets([/\\]|$)|[^/\\]*\.(key|pem)$|\.env(?!\.example$)(\.[\w-]+)?$'
                    r'|data[/\\]user([/\\]|$)|logs([/\\]|$)|[^/\\]*audit[^/\\]*\.jsonl$|user_profiles[^/\\]*$'
                    r'|chat_history[^/\\]*$)', re.IGNORECASE)
SEPARATORS = {';', '&&', '||', '|', '&', '\n'}
GLOBAL_WITH_VALUE = {'-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--super-prefix',
                     '--config-env', '--attr-source'}
COMMIT_WITH_VALUE = {'-m', '--message', '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message',
                     '--author', '--date', '-t', '--template', '--cleanup', '--fixup', '--squash', '--trailer',
                     '--pathspec-from-file'}
SHORT_VALUE_FLAGS = set('mFCctu')   # in a short cluster, the rest of the token is this option's value
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", re.DOTALL | re.MULTILINE)


def deny(reason):
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny',
                                             'permissionDecisionReason': 'Blocked by .claude/hooks/guard_secrets.py: '
                                             + reason}}))
    sys.exit(0)


def segments(cmd, windows):
    lex = shlex.shlex(HEREDOC.sub(' ', cmd), posix=True, punctuation_chars=';&|')
    lex.whitespace_split = True
    lex.commenters = ''
    if windows:   # PowerShell and cmd keep backslashes (.secrets\star_gazer.key); bash treats them as escapes
        lex.escape = ''
    seg = []
    for tok in lex:
        if tok in SEPARATORS or set(tok) <= set(';&|'):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def is_git(tok):
    return re.search(r'(^|[/\\])git(\.exe)?$', tok, re.IGNORECASE) is not None


def hooks_path(text):
    return 'core.hookspath' in text.lower()


def check_commit(args):
    k = 0
    while k < len(args):
        a = args[k]
        if a == '--':
            if any(SECRET.search(p) for p in args[k + 1:]):
                deny('this git commit names a secret file.')
            return
        if a.startswith('--'):
            name = a.split('=', 1)[0]
            if len(name) > 5 and '--no-verify'.startswith(name):
                deny('git commit --no-verify would skip the pre-commit hook that guards the keys and user data.')
            if name in COMMIT_WITH_VALUE and '=' not in a:
                k += 1
        elif a.startswith('-') and len(a) > 1:
            for j, ch in enumerate(a[1:]):
                if ch == 'n':
                    deny('git commit -n (--no-verify) would skip the pre-commit hook that guards the keys and user data.')
                if ch in SHORT_VALUE_FLAGS:
                    if j == len(a) - 2 and ch != 'u':   # the value is the next token (-u takes it glued only)
                        k += 1
                    break
        elif SECRET.search(a):
            deny('this git commit names a secret file.')
        k += 1


def check_git(args, env):
    if any(k.upper().startswith('GIT_CONFIG') for k in env):
        deny('setting GIT_CONFIG_* could redirect the git hook that guards the keys and user data.')
    k = 0
    while k < len(args) and args[k].startswith('-'):
        a = args[k]
        joined = ('=' in a and a.split('=', 1)[0] in GLOBAL_WITH_VALUE) or (a[:2] in ('-c', '-C') and len(a) > 2)
        value = args[k + 1] if a in GLOBAL_WITH_VALUE and k + 1 < len(args) else ''
        if hooks_path(a) or hooks_path(value):   # -c core.hooksPath=..., -ccore..., --config-env=core.hooksPath=...
            deny('changing core.hooksPath would bypass the git pre-commit hook that guards the keys and user data.')
        k += 2 if a in GLOBAL_WITH_VALUE and not joined else 1
    if k >= len(args):
        return
    sub, rest = args[k].lower(), args[k + 1:]
    if sub not in ('commit', 'log', 'show', 'grep', 'diff', 'config', 'help') and any(hooks_path(a) for a in rest):
        deny('changing core.hooksPath would bypass the git pre-commit hook that guards the keys and user data.')
    if sub in ('add', 'stage', 'update-index') and any(SECRET.search(a) for a in rest if not a.startswith('-')):
        deny('this git command stages an API key or user data (config/.env, *.key, *.pem, data/user/, logs/, '
             'profiles, chat history, audit logs). These must never be committed.')
    reading = any(a in ('--get', '--get-all', '--list', '-l', 'get', '--show-origin') for a in rest)
    if sub == 'config' and any(hooks_path(a) for a in rest) and not reading:
        deny('changing core.hooksPath would bypass the git pre-commit hook that guards the keys and user data.')
    if sub == 'commit':
        check_commit(rest)
        return True
    return False


def scan(cmd, depth=0):
    """Check every git call in a command; returns True if one of them commits. Command strings handed to another
    shell (bash -c "...", cmd /c "...", powershell -Command "...", iex "...") are read the same way, recursively."""
    if depth > 3:
        deny('this command nests shells too deeply to read safely.')
    segs = []
    for windows in (False, True):   # read it both ways; either reading finding a problem is enough
        try:
            segs += list(segments(cmd, windows))
        except ValueError:   # unbalanced quotes: refuse if it could touch a secret
            if SECRET.search(cmd.replace('"', ' ').replace("'", ' ')) or hooks_path(cmd):
                deny('could not read this command safely, and it mentions a secret.')
    commits = False
    for seg in segs:
        env = []
        while seg and re.match(r'^[A-Za-z_]\w*=', seg[0]):
            env.append(seg.pop(0))
        if any(re.match(r'-e(nc(odedcommand)?)?$', t, re.IGNORECASE) for t in seg) and \
                any(re.search(r'(^|[/\\])(powershell|pwsh)(\.exe)?$', t, re.IGNORECASE) for t in seg):
            deny('an encoded PowerShell command cannot be checked for secrets.')
        for tok in seg:   # strings run by another shell or by Invoke-Expression
            if re.search(r'\s', tok) and re.search(r'git', tok, re.IGNORECASE):
                commits |= scan(tok, depth + 1)
        for i, tok in enumerate(seg):   # also after wrappers like `env`, `command`, `&`, `cmd /c`
            if is_git(tok):
                commits |= bool(check_git(seg[i + 1:], env))
                break
    return commits


def main():
    data = json.load(sys.stdin)
    cmd = (data.get('tool_input') or {}).get('command', '')
    if re.search(r'(powershell|pwsh)(\.exe)?\b.*\s(-|/|--)e\w*\b', cmd, re.IGNORECASE):   # -e, -ec, -enc, /e...
        deny('an encoded PowerShell command cannot be checked for secrets.')
    if not re.search(r'git', cmd, re.IGNORECASE):
        return
    if re.search(r'git(\.exe)?["\']?(\$\{?IFS|\$\(|`|\$[\w{])', cmd, re.IGNORECASE):   # git${IFS}add, git$(...)
        deny('shell expansion right after git hides what it runs.')
    if re.search(r'GIT_CONFIG', cmd, re.IGNORECASE):   # GIT_CONFIG_GLOBAL=..., $env:GIT_CONFIG_COUNT = ..., set ...
        deny('setting GIT_CONFIG_* could redirect the git hook that guards the keys and user data.')
    if scan(cmd):
        out = subprocess.run(['git', 'diff', '--cached', '--name-only'], capture_output=True, text=True, check=False)
        bad = [f for f in out.stdout.splitlines() if SECRET.search(f)] if out.returncode == 0 else []
        if bad:
            deny(f'secret files are staged ({", ".join(bad)}). Unstage them with git restore --staged.')


if __name__ == '__main__':
    main()
