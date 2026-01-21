---
name: draft-issue
description: Draft GitHub issues for i-am-bee/agentstack. Use when the user wants to report a bug, request a feature, or draft a general GitHub issue.
---

# Draft GitHub Issue

Your goal is to draft GitHub issue in form of markdown that user can easily file. Drafting issue can be iterative process, so you might need to ask user for refinements.

## Your Workflow

1. Based on user request perform deep analysis of the code base to have as much context as possible
2. Ask for clarification for anything that is unclear
3. Explore templates in `./github/ISSUE_TEMPLATE` folder
  - `bug_report.md` for bugs
  - `feature_request.md` for features
4. Search for potential ducplicates: `gh issue list -R i-am-bee/agentstack -S "<keywords>" --state all`
5. Show draft as a markdown for user approval

## Rules

- Keep issues very concise
- Don't include implementation details - define the problem, not the solution
- Always show draft for user approval before creating
