# Architecture

## The Three Layers

The second-brain system has three layers:

1. **Obsidian Vault** — the persistent data layer. Daily journals, meeting notes, people files, topic hubs, and domain reference docs. This is the knowledge that survives across Claude sessions.

2. **Scheduled Tasks** — automated agents that keep the vault current:
   - **Nightly Journal** (8pm) — exports meetings from Granola, enriches with Google Drive transcripts, gathers session logs + Slack activity, writes a daily journal entry
   - **Meeting Debriefs** (8:30pm) — researches tomorrow's calendar and outputs prep briefings
   - **Weekly Rollup** (Sunday 9pm) — synthesizes the week's journals into a single onboarding-quality document, updates topic nodes, regenerates the topic index
   - **Daily Kickoff** (midnight) — sends a morning accountability message via Slack

3. **CLAUDE.md** — project instructions that teach Claude Code how to navigate the vault using the 3-tier lookup pattern

## The Cycle

```
Daytime Work (sessions, meetings, Slack)
         ↓
Nightly Journal (8pm) → writes Journal/YYYY-MM-DD.md
         ↓
Meeting Debriefs (8:30pm) → preps tomorrow
         ↓
Weekly Rollup (Sunday 9pm) → synthesizes into Journal/YYYY-WXX-rollup.md
         ↓
Next Session reads vault → cold-starts in seconds
```

## Two-Repo Split

- **second-brain** (this repo) — the reusable framework. Generic task prompts with {{variables}}, vault template, CLAUDE.md with lookup patterns. Shareable.
- **work-automation** (private) — your specific instance. Filled config, domain context, task overrides for features specific to your tools (e.g., Jira sync, Slack screenshots). Not shareable.

The vault itself stays unversioned — it's the runtime data store that changes daily.

## Config Substitution

Scheduled task prompts use `{{variable}}` syntax. The agent reads config.yaml at runtime and substitutes values. This means config changes take effect immediately without re-registering tasks.

## Task Overrides

The generic task prompts in second-brain/ can be extended with override files in work-automation/task-overrides/. Each override appends additional steps to a parent task. This keeps the generic prompts clean while allowing user-specific features.
