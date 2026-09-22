---
name: qa-finish
description: Complete, standalone skill for handling QA defect resolution & acceptance. Generates local success report, uploads nested Notion subpage, and updates Google Sheets to 'Finalizada'.
---

# ✅ Skill: QA Defect Resolution Workflow (`qa-finish`)

Use this skill when a defect has been empirically verified and resolved in development/staging.

---

## 🛠️ Usage Command

```bash
python .agents/plugins/iafactory-qa-kit/skills/qa-finish/scripts/qa_finish_publisher.py \
  "AF-XXX" \
  "<summary_of_verification>" \
  "<test_details_and_evidence>" \
  "[verification_conclusion]" \
  "[level1_page_id]"
```
