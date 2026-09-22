---
name: qa-rejection
description: Complete, standalone skill for handling QA defect rejections. Generates local rejection report with AI warning banner, uploads nested Notion subpage, and updates Google Sheets to 'Rechazada por QA'.
---

# ❌ Skill: QA Defect Rejection Workflow (`qa-rejection`)

Use this skill when a defect fails verification testing, when code changes do not address the root cause, or when a fix causes regressions.

---

## 🛠️ Usage Command

```bash
python .agents/plugins/iafactory-qa-kit/skills/qa-rejection/scripts/qa_rejection_publisher.py \
  "AF-XXX" \
  "<reason_for_rejection>" \
  "<replication_test_details>" \
  "<code_changes_found>" \
  "[level1_page_id]"
```
