# Second Brain

An AI-powered work knowledge base built on Claude Code and Obsidian. Second Brain automatically captures your meetings, emails, Slack threads, and Jira work into a structured Obsidian vault, then synthesizes daily journals, weekly rollups, and actionable kickoff briefs -- all driven by scheduled Claude Code tasks and MCP connectors.

## Architecture

```
second-brain/              # This repo -- the shared framework
  vault-template/          # Default vault folder structure
  scripts/                 # Prompt templates for each scheduled task
  scheduled-tasks/         # Task definitions (cron schedules, prompts)
  docs/                    # Detailed guides

work-automation/           # Your private repo -- personal config + overrides
  config.yaml              # Filled-in copy of config.example.yaml
  skills/                  # Domain-specific skills (e.g., Hex, dbt)
  task-overrides/          # Custom prompt tweaks per task
```

Scheduled Claude Code tasks read your `config.yaml`, pull data from MCP connectors (Slack, Google Calendar, Granola, Gmail, Jira), and write structured Markdown into your Obsidian vault. A project-level `CLAUDE.md` gives Claude persistent context about your role, preferences, and vault conventions.

## Prerequisites

- **Obsidian** with a vault dedicated to work notes
- **Claude Code** CLI installed and authenticated
- **MCP connectors** enabled in Claude Code for:
  - Slack
  - Google Calendar
  - Granola (meeting transcripts)
  - Gmail
  - Atlassian / Jira

## Quick Start

1. **Fork this repo** (or clone it to `~/github-projects/second-brain/`).

2. **Copy the config template** to your private work-automation repo:
   ```bash
   cp config.example.yaml ~/github-projects/work-automation/config.yaml
   ```

3. **Fill in your values** in `config.yaml` -- Slack IDs, Jira IDs, vault path, etc.

4. **Initialize your vault** from the template:
   ```bash
   ./scripts/setup.sh
   ```

5. **Create scheduled tasks** for each automation:
   ```bash
   claude schedule create --from scheduled-tasks/nightly-journal.yaml
   claude schedule create --from scheduled-tasks/meeting-debriefs.yaml
   claude schedule create --from scheduled-tasks/weekly-rollup.yaml
   claude schedule create --from scheduled-tasks/daily-kickoff.yaml
   ```

6. Verify tasks are running with `claude schedule list`.

## Documentation

See the `docs/` directory for detailed guides on each task, vault structure conventions, and how to add custom skills or overrides.
