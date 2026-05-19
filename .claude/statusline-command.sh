#!/usr/bin/env bash
# Claude Code status line script

input=$(cat)

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
model_id=$(echo "$input" | jq -r '.model.id // ""')

# --- Directory ---
dir=$(echo "$input" | jq -r '.workspace.current_dir // ""')
dir_name=$(basename "$dir")

# --- Git branch ---
branch=$(git --git-dir="$dir/.git" --work-tree="$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
if [ -n "$branch" ]; then
  dirty=$(git --git-dir="$dir/.git" --work-tree="$dir" status --porcelain 2>/dev/null | head -1)
  [ -n "$dirty" ] && branch="${branch}*"
fi

# --- Context battery ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
if [ -n "$used_pct" ]; then
  pct_int=$(printf '%.0f' "$used_pct")
  filled=$(( pct_int * 10 / 100 ))
  empty=$(( 10 - filled ))
  bar=""
  for i in $(seq 1 $filled); do bar="${bar}#"; done
  for i in $(seq 1 $empty);  do bar="${bar}-"; done
  battery="[${bar}] ${pct_int}%"
else
  battery=""
fi

# --- 5-hour rolling quota (Pro/Max only; populated after first API response) ---
five_hour_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
five_hour_resets=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
five_hour=""
if [ -n "$five_hour_pct" ]; then
  fh_int=$(printf '%.0f' "$five_hour_pct")
  reset_str=""
  if [ -n "$five_hour_resets" ]; then
    secs_left=$(( five_hour_resets - $(date +%s) ))
    if [ $secs_left -gt 0 ]; then
      hrs=$(( secs_left / 3600 ))
      mins=$(( (secs_left % 3600) / 60 ))
      reset_str=" ${hrs}h${mins}m"
    fi
  fi
  five_hour="5h:${fh_int}%${reset_str}"
fi

# --- Token cost ---
# Pricing per million tokens
current_usage=$(echo "$input" | jq '.context_window.current_usage')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')

cost=""
if [ "$current_usage" != "null" ] && [ -n "$current_usage" ]; then
  cache_create=$(echo "$current_usage" | jq -r '.cache_creation_input_tokens // 0')
  cache_read=$(echo "$current_usage"   | jq -r '.cache_read_input_tokens // 0')

  # Determine per-million rates based on model id
  case "$model_id" in
    *opus-4*|*opus-4-7*)
      in_rate="15.0"; out_rate="75.0"; cw_rate="18.75"; cr_rate="1.50"
      ;;
    *sonnet-4*|*sonnet-4-6*)
      in_rate="3.0"; out_rate="15.0"; cw_rate="3.75"; cr_rate="0.30"
      ;;
    *haiku*)
      in_rate="0.80"; out_rate="4.0"; cw_rate="1.0"; cr_rate="0.08"
      ;;
    *)
      in_rate="3.0"; out_rate="15.0"; cw_rate="3.75"; cr_rate="0.30"
      ;;
  esac

  cost=$(awk -v tin="$total_input" -v tout="$total_output" \
             -v ccw="$cache_create" -v ccr="$cache_read" \
             -v ir="$in_rate" -v or_="$out_rate" \
             -v cwr="$cw_rate" -v crr="$cr_rate" \
    'BEGIN {
      # plain input = total_input minus cache tokens (they are counted separately)
      plain_in = tin - ccw - ccr
      if (plain_in < 0) plain_in = 0
      cost = (plain_in / 1000000) * ir \
           + (tout    / 1000000) * or_ \
           + (ccw     / 1000000) * cwr \
           + (ccr     / 1000000) * crr
      if (cost < 0.01)
        printf "$%.4f", cost
      else
        printf "$%.2f", cost
    }')
fi

# --- Assemble ---
parts=()
parts+=("$model")
parts+=("$dir_name")
[ -n "$branch" ]  && parts+=("$branch")
[ -n "$battery" ]   && parts+=("$battery")
[ -n "$five_hour" ] && parts+=("$five_hour")
[ -n "$cost" ]      && parts+=("$cost")

# Join with " | "
output=""
for part in "${parts[@]}"; do
  if [ -z "$output" ]; then
    output="$part"
  else
    output="$output | $part"
  fi
done

printf '%s' "$output"
