#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: $0 <start-tag> <end-tag>"
  exit 1
fi

START_TAG=$1
END_TAG=$2

START_DATE=$(git log -1 --format=%aI "$START_TAG" 2>/dev/null)
END_DATE=$(git log -1 --format=%aI "$END_TAG" 2>/dev/null)

if [ -z "$START_DATE" ]; then
  echo "Error: Tag '$START_TAG' not found"
  exit 1
fi

if [ -z "$END_DATE" ]; then
  echo "Error: Tag '$END_TAG' not found"
  exit 1
fi

gh pr list --state merged --search "merged:${START_DATE}..${END_DATE}" --limit 1000 --json number,title,url
