---
name: qa-welcome
description: Acondiciona la conversación para trabajar con el IAFactory QA Kit. Revisa el entorno (Python, git, token de Google Sheets, repos) y carga las reglas de operación del kit (rules/AGENTS.md), que pasan a regir todo el chat. Úsala AL EMPEZAR cualquier chat de QA con este kit, cuando alguien nuevo pregunte por dónde empezar o cómo configurarlo, o cuando notes que las reglas del kit no se están aplicando. / Conditions the chat: environment check plus the kit's operating rules for the whole conversation.
---

# QA Welcome (`qa-welcome`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.

## Qué hacer

1. Ejecuta el script **sin `--json`**, porque la salida normal incluye las reglas completas:

   ```bash
   python <KIT>/skills/qa-welcome/scripts/welcome.py
   ```

2. Lee la salida completa. Termina con el bloque **"REGLAS DE OPERACIÓN DEL KIT"** (el contenido de `rules/AGENTS.md`). **Esas reglas rigen el resto de la conversación**, no solo este turno: aplícalas en cada tarea de QA, aunque el usuario no las vuelva a mencionar.

3. Responde con el estado del entorno y confirma en pocas líneas qué reglas vas a aplicar. Como mínimo:
   - Honestidad primero: distingue hecho, inferencia y suposición, y no des nada por verificado sin evidencia.
   - Al revisar una incidencia (AF-XXX) usas la **plantilla de 4 fases** de la sección 3 de las reglas, siempre completa, con su advertencia de seguridad y la trazabilidad de la VM.
   - Todo lo que escribe en Google Sheets (`report-bug`, `qa-finish`, `qa-rejection`, `qa-amplify`) va primero con `--dry-run` y con confirmación explícita del usuario, y antes de cada publicación o cambio de estado le pides a la persona el token de Sheets fresco (`SHEETS_ACCESS_TOKEN` en el `.env`; caduca cada hora).
   - Nada de commit ni push sin que el usuario lo pida.
   - Las VMs (dev, qa, team-devs) son compartidas: solo lectura, y nunca levantes ni reinicies servicios por iniciativa propia.

4. Si la salida marca algo sin configurar (token de Sheets, repos), dile al usuario qué falta y cómo resolverlo. No lo resuelvas por tu cuenta.

## Qué revisa el script

1. Sistema operativo, versión de Python y git.
2. Qué fuente da el token de Google Sheets: `pegado` (SHEETS_ACCESS_TOKEN), `refresh` (cliente OAuth propio) o `gcloud`.
3. Identidad con la que se firmarán los reportes (`USER_NAME` en el `.env`, o `git config user.name`).
4. Qué repos de producto encuentra en el workspace.

Opciones: `--no-rules` omite las reglas (solo diagnóstico) y `--json` da solo el estado en JSON, con la ruta de las reglas en `rules_path`.

## Flujo de QA para explicar a alguien nuevo

1. `qa-preflight`: comprobar que el entorno responde.
2. `qa-backlog`: ver qué defectos esperan verificación.
3. `qa-code-audit --issue AF-XXX`: revisar qué cambió el desarrollador.
4. Probar el defecto.
5. Cerrar con `qa-finish`, rechazar con `qa-rejection`, registrar uno nuevo con `report-bug`, o sumar evidencia a un ticket existente sin cambiar su estado con `qa-amplify`.

Para probar el pipeline completo con un proyecto piloto (o auditar una corrida ya terminada) se usa `qa-e2e-corrida`: documento "Antes" del proyecto, plan opcional de issues a revisar, una sección por agente y cierre con discrepancias. Puede incluir en su plan issues del paso 2 y cerrarlos con el paso 5.

## Si falta configuración

- Copiar `<KIT>/.env.example` a `.env` y completar `USER_NAME` y, cuando toque publicar, `SHEETS_ACCESS_TOKEN`. Si instalaste el kit como plugin de Claude Code, pon ese `.env` en la **raíz de tu workspace**: la carpeta del plugin se reemplaza en cada actualización.
- Si el workspace no tiene los repos de IAFactory con esos nombres, definir `QA_KIT_REPOS` y, si hace falta, `WORKSPACE_ROOT`.
- Sin token pegado, ejecutar `gcloud auth login --enable-gdrive-access`.
