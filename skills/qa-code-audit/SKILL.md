---
name: qa-code-audit
description: Audita los cambios de código asociados a un defecto AF-XXX (resuelve sus commits desde Google Sheets) o el estado git de los repos de producto, y ejecuta tests unitarios dirigidos. Úsala cuando el usuario pida revisar el fix de un AF-XXX, ver qué cambió en un commit, comparar ramas o correr un test puntual. Solo lectura salvo que se pidan tests. / Audit code changes for a defect or commit across product repos.
---

# QA Code Audit (`qa-code-audit`)

Reúne git status, commits y diffs de los repos de producto sin navegar carpeta por carpeta. Con `--issue` busca los hashes de commit del defecto en la planilla.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Qué repos revisa

Por defecto revisa `ai-factory-core`, `ai-factory-agents`, `ai-factory-frontend` y `ai-factory-platform`, como carpetas dentro de `WORKSPACE_ROOT`. Si tu workspace tiene otra estructura, define `QA_KIT_REPOS=repoA,repoB` (y opcionalmente `WORKSPACE_ROOT`) en el `.env` del kit. Un repo que no esté clonado aparece como `Not cloned locally`: eso no es un error del defecto.

## Comandos

```bash
# Auditar por ID de defecto
python <KIT>/skills/qa-code-audit/scripts/audit_changes.py --issue "AF-185" --json

# Inspeccionar un commit en cualquiera de los repos
python <KIT>/skills/qa-code-audit/scripts/audit_changes.py --commit "a1b2c3d" --json

# Estado y últimos commits de todos los repos, o de uno solo
python <KIT>/skills/qa-code-audit/scripts/audit_changes.py --json
python <KIT>/skills/qa-code-audit/scripts/audit_changes.py --repo "ai-factory-agents"

# Además ejecutar tests locales (por defecto no se corren: los cubre CI)
python <KIT>/skills/qa-code-audit/scripts/audit_changes.py --issue "AF-185" --run-tests

# Test puntual
python <KIT>/skills/qa-code-audit/scripts/fast_test_runner.py --frontend --file "src/hooks/orchestrator/__tests__/eventId.test.ts" --json
python <KIT>/skills/qa-code-audit/scripts/fast_test_runner.py --agent all --test-voseo --json
```

## Cómo presentar el resultado

Separa siempre:
1. **Lo que el código hace** (verificable en el diff).
2. **Si eso corrige la causa raíz del defecto** (inferencia: dilo así).
3. **Riesgos o regresiones** que veas.

Un test que pasa no prueba el fix si no ejercita el caso del defecto: dilo cuando ocurra. Si el defecto no tiene commits en la planilla, repórtalo; no adivines qué commit es.
