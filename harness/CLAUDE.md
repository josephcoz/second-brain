# Global Claude Code instructions

These apply to every Claude Code session on this machine, regardless of which repo or directory you start in.

## Context switching

This machine hosts two separate contexts — **work** ({{company}} {{team}}) and **personal** (home automation, MeetingScribe, life-automations). They must not cross-contaminate.

Shell invocation (defined as a function in `~/.zshrc`):

- `claude work` — loads `work-automation`, `second-brain`, `analyses` via `--add-dir`. Sets `CLAUDE_CONTEXT=work`. Vault destination: `{{work_vault}}/`. Also runs `gh auth switch -u {{gh_work_account}}` so HTTPS git ops use the work account.
- `claude personal` — loads `life-automations`, `second-brain`, `{{meetingscribe_repo}}` via `--add-dir`. Sets `CLAUDE_CONTEXT=personal`. Vault destination: `{{personal_vault}}/`. Also runs `gh auth switch -u {{gh_personal_account}}` so HTTPS git ops use the personal account.
- `claude` (no arg) — defaults to work context (preserves legacy muscle memory).

At session start, `~/.claude/hooks/session-start-context.sh` emits a visible "Session context: WORK/PERSONAL + vault destination" block to the first turn of every session. It also appends a JSON line to `~/.claude/session-log.jsonl` for audit and future nightly-task consumption.

## Vault routing rule

The rule is about **where vault outputs land**, not **which code you're allowed to run**.

- **Vault content** — journal entries, topic notes, meeting notes, analyses, people files, any Obsidian write — goes to the vault destination shown in the session-start block. Never cross-write vault content: work sessions never write to `{{personal_vault}}/`, and personal sessions never write to `{{work_vault}}/`.
- **Tools and code** are separate. A personal-owned tool (e.g., MeetingScribe, which lives under `{{meetingscribe_repo}}/`) can be invoked from a work session to transcribe a work meeting — the resulting transcript then lands in the Work vault because the session is a work session. Likewise, patterns or scripts borrowed across contexts are fine as long as the final outputs route to the correct vault.
- When in doubt, ask before writing outside the destination.

The same rule applies to scheduled launchd tasks: `com.{{user_slug}}.second-brain.*` (tagged `CLAUDE_CONTEXT=work`) write only to the Work vault; `com.{{user_slug}}.life-automations.*` (tagged `CLAUDE_CONTEXT=personal`) write only to the Personal vault.

## Discovery

| Thing | Location |
|---|---|
| Shell function | `~/.zshrc` (`claude()` function) |
| SessionStart hook script | `~/.claude/hooks/session-start-context.sh` |
| Hook registration | `~/.claude/settings.json` → `hooks.SessionStart` |
| Session audit log | `~/.claude/session-log.jsonl` (JSONL, append-only) |
| Work repo CLAUDE.md | `{{work_automation_repo}}/CLAUDE.md` |
| Personal repo CLAUDE.md | `{{personal_automation_repo}}/CLAUDE.md` |
| Shared framework | `{{second_brain_repo}}/CLAUDE.md` (host-repo-agnostic) |
