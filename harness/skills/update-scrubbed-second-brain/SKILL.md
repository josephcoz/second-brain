---
name: update-scrubbed-second-brain
description: >
  Publish a SCRUBBED, shareable copy of the Work second brain to Google Drive,
  diffed against what's already there — for the team covering during {{user}}'s leave.
  Scope is KNOWLEDGE ONLY (Topics/DataContext/Analysis/Projects/People); Journal,
  Meetings, Kickoffs, Memory are excluded. It scope-filters, runs a regex pre-pass
  AND an LLM judgment pass to redact comp/OTE, opinions-on-people, and personal
  info (redact spans in place; exclude whole episodic/comp files), builds a
  git-backed staging tree you review, then syncs to Drive as Google Docs. Runs
  NON-DESTRUCTIVELY and is REVIEW-GATED — nothing uploads until {{user}} approves. Use
  when {{user}} says "/update-scrubbed-second-brain", "update the scrubbed brain",
  "sync the scrubbed second brain", "scrub and share the vault". Modes: default
  (full), --report-only (audit, no build/upload), --since <ref> (incremental).
allowed-tools: Bash, Read, Write, Glob, Grep, Task
---

# update-scrubbed-second-brain — Agent Skill

Produces a redacted, shareable mirror of the Work vault's *knowledge* and pushes
it to a Google Drive folder for {{user}}'s leave-coverage team. Mirrors `/dream`'s
staged, non-destructive, review-before-adopt pattern — except "adopt" here means
"publish to Drive", and that step is gated on {{user}}'s explicit approval.

**Why this is careful:** the vault holds per-rep compensation and (rarely, in
scope) candid opinions on people. Regex alone is NOT safe — it redacts a line
that says "OTE" but misses the roster table beneath it. So the safety model is
two layers: an **LLM judgment pass** that reads each file, plus a **human review
gate** before anything leaves the machine. Never skip either.

Files this skill drives (all already built):
- `{{work_automation_repo}}/scrub-config.toml` — the sensitivity ruleset
  (scope allowlist + tiered regex + per-item exclusions). Single source of truth.
- `{{work_automation_repo}}/scripts/scrub_vault.py` — `--report-only`
  (audit) and `--apply --decisions <file>` (build staging tree + git commit).
- `{{work_automation_repo}}/scripts/sync_scrubbed_to_drive.py` — manifest
  diff → create/update/trash Google Docs, wiki-link → Doc hyperlink rewrite.
- Staging dir `{{work_vault}}-scrubbed/` — git-backed; `vault/` is the
  scrubbed tree, plus `Scrub-Report.md`, `scrub-decisions.json`, `.gdoc-manifest.json`.

---

## Step 0 — Context & guards

1. Confirm `CLAUDE_CONTEXT=work` (this skill is work-only). Vault `{{work_vault}}`.
2. `cd {{work_automation_repo}}`. Confirm `scrub-config.toml` and both scripts exist.
3. Parse args: `--report-only` (stop after the audit), `--since <git-ref|date>`
   (only re-judge vault files changed since then — the incremental path), default = full.
4. The vault should be committed-ish (it's git-backed); not required, but note any
   uncommitted changes so the audit reflects current content.

## Step 1 — Audit (regex pre-pass)

Run `python3 scripts/scrub_vault.py --report-only`. Read
`{{work_vault}}-scrubbed/Scrub-Report.md` and `scrub-candidates.json`.
This gives the in-scope file list, the heat ranking, and per-line candidate hits.
If `--report-only`, print the summary and STOP here.

## Step 2 — LLM judgment pass (the core safety layer)

Decide which files to judge:
- **Full run:** every in-scope file. Prioritize the flagged/heat-ranked ones, but
  also sample "clean" files — regex misses keyword-less sensitivity (e.g.
  `reference/josh-smith-rehire-sfdc.md`, roster tables with no "OTE" header on the
  data rows).
- **`--since` run:** only files changed in the vault since the ref
  (`git -C {{work_vault}} diff --name-only <ref>`), intersected with scope.
  Reuse prior `scrub-decisions.json` entries for unchanged files.

Spawn **parallel sub-agents in batches** (Task tool, ~15–25 files each). Give each
batch the file paths + the rubric below; have each return STRICT JSON it appends to
the decisions set. Rubric (audience = internal coverers; real names/customers/pricing
are fine — do NOT redact those):

- **Redact (span):** any individual's compensation (OTE / salary / OTC / paymix /
  base / variable / bonus / equity) — including in tables/rosters, redact every such
  cell or row; comp-PLAN design dollar figures (keep the reasoning); {{user}}'s
  leave/paternity references; any candid assessment of a named person ("top rep",
  "high performer", "being considered for X", "50% attainment", "underperforming",
  "not a fit"). Quote the EXACT substring to redact so the apply step is surgical.
- **Exclude (whole file):** files that are fundamentally per-rep pay or a candid
  personnel/1:1/handoff artifact that slipped scope. (Config already excludes
  `quota-master-audits/`, `Leave Handoff 2026/`, `working-with-joe/`.)
- **Keep:** everything else — the reusable knowledge.
- **When unsure → choose the safer action (redact/exclude) and flag it** for {{user}}.

Decisions JSON shape (merge all batches into one file at `scrub-decisions.json`):
```json
{ "files": {
    "Projects/2026-03-17 Pipeline Model Defensibility Analysis.md": {
      "action": "redact",
      "redactions": [
        {"line": 125, "match": "$100K | $107,500 | Ramping (hired Jan 1)", "reason": "rep comp"},
        {"line": 194, "match": "underperforming by ~$240K annual", "reason": "opinion on person"}
      ]
    },
    "DataContext/reference/josh-smith-rehire-sfdc.md": {"action": "exclude", "reason": "personnel"}
}}
```
(`line` is 1-based; `match` is replaced with `[redacted — reason]`. Omit `match` to
blank the whole line; `line: 0` matches the substring anywhere in the file.)

## Step 3 — Apply (build the staging tree)

`python3 scripts/scrub_vault.py --apply --decisions {{work_vault}}-scrubbed/scrub-decisions.json`

This copies in-scope, non-excluded files to `{{work_vault}}-scrubbed/vault/`,
applies redactions, flattens wiki-links that point at excluded/out-of-scope notes,
and commits the result (the staging git history is the audit trail of what shipped).

## Step 4 — REVIEW GATE (do not skip)

1. **Self-check leak grep** on the staged tree — a BACKSTOP, not proof (a clean
   grep does NOT mean the tree is safe — the LLM pass is what catches keyword-less
   leaks like roster tables). Include evaluative phrases, not just comp keywords:
   ```bash
   cd {{work_vault}}-scrubbed/vault
   grep -rniE '\bOTE\b|\bsalary\b|\bpaymix\b|on-target (comm|earn)' . | grep -v 'redacted'
   grep -rniE 'underperform|top rep|high performer|attainment|being considered for|not a (good )?fit|managing out' . | grep -v 'redacted'
   # roster heuristic: person-name rows carrying $NNK comp figures
   grep -rnE '\| *[A-Z][a-z]+ [A-Z][a-z]+ *\|.*\$[0-9]+[Kk]' . | grep -v 'redacted'
   ```
   Any real comp/opinion hit → fix the decisions file and re-run Step 3.
2. Show {{user}}: the apply summary, `git -C {{work_vault}}-scrubbed show --stat HEAD`,
   and the list of excluded files + a few sample redactions from `scrub-decisions.json`.
   Call out anything in the "unsure/flagged" bucket.
3. **Wait for {{user}}'s explicit approval to publish.** Nothing has left the machine yet.

## Step 5 — Publish to Drive (only after approval)

1. Dry-run: `python3 scripts/sync_scrubbed_to_drive.py --dry-run` (shows create/update/trash counts).
2. If first run, confirm `[drive].share_with` is set in `scrub-config.toml` (the
   coverage group). Then live: `python3 scripts/sync_scrubbed_to_drive.py`.
3. Report the folder URL, and created/updated/trashed counts. On the first run,
   confirm sharing was applied to the coverage group only.

## Step 6 — Record

Append a one-line entry to today's `Journal/YYYY-MM-DD.md` (`## Learned:` or a run
log): files shared, redactions, excluded, Drive folder URL, staging commit hash.
Update `Projects/Phase 2 — Second Brain Documentation & Scrub.md` status.

---

## Rules / safety

- **Never upload a `--auto` baseline.** `scrub_vault.py --auto` only whole-line-redacts
  regex hits and leaks roster tables — it exists for engine testing, not publishing.
- **Never publish without {{user}}'s explicit approval** of the review gate (Step 4).
- **Default to over-redaction.** If a file is borderline, exclude or redact and flag it.
- **Tune the ruleset, not one-off hacks:** systematic false positives/negatives go into
  `scrub-config.toml`; re-run the audit.
- **Stay in scope:** never widen beyond the `include_dirs` allowlist without {{user}}'s say —
  Journal/Meetings hold the candid 1:1 content and must remain excluded.
- The staging repo and Drive manifest make every run a diff: changed files re-judged
  and re-uploaded, removed files trashed, unchanged files skipped.
