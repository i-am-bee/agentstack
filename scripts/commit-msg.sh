#!/usr/bin/env bash
set -euo pipefail

COMMIT_MSG_FILE="$1"
TEMP_FILE=$(mktemp)

# Check if any AI co-author trailers exist before stripping
HAS_AI_TRAILER=false
if grep -qi -E '^Co-authored-by:.*(Claude|Cursor|anthropic|cursor)' "$COMMIT_MSG_FILE"; then
  HAS_AI_TRAILER=true
fi

# Strip Co-authored-by lines for Claude/Cursor and Made-with lines
grep -vi -E '^Co-authored-by:.*(Claude|Cursor|anthropic|cursor)' "$COMMIT_MSG_FILE" \
  | grep -vi '^Made-with:' \
  > "$TEMP_FILE" || true

# Remove trailing blank lines
awk '/^[[:space:]]*$/{buf=buf $0 ORS; next} {if(buf) printf "%s",buf; buf=""; print}' "$TEMP_FILE" > "$COMMIT_MSG_FILE"

# If AI trailers were present, add Assisted-By instead
if [ "$HAS_AI_TRAILER" = true ]; then
  # Ensure there's a blank line before the trailer
  echo "" >> "$COMMIT_MSG_FILE"
  echo "Assisted-By: Claude (Anthropic AI) <noreply@anthropic.com>" >> "$COMMIT_MSG_FILE"
fi

rm -f "$TEMP_FILE"