# Context-switching wrapper for Claude Code.
#
# `claude work` and `claude personal` each load a different settings
# file, a different set of --add-dir repos, and switch the active gh
# account so git operations use the right identity. CLAUDE_CONTEXT is
# read by the SessionStart hook to pick the vault destination.
#
# Paste into ~/.zshrc and fill in the bracketed values.

claude() {
  local sub="${1:-}"
  case "$sub" in
    work)
      shift
      gh auth switch -u {{gh_work_account}} >/dev/null 2>&1 || true
      CLAUDE_CONTEXT=work command claude \
        --settings ~/.claude/work-settings.json \
        --add-dir {{work_automation_repo}} \
        --add-dir {{second_brain_repo}} \
        --add-dir {{work_analyses_repo}} \
        "$@"
      ;;
    personal)
      shift
      gh auth switch -u {{gh_personal_account}} >/dev/null 2>&1 || true
      CLAUDE_CONTEXT=personal command claude \
        --settings ~/.claude/personal-settings.json \
        --add-dir {{personal_automation_repo}} \
        --add-dir {{second_brain_repo}} \
        --add-dir {{meetingscribe_repo}} \
        "$@"
      ;;
    *)
      gh auth switch -u {{gh_work_account}} >/dev/null 2>&1 || true
      CLAUDE_CONTEXT=work command claude \
        --settings ~/.claude/work-settings.json \
        --add-dir {{work_automation_repo}} \
        --add-dir {{second_brain_repo}} \
        --add-dir {{work_analyses_repo}} \
        "$@"
      ;;
  esac
}
