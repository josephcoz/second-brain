# Weekly Rollup

## Configuration

Read `config.yaml` from the work-automation repo to resolve all `{{variables}}` used in this prompt. Required config keys:
- `vault_path` — absolute path to Obsidian work vault
- `work_automation_repo` — path to your work-automation repo

Check for task-override files matching `rollup-*` in `{{work_automation_repo}}/task-overrides/` and append their instructions after this prompt's steps.

## Context

This is an automated task running without user interaction. Execute autonomously — make reasonable choices and note them in your output. Only take "write" actions this task explicitly asks for.

This task synthesizes the week's daily journal entries into a weekly rollup, updates topic nodes in Topics/, and regenerates DataContext/Topic-Index.md for fast onboarding of new Claude instances.

## IMPORTANT: Read the Template First

Before doing anything else, read the full rollup template and vault contract:

```bash
cat {{vault_path}}/DataContext/Weekly-Rollup-Template.md
cat {{vault_path}}/DataContext/vault-contract.md
```

The template has detailed instructions for data sources, output format, theme identification heuristics, and rules. The vault contract defines folder structure, file naming, and wiki link conventions. Follow both.

## Steps

### Step 1: Gather Data

Read all data sources listed in the template: this week's journal entries, session transcripts, meetings, Slack activity, TODO.md, last week's rollup, modified files. Be thorough — this task runs when token budget is least constrained.

Data sources include:
- Journal entries from this week in `{{vault_path}}/Journal/`
- Meeting files from this week in `{{vault_path}}/Meetings/`
- Claude Code session logs in `~/.claude/projects/` (current primary source)
- Cowork session logs in `~/Library/Application Support/Claude/local-agent-mode-sessions` (legacy source — include if present)
- TODO.md for tracking open items
- Last week's rollup for continuity

### Step 2: Write the Weekly Rollup

Write to `{{vault_path}}/Journal/YYYY-WXX-rollup.md` following the template format. Use `[[wiki links]]` for people, topics, and meetings per the vault contract.

### Step 3: Update Topic Nodes

After writing the rollup, scan `{{vault_path}}/Topics/` and update or create topic nodes for major workstreams identified in the rollup. Follow the format of existing topic nodes. Keep each at ~1-2KB. See the template's "Topic Node Updates" section for when to create vs update.

### Step 4: Regenerate Topic Index

Regenerate `{{vault_path}}/DataContext/Topic-Index.md` by scanning Topics/, DataContext/, and People/ as described in the template's "Topic Index Regeneration" section. This is the fast-path lookup table interactive sessions use during the day — keeping it current saves significant tokens across all daytime sessions.

### Step 5: Aggregate Context Gaps from the Week

Scan all 7 daily journal entries from this week for `## Open Questions for {{user}}` sections (added by the nightly journal task when it hit gaps). Consolidate, dedupe, and prioritize.

Also do a fresh scan across the week's content for **recurring gaps the journal task didn't flag**:

- People who attended ≥2 meetings this week with no `People/` file or only a bare one
- Workstreams referenced ≥3 times across journal entries with no `Topics/` node
- DataContext or Analysis files that were referenced repeatedly but seem stale (last modified > 30 days ago)
- Any term, project, or system mentioned without grounding in any vault file

Append a `## Open Questions for {{user}} (Week of YYYY-MM-DD)` section to the rollup file. Format each question to be answerable in one back-and-forth — be specific so the next interactive session knows exactly what's missing.

Cap at the 10 most-impactful gaps. Prioritize: recurring (3+ mentions) > new people you actually met > stale references.

Example:

```markdown
## Open Questions for {{user}} (Week of 2026-04-07)

**Recurring this week:**
- **Lukas Ming** — 3 meetings this week, only a bare `People/` file. Role and which workstream?
- **"Pricing Migration"** — referenced in 4 journal entries, no `Topics/` node. Standalone workstream or part of [[Pricing and Packaging]]?

**New people met:**
- **Jackson Lieu** — AE candidate, interviewed Tue. What role is he being considered for?

**Conflicts to reconcile:**
- DATA-3110 — TODO.md says In Progress, Mon journal says shipped. Which is correct?
```

The next interactive Claude session reading the rollup will engage the Learning Loop (see `~/github-projects/second-brain/CLAUDE.md`) and resolve these — persisting answers to the right vault file (People, Topics, DataContext, etc.) and removing them from the rollup.

Omit this section entirely if there are no gaps. Don't pad the rollup.

### Step 5b: Questions Resolved This Week

After aggregating open questions, also scan `{{vault_path}}/DataContext/kickoff-resolutions.md` for resolution entries **from this week** that include vault-write annotations (lines containing `→ Written to`). These represent questions that were answered via the daily kickoff thread and persisted to the vault by the Learning Loop closer (Sub-step B2 in `kickoff-resolutions-log.md`).

Append a `## Questions Resolved This Week` section to the rollup, after the Open Questions section:

```markdown
## Questions Resolved This Week

- **RAW_ORDERS vs STG_ORDERS_PROD** — clarified: raw vs cleaned, use STG for analytics → `DataContext/warehouse-data-dictionary.md`
- **Lukas Ming's role** — SMB AE manager, reports to Dana Reyes → `People/Lukas Ming.md`
```

This gives visibility that the Learning Loop is closing. If no questions were resolved this week, omit this section.

### Step 5c: Staleness escalation

Scan the week's journal entries for Open Questions that have appeared in **3 or more consecutive daily journals** without resolution. For each:

1. Count the number of consecutive appearances (grep for the same question text or topic across journal dates).
2. Note the date it was first surfaced.
3. In the rollup's Open Questions section, annotate these with an age warning:

```markdown
**Overdue (first surfaced YYYY-MM-DD, appeared N times):**
- **Commissionable Amount calculation** — flagged since 2026-03-26, appeared in 8 journal entries. Still unresolved.
```

This surfaces systemic blockers that repeated daily flagging hasn't resolved. Cap escalations at 3 per rollup — focus on the oldest/most-repeated items.

## Rules

- WORK CONTENT ONLY — no personal topics
- Be concrete: Hex IDs, file names, full names, dollar figures
- Use Obsidian `[[wiki links]]` for cross-references (see vault contract for conventions)
- Self-contained: a new Claude reading the rollup + Onboarding.md should be immediately useful
- Journal is ground truth, TODO.md is aspirational
- Never fabricate — only report what's verifiable from sources
