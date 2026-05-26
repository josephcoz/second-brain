# Weekly Rollup (rollup sub-spec of the `dream` skill)

> **This is now Step 4 of the `dream` skill** (`~/.claude/skills/dream/SKILL.md`).
> The dream skill orchestrates the weekly run: it sets up the review worktree,
> consolidates the memory store (dedup / archive / contradictions / insights /
> trim MEMORY.md / regenerate Topic-Index), and writes this rollup — all on a
> `dream/<YYYY-Wxx>` branch for review. This file defines the **rollup document
> format and the context-gap aggregation** the skill follows. The dream is run
> on-demand (`/dream`) or by the Sunday launchd job (`weekly-rollup.prompt.md`,
> which passes `--notify`).

## Configuration

Resolve `{{vault_path}}` etc. from the host repo's `config.yaml` (`work-automation`
for work, `life-automations` for personal). All paths below are under `{{vault_path}}`.

## The rollup document

Write `Journal/YYYY-WXX-rollup.md` following `DataContext/Weekly-Rollup-Template.md`.
It is an **append** (a new file) — the rollup never rewrites prior journals or meetings.
Use `[[wiki links]]` per `DataContext/vault-contract.md`. Be concrete (Hex IDs, file
names, full names, dollar figures). Synthesize from: this week's daily journals
(ground truth), the week's meetings, the week's Claude Code session transcripts
(`~/.claude/projects/*.jsonl`), and the previous rollup (continuity).

## Context-gap aggregation (the unique value here)

### Open Questions for the user
Scan the week's daily journals for `## Open Questions for {{user}}` sections, plus a
fresh scan for recurring gaps the daily task didn't flag:
- People who attended ≥2 meetings this week with no `People/` file (or only a stub)
- Workstreams referenced ≥3 times across journals with no `Topics/` node
- DataContext/Analysis files referenced repeatedly but last modified >30 days ago
- Any term/project/system mentioned without grounding in any vault file

Append `## Open Questions for {{user}} (Week of YYYY-MM-DD)`. Make each answerable in
one back-and-forth; be specific. Cap at the 10 most impactful (recurring 3+ > new
people you met > stale references). Omit the section if there are none — don't pad.

### Questions Resolved This Week
Scan `DataContext/kickoff-resolutions.md` for this week's entries with `→ Written to`
annotations (answers persisted via the kickoff Learning Loop). Append a
`## Questions Resolved This Week` section listing them with their vault destination.
Omit if none.

### Staleness escalation
For Open Questions appearing in 3+ consecutive daily journals unresolved, annotate with
an age warning (`first surfaced YYYY-MM-DD, appeared N times`). Cap at 3 — oldest/most
repeated first. Surfaces systemic blockers daily flagging hasn't cleared.

## Rules

- WORK CONTENT ONLY (work context) — no personal topics; never cross-write vaults.
- Journal is ground truth; never fabricate — report only what's verifiable from sources.
- Self-contained: a new Claude reading the rollup + `Onboarding.md` should be useful immediately.
