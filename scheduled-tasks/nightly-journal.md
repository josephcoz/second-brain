# Nightly Journal

## Configuration

Read `config.yaml` from the work-automation repo to resolve all `{{variables}}` used in this prompt. Required config keys:
- `vault_path` — absolute path to Obsidian work vault (e.g., `~/obsidian-vaults/Work`)
- `slack_user_id` — your Slack member ID
- `log_dir` — directory for task logs (e.g., `~/.local/share/second-brain/logs`)
- `work_automation_repo` — path to your work-automation repo

Check for task-override files matching `journal-*` in `{{work_automation_repo}}/task-overrides/` and append their instructions after this prompt's steps.

## Context

This is an automated task running without user interaction. Execute autonomously — make reasonable choices and note them in your output. Only take "write" actions this task explicitly asks for.

This task is the nightly pipeline: export Granola meetings, enrich them with Google Drive transcripts, then write the daily work journal to the Obsidian vault. It runs in the evening after the workday ends.

## Objective

1. Export any new/updated Granola meetings to the Obsidian vault (Step 0 — via Granola MCP connector)
2. Enrich meeting files with Google Meet transcripts from Google Drive (Step 1 — primary content source)
3. Gather context about everything worked on today (WORK ONLY) and write a structured journal entry

## CRITICAL: Work content only

Only log work-related activity. Do NOT log personal topics — the user may use Claude for personal research and none of that belongs in this vault. When scanning Claude sessions, skip any conversation that is clearly personal.

## Step 0: Granola Meeting Export (RUN THIS FIRST)

Before gathering journal data, export new Granola meetings to Obsidian using the **Granola MCP connector**.

### 0a. Fetch today's meetings from Granola

1. Call `list_meetings` with `time_range: "this_week"` to get a list of recent meetings.
2. Filter the results to meetings from **today** (by date in the title or metadata).
3. For each meeting from today, call `get_meetings` with the meeting IDs to retrieve full details (attendees, AI-generated summary, notes).

### 0b. Check what already exists in Obsidian

```bash
MEETINGS_DIR={{vault_path}}/Meetings
PEOPLE_DIR={{vault_path}}/People
COMPANIES_DIR={{vault_path}}/Meetings/_Companies
today=$(date +%Y-%m-%d)

# Ensure directories exist
mkdir -p "$MEETINGS_DIR" "$COMPANIES_DIR" "$PEOPLE_DIR"

# List existing meeting files for today
ls "$MEETINGS_DIR"/${today}*.md 2>/dev/null
```

For each Granola meeting, build the expected filename as `{date} {sanitized_title}.md`. If the file already exists AND has real content (not the placeholder `*AI summary not yet available*`), skip it. If it exists but only has the placeholder, update it with the Granola summary.

### 0c. Write meeting files to Obsidian

For each new or updated meeting, use a Python script to write the markdown file. The script handles filename sanitization and index updates:

```python
import os, re

VAULT_DIR = os.environ.get("VAULT_PATH", os.path.expanduser("{{vault_path}}"))
MEETINGS_DIR = os.path.join(VAULT_DIR, "Meetings")
COMPANIES_DIR = os.path.join(MEETINGS_DIR, "_Companies")
PEOPLE_DIR = os.path.join(VAULT_DIR, "People")

def sanitize_filename(title):
    clean = re.sub(r'[<>:"/\\|?*]', '', title)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:120].rsplit(' ', 1)[0] if len(clean) > 120 else clean

def write_meeting(date, title, attendees, notes):
    """
    attendees: list of dicts with keys: name, email (optional), company (optional)
    notes: string — the AI-generated summary from Granola
    """
    filename = f"{date} {sanitize_filename(title)}"
    att_links = ", ".join(f"[[{a['name']}]]" for a in attendees)
    companies = list(set(a.get("company", "") for a in attendees if a.get("company")))
    comp_links = ", ".join(f"[[{c}]]" for c in companies)

    lines = ["---", f"date: {date}", f"title: {title}", f"attendees: [{att_links}]",
             f"companies: [{comp_links}]", "source: granola", "---", "",
             f"# {title}", "", "## Attendees"]
    for a in attendees:
        email_part = f" ({a['email']})" if a.get('email') else ""
        lines.append(f"- [[{a['name']}]]{email_part}")
    lines.extend(["", "## Notes",
                   notes if notes else "*AI summary not yet available — will be updated on next export.*", ""])

    with open(os.path.join(MEETINGS_DIR, filename + ".md"), "w") as f:
        f.write("\n".join(lines))

    # Update People/ index
    for att in attendees:
        pfile = os.path.join(PEOPLE_DIR, f"{sanitize_filename(att['name'])}.md")
        if os.path.exists(pfile):
            with open(pfile) as f: pcontent = f.read()
            if filename not in pcontent:
                pcontent = pcontent.replace("## Meetings\n", f"## Meetings\n- [[{filename}]]\n")
                with open(pfile, "w") as f: f.write(pcontent)
        else:
            plines = []
            if att.get('email'): plines.extend(["---", f"email: {att['email']}", "---", ""])
            plines.extend([f"# {att['name']}", "", "## Meetings", f"- [[{filename}]]", ""])
            with open(pfile, "w") as f: f.write("\n".join(plines))

    # Update _Companies/ index
    for comp in companies:
        if not comp: continue
        cfile = os.path.join(COMPANIES_DIR, f"{sanitize_filename(comp)}.md")
        if os.path.exists(cfile):
            with open(cfile) as f: ccontent = f.read()
            if filename not in ccontent:
                ccontent = ccontent.replace("## Meetings\n", f"## Meetings\n- [[{filename}]]\n")
                with open(cfile, "w") as f: f.write(ccontent)
        else:
            with open(cfile, "w") as f:
                f.write("\n".join([f"# {comp}", "", "## Meetings", f"- [[{filename}]]", ""]))

    return filename
```

### 0d. Map Granola data to the write_meeting function

For each meeting returned by `get_meetings`:

1. **Date**: Extract from the meeting's start time or creation date. Format as `YYYY-MM-DD`.
2. **Title**: Use the meeting title from Granola.
3. **Attendees**: Build the list from Granola's attendee data. Each attendee should have `name` and optionally `email` and `company`. If company info isn't available from Granola, leave it empty.
4. **Notes**: Use the AI-generated summary from `get_meetings`. This is Granola's processed meeting summary.

Call `write_meeting(date, title, attendees, notes)` for each meeting.

Log results:
```python
from datetime import datetime

LOG_DIR = os.environ.get("LOG_DIR", os.path.expanduser("{{log_dir}}"))
LOG_FILE = os.path.join(LOG_DIR, "granola-export.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(LOG_FILE, "a") as f:
    f.write(f"[{ts}] Granola MCP export: {exported} new, {updated} updated, {skipped} unchanged\n")
```

After the export completes, proceed to Step 1 to enrich meetings with Google Drive transcripts.

## Step 1: Google Drive Transcript Enrichment (PRIMARY content source)

Google Meet auto-saves transcripts as Google Docs in Drive. These are the **primary** content source for meeting files — Granola notes are the **backup** (only used when no Drive transcript exists).

Transcript titles in Drive follow this format: `{Meeting Title} - {YYYY/MM/DD HH:MM TZ} - Transcript`

### 1a. Find today's meetings that need content

First, identify meeting files from today that don't already have a transcript:

```bash
today=$(date +%Y-%m-%d)
find {{vault_path}}/Meetings/ -name "${today}*.md" -type f 2>/dev/null
```

For each meeting file found, check if it already has `transcript_source: google_meet` in its frontmatter. If it does, skip it — it's already enriched.

### 1b. Search Google Drive for matching transcripts

Use the `google_drive_search` MCP tool to find transcripts from today:

```
api_query: name contains 'Transcript' and mimeType = 'application/vnd.google-apps.document' and modifiedTime > '{today}T00:00:00'
```

Where `{today}` is today's date in `YYYY-MM-DD` format.

If that returns no results, try a broader search:
```
api_query: fullText contains 'Transcript' and mimeType = 'application/vnd.google-apps.document' and modifiedTime > '{today}T00:00:00'
```

### 1c. Match transcripts to meeting files

For each Drive transcript found, match it to a meeting file using this logic:

1. **Parse the transcript title**: Extract the meeting name and date from the Drive doc title. The format is `{Meeting Title} - {YYYY/MM/DD HH:MM TZ} - Transcript`. Split on ` - ` and take the first part as the meeting title, parse the date from the second part.

2. **Match by date + title overlap**: Compare the transcript's meeting title against today's meeting filenames. Use word overlap — normalize both titles to lowercase, split into words, and check if at least 50% of the shorter title's words appear in the longer one.

3. **Greedy assignment**: Sort matches by overlap score descending. Each transcript and each meeting file can only be matched once.

### 1d. Fetch and write transcripts

For each matched pair:

1. Use `google_drive_fetch` MCP tool to retrieve the full transcript content using the document ID.

2. Update the meeting file:
   - Add `transcript_source: google_meet` to the YAML frontmatter
   - Add `transcript_doc_id: {document_id}` to the YAML frontmatter
   - Replace the `## Notes` section with `## Transcript` containing the full transcript text
   - If the file had Granola notes content (not the placeholder), preserve it as a `## Granola Notes` section below the transcript

3. Log the result: `log(f"ENRICHED: {filename} with Drive transcript {doc_id}")`

### 1e. Fallback: Granola notes

For any meeting files from today that did NOT get a Drive transcript match:
- If the Granola export already wrote notes content (not the "*AI summary not yet available*" placeholder), leave it as-is — that's the backup content.
- If there's no content from either source, leave the placeholder. It may get enriched on the next run.

### Example of enriched meeting file format:
```markdown
---
date: 2026-03-12
title: Weekly Sync
attendees: [[[Person A]], [[Person B]]]
companies: [[[Company X]]]
source: granola
transcript_source: google_meet
transcript_doc_id: 1abc123def456
---

# Weekly Sync

## Attendees
- [[Person A]] (persona@company.com)
- [[Person B]] (personb@company.com)

## Transcript
Person A: Hello. How you doing?
Person B: Hi, good morning...
```

After Step 1 completes, proceed to the journal data gathering below.

## Data Sources — Check All of These (in priority order)

### 1. Cowork Session JSONL Files (legacy source)
Cowork sessions are stored as JSONL files on disk. To find today's sessions:

```bash
find ~/Library/Application\ Support/Claude/local-agent-mode-sessions -name "*.jsonl" -path "*projects*" -mtime 0 -type f
```

Each JSONL file contains one JSON object per line. Parse it like this:
```python
import json
from datetime import datetime, date

today = date.today().isoformat()
with open(jsonl_path) as f:
    for line in f:
        entry = json.loads(line)
        ts = entry.get('timestamp', '')
        if not ts.startswith(today):
            continue
        msg = entry.get('message', {})
        role = msg.get('role', '')
        if role == 'user':
            content = msg.get('content', '')
            if isinstance(content, str):
                print(f"[USER] {content[:200]}")
        elif role == 'assistant':
            content = msg.get('content', [])
            if isinstance(content, list):
                for block in content:
                    if block.get('type') == 'text':
                        print(f"[ASSISTANT] {block['text'][:200]}")
```

Extract the key topics, decisions, and work done. Skip thinking blocks (type: "thinking"). Focus on user requests and assistant summaries. Filter out personal topics.

### 2. Claude Code Session JSONL Files
Same format, stored in `~/.claude/projects/`. Find today's:
```bash
find ~/.claude/projects -name "*.jsonl" -mtime 0 -type f 2>/dev/null
```
Parse identically to Cowork sessions.

### 3. Meetings (exported in Step 0, enriched in Step 1)
Steps 0 and 1 already exported meetings and enriched them with Google Drive transcripts. Check for meetings from today:
```bash
find {{vault_path}}/Meetings/ -name "$(date +%Y-%m-%d)*.md" -type f 2>/dev/null
```
For each meeting file from today, read it and include a summary in the journal entry under a "## Meetings" section. Include the meeting title, attendees, and key topics discussed. If the file has a `## Transcript` section, summarize the key discussion points from it. If it only has Granola notes or is still empty, note that.

Also check the export log for any errors:
```bash
tail -20 {{log_dir}}/granola-export.log 2>/dev/null
```

### 4. Slack Activity (targeted)
Search Slack using MCP tools for three categories ONLY:
- **Messages the user sent today:** `from:<@{{slack_user_id}}> after:YYYY-MM-DD before:YYYY-MM-DD+1`
- **DMs and group DMs to the user:** search in DMs/group DMs for today's date
- **Channel messages where the user is tagged:** `<@{{slack_user_id}}> after:YYYY-MM-DD before:YYYY-MM-DD+1`

Do NOT include random channel messages the user didn't write or wasn't tagged in. Summarize themes — do NOT reproduce full messages.

### 5. File Changes in Obsidian Work Vault
Run: `find {{vault_path}}/ -name "*.md" -mtime 0 -type f` to find files modified today.
- New meetings in Meetings/ = meetings attended
- Changes to Analysis/, DataContext/, Questions-Log.md = analytical work done

### 6. Daily Notes (manual supplement)
Check `{{log_dir}}/daily-notes/YYYY-MM-DD.md` for any manually logged notes from the day.

## Output Format

Write the journal entry to: `{{vault_path}}/Journal/YYYY-MM-DD.md` (use today's date).

**If the file already exists**, append a horizontal rule (`---`) and a new section header (`## Evening Summary (auto-generated)`) below the existing content. Do NOT overwrite manual notes.

**If the file does not exist**, create it fresh.

### Wiki Link Convention — Link to Existing Topics

The vault has topic hub nodes in `Topics/`. When writing the journal, use `[[wiki links]]` to reference **existing** topic nodes wherever a workstream is clearly relevant. This strengthens the Obsidian graph view over time.

First, check what topic nodes exist:
```bash
ls {{vault_path}}/Topics/
```

Then, when writing about a workstream that matches a topic node, link to it naturally in the text. For example, write "Worked on [[Commission]] calculations" instead of just "Worked on commission calculations." Use the `[[Topic Name|display text]]` syntax when the topic name doesn't fit grammatically: `[[Pricing and Packaging|pricing]] discussions`.

**Important:** Only link to topics that already exist in `Topics/`. Do NOT create new topic nodes — that's the weekly rollup's job. If a workstream doesn't have a topic node yet, just write it in plain text.

Follow this format (match the style of existing journal entries):

```markdown
# Session Notes — YYYY-MM-DD

## Summary
[1-3 sentence overview of what was worked on today]

---

## [Project/Topic Name]
- Key details, decisions, results
- hexVersionId if relevant
- Status updates

## [Another Project/Topic]
...

## Meetings
- [Meeting title] — attendees, key topics/decisions (from Granola export)

## Slack Highlights
- Notable threads, decisions, or questions (summarized, not quoted)

## Open Items (Carried Forward)
- [ ] Any unfinished work or next steps identified today

---

## Related Topics
[[Topic 1]], [[Topic 2]], [[Topic 3]]

## Related Files
- Links to any files created or modified today
```

## Rules

- WORK CONTENT ONLY — no personal topics
- Be concise and factual — this is a reference log, not a narrative
- Include hexVersionIds when you know them
- If a source has no relevant content, skip that section entirely
- If there's very little work activity across all sources, write a short log noting it was a light day
- Never fabricate work that didn't happen — only log what you can verify from sources
- Use relative Obsidian vault paths in Related Files links (e.g., `Analysis/filename.md`)
- When summarizing Claude sessions, focus on WHAT was built/decided/analyzed, not the back-and-forth of the conversation
- Use `[[wiki links]]` when referencing people and existing topic nodes (see Wiki Link Convention above)
- Always end the journal with a `## Related Topics` section listing all topic nodes referenced in the entry
