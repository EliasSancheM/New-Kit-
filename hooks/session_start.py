#!/usr/bin/env python3
"""
SessionStart hook (Claude Code).

Claude Code loads CLAUDE.md files but never a plugin's rules/AGENTS.md, so
without this the operating rules are only applied if someone remembers to point
at them. This hook adds a short, conditional reminder to the session context
with the absolute path of the rules file (which differs when the kit is
installed as a plugin, because Claude Code copies it into its plugin cache).

It only injects a pointer, not the whole rules file, so chats that have nothing
to do with QA pay almost no context. The full rules are loaded by the
qa-welcome skill or by reading the file, as the reminder instructs.
"""
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rules_path = os.path.join(plugin_root, "rules", "AGENTS.md")

message = f"""El IAFactory QA Kit está instalado. Estas instrucciones aplican SOLO cuando el usuario haga trabajo de QA con el kit (revisar o probar una incidencia AF-XXX, consultar el backlog, verificar en una VM, reportar, cerrar o rechazar un defecto, o hacer o auditar una corrida E2E de un proyecto piloto). Para cualquier otro tema, ignóralas.

Antes de responder a la primera tarea de QA de esta conversación:
1. Si aún no lo has hecho, carga las reglas de operación completas ejecutando la skill `iafactory-qa-kit:qa-welcome` (imprime el estado del entorno y las reglas), o leyendo este archivo: {rules_path}
2. Esas reglas rigen toda la conversación. Las que más se olvidan: (a) la revisión de una incidencia usa SIEMPRE la plantilla de 4 fases de la sección 3, completa y con su advertencia de seguridad; (b) nada que escriba en Google Sheets sin `--dry-run` previo y confirmación explícita del usuario, y antes de cada publicación o cambio de estado pídele a la persona el token de Sheets fresco (SHEETS_ACCESS_TOKEN en el .env, caduca cada hora); (c) nada de git commit/push sin que lo pida; (d) las VMs dev, qa y team-devs son compartidas: solo lectura, sin levantar ni reiniciar servicios por iniciativa propia; (e) distingue hecho, inferencia y suposición, y no des nada por verificado sin evidencia; (f) una corrida E2E empieza con la skill `qa-e2e-corrida` y `new_run.py`, nunca copiando un informe anterior, y termina con `validate_run.py` sin errores. En método, la skill manda sobre tu memoria."""

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": message,
    }
}, ensure_ascii=False))
sys.exit(0)
