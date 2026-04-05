# Daily Kickoff

## Configuration

Read `config.yaml` from the work-automation repo to resolve all `{{variables}}` used in this prompt. Required config keys:
- `vault_path` — absolute path to Obsidian work vault
- `slack_user_id` — your Slack member ID
- `slack_dm_channel` — your Slack DM channel ID (for self-messages)
- `timezone` — your IANA timezone
- `work_automation_repo` — path to your work-automation repo

Check for task-override files matching `kickoff-*` in `{{work_automation_repo}}/task-overrides/` and append their instructions. These may include additional context-gathering steps (e.g., Slack screenshot parsing, Jira sync) that run between Step 0.5 and Step 1.

## Context

This is an automated task running without user interaction. Execute autonomously — make reasonable choices and note them in your output. Only take "write" actions this task explicitly asks for.

This is the daily work accountability check. The job is to surface what actually needs attention TODAY — not pad out a status report. Shorter is better. The user wants signal, not noise.

## Steps

### Step 0 — Load Context from Obsidian Vault

This is your PRIMARY and usually ONLY data source. The nightly journal task (runs in the evening) already synthesizes Granola meetings, Slack activity, Google Calendar, and Claude session logs into the vault. By morning, the vault has everything you need.

Locate the vault at `{{vault_path}}`. If the vault is not accessible, send a Slack DM saying the kickoff couldn't run because the vault wasn't found, and stop.

Read these files to orient yourself:
- TODO.md — active work items and backlog
- The 3 most recent files in Journal/ — recent daily logs (these contain meeting summaries, action items, commitments, and open items already extracted from Granola transcripts)
- List Projects/ and skim any recently modified project files

### Step 0.5 — Read Feedback from Yesterday's Kickoff Thread

Before building today's message, check for replies to the previous kickoff. This is how the user tells you what's done, what to deprioritize, and what they're actively working on.

1. Read the DM channel (channel ID: {{slack_dm_channel}}) using slack_read_channel — look at the most recent messages to find yesterday's kickoff (it starts with "*Daily Kickoff —").
2. If found, read the thread on that message using slack_read_thread with the message's timestamp.
3. Parse replies for status updates. Look for patterns like:
   - **Done / completed**: "done", "finished", "sent", "replied", "handled", "took care of", "closed", "shipped" — Remove these items from today's kickoff entirely.
   - **Not a priority / defer**: "not a priority", "deprioritize", "backburner", "skip", "ignore", "not now", "later", "park this" — Do NOT surface these items unless they become urgent (approaching a hard deadline). If you omit something due to deprioritization, add a one-liner at the bottom: "Suppressed: [item] (marked not a priority [date])"
   - **Working on it**: "working on", "in progress", "on it", "started", "picking up" — Move to Active Work section with a note that it was flagged as in-progress.
   - **Context / notes**: Any other replies — treat as context to include in today's message where relevant.
4. If there was no previous kickoff or no thread replies, proceed normally.

### Step 1 — Extract Commitments from Meetings

From the recent Journal entries (which include meeting summaries), scan for:
- **Action items agreed to** — phrases like "I'll do X", "I can get that to you", "let me take that", "I'll follow up", "I'll send", "I'll have that by", "I'll look into"
- **Deadlines committed to** — "by Friday", "by end of week", "by next Tuesday", "tomorrow", any specific date
- **Promises or offers** — "I'll loop in", "I'll set up a meeting", "I'll share that", "I'll pull the data"

Cross-reference against TODO.md to see if these are already tracked. Also cross-reference against thread feedback — if something was marked done, don't surface it again.

### Step 2 — Review In-Progress and Waiting Items

From TODO.md and recent Journal entries, identify:
- Tasks marked as in-progress or active
- Items that are blocked or waiting on something
- Any projects with unclear next steps

### Step 3 — Check for Approaching Deadlines (Next 48 Hours)

Look across TODO.md, Journal entries, and the commitments from Step 1 for anything due within the next 48 hours. Flag these prominently.

Also check Google Calendar (gcal_list_events) for the next 48 hours — meetings that require deliverables or prep. This is the ONE live API call worth making since the calendar is real-time.

### Step 4 — Flag Idle Items

Identify anything in TODO.md or recent Journal entries that was mentioned 3+ days ago but hasn't shown progress since. These are things slipping through the cracks.

EXCEPTION: Do not flag items explicitly deprioritized in a kickoff thread reply. Those go in the Suppressed line instead.

### Step 5 — Surface Follow-Up Needs

From Journal entries and TODO.md, find items where the user is waiting on someone else. Look for items tagged as "waiting on" someone or where a question was asked and a response is pending.

## Output — Slack DM

Send a single Slack message to the user (user_id: {{slack_user_id}}) with the following format. Be concise and direct. Skip any section that has nothing to report.

```
*Daily Kickoff — [Today's Date]*

[Sections from task-overrides, if any — e.g., Jira status updates]

*Commitments from Meetings*
[List each commitment: what, to whom, deadline if any. Bold anything overdue or due today.]

*Due in Next 48 Hours*
[Items with approaching deadlines]

*Active Work*
[Brief status on in-progress items — only mention if there's something actionable]

*Going Stale*
[Items idle 3+ days that need attention]

*Waiting On Others*
[Follow-ups needed — who owes what]

*Suppressed:* [items marked as not-a-priority, with date] (only include this line if there are suppressed items)
```

If a section is empty, omit it entirely. If everything looks clear, just say:
"*Daily Kickoff — [Date]* — Nothing urgent. All tracked items are on schedule."

Do NOT pad the message. Shorter is better. Signal, not noise.
