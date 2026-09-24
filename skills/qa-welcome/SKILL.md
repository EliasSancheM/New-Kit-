---
name: qa-welcome
description: Onboarding del IAFactory QA Kit. Explica cómo funciona el kit y el flujo de QA, y revisa el entorno (Python, git, gcloud, token de Notion, repos presentes). Úsala cuando alguien nuevo empiece a usar el kit, pregunte por dónde empezar o cómo configurarlo, o cuando haya que comprobar que la instalación está lista. Solo lectura. / Onboarding and environment check for the QA kit.
---

# QA Welcome (`qa-welcome`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.

```bash
python <KIT>/skills/qa-welcome/scripts/welcome.py
python <KIT>/skills/qa-welcome/scripts/welcome.py --json
```

## Qué revisa

1. Sistema operativo, versión de Python y git.
2. Sesión de Google Cloud y token de Notion.
3. Identidad con la que se firmarán los reportes (`USER_NAME` en el `.env`, o `git config user.name`).
4. Qué repos de producto encuentra en el workspace.

## Flujo de QA para explicar a alguien nuevo

1. `qa-preflight`: comprobar que el entorno responde.
2. `qa-backlog`: ver qué defectos esperan verificación.
3. `qa-code-audit --issue AF-XXX`: revisar qué cambió el desarrollador.
4. Probar el defecto.
5. Cerrar con `qa-finish`, rechazar con `qa-rejection`, o registrar uno nuevo con `report-bug`. Los tres escriben en sistemas compartidos: siempre con `--dry-run` primero y confirmación del usuario.

## Si falta configuración

- Copiar `<KIT>/.env.example` a `<KIT>/.env` y completar `NOTION_TOKEN` y `USER_NAME`.
- Si el workspace no tiene los repos de IAFactory con esos nombres, definir `QA_KIT_REPOS` y, si hace falta, `WORKSPACE_ROOT`.
- Ejecutar `gcloud auth login --enable-gdrive-access`.
