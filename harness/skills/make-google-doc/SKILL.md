---
name: make-google-doc
description: >
  Convert an existing markdown file into a Google Doc in {{user}}'s My Drive. Use
  when {{user}} says "share this as a gdoc", "make a Google Doc out of this",
  "convert this writeup to a doc", "upload this to Drive as a doc", or similar.
  Default workflow: {{user}} writes a .md file (in whatever working folder he's in),
  then asks for a Doc — this skill pipes the .md through the gdoc-create
  helper. The default destination is My Drive root (no folder).
allowed-tools: Bash, Read
---

# make-google-doc — Agent Skill

{{user}}'s default writeup format is a local `.md` file. When he wants to share that
writeup with someone, he asks to "make it a Google Doc". This skill is the
consistent, low-token workflow for that conversion.

## Workflow

1. **Identify the source `.md` file.** {{user}} will usually point at it ("the
   writeup I just made", a path, "the file in this directory"). If it's
   ambiguous and there's more than one candidate `.md` in the conversation
   context, ask before guessing.

2. **Pick the title.** Default rule: use the first H1 in the file (`# Title`),
   stripped of leading `#` and whitespace. If there's no H1, fall back to the
   filename without `.md`, with hyphens/underscores converted to spaces.
   {{user}} can override by stating a title explicitly.

3. **Pick the folder.** Default: **none** (lands in {{user}}'s My Drive root). Only
   pass `--folder` when {{user}} explicitly names one (e.g. "put it in the X
   folder"). Don't infer.

4. **Run the helper.** Read the `.md` via `cat` and pipe to the script:

   ```bash
   cat <path-to-md> \
     | python3 {{work_automation_repo}}/scripts/gdoc-create.py \
         --title "<title>"
   ```

   Add `--folder "<folder name>"` only when {{user}} named one.

5. **Return the URL.** The script prints a single JSON line:
   `{"id":"...","url":"https://docs.google.com/document/d/.../edit"}`.
   Surface the `url` to {{user}} as a clickable link. Don't echo the JSON.

## Notes

- **Don't pre-process the markdown.** Drive's import handles headings,
  bullets, tables, code blocks, links, and bold/italic correctly. Sending raw
  `.md` produces a cleanly-formatted Doc.
- **Auth.** Uses {{user}}'s user OAuth at `~/.config/gspread/authorized_user.json`
  (full Drive scope). Doc lands in his personal My Drive — not a Shared
  Drive, not a service account drive.
- **The `.md` stays put.** This skill only publishes; it doesn't move,
  rename, or delete the source file.
- **Don't use this for recurring/programmatic Drive workflows** that need to
  land in a Shared Drive (those use the RevOps service account — see
  memory `reference_google_drive_slides.md`).
- **Permission prompt on first run:** the bash command may need user approval
  the first time it runs from a new working directory. That's expected.
