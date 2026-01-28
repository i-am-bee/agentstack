---
name: Documentation Revision
about: Template for revising specific documentation pages for consistency.
title: 'Doc Revision: [Page Name]'
labels: docs
assignees: ''

---

**Summary of Requested Changes:**
Enter the summary of requested changes with reasoning for the change.

**Requirements**
Enter the requirements that would warrant success for this issue.

**Task Checklist**
- [ ] **Contributing Guideline Compliance:** I read and complied by "Documentation Contribution Guidelines" section of the Agent Stack project [CONTRIBUTING.md](https://github.com/i-am-bee/agentstack/blob/main/CONTRIBUTING.md) guide.
- [ ] **Snippet Test:** Verified all code works in a fresh environment (fresh agent stack install and clean environment).
- [ ] **Visual Preview:** Checked formatting/layout via Mintlify.
- [ ] **CLI Sync:** Ran `mise run agentstack-cli:docs` (if applicable).
- [ ] **Location:** Updates placed in `docs/development` for go live during next release or both `docs/development` and `docs/stable` for urgent go live.
