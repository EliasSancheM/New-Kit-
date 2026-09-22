---
name: qa-preflight
description: Ultra-fast (<500ms) pre-flight diagnostic skill to check IAP tunnels, database ports, telemetry services, and cloud credentials before live QA testing.
---

# 🚀 Skill: QA Pre-Flight Connectivity Check (`qa-preflight`)

Always run this skill before executing live verification tests to confirm that GCP IAP tunnels, PostgreSQL, Qdrant, and Notion authentication are reachable.

---

## 🛠️ Usage Commands

```bash
# 1. Pre-flight connectivity diagnostic
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py

# 2. Machine / Agent JSON format
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py --json

# 3. Remote batch inspection on iafactory-dev (Consolidated in 1 SSH roundtrip)
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/remote_batch_inspect.py
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/remote_batch_inspect.py --json

# 4. Check single repo checkout in VM (e.g. frontend, core, agents, platform)
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/remote_batch_inspect.py --repo frontend

# 5. IAP Tunnel Management (Start, status, stop)
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py start
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py status --json
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py stop

# 6. Generate clean, pre-authenticated storageState.json for browser tests
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/refresh_auth.py
```
