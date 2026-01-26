---
name: draft-issue
description: Draft GitHub issues for i-am-bee/agentstack. Use when the user wants to report a bug, request a feature, or draft a general GitHub issue.
---

# Draft GitHub Issue

Your goal is to draft GitHub issue in form of markdown that user can easily file. Drafting issue can be iterative process, so you might need to ask user for refinements.

## Your Workflow

1. Based on user request perform deep analysis of the code base to have as much context as possible
2. Ask for clarification for anything that is unclear
3. Explore templates in .github/ISSUE_TEMPLATE folder
  - `bug_report.md` for bugs
  - `feature_request.md` for features
4. Search for potential duplicates: gh issue list -R i-am-bee/agentstack -S "<keywords>" --state all
5. Fetch all available labels from Github using gh label list -R i-am-bee/agentstack
6. Show draft as a markdown for user approval

## Rules

- Keep issues very concise
- Don't include implementation details - define the problem, not the solution
- Always show draft for user approval before creating
- Always provide proper title and labels, nothing else in the header

## Example of a draft

```markdown
---
title: "Add Hello World button to login page"
labels: ["enhancement", "ui"]
---

**Is your feature request related to a problem? Please describe.**
Users don't have a chance to test buttons, this proposal adds empty Hello World button that serves as a testing component for users who are willing to test the app.

**Describe the solution you'd like**
Add new button with title 'Hello World' right next to the Login button (on the right)

**Describe alternatives you've considered**
Add Hello World automatic alert when page loads, but it's too disturbing.

**Additional context**
This is a testing feature, solely for illustration purposes.
```