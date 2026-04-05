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

## Rules

- WORK CONTENT ONLY — no personal topics
- Be concrete: Hex IDs, file names, full names, dollar figures
- Use Obsidian `[[wiki links]]` for cross-references (see vault contract for conventions)
- Self-contained: a new Claude reading the rollup + Onboarding.md should be immediately useful
- Journal is ground truth, TODO.md is aspirational
- Never fabricate — only report what's verifiable from sources
