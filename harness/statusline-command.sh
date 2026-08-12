#!/usr/bin/env bash
input=$(cat)

# Context window usage
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# Rate limit usage
five=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
week=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# Git repo and branch — use cwd so it follows `cd` within the session.
# Uses `git rev-parse --show-toplevel` to handle worktrees / submodules /
# any nested dir inside a repo, not just the literal project root.
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // .workspace.project_dir // empty')
git_info=""
if [ -n "$cwd" ]; then
  toplevel=$(git -C "$cwd" --no-optional-locks rev-parse --show-toplevel 2>/dev/null)
  if [ -n "$toplevel" ]; then
    repo=$(basename "$toplevel")
    branch=$(git -C "$cwd" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null)
    if [ -z "$branch" ]; then
      branch="detached"
    fi
    git_info="${repo}:${branch}"
  fi
fi

parts=()

if [ -n "$git_info" ]; then
  parts+=("$git_info")
fi

if [ -n "$used" ]; then
  pct=$(printf '%.0f' "$used")
  if [ "$pct" -ge 60 ]; then
    parts+=("\033[31mctx:${pct}%\033[0m")
  elif [ "$pct" -ge 40 ]; then
    parts+=("\033[33mctx:${pct}%\033[0m")
  else
    parts+=("ctx:${pct}%")
  fi
fi

if [ -n "$five" ]; then
  five_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
  if [ -n "$five_resets" ]; then
    reset_time=$(date -r "$five_resets" +'%l:%M %p')
    reset_time="${reset_time# }"  # strip leading space from %l
    parts+=("5h:$(printf '%.0f' "$five")% (resets $reset_time)")
  else
    parts+=("5h:$(printf '%.0f' "$five")%")
  fi
fi

if [ -n "$week" ]; then
  parts+=("7d:$(printf '%.0f' "$week")%")
fi

if [ ${#parts[@]} -gt 0 ]; then
  printf '%b' "$(IFS=' | '; echo "${parts[*]}")"
fi
