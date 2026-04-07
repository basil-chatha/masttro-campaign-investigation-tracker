#!/bin/bash
# PreToolUse guard: blocks dangerous Bash commands before execution.
# exit 0 = allow, exit 2 = block (stderr fed to Claude as feedback)
INPUT=$(< /dev/stdin)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')

# Lowercase once for case-insensitive matching (tr for bash 3.2 compat on macOS)
CMD_LOWER=$(printf '%s' "$COMMAND" | tr '[:upper:]' '[:lower:]')

# Blocked patterns — uses bash regex matching (zero forks)
if [[ "$CMD_LOWER" =~ rm\ -rf\ / ]] ||
   [[ "$CMD_LOWER" =~ rm\ -rf\ ~ ]] ||
   [[ "$CMD_LOWER" =~ drop\ table ]] ||
   [[ "$CMD_LOWER" =~ drop\ database ]] ||
   [[ "$CMD_LOWER" =~ git\ push.*--force.*main ]] ||
   [[ "$CMD_LOWER" =~ truncate.*supabase ]]; then
  echo "Blocked by safety-guard hook. See CLAUDE.md approval boundaries." >&2
  exit 2
fi

# Block direct file manipulation of protected paths (migrations, seed data)
if [[ "$COMMAND" =~ supabase/migrations|supabase/seed\.sql ]] &&
   [[ "$COMMAND" =~ \>|sed\ -i|\brm\b|\bmv\b|\bcp\b ]]; then
  echo "Blocked: direct modification of migration/seed files via Bash." >&2
  exit 2
fi

exit 0
