---
name: qa-help
description: Displays a comprehensive, structured catalog of all skills, scripts, parameters, and flags available in the IAFactory QA Kit for quick reference by users and AI agents.
---

# 📖 Skill: IAFactory QA Kit Command & Flag Catalog (`qa-help`)

Use this skill whenever a user or agent needs a quick reminder, sitemap, or syntax reference for all available skills and CLI scripts in `iafactory-qa-kit`.

---

## 🛠️ Quick Commands

```bash
# 1. Visual catalog of all skills, scripts, and flags
python skills/qa-help/scripts/help.py

# 2. Machine JSON catalog (structured documentation for AI agents)
python skills/qa-help/scripts/help.py --json

# 3. Filter help by specific skill or script name
python skills/qa-help/scripts/help.py --skill qa-code-audit
python skills/qa-help/scripts/help.py --skill qa-preflight
```
