---
name: qa-welcome
description: Explains IAFactory QA Kit architecture, workflows, prerequisites, and gives an interactive environment check and onboarding guide for new developers and AI assistants.
---

# 👋 Skill: IAFactory QA Kit Onboarding & Welcome (`qa-welcome`)

Use this skill whenever a new developer, engineer, or AI assistant joins the workspace or wants to understand how the QA Kit works, how to run tests, and what commands are available.

---

## 🛠️ Quick Execution

```bash
# 1. Interactive Welcome & Environment Diagnostic
python skills/qa-welcome/scripts/welcome.py

# 2. Machine JSON Output (for AI agents)
python skills/qa-welcome/scripts/welcome.py --json
```

---

## 💡 What this skill does
1. **Detects Environment:** Verifies OS, Python version, Git status, Google Cloud auth, and Notion token.
2. **Identifies User:** Shows active reporter identity (`USER_NAME`).
3. **Inspects Submodules:** Checks presence of `ai-factory-core`, `ai-factory-agents`, `ai-factory-frontend`, and `ai-factory-platform`.
4. **Displays Cheatsheet:** Prints essential commands for triage, diff auditing, preflight checks, and defect closure.
