---
name: report-bug
description: Complete, production-grade defect reporting across local files, Notion MCP server, and Google Sheets API.
---

# 🛡️ Skill: Enterprise Defect Reporting (`report-bug`)

Use this skill to audit the next available `AF-XXX` ID, generate local executive/technical reports with the mandatory AI warning banner, publish to Notion, and synchronize Google Sheets.

---

## 🛠️ Usage Commands

```bash
# 1. Audit Next ID and Target Row in Google Sheets
python .agents/plugins/iafactory-qa-kit/skills/report-bug/scripts/gsheets_updater.py --audit

# 2. Publish 2-Level Nested Notion Pages
python .agents/plugins/iafactory-qa-kit/skills/report-bug/scripts/notion_mcp_publisher.py \
  "Reportes/AF-XXX_<short_name>.md" \
  "Reportes/AF-XXX_<short_name>_tecnico.md" \
  "AF-XXX" \
  "<short_name>"

# 3. Insert Row in Google Sheets
python .agents/plugins/iafactory-qa-kit/skills/report-bug/scripts/gsheets_updater.py \
  "<defect_name>" \
  "<technical_description>" \
  "<severity>" \
  "[level1_notion_url]"
```
