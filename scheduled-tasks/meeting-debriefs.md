# Meeting Debriefs

## Configuration

Read `config.yaml` from the work-automation repo to resolve all `{{variables}}` used in this prompt. Required config keys:
- `vault_path` — absolute path to Obsidian work vault
- `user_email` — your work email address (used to filter yourself out of attendee lists)
- `timezone` — your IANA timezone (e.g., `America/Denver`)
- `work_automation_repo` — path to your work-automation repo

Check for task-override files matching `debriefs-*` in `{{work_automation_repo}}/task-overrides/` and append their instructions after this prompt's steps.

## Context

This is an automated task running without user interaction. Execute autonomously — make reasonable choices and note them in your output. Only take "write" actions this task explicitly asks for.

This task builds personalized meeting debrief summaries for tomorrow's calendar events. It runs in the evening so the output is ready to review in the morning.

## Steps

### Step 1 — Get tomorrow's calendar events

Use `gcal_list_events` with `condenseEventDetails: false` and timezone `{{timezone}}`. Tomorrow = the day after today's date.

### Step 2 — Filter out events that don't need prep

Remove:
- All-day events (working location, OOO, holidays)
- Events with no attendees (personal blocks, lunch, focus time)
- Events with >8 individual attendees (skip group/DL emails when counting)
- Title contains (case-insensitive): "all hands", "all-hands", "town hall", "standup", "stand-up", "lunch", "social", "happy hour", "office hours", "company meeting"
- Events the user has declined

### Step 3 — Research each remaining meeting (in parallel)

For each meeting:

a. Look up each attendee (excluding yourself: {{user_email}}, and group emails) in Obsidian People files. The vault is at `{{vault_path}}` — look for People/, Meetings/, Journal/, Analysis/, Projects/, TODO.md there.

b. Read the 2-3 most recent meeting notes involving these people from Meetings/

c. Query Granola for recent meetings with these people

d. Search Slack (public) for recent messages from/about these people (last 2 weeks). Use `include_context: false` and `response_format: "concise"` to minimize tokens.

e. **CRITICAL: Check prior work on the topic.** Read the last 5-7 Journal entries, the Analysis/ folder, and the Projects/ folder. Search for keywords related to the meeting title, topic, and attendees. If a Hex dashboard was already built, an analysis completed, or a deliverable already shared related to this meeting's topic, that MUST be reflected in the debrief. The journal is ground truth — TODO.md is aspirational and often stale.

f. Read TODO.md for items related to attendees or meeting topic. Cross-reference against journal findings — if a TODO says "build X" but the journal shows it was already built and shared, do NOT present it as unfinished. Instead note what's actually still open.

### Step 4 — Output the full debrief inline

This is what the user sees when they open the completed run notification in the morning. Do NOT create Notion pages, do NOT write to calendar event descriptions. Everything goes in this output.

## Output Format

```
## Tomorrow's Meeting Prep — [Date]

---

### [Meeting Title] — [time] {{timezone}}
**With:** [attendee names and what they do]

#### What You Need to Know
- [2-4 concise bullet points: what was last discussed, work already completed on the topic (be specific), any surprises or stale commitments]

#### Still Open
- [Genuinely unfinished items after cross-referencing journals. Frame as questions where appropriate.]

#### Meeting Docs
- [Links to Google Docs/attachments on the calendar event. Skip section if none.]

#### Prep Tasks for Claude
- [1-3 concrete, executable tasks a fresh Claude Code session can run. Focus on data pulls/analysis. Include project names, Hex notebooks, Salesforce objects. If the main deliverable was already built, focus on extending it.]

---

(repeat for each meeting)
```

## Quality Principles

- Be specific — "You built the MSA Efficacy Analysis Hex app on March 13 and shared WIP with Angel" not "You've been working on MSA analysis"
- Journal is ground truth, TODO is aspirational. When they conflict, trust the journal.
- Prep tasks should lean toward data/analysis (primary prep need)
- If no meetings pass the filter, just output "No prep-worthy meetings tomorrow" and stop
- Keep tool calls minimal — batch research in parallel, use concise Slack options, skip sources that won't add value
