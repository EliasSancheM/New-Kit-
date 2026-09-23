---
name: qa-update
description: Checks for new versions of iafactory-qa-kit against origin/main and safely updates the plugin repository with changelog inspection.
---

# 🔄 Skill: Plugin Auto-Updater & Version Manager (`qa-update`)

Use this skill whenever you need to verify if there is a newer version of the `iafactory-qa-kit` plugin, inspect incoming commits, or pull updates.

---

## 🛠️ Usage Commands

```bash
# 1. Check if updates are available
python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --check

# 2. Machine JSON format (for agents and CI)
python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --check --json

# 3. Perform update (pull latest changes from origin/main)
python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --update

# 4. View current installed version and commit
python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --version
```
