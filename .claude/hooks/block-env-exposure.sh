#!/usr/bin/env bash
# PreToolUse hook: deny any tool call that would read or print the contents
# of a .env file (or .env.* variant). Errs on the side of blocking.

set -euo pipefail

input="$(cat)"
tool_name="$(printf '%s' "$input" | jq -r '.tool_name // empty')"

deny() {
  local reason="$1"
  jq -n --arg reason "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

# Matches a bare .env, .env.local, .env.production, foo/.env, etc.
# Does NOT match unrelated names like .environment or env.example.
env_path_regex='(^|/)\.env(\.[A-Za-z0-9_.-]+)?$'

case "$tool_name" in
  Read|Edit|Write|NotebookEdit)
    file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"
    if [[ -n "$file_path" ]] && [[ "$file_path" =~ $env_path_regex ]]; then
      deny "Access to .env files is blocked by project hook (.claude/hooks/block-env-exposure.sh). These files may contain secrets and must not be read, edited, or written by the agent."
    fi
    ;;

  Grep)
    path="$(printf '%s' "$input" | jq -r '.tool_input.path // empty')"
    glob="$(printf '%s' "$input" | jq -r '.tool_input.glob // empty')"
    if [[ -n "$path" ]] && [[ "$path" =~ $env_path_regex ]]; then
      deny "Grep on .env files is blocked by project hook. These files may contain secrets."
    fi
    if [[ -n "$glob" ]] && [[ "$glob" == *.env* || "$glob" == .env* ]]; then
      deny "Grep glob targeting .env files is blocked by project hook."
    fi
    ;;

  Bash)
    command="$(printf '%s' "$input" | jq -r '.tool_input.command // empty')"
    # Block any command that references a .env file. This is broad on purpose:
    # cat, head, tail, less, more, bat, grep, awk, sed, xxd, od, source, ., cp,
    # mv to stdout-equivalents, scripts that print it -- all touch the literal
    # token .env. If a legitimate use case is blocked, run it outside the
    # agent or temporarily disable this hook.
    if printf '%s' "$command" | grep -Eq '(^|[^A-Za-z0-9_.-])\.env([^A-Za-z0-9_-]|$)|(^|/)\.env(\.[A-Za-z0-9_.-]+)?([^A-Za-z0-9_.-]|$)'; then
      deny "Bash command references a .env file. Reading or printing .env contents is blocked by project hook (.claude/hooks/block-env-exposure.sh)."
    fi
    ;;
esac

exit 0
