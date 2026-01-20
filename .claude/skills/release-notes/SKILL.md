---
name: release-notes
description: Helps generate release notes to be published on GitHub as well as in a Slack community channel
---

When tasked to generate release notes for a given version, your goal is to produce good-quality release notes focused on the user of Agent Stack. You don't need to provide a list of changed tickets or merged PRs; your goal is to provide human-readable release notes focused on the impact on the user.

## Scope of the release

The user generally provides a version tag for which they want to generate release notes. For example, they might tell you something like "Generate release notes for release-v0.5.0". Your first task is to figure out what the scope of the release is. The scope is basically a list of all merged PRs; once you have this list, you can proceed to the next steps.

### How to figure out the scope of the release

The user tells you for which version they want to generate the release notes, e.g., `release-v0.5.0`. Your next step is to figure out what the start commit in the git history is, and then you compare that with the head of the given release, e.g., `release-v0.5.0`.

The start commit is the latest stable version of the Agent Stack.

You can easily find the last release commit by looking at the `install` branch in `i-am-bee/agentstack` and checking the `install.sh` script in the root of the repo, which contains the `LATEST_STABLE_AGENTSTACK_VERSION` variable.

For example, you can do something like this:
```bash
curl -s https://raw.githubusercontent.com/i-am-bee/agentstack/install/install.sh | grep 'LATEST_STABLE_AGENTSTACK_VERSION=' | cut -d'=' -f2
```

This gives you a number, but the tag of the latest stable Agent Stack version is named `release-vX.Y.Z`.

Now, knowing the start and end of the scope, you can figure out what the merged PRs are by calling the attached utility script:
```bash
./.claude/skills/release-notes/scripts/find-merged-prs.sh release-v0.5.2 release-v0.5.3
```

## Identify high-impact features and changes

Knowing the list of all merged PRs, you need to go through all of them and fetch their comments via the `gh` command.

E.g.:
```bash
gh pr view PR_NUMBER --comments
```

This will give you a brief idea of what the feature is about. Look for comments from the `gemini-code-assist` user. These usually contain a comprehensive description of the PR, which should help you understand what has changed. If it's still unclear, you can look into the codebase to see more context.

Based on the description of the PR, your goal is then to identify high-impact PRs that we want to surface in the release notes.

### Rules for high-impact PRs

- You can ignore PRs without description, you need factual data to present to user.
- Breaking changes in the SDK are very important and should be mentioned
- New features in the SDK that extend the agent-building capabilities
- Any feature changes in the SDK, both client and server, both TypeScript and Python
- New features in the UI
- New features in the CLI
- Changes in the Helm chart for deployments

## Assemble the release notes

With all the prior knowledge, you are capable of drafting the release notes. They should be in the form of markdown that you present to the user and let them iterate on if needed.

Instead of PRs focus on factual changes, described with couple paragraphs. The goal is to keep the release notes short, on point and providing reader a good idea what the new release means to them.

Keep in mind that user of Agent Stack is either of these personas:

- A system administrator who is using the to manage agents and system via CLI
- A system administrator who is deploying producting using kubernetes or openshift
- A developer who is building agent via Agent Stack SDK (Python/TypeScript)
- A developer who is integrating the Agent Stack in their custom GUI and using Agent Stack as backend for agents (TypeScript)
- An end user who is running agents via GUI

Then at the end, provide list of all merged PRs (links + titles)

### Example of great release notes

```markdown
# 🚀 Agent Stack version 0.5.3 has been released 

This release brings major improvements to the CLI experience and web UI, a redesigned form extension architecture, plus many platform and SDK enhancements.

## Major Changes

**CLI Improvements** - The CLI has been redesigned with organized help text, improved agentstack list formatting with status indicators, and agentstack build now builds on the server by default - removing the need for Docker to be installed locally.

**UI Enhancements** - Agent execution steps (trajectory) are now grouped together for easier reading. Both agent responses and trajectory now display Mermaid diagrams, LaTeX math, and images as rendered content instead of raw markdown code.

**Breaking Change: Form Extension** - The Form Extension is now split into two separate extensions: FormServiceExtension for initial forms (shown before conversation starts) and FormRequestExtension for dynamic forms (requested during conversation). This prevents initial setup forms from being overridden by runtime forms. Agents using forms need to be updated (See docs).

**Connector Management** - Added comprehensive connector UI and presets system. Users can browse, connect, and disconnect predefined connector presets without manually entering configuration details. The system intelligently creates new connectors on first connection and provides table-based management with search functionality.

## What's changed
- [#1737 feat(ui): add agent management under Providers feature flag](https://github.com/i-am-bee/agentstack/pull/1737)
- [#1737 feat(ui): add agent management under Providers feature flag](https://github.com/i-am-bee/agentstack/pull/1737)
...
```
