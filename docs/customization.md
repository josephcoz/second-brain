# Customization Guide

How to adapt the second-brain system to your workflow.

## Adding New Data Sources to the Nightly Journal

The nightly journal task prompt (`scheduled-tasks/nightly-journal.md`) defines which sources the agent reads. To add a new source:

1. Add a new section to your `work-automation/scripts/tasks/nightly-journal.sh` data gathering script that checks for or collects the raw data.
2. Create a task override file in `work-automation/task-overrides/` (e.g., `journal-linear-sync.md`) that tells the agent how to process the new source.
3. The override is automatically picked up — no changes to the generic task prompt needed.

Examples of sources you might add:
- Linear/Jira issue activity
- GitHub PR reviews and merges
- Slack channel summaries beyond the default DMs
- Browser bookmark exports
- Local app usage logs

## Creating Topic Nodes

Topic nodes live in `Topics/` and act as evergreen hubs that link to journals, meetings, and people.

To create one manually:
1. Create `Topics/topic-name.md` in the vault.
2. Add a YAML frontmatter block with `type: topic` and a `summary` field.
3. Add `## Related` and `## Timeline` sections. The weekly rollup agent will append to Timeline automatically.

The weekly rollup also creates topic nodes when it detects recurring themes across journal entries.

## Adding Task Overrides

Task overrides let you extend the generic scheduled-tasks prompts without modifying the second-brain repo.

1. Create a markdown file in `work-automation/task-overrides/` named with the pattern `{task}-{feature}.md` (e.g., `journal-slack-screenshot.md`, `kickoff-jira-sync.md`).
2. Write the additional instructions the agent should follow. These are appended after the base task instructions.
3. Reference any config variables with `{{variable}}` syntax — they get substituted from `config.yaml`.

Each prompt wrapper (`.prompt.md`) specifies which overrides to check for. You can also add new override references by editing the prompt wrapper in `work-automation/scripts/tasks/`.

## Adjusting Scheduled Task Timing

Task schedules are defined in `second-brain/scheduled-tasks/crontab.example`. To change timing:

1. Copy the example crontab and adjust the cron expressions.
2. Re-register the tasks with your scheduler (Claude Code triggers, launchd, or cron).

Default schedule:
- Nightly Journal: 8:00 PM daily
- Meeting Debriefs: 8:30 PM daily
- Weekly Rollup: 9:00 PM Sundays
- Daily Kickoff: 12:00 AM daily

## Adding New MCP Connectors

The system uses MCP (Model Context Protocol) tools for live data access. To add a new connector:

1. Install or enable the MCP server (e.g., via Claude Desktop settings or `claude mcp add`).
2. Add any required config variables to `work-automation/config.yaml`.
3. Create a task override or new task that references the MCP tool calls.
4. The agent will have access to the tools at runtime — no code changes needed, just prompt instructions.

Currently used MCP connectors:
- **Granola** — meeting summaries and transcripts
- **Google Calendar** — calendar events for meeting debriefs
- **Slack** — channel activity, DM summaries, message sending
- **Google Drive** — Google Meet transcript documents
