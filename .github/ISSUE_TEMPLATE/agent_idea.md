---
name: "Agent Idea"
about: Suggest an agent idea to build
title: "[Agent]: <agent name>"
labels: ["agent-idea"]
---

_If this idea excites you, vote with a 👍 so the community knows it’s worth building._

### 1. What it does
Give a short description of the agent and why it’s interesting (1–2 sentences).

_Example: A Q&A Builder that watches Slack and Discord, spots new questions, retrieves answers from project docs, and proposes new Q&A entries for review._

### 2. Why this is valuable
Explain the motivation:
- What problem does it solve?  
- Who benefits from it?  

_Example: Teams repeat answers across channels, answers drift from the docs, and there’s no central Q&A source of truth._

### 3. How it behaves
Describe how the agent works in practice:
- Triggers (when does it run?)  
- Inputs (what does it look at?)  
- Outputs (what does it produce?)  
- Human in the loop?

_Example: Trigger when a message ends with a question mark. Retrieve context from docs. Draft an answer. Send to a reviewer if confidence is low._

### 4. What the agent needs access to
List the main sources, tools, or systems the agent depends on.

_Examples: Slack channels, Discord channels, Docs folder, GitHub issues, Knowledge base entries_

### 5. Rough architecture (very high level)
Share the big picture. Bullet points or simple diagrams are perfect.

_Example: Detect question → Retrieve context → Draft answer with citations → Send to review → Publish to Q&A database_

### 6. Open questions
List anything that’s intentionally unscoped or needs discussion.

_Example: Should outdated Q&A items be auto-detected and refreshed?_

### 7. Who could build this?
(Optional) Tag people or teams who might be excited to take this on.