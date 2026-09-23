---
name: qa-code-audit
description: Aggregates git diffs, status, recent commits, and static changes across IAFactory's 4 product repositories without manual folder navigation.
---

# 🔍 Skill: QA Code Audit & Diff Aggregator (`qa-code-audit`)

Audits code modifications across `ai-factory-core`, `ai-factory-agents`, `ai-factory-frontend`, and `ai-factory-platform`.

---

## 🛠️ Usage Commands

```bash
# Audit code directly by Defect ID (resolves commits from Google Sheets)
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py --issue "AF-185"

# Audit code and optionally execute local unit tests (omitted by default, covered by Jenkins CI/CD)
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py --issue "AF-185" --run-tests

# Check status and recent commits across all 4 repos (JSON format)
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py --json

# Inspect a specific commit hash wherever it exists
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py --commit "a1b2c3d"

# Target a single repository
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py --repo "ai-factory-agents"

# Fast surgical test runner for targeted fixes (Frontend / Agents)
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/fast_test_runner.py --frontend --file "src/hooks/orchestrator/__tests__/eventId.test.ts"
python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/fast_test_runner.py --agent all --test-voseo
```
