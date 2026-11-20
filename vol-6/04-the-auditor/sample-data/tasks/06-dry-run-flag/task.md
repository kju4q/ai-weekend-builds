# Task: add a dry run flag

Add `--dry-run` to `notify.py`. With the flag, print each message that would be
sent and send nothing.

Acceptance checks:
- With `--dry-run`, `send()` is never called
- With `--dry-run`, each message is printed as `would send: <text>`
- Without the flag, behaviour is unchanged
