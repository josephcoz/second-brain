---
name: document
description: >
  Capture current-session state into a canonical handoff so a future
  Claude Code session can resume without re-asking {{user}}. Use when {{user}}
  says "document this session", "save context for next session",
  "handoff this", "before we wrap, write down where we are", "/document",
  or similar. Default target is the active plan file's NEXT SESSION
  block; falls back to NEXT_SESSION.md in the project working dir if no
  plan applies; vault Journal entry is opt-in for decision/pivot
  sessions only. Durable facts surfaced this session (people, topics,
  data semantics, preferences) are persisted into the vault graph (the
  memory store) via the routing table.
allowed-tools: Bash, Read, Edit, Write, Glob, Grep
---

# document — Agent Skill

{{user}}'s actually-used persistence pattern across sessions is **tri-layer**:

1. **`~/.claude/plans/<slug>.md`** — narrative blueprint, kept live.
   The memory entry `project_pricing_refactor` literally says
   "read plan's NEXT SESSION block first." This is the navigation
   layer most projects already use.
2. **`runs/YYYY-MM-DD/`** dirs inside the project repo — executable
   state (CSVs, JSON metadata, audit logs). Self-archiving. These are
   immutable artifacts; the skill never edits inside them.
3. **Vault Journal entries** — context pivots and decision dates. Sparse
   on execution detail; mostly handled by the weekly-rollup pipeline,
   not per-session.

There is no pre-existing `NEXT_SESSION.md` / `STATE.md` convention; the
plan file plays that role when one exists.

## Workflow

Walk this decision tree in order. Always tell {{user}} in one short sentence
which layer(s) you're about to touch *before* writing.

### 1. Look for an active plan file

```bash
ls -lt ~/.claude/plans/*.md | head -10
```

Then narrow to plans that match this session's work. Two signals:

- **Recency** — `stat -f "%m %N" ~/.claude/plans/*.md` and prefer plans
  touched in the last ~7 days.
- **Topic match** — `grep -l <keywords> ~/.claude/plans/*.md` where
  keywords are file paths edited this session, project slugs, or
  distinctive identifiers (e.g., a Jira key, a Hex project ID, a rep
  name).

Resolve to one of:

- **0 plans match** → no plan applies. Go to step 2.
- **1 plan matches** → that's the target. Confirm:
  *"Updating the NEXT SESSION block in `<slug>.md`. Anything else to
  capture?"*
- **≥2 plans match** → list them with a 1-line summary each and ask
  which (or both).

### 2. Find the project working dir (fallback when no plan applies)

Identify where this session's edits landed. Heuristics:

- Most-edited directory across `Edit` / `Write` tool calls this session.
- `--add-dir` roots from the session-start hook are eligible candidates
  (see `~/.claude/CLAUDE.md`).
- If the dir contains `runs/<YYYY-MM-DD>/` or `runs/<run-id>/`, write
  the handoff **next to** the run dir (at the project root), not
  inside it.
- If no edits happened this session (pure exploration / Q&A), skip
  this step — there's nothing material to hand off; tell {{user}} so and
  stop.

**Shared work repo guard** — if the candidate dir is inside
`work-automation`, `analyses`, or `second-brain`, ask before writing
(per the [[feedback_work_repos]] memory).

Filename: `NEXT_SESSION.md` at the project root.

### 3. Vault Journal — opt-in only

Default behavior is **no vault write**. Only surface a one-line offer
when the session contained one of these markers:

- A locked decision ("let's go with X because Y").
- A stakeholder-visible pivot ("Angel pivoted from upsell-packages →
  MSA renewals").
- A blocked-on-async resolution (someone replied, you can move).
- A first-time discovery worth dating (new SFDC field constraint,
  Hex behavior, contract structure detail).

Phrasing: *"This looked journal-worthy — `<one-line summary>`. Add a
short Journal entry?"* If {{user}} confirms, write to
`$CLAUDE_CONTEXT`-derived vault Journal folder:

- `CLAUDE_CONTEXT=work` (or unset) → `{{work_vault}}/Journal/`
- `CLAUDE_CONTEXT=personal` → `{{personal_vault}}/Journal/`

Honor the vault routing rule in `~/.claude/CLAUDE.md`: **never
cross-write vaults.** If unsure of context, ask.

Filename: `YYYY-MM-DD <one-line summary>.md`. Single paragraph plus a
link back to the plan file / handoff path. Don't duplicate the full
state block — the plan file is the source of truth.

### 4. Persist durable facts to the memory store (the vault graph)

If the session produced **durable cross-session knowledge** — a person's
role, a workstream/project worth referencing, a data semantic, a decision,
or a working preference — route it into the vault graph in the same turn
(this is the Learning-Loop closer; the vault is now Claude's memory store):

- Person → `<vault>/People/Full Name.md`
- Workstream / project → `<vault>/Topics/Topic Name.md` (lightweight hub)
- Data semantics / schema / system → `<vault>/DataContext/kebab-name.md`
- Working preference about how to help {{user}} → `<vault>/DataContext/working-with-joe/<theme>.md`
- One-off finding / decision → `## Learned:` append to `<vault>/Journal/YYYY-MM-DD.md`

`<vault>` is `{{work_vault}}` (work) or `{{personal_vault}}`
(personal) per `CLAUDE_CONTEXT`. Cross-link the new note from related notes
(an unlinked file is invisible to lookup). Do NOT reorganize or dedup existing
notes — that's `/dream`. This is distinct from the task-state handoff (steps
1–2): handoff is a *work bookmark*; this is *memory*.

## NEXT SESSION block format

Whether written into a plan file or a fresh `NEXT_SESSION.md`, use the
same six sections. Machine-readable bullets, not prose paragraphs
(per [[feedback_vault_audience]]).

```markdown
## NEXT SESSION — <YYYY-MM-DD> — <short summary>

**TL;DR**: <1–2 sentence summary of what this session accomplished>

**State**
- Done: <what shipped / merged / froze this session>
- In-flight: <what's mid-stream, with file paths>
- Blocked / waiting on: <async asks; owner + ask>

**Files touched**
- `<abs path>` — <what changed in 1 line>

**Key decisions**
- <decision> — <reasoning in one line>

**Next concrete actions** (do these first when resuming)
1. <action with file path or command>
2. ...

**Memory pointers**
- [[Topic / Person / DataContext note]] — why it's relevant (link to vault-graph notes, not `~/.claude` memory files)
```

### Placement rules in existing plan files

- {{user}}'s existing convention puts the block **at the top of the file**,
  immediately after the H1 title — `## ⏭️ NEXT SESSION — <summary>`
  with the emoji.
- If the plan already has a `## NEXT SESSION` (or `## ⏭️ NEXT SESSION`)
  heading: **replace the whole block** (heading + body, up to the next
  `## ` heading or `---` divider). Preserve the existing heading's
  emoji prefix if it had one.
- If the plan has no such heading: insert immediately after the H1
  title. Don't append at bottom — that's not where the next session
  will look.
- Never delete other plan sections (Context, Phase X, etc.).

### Fresh `NEXT_SESSION.md` format

When writing a standalone file at a project root, the file IS the
block — start with an H1 (`# NEXT SESSION — <YYYY-MM-DD> — <summary>`)
and use the same six sections. No surrounding context needed.

## What this skill does NOT do

- **Does not** consolidate, reorganize, dedup, or bulk-rewrite the
  memory store — that's `/dream`'s job. `/document` *writes* durable
  facts into the vault graph (see step 4) and may add a one-line pointer
  to the manifest, but it never restructures the graph or trims
  `MEMORY.md`. **`/document` writes; `/dream` cleans up.**
- **Does not** create new plan files. If no plan exists and {{user}} wants
  one, that's a separate `/plan` request. The fallback here is the
  project working dir, not a new plan.
- **Does not** write inside `runs/<...>/` directories — those are
  immutable artifacts. Handoff lives next to them, at the project
  root.
- **Does not** write to shared work repos (`work-automation`,
  `analyses`, `second-brain`) without per-session confirmation
  (per [[feedback_work_repos]]).
- **Does not** cross-write vaults (work session → Personal vault, or
  vice versa).

## Reporting back

After writing, return a single short summary to {{user}}:

> Wrote handoff to `<path>`. Next session resumes at: `<top next-action from the block>`.
> [Optional, only if applicable:] Journal entry: `<path>`.
> [Optional, only if applicable:] Persisted to memory: `<vault note path>` — `<one-line fact>`.

Keep it under 3 lines. No echoing of the block contents.
