---
name: "Agent Idea"
about: Suggest an agent concept for others to build
title: "[Agent] <agent name>"
labels: ["agent-idea"]
---

# Agent Idea: <agent name>

**If you like this idea, vote with a 👍 reaction on this issue.**

---

## 1. What it does (1–2 sentences)
Describe the core idea and why it is interesting.

_Example:_  
A Q&A Builder that watches Slack and Discord, detects new questions, retrieves answers from project docs, and proposes new Q&A entries for review.

---

## 2. Why this is valuable
- What problem does it solve?  
- Who benefits from it?

_Example:_  
Repeated questions across channels, answers drifting from the docs, and no central Q&A database.

---

## 3. How it behaves
- Triggers (when does it run?)  
- Inputs (what does it look at?)  
- Outputs (what does it produce?)  
- Human in the loop? (optional)

_Example:_  
Trigger when a new message ends with a question mark. Retrieve context from docs. Draft answer. Send to a reviewer if confidence is low.

---

## 4. What the agent needs access to
List the key sources or tools it relies on.

_Examples:_  
- Slack channels  
- Discord channels  
- Docs folder  
- GitHub issues  
- Knowledge base entries  

---

## 5. Rough architecture (very high level)
Bullet points or simple diagrams are fine. Keep it lightweight.

_Example:_  
- Detect question  
- Retrieve context  
- Draft answer with citations  
- Send to review  
- Publish to Q&A database  

---

## 6. Open questions
Anything intentionally unscoped or still under consideration.

_Example:_  
Should outdated Q&A items be auto-detected and refreshed?

---

## 7. Who could build this?
(Optional) Tag people or teams who might pick it up.
