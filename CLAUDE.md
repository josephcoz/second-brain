# Second Brain Framework

This repo is a framework for maintaining a persistent personal knowledge base using Claude Code and an Obsidian vault. It provides structure, conventions, and automation so that Claude Code can reliably read from and write to your vault across sessions.

---

## Configuration

Read `config.yaml` from the `{{work_automation_repo_path}}` repo for runtime values:

- `vault_path` -- absolute path to the Obsidian vault
- `slack_user_id` -- your Slack member ID
- `timezone` -- IANA timezone string (e.g. `America/New_York`)

All paths below are relative to `{{vault_path}}` unless stated otherwise.

---

## 3-Tier Vault Lookup

When you need context on a topic, follow these tiers in order. Stop as soon as you have enough.

### Tier 1 -- Topic Node

Check `{{vault_path}}/Topics/` for a hub note matching the subject.

Topic nodes are lightweight MOC (Map of Content) files. They contain:
- A short description of the workstream or area
- Key people involved
- Pointers to related Analysis files, DataContext files, and Hex notebooks
- Active/inactive status

If a topic node exists, it is your starting point.

### Tier 2 -- Backlink Grep

If no topic node exists or you need broader context, grep for wiki-link references across the vault:

```
grep -rl '[[Search Term]]' {{vault_path}}/Topics/ {{vault_path}}/DataContext/ {{vault_path}}/Journal/
```

This surfaces every file that mentions the term.

### Tier 3 -- Cold Start

When you have no prior context at all, read these files in order:

1. `{{vault_path}}/Onboarding.md` -- high-level orientation
2. Latest weekly rollup in `{{vault_path}}/Journal/` (file pattern: `YYYY-WXX-rollup.md`)
3. Recent daily journal entries in `{{vault_path}}/Journal/`
4. `{{vault_path}}/TODO.md` -- current priorities and open items

---

## Vault Structure

```
{{vault_path}}/
  Topics/          # Hub notes (one per workstream or domain area)
  Journal/         # Daily entries and weekly rollups
  People/          # One file per person
  Meetings/        # Meeting notes
  DataContext/      # Reference data, schemas, queries, dashboards
  Analysis/        # Detailed analysis write-ups
  Onboarding.md    # High-level vault orientation
  TODO.md          # Current priorities and tasks
```

---

## File Naming Conventions

| Type           | Pattern                              | Example                              |
|----------------|--------------------------------------|--------------------------------------|
| Journal daily  | `YYYY-MM-DD.md`                      | `2026-03-17.md`                      |
| Weekly rollup  | `YYYY-WXX-rollup.md`                | `2026-W12-rollup.md`                 |
| Meeting        | `YYYY-MM-DD Meeting Title.md`       | `2026-03-17 Pipeline Review.md`      |
| Analysis       | `YYYY-MM-DD Analysis Title.md`      | `2026-03-17 Churn Deep Dive.md`      |
| Person         | `Full Name.md`                       | `Jane Smith.md`                      |
| Topic          | `Topic Name.md`                      | `Revenue Forecasting.md`             |
| DataContext    | `Descriptive-Name.md` (kebab-case)  | `monthly-arr-snapshot.md`            |

---

## Wiki Link Conventions

Always use `[[wiki links]]` when referencing vault entities. Obsidian resolves these by filename.

| Entity      | Link Format                             | Resolves To                                  |
|-------------|-----------------------------------------|----------------------------------------------|
| Person      | `[[Full Name]]`                         | `People/Full Name.md`                        |
| Topic       | `[[Topic Name]]`                        | `Topics/Topic Name.md`                       |
| Meeting     | `[[YYYY-MM-DD Meeting Title]]`          | `Meetings/YYYY-MM-DD Meeting Title.md`       |
| DataContext | `[[Descriptive-Name]]`                  | `DataContext/Descriptive-Name.md`            |

---

## Writing Rules

1. **Work content only.** The vault is for professional knowledge. Do not add personal content.
2. **Use wiki links.** Every reference to a person, topic, meeting, or data source must be a `[[wiki link]]`.
3. **Only link to existing targets.** Never create a wiki link to a file that does not yet exist unless you are about to create that file.
4. **Be concrete.** Include ticket IDs, file names, full names, dollar figures, and dates. Vague summaries lose value fast.
5. **Don't duplicate reference data.** If the data lives in DataContext, link to it rather than copying it inline.
6. **Journal is ground truth.** Daily journals record what actually happened. They are the authoritative record.
7. **TODO is aspirational.** TODO.md captures intent and priorities, not completed work.
8. **Topic nodes are hubs, not documents.** Keep them to ~1-2 KB of pointers, descriptions, and status. Detailed analysis belongs in `Analysis/`.

---

## Context Gap Flagging

If you encounter a topic, person, or workstream that has no topic node, no backlinks, and no journal mentions, flag it explicitly:

> **Context gap:** No vault coverage found for `[subject]`. Consider creating a topic node or adding context to the next journal entry.

Do not fabricate context. Say what you do not know.

---

## Automated Pipeline Overview

The `{{work_automation_repo_path}}` repo contains scheduled scripts that keep the vault current:

- **Journal generation** -- Aggregates daily activity into a journal entry
- **Weekly rollups** -- Summarizes the week's journal entries into a rollup file
- **Meeting notes** -- Transcribes and formats meeting recordings into `Meetings/`
- **TODO sync** -- Updates `TODO.md` based on open action items

Refer to the work-automation repo's own CLAUDE.md and `config.yaml` for pipeline details and scheduling.
