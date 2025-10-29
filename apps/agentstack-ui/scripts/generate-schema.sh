#!/bin/sh
set -e

SCHEMA_URL="$1"
OUTPUT_FILE="$2"

if [ -z "$SCHEMA_URL" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: $0 <schema_url> <output_file>"
  exit 1
fi

# Generate OpenAPI schema
pnpm dlx openapi-typescript "$SCHEMA_URL" -o "$OUTPUT_FILE" --alphabetize

# Fix license headers
mise run common:fix:license

# Format with Prettier
pnpm prettier --log-level silent --write "$OUTPUT_FILE"