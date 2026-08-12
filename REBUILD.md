# REBUILD

How to stand the second brain back up on a machine that has nothing on it.

Written for the case that matters: **you have left the employer whose laptop
this was built on.** Anything that lived only on that machine, or only in a
repo behind their SSO, is gone. What survives is what was pushed to your
personal GitHub account, and this file is the instructions for turning that
back into a working system.

## What you are rebuilding

Four layers. The first two are the point; the second two are what people forget
and then cannot reconstruct.

| Layer | Comes from | What it is |
|---|---|---|
| Vault content | `obsidian-vault-personal` (private) | The notes. Journal, People, Projects, Reference. |
| Framework | this repo | The conventions the agent follows: vault contract, 3-tier lookup, Learning Loop, scheduled-task prompts. |
| **Harness** | `harness/` in this repo | The config that makes it *run*: context-switching hook, `/dream` and `/document` skills, settings, statusline. |
| **Automation** | `life-automations` (private) + `launchd/` | The scheduled tasks that keep the vault current without you. |

A rebuild that stops after the first two gives you a folder of markdown and no
second brain.

---

## 0. Prerequisites

```bash
# Homebrew, if the machine is fresh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install git gh python@3.12
brew install --cask obsidian

# Claude Code
curl -fsSL https://claude.ai/install.sh | bash

gh auth login          # personal account
```

Python 3.11+ is required — the scripts use `tomllib` from the standard library.

## 1. Clone

```bash
mkdir -p ~/github-projects ~/personal-projects ~/obsidian-vaults

git clone https://github.com/josephcoz/second-brain.git ~/github-projects/second-brain
git clone https://github.com/josephcoz/obsidian-vault-personal.git ~/obsidian-vaults/Personal
git clone https://github.com/josephcoz/life-automations.git ~/personal-projects/life-automations
```

`life-automations` needs its secrets restored separately — `secrets/` is
gitignored, by design. Recreate `secrets/config-private.yaml` from
`config.yaml`'s structure and re-download the Google OAuth credentials.

## 2. Fill in the harness

`harness/` ships templated: every employer-specific and machine-specific value
is a `{{placeholder}}`.

```bash
cd ~/github-projects/second-brain
cp scripts/harness-values.example.toml scripts/harness-values.toml
$EDITOR scripts/harness-values.toml     # every field is commented
python3 scripts/fill-harness.py         # writes ./harness-filled for review
```

Two of these are easy to get wrong:

- **`home`** must be an absolute path, not `~`. launchd does not expand a
  tilde, and a plist containing one loads without error and then never runs.
- **`unix_user_dashed`** is how Claude Code flattens your home path into a
  directory name under `~/.claude/projects/`. Read the real directory name
  there rather than guessing it.

The script refuses to write if any placeholder has no value, and errors if any
survives into the output. Review `harness-filled/`, then install:

```bash
python3 scripts/fill-harness.py --install
```

It will not overwrite an existing `~/.claude` unless you pass `--force`.

## 3. Shell function

`harness-filled/zshrc-claude-function.sh` defines `claude work` and
`claude personal`. Each loads a different settings file, a different set of
`--add-dir` repos, and switches the active `gh` account so git operations use
the right identity. It also sets `CLAUDE_CONTEXT`, which the SessionStart hook
reads to decide which vault the session may write to.

```bash
cat harness-filled/zshrc-claude-function.sh >> ~/.zshrc
exec zsh
```

If you are not running two contexts at the new job, keep only the `personal`
branch and make it the default.

## 4. Scheduled tasks

```bash
cp harness-filled/launchd/*.plist ~/Library/LaunchAgents/
for f in ~/Library/LaunchAgents/com.*.plist; do launchctl load "$f"; done
```

The plists are still named `com.joe.*` — only the `Label` inside was
templated. Rename the files to match your own slug if you care; launchd keys
off the `Label`, so it works either way.

The work-side tasks (`daily-kickoff`, `nightly-journal`, `meeting-debriefs`,
`weekly-rollup`) expect a host repo at `work_automation_repo` containing
`config.yaml` and `scripts/tasks/*.prompt.md`. At a new employer that repo does
not exist yet — see `SETUP.md` for creating it, and start from
`config.example.yaml`.

## 5. Obsidian

Open Obsidian → **Open folder as vault** → `~/obsidian-vaults/Personal`.

Then **Settings → Files & Links → Excluded files**, add `harness-private` —
it is config, not notes, and should stay out of search and graph view.

## 6. Verify

```bash
# Context hook fires and names the right vault
claude personal
#   expect: "Session context: PERSONAL" and the Personal vault path

# Skills resolve
/dream --quick
/document
```

Then confirm the vault contract holds: ask a question whose answer is only in
the vault (`"who is <someone in People/>"`) and check it does the 3-tier lookup
rather than guessing.

---

## Keeping this true

Both harness copies are **generated**. Neither is hand-maintained, so neither
drifts — but both go stale if you forget to regenerate them.

```bash
# public, templated — from this repo
python3 scripts/sanitize-harness.py
python3 scripts/sanitize-harness.py --check    # is harness/ current?

# private, verbatim — from the vault repo
~/obsidian-vaults/Personal/harness-private/sync-harness.sh
```

Run both before any machine handover, and commit the results. `--check`
regenerates into a temp dir and diffs, so a stale `harness/` is something you
detect rather than something you assume.

The sanitizer fails closed: if a new secret, employer name, or opaque ID
appears in `~/.claude` later, the forbidden-pattern gate stops the run instead
of publishing it. If it flags something that is genuinely generic English, add
the exact phrase to `protect` in `scripts/harness-scrub.toml` rather than
deleting the rule.
