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

This gives you a version number (e.g., `0.5.0`). The corresponding git tag for the latest stable Agent Stack version is formed by prepending `release-v` to this number (e.g., `release-v0.5.0`).

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
- A system administrator who is deploying production using kubernetes or openshift
- A developer who is building agent via Agent Stack SDK (Python/TypeScript)
- A developer who is integrating the Agent Stack in their custom GUI and using Agent Stack as backend for agents (TypeScript)
- An end user who is running agents via GUI

Then at the end, provide list of all merged PRs (links + titles)

### Example of great release notes

```markdown
# 🚀 Agent Stack version 0.5.3 has been released 

This release brings a major TypeScript SDK restructuring, a new Canvas agent, comprehensive UI redesign, and significant improvements to authentication and CLI experience.

## Major Changes

### Breaking: TypeScript SDK Restructuring
The `agentstack-sdk-ts` has been completely refactored with a new modular architecture. The API client is now organized into dedicated subdirectories (`auth`, `services`, `ui`, `configuration`, `connectors`, etc.) with proper `schemas.ts` and `types.ts` files. A new `buildApiClient` core function with `unwrapResult` utility provides standardized response handling. Error handling is now structured with `ApiErrorException` and specific error types (Http, Network, Parse, Validation). All consumers of the TS SDK need to update imports and usage patterns.

### New Canvas Agent
A new agent for multi-turn artifact editing is now available. Users can select and modify specific sections of text content, enabling precise iterative refinement of generated artifacts.

### SDK: User Approval Extension
New `ApprovalExtensionServer` and `ApprovalExtensionClient` enable explicit human-in-the-loop workflows. Agents can request user approval for critical actions using structured `ApprovalRequest`/`ApprovalResponse` models. The older `ToolCallRequest` and `ToolCallExtensionServer` are now deprecated.

## What's changed
- [#1737 feat(ui): add agent management under Providers feature flag](https://github.com/i-am-bee/agentstack/pull/1737)
- [#1737 feat(ui): add agent management under Providers feature flag](https://github.com/i-am-bee/agentstack/pull/1737)
...
```
