#!/bin/bash
# SessionStart hook — surface work/personal context at the top of the session.
# Reads CLAUDE_CONTEXT env var (set by the .zshrc claude function) and emits a
# block to stdout that Claude Code injects as a session-start system message.
# Also appends an audit entry to ~/.claude/session-log.jsonl.

context="${CLAUDE_CONTEXT:-unset}"
case "$context" in
  work)
    vault="{{work_vault}}/"
    label="WORK"
    ;;
  personal)
    vault="{{personal_vault}}/"
    label="PERSONAL"
    ;;
  *)
    vault="(unset — no vault routing rule applies)"
    label="UNTAGGED"
    ;;
esac

cat <<EOF
Session context: $label
Vault destination: $vault
Working directory: $(pwd)

Routing rule: any notes, journal entries, or vault writes made during this session
go to the vault destination above. Do not cross-write into the other context's vault.
When in doubt, ask before writing outside the destination.
EOF


log="$HOME/.claude/session-log.jsonl"
mkdir -p "$(dirname "$log")"
printf '{"ts":"%s","context":"%s","cwd":"%s","pid":%s}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$context" "$(pwd)" "$$" >> "$log"
