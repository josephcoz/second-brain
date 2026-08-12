# Second Brain Framework

This repo is a framework for maintaining a persistent personal knowledge base using Claude Code and an Obsidian vault. It provides structure, conventions, and automation so that Claude Code can reliably read from and write to your vault across sessions.

---

## Configuration

Read `config.yaml` from this same folder for runtime values:

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

1. **Write vault content only to the configured vault.** All journal entries, topic notes, meeting notes, analyses, and people files go under the `vault.path` defined in `config.yaml`. Never write vault content anywhere else.
2. **Use wiki links.** Every reference to a person, topic, meeting, or data source must be a `[[wiki link]]`.
3. **Only link to existing targets.** Never create a wiki link to a file that does not yet exist unless you are about to create that file.
4. **Be concrete.** Include ticket IDs, file names, full names, dollar figures, and dates. Vague summaries lose value fast.
5. **Don't duplicate reference data.** If the data lives in DataContext, link to it rather than copying it inline.
6. **Journal is ground truth.** Daily journals record what actually happened. They are the authoritative record.
7. **TODO is aspirational.** TODO.md captures intent and priorities, not completed work.
8. **Topic nodes are hubs, not documents.** Keep them to ~1-2 KB of pointers, descriptions, and status. Detailed analysis belongs in `Analysis/`.

---

## Learning Loop

You are not a passive reader of the vault. You are its active maintainer. Your job is to feed it new context whenever you discover the vault is missing something the user knows. **Sessions are ephemeral; the vault is permanent. If you don't write it down, future-you won't have it.**

### When to engage the loop

Engage when ANY of these is true:

- The 3-tier lookup returned nothing for a person, topic, or workstream you need to understand
- Two vault sources contradict each other and you can't reconcile from journal timestamps alone
- The user references something with no vault coverage ("the X project", "talk to Y", "use the Z model")
- You're about to make an assumption that you can't verify from the vault

If you're not sure whether you need context, default to asking. A 5-second clarification is cheaper than a confidently-wrong action.

### How to ask

One targeted question at a time. Be specific. Show what you already know so the user only fills the gap, not the whole picture.

| Bad | Good |
|---|---|
| "Tell me about Pricing Migration." | "I see Pricing Migration mentioned in last week's journal but no Topic node. Is it a standalone workstream or part of an existing topic like Pricing and Packaging?" |
| "Who is Lukas Ming?" | "I don't have a People file for Lukas Ming. What's his role and which workstreams does he touch?" |
| "How does the commission model work?" | "DataContext/Commission-Model.md mentions a 'v2' but I can't find a separate doc. Is the DataContext file out of date, or is there a v2 file I should know about?" |

In interactive sessions, ask directly in the conversation (or via `AskUserQuestion` if available). In automated/scheduled tasks, do not block — instead, surface the unanswered question in your output (e.g., a Slack DM, a journal annotation, or a `**Question for [user]:**` line in the rollup) so the user can answer asynchronously.

### Where to put the answer

When the user answers, route based on what kind of knowledge it is:

| Type of answer | Destination | Action |
|---|---|---|
| Person — name, role, team, relationships | `People/Full Name.md` | Create if missing; otherwise append to existing |
| Workstream / project / initiative (something other notes will reference) | `Topics/Topic Name.md` | Create a lightweight hub (~1-2 KB); deep details go in `Analysis/` |
| Data semantics, schema, query patterns, system definitions | `DataContext/kebab-name.md` | Create or update |
| One-off conversation, decision, or finding | Append a `## Learned: [topic]` section to today's `Journal/YYYY-MM-DD.md` | The journal is the catch-all for episodic context |
| Polished writeup or analysis (multi-section, deep) | `Analysis/YYYY-MM-DD Title.md` | New file |
| Foundational fact every future session needs | `Onboarding.md` | Sparingly — this file should stay short |

When in doubt, default to **Topic node + Journal append**. Topic nodes are cheap to create and become the seed for future organic context. Journal entries are append-only and never lost.

### Cross-linking is mandatory

A file that isn't linked from anywhere is invisible to Tier 2 of the lookup. Whenever you create a new file, also update related files to point at it.

| New file | Also update |
|---|---|
| `People/[Name].md` | Add the person to the relevant `Topics/[Topic].md` "Key People" section |
| `Topics/[Topic].md` | If an `Analysis/` writeup or `DataContext/` doc covers it, link both directions. Add the topic to the broader Topic Index if one exists. |
| `DataContext/[doc].md` | Link from any Topic node that references the domain |
| `Analysis/[writeup].md` | Link from the relevant Topic node and from today's Journal entry |

The link graph is the navigation system. Disconnected files are dead context.

### Confirm the write

After you persist, tell the user explicitly what landed where, in the same turn:

> **Learned:** Created `Topics/Pricing Migration.md` (new topic node) and added Mike Griffith to its Key People list. Linked from today's journal entry. Future sessions will find this via the 3-tier lookup.

This gives the user a chance to correct routing mistakes ("no, that should be in DataContext, not Topics") before the file proliferates and the wrong placement spreads.

### The "no loose context" rule

**If you ask the user a clarifying question and use the answer, you MUST persist that answer to the vault in the same turn before the conversation moves on.**

It is not acceptable to ask "what's X?", get an answer, rely on it for the rest of the session, and let it evaporate at session end. The whole point of the vault is that next session's Claude has the same context this session does. Persisting in-turn is the mechanism that makes that true.

The only exception: if the user explicitly says "this is one-off, don't save it" — respect that.

### When the user volunteers context unprompted

The same rule applies in reverse. If the user shares something the vault doesn't have, persist it via the same routing table — even if you didn't ask. The user should never have to say "remember that" or "save that for later." Your default is to capture anything novel.

### What NOT to do

- ❌ **Don't fabricate.** If you don't know and can't ask, say so. Write `Status unknown — needs investigation.` in the file rather than inventing plausible-sounding details.
- ❌ **Don't duplicate.** Pick the single most-specific destination from the routing table and link from related files. Don't paste the same content into both a Topic node and a DataContext file.
- ❌ **Don't bloat Topic nodes.** Topic nodes are pointers, not documents. If you find yourself writing a section longer than ~500 bytes, that section belongs in `Analysis/` or `DataContext/` with a link from the Topic.
- ❌ **Don't skip cross-linking.** A new Person file that no Topic node references is invisible to the lookup. Cross-link or accept that the work was wasted.
- ❌ **Don't ask without persisting.** This is the core failure mode — getting an answer and treating it as session-local. Always write before moving on.

---

## Automated Pipeline Overview

The `scheduled-tasks/` folder next to this file contains prompts for agents that keep the vault current:

- **Journal generation** (`nightly-journal.md`) — Aggregates daily activity into a journal entry
- **Weekly rollups** (`weekly-rollup.md`) — Summarizes the week's journal entries into a rollup file
- **Meeting debriefs** (`meeting-debriefs.md`) — Preps tomorrow's calendar
- **Daily kickoff** (`daily-kickoff.md`) — Morning accountability nudge

These are registered as scheduled Claude Code tasks via `/schedule` and run at the cron times defined in `config.yaml`.
