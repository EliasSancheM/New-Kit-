---
name: qa-backlog
description: Standalone skill to inspect, filter, and triage active QA defects from Google Sheets online. Delivers structured JSON or Markdown summaries for AI agents and users.
---

# 📋 Skill: QA Backlog Triage (`qa-backlog`)

Use this skill whenever you need to inspect pending defects, filter issues by status (`Pendiente`, `En Revisión`, `Reportada`), or search details of a specific `AF-XXX` issue from Google Sheets without manual queries.

---

## 🛠️ Usage Commands

```bash
# List all active defects (JSON format for agents)
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente,En Revisión,Reportada" --json

# List specific issue details
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --id "AF-185" --json

# Markdown table output for user
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --status "En Revisión"
```

---

## 🔑 Output Schema (JSON)
* `id`: Defect identifier (`AF-XXX`)
* `nombre`: Title / description summary
* `estado`: Current workflow status
* `gravedad`: `Critica`, `Alta`, `Media`, `Baja`
* `responsable`: Assigned developer or agent
* `commits` / `id_commits`: Associated commit hashes
* `comentario_qa`: Notion URL and QA notes
