# Secret scan (2026-11-22)

`scripts/governance/secret_scan.py` read 478 tracked text files for 14 kinds of secret (API keys for Anthropic, OpenAI, Google, AWS, Azure, GitHub, Slack, Hugging Face and Kaggle, private keys, JWTs, passwords in connection strings, and long values assigned to names like `api_key`, `secret`, `password`, `token` or `cookie`). Values are shown redacted.

**Result: 0 findings.**


## Allowed (known false positives)

None.

## What else guards secrets

- `.gitignore` keeps `config/.env`, key files, `data/user/` and `logs/` out of git.
- The git pre-commit hook (`.claude/hooks/precommit_secrets.py`) refuses a commit that stages them.
- This scan runs in CI on every push and pull request and fails the run on any finding.
