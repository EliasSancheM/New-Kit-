#!/usr/bin/env python3
"""
IAFactory QA Kit - Help & Capabilities Catalog
----------------------------------------------
Provides an exhaustive reference of all skills, scripts, and flags
for AI agents and human engineers.
"""

import sys
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CATALOG = {
    "qa-welcome": {
        "description": "Onboarding interactivo, diagnóstico de dependencias y cheatsheet rápido.",
        "scripts": {
            "welcome.py": {
                "path": "skills/qa-welcome/scripts/welcome.py",
                "purpose": "Verifica Python, Git, la fuente del token de Google Sheets y la presencia de los repos de producto.",
                "flags": [
                    {"flag": "--json", "type": "boolean", "description": "Devuelve el estado del sistema en JSON estructurado para el agente."},
                    {"flag": "--help, -h", "type": "boolean", "description": "Muestra la ayuda básica del script."}
                ],
                "examples": [
                    "python skills/qa-welcome/scripts/welcome.py",
                    "python skills/qa-welcome/scripts/welcome.py --json"
                ]
            }
        }
    },
    "qa-backlog": {
        "description": "Consulta, filtrado y triaje de incidencias desde Google Sheets online.",
        "scripts": {
            "fetch_issues.py": {
                "path": "skills/qa-backlog/scripts/fetch_issues.py",
                "purpose": "Lee la matriz online de Google Sheets en tiempo real.",
                "flags": [
                    {"flag": "--status", "type": "string", "default": "Reportada,En Revisión,En curso", "description": "Filtro por estados separados por coma (ej. 'En Revisión' o 'all')."},
                    {"flag": "--id", "type": "string", "default": "None", "description": "Filtra por identificador exacto de defecto (ej. AF-228)."},
                    {"flag": "--responsable", "type": "string", "default": "None", "description": "Filtra por responsable: coincidencia parcial sin mayúsculas ni tildes, varias personas separadas por coma. Se aplica antes de --limit."},
                    {"flag": "--limit", "type": "integer", "default": 20, "description": "Límite máximo de incidencias a devolver."},
                    {"flag": "--json", "type": "boolean", "description": "Entrega salida en formato JSON para procesamiento de agentes."}
                ],
                "examples": [
                    "python skills/qa-backlog/scripts/fetch_issues.py --status \"En Revisión\"",
                    "python skills/qa-backlog/scripts/fetch_issues.py --id \"AF-228\" --json",
                    "python skills/qa-backlog/scripts/fetch_issues.py --status all --limit 50",
                    "python skills/qa-backlog/scripts/fetch_issues.py --status all --responsable \"Fabio,Marcelo\" --limit 500"
                ]
            }
        }
    },
    "qa-e2e-corrida": {
        "description": "Planificación y documentación de corridas E2E (documento 'Antes', plan de issues, una sección por agente, contraste con el Sheet, auditoría retroactiva). El método está en su SKILL.md.",
        "scripts": {
            "new_run.py": {
                "path": "skills/qa-e2e-corrida/scripts/new_run.py",
                "purpose": "Crea los documentos de la corrida desde las plantillas en QA_KIT_E2E_DIR (por defecto Reportes/E2E/), con el bloque de cada agente y su tabla 📦 de artefactos esperados ya llena. Solo archivos locales; nunca sobrescribe.",
                "flags": [
                    {"flag": "proyecto <slug>", "type": "subcommand", "description": "Crea proyectos/<slug>_requisitos.md (documento 'Antes')."},
                    {"flag": "corrida <empresa> <slug> [fecha]", "type": "subcommand", "description": "Crea <empresa>_<slug>_<fecha>.md (fecha por defecto: hoy)."},
                    {"flag": "where", "type": "subcommand", "description": "Muestra la carpeta de salida resuelta."},
                    {"flag": "--json", "type": "boolean", "description": "Salida en JSON (va antes del subcomando)."}
                ],
                "examples": [
                    "python skills/qa-e2e-corrida/scripts/new_run.py where",
                    "python skills/qa-e2e-corrida/scripts/new_run.py proyecto logistica-inversa",
                    "python skills/qa-e2e-corrida/scripts/new_run.py corrida shouko logistica-inversa"
                ]
            },
            "validate_run.py": {
                "path": "skills/qa-e2e-corrida/scripts/validate_run.py",
                "purpose": "Valida un documento de corrida contra la plantilla: secciones, metadatos, tabla 📦 de artefactos verificada por el asistente ([R]/[DB] y resultado), ✅/❌/🔍 por agente, hallazgos con evidencia (no solo [H]) y gravedad con motivo, §9.1 por agente, decisiones humanas en §9.2, método de 6.b, estado final. Solo lectura. El documento está terminado solo con 0 errores.",
                "flags": [
                    {"flag": "<documento.md>", "type": "positional", "description": "Documento de corrida a validar."},
                    {"flag": "--strict", "type": "boolean", "description": "Las advertencias también hacen fallar (código 1)."},
                    {"flag": "--json", "type": "boolean", "description": "Errores y advertencias en JSON."},
                    {"flag": "--metrics", "type": "boolean", "description": "Solo los conteos (artefactos esperados/verificados/correctos, hallazgos por gravedad, decisiones de §9.2) en JSON, para comparar corridas."}
                ],
                "examples": [
                    "python skills/qa-e2e-corrida/scripts/validate_run.py Reportes/E2E/apiux_prestamo-equipos_2026-10-01.md"
                ]
            }
        }
    },
    "qa-code-audit": {
        "description": "Auditoría de diffs cruzados, commits recientes y ejecución quirúrgica de tests.",
        "scripts": {
            "audit_changes.py": {
                "path": "skills/qa-code-audit/scripts/audit_changes.py",
                "purpose": "Inspecciona diffs Git, ramas y estado en los 4 repositorios locales.",
                "flags": [
                    {"flag": "--issue", "type": "string", "description": "ID del defecto (AF-XXX). Resuelve automáticamente los commits asociados desde Google Sheets."},
                    {"flag": "--commit", "type": "string", "description": "Hash del commit específico a inspeccionar en cualquier repo."},
                    {"flag": "--repo", "type": "string", "default": "all", "description": "Repositorio específico ('ai-factory-core', 'ai-factory-agents', 'ai-factory-frontend', 'ai-factory-platform', o 'all')."},
                    {"flag": "--run-tests", "type": "boolean", "description": "Ejecuta suite de pruebas unitarias localmente con fast_test_runner (desactivado por defecto; la validación está cubierta por Jenkins CI/CD)."},
                    {"flag": "--json", "type": "boolean", "description": "Salida en JSON crudo para agentes."}
                ],
                "examples": [
                    "python skills/qa-code-audit/scripts/audit_changes.py --issue \"AF-228\"",
                    "python skills/qa-code-audit/scripts/audit_changes.py --issue \"AF-228\" --run-tests",
                    "python skills/qa-code-audit/scripts/audit_changes.py --commit \"2d6a6772\"",
                    "python skills/qa-code-audit/scripts/audit_changes.py --repo ai-factory-frontend --json"
                ]
            },
            "fast_test_runner.py": {
                "path": "skills/qa-code-audit/scripts/fast_test_runner.py",
                "purpose": "Ejecuta pruebas unitarias dirigidas en Frontend (Vitest) o Agentes (Python).",
                "flags": [
                    {"flag": "--frontend", "type": "boolean", "description": "Activa runner para Next.js / Frontend con Vitest."},
                    {"flag": "--file", "type": "string", "description": "Ruta del archivo de pruebas a ejecutar."},
                    {"flag": "--test", "type": "string", "description": "Patrón de nombre de test específico (-t de Vitest)."},
                    {"flag": "--agent", "type": "string", "description": "Nombre del agente o 'all' (ej. owner-agent, architect-agent)."},
                    {"flag": "--test-voseo", "type": "boolean", "description": "Ejecuta suite de validación de dialecto/voseo en agentes."},
                    {"flag": "--json", "type": "boolean", "description": "Entrega resultados del runner en JSON."}
                ],
                "examples": [
                    "python skills/qa-code-audit/scripts/fast_test_runner.py --frontend --file \"src/lib/__tests__/roles.test.ts\"",
                    "python skills/qa-code-audit/scripts/fast_test_runner.py --agent owner-agent --test-voseo"
                ]
            }
        }
    },
    "qa-preflight": {
        "description": "Diagnóstico de conectividad TCP local e inspección remota consolidada en GCP VM.",
        "scripts": {
            "check_env.py": {
                "path": "skills/qa-preflight/scripts/check_env.py",
                "purpose": "Verifica en <500ms los puertos del túnel del entorno (Postgres, Qdrant, Redis, Prometheus...) y qué fuente da el token de Google Sheets.",
                "flags": [
                    {"flag": "--env", "type": "string", "default": "QA_KIT_ENV o dev", "description": "Entorno de environments.json (dev, qa, team-devs...). Aplica su offset de puertos."},
                    {"flag": "--json", "type": "boolean", "description": "Entrega diagnósticos en JSON estructurado."}
                ],
                "examples": [
                    "python skills/qa-preflight/scripts/check_env.py",
                    "python skills/qa-preflight/scripts/check_env.py --env qa --json"
                ]
            },
            "remote_batch_inspect.py": {
                "path": "skills/qa-preflight/scripts/remote_batch_inspect.py",
                "purpose": "Inspección consolidada vía SSH en la VM del entorno (checkout de los repos + contenedores Docker). Solo lectura.",
                "flags": [
                    {"flag": "--env", "type": "string", "default": "QA_KIT_ENV o dev", "description": "Entorno de environments.json."},
                    {"flag": "--repo", "type": "string", "description": "Filtra un repositorio (core, agents, frontend, platform u otro de QA_KIT_REPOS)."},
                    {"flag": "--json", "type": "boolean", "description": "Salida JSON estructurada."},
                    {"flag": "--instance / --zone / --project", "type": "string", "description": "Sobrescriben los datos del entorno."}
                ],
                "examples": [
                    "python skills/qa-preflight/scripts/remote_batch_inspect.py --env dev",
                    "python skills/qa-preflight/scripts/remote_batch_inspect.py --env qa --repo frontend --json"
                ]
            },
            "iap_tunnel.py": {
                "path": "skills/qa-preflight/scripts/iap_tunnel.py",
                "purpose": "Inicia, detiene o inspecciona túneles IAP hacia las VMs. Cada entorno usa su offset de puertos, así que varios túneles pueden convivir.",
                "flags": [
                    {"flag": "envs", "type": "subcommand", "description": "Lista los entornos configurados."},
                    {"flag": "start --env <env>", "type": "subcommand", "description": "Inicia el túnel del entorno en segundo plano (--foreground para primer plano)."},
                    {"flag": "stop --env <env>", "type": "subcommand", "description": "Detiene el túnel del entorno."},
                    {"flag": "status [--env <env> | --all] [--json]", "type": "subcommand", "description": "Estado de uno o de todos los túneles."}
                ],
                "examples": [
                    "python skills/qa-preflight/scripts/iap_tunnel.py envs",
                    "python skills/qa-preflight/scripts/iap_tunnel.py status --all",
                    "python skills/qa-preflight/scripts/iap_tunnel.py start --env qa",
                    "python skills/qa-preflight/scripts/iap_tunnel.py stop --env qa"
                ]
            },
            "refresh_auth.py": {
                "path": "skills/qa-preflight/scripts/refresh_auth.py",
                "purpose": "Hace login contra la API del entorno y genera auth/storageState_<env>.json para pruebas de navegador. Falla (código 1) si no hay login válido.",
                "flags": [
                    {"flag": "--env", "type": "string", "default": "QA_KIT_ENV o dev", "description": "Entorno de environments.json."},
                    {"flag": "--api-url / --frontend-origin", "type": "string", "description": "Sobrescriben las URLs del entorno."},
                    {"flag": "--user / --output / --json", "type": "string", "description": "Usuario de pruebas, ruta destino e impresión en stdout."}
                ],
                "examples": [
                    "python skills/qa-preflight/scripts/refresh_auth.py --env dev"
                ]
            }
        }
    },
    "report-bug": {
        "description": "Reporte formal de nuevos defectos en Google Sheets: fila nueva con el reporte ejecutivo y el técnico en Comentario QA.",
        "scripts": {
            "gsheets_updater.py": {
                "path": "skills/report-bug/scripts/gsheets_updater.py",
                "purpose": "Lee título, gravedad y síntoma del reporte ejecutivo, pasa report_lint, audita el próximo ID e inserta la fila con ambos reportes en Comentario QA. Exige dry-run, --confirm, token de Sheets y confirmación de una persona en su terminal.",
                "flags": [
                    {"flag": "--audit", "type": "boolean", "description": "Solo audita e imprime el próximo ID (AF-XXX) y fila destino sin escribir nada."},
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra qué se escribiría sin escribir nada e imprime confirm_code. Usarlo siempre antes de publicar."},
                    {"flag": "--confirm <código>", "type": "string", "description": "Obligatorio para escribir: el confirm_code del dry-run de los mismos archivos. Sin él sale con código 4."},
                    {"flag": "<ejecutivo.md> <tecnico.md>", "type": "positional", "description": "Los dos reportes escritos con las plantillas; el encabezado del ejecutivo debe ser '# AF-NNN — título' con el ID que devolvió --audit."},
                    {"flag": "--gravedad <Critica|Alta|Media|Baja>", "type": "string", "description": "Sobrescribe la gravedad leída del reporte ejecutivo."}
                ],
                "examples": [
                    "python skills/report-bug/scripts/gsheets_updater.py --audit",
                    "python skills/report-bug/scripts/gsheets_updater.py --dry-run Reportes/AF-380_login_sso.md Reportes/AF-380_login_sso_tecnico.md",
                    "python skills/report-bug/scripts/gsheets_updater.py --confirm 1a2b3c4d Reportes/AF-380_login_sso.md Reportes/AF-380_login_sso_tecnico.md"
                ]
            },
            "report_lint.py": {
                "path": "skills/report-bug/scripts/report_lint.py",
                "purpose": "Revisa que el reporte ejecutivo y el técnico sigan las plantillas de report-bug (síntoma, impacto, pasos numerados, entorno y versión, evidencia, causa con archivo:línea o 'Causa no identificada', corrección). Solo lectura. gsheets_updater.py lo ejecuta y no publica con errores.",
                "flags": [
                    {"flag": "<ejecutivo.md> [<tecnico.md>]", "type": "positional", "description": "Reportes a revisar; el que termina en _tecnico.md se revisa como técnico."},
                    {"flag": "--tecnico <archivo>", "type": "string", "description": "Revisa ese archivo como reporte técnico aunque no termine en _tecnico.md."},
                    {"flag": "--json", "type": "boolean", "description": "Errores y advertencias en JSON."}
                ],
                "examples": [
                    "python skills/report-bug/scripts/report_lint.py Reportes/AF-351_x.md Reportes/AF-351_x_tecnico.md"
                ]
            }
        }
    },
    "qa-finish": {
        "description": "Cierre formal de defectos verificados en vivo por el asistente: veredicto desde plantilla, lint y fila 'Finalizada' en Google Sheets.",
        "scripts": {
            "qa_finish_publisher.py": {
                "path": "skills/qa-finish/scripts/qa_finish_publisher.py",
                "purpose": "Publica un veredicto de cierre: pasa verdict.py lint, resuelve la fila, pide confirmación y escribe ESTADO Finalizada, FECHA TERMINO, CERRADA POR y el veredicto completo en COMENTARIO QA.",
                "flags": [
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra fila, estado actual y lo que se escribiría sin escribir nada; imprime confirm_code si el lint pasa."},
                    {"flag": "--confirm <código>", "type": "string", "description": "Obligatorio para publicar: el confirm_code del dry-run del mismo archivo. Sin él sale con código 4."},
                    {"flag": "<veredicto.md>", "type": "positional", "description": "Veredicto escrito desde skills/shared/templates/veredicto.md con encabezado '# AF-NNN — Veredicto QA: Finalizada'."}
                ],
                "examples": [
                    "python skills/shared/verdict.py lint Reportes/exito/AF-228_veredicto.md",
                    "python skills/qa-finish/scripts/qa_finish_publisher.py --dry-run Reportes/exito/AF-228_veredicto.md",
                    "python skills/qa-finish/scripts/qa_finish_publisher.py --confirm 1a2b3c4d Reportes/exito/AF-228_veredicto.md"
                ]
            },
            "verdict.py (shared)": {
                "path": "skills/shared/verdict.py",
                "purpose": "Lint del veredicto (cierre o rechazo): versión probada, criterio del ticket, tres preguntas sobre el cambio, casos ejecutados con evidencia [R]/[DB] (ticket + control), límites, sin frases de suposición. Solo lectura.",
                "flags": [
                    {"flag": "lint <veredicto.md>", "type": "subcommand", "description": "Revisa el archivo; código 1 con errores."},
                    {"flag": "--json", "type": "boolean", "description": "Errores y advertencias en JSON."}
                ],
                "examples": ["python skills/shared/verdict.py lint Reportes/rechazo/AF-181_veredicto.md --json"]
            }
        }
    },
    "qa-rejection": {
        "description": "Rechazo formal de fixes que fallaron en la verificación en vivo: veredicto desde plantilla, lint y fila 'Rechazada por QA' en Google Sheets.",
        "scripts": {
            "qa_rejection_publisher.py": {
                "path": "skills/qa-rejection/scripts/qa_rejection_publisher.py",
                "purpose": "Publica un veredicto de rechazo (al menos un caso en Falla): pasa verdict.py lint, resuelve la fila, pide confirmación y escribe ESTADO Rechazada por QA, FECHA TERMINO, CERRADA POR y el veredicto completo en COMENTARIO QA.",
                "flags": [
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra fila, estado actual y lo que se escribiría sin escribir nada; imprime confirm_code si el lint pasa."},
                    {"flag": "--confirm <código>", "type": "string", "description": "Obligatorio para publicar: el confirm_code del dry-run del mismo archivo. Sin él sale con código 4."},
                    {"flag": "<veredicto.md>", "type": "positional", "description": "Veredicto con encabezado '# AF-NNN — Veredicto QA: Rechazada por QA'."}
                ],
                "examples": [
                    "python skills/qa-rejection/scripts/qa_rejection_publisher.py --dry-run Reportes/rechazo/AF-181_veredicto.md"
                ]
            }
        }
    },
    "qa-amplify": {
        "description": "Agrega evidencia a un defecto existente sin cambiar su estado (bloque 'Ampliación (<origen>)' al final de Comentario QA).",
        "scripts": {
            "qa_amplify_publisher.py": {
                "path": "skills/qa-amplify/scripts/qa_amplify_publisher.py",
                "purpose": "Agrega la evidencia al final de Comentario QA del ticket, guarda copia en Reportes/ampliaciones/ y no toca el estado. No duplica un origen ya agregado.",
                "flags": [
                    {"flag": "<defect_id> <origen> <evidencia>", "type": "positional", "description": "Modo un ticket. La evidencia puede venir de --body-file."},
                    {"flag": "--file / --origin", "type": "string", "description": "Modo lote: archivo con secciones '## AF-XXX — título' separadas por '---'."},
                    {"flag": "--only", "type": "string", "description": "Con --file, solo estos IDs (separados por coma)."},
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra destinos y contenido sin escribir nada e imprime confirm_code del lote. Usarlo siempre antes de publicar."},
                    {"flag": "--confirm <código>", "type": "string", "description": "Obligatorio para publicar: el confirm_code del dry-run del mismo lote. Sin él sale con código 4."}
                ],
                "examples": [
                    "python skills/qa-amplify/scripts/qa_amplify_publisher.py --dry-run \"AF-259\" \"E2E_Apiux_2026-09-25\" \"Causa confirmada en logs de qa-agent: ...\"",
                    "python skills/qa-amplify/scripts/qa_amplify_publisher.py --dry-run --file Reportes/ampliaciones/lote.md --origin \"E2E_Apiux_2026-09-25\""
                ]
            }
        }
    },
    "qa-help": {
        "description": "Catálogo completo de skills, scripts, sintaxis y flags.",
        "scripts": {
            "help.py": {
                "path": "skills/qa-help/scripts/help.py",
                "purpose": "Muestra este catálogo interactivo.",
                "flags": [
                    {"flag": "--skill", "type": "string", "description": "Filtra por una skill específica (ej. qa-preflight)."},
                    {"flag": "--json", "type": "boolean", "description": "Entrega todo el catálogo en formato JSON."}
                ],
                "examples": [
                    "python skills/qa-help/scripts/help.py",
                    "python skills/qa-help/scripts/help.py --skill qa-preflight",
                    "python skills/qa-help/scripts/help.py --json"
                ]
            }
        }
    },
    "qa-update": {
        "description": "Detección de nuevas versiones y actualización segura del plugin desde GitHub.",
        "scripts": {
            "update_plugin.py": {
                "path": "skills/qa-update/scripts/update_plugin.py",
                "purpose": "Comprueba si hay nuevos commits en origin/main, muestra changelog y actualiza el plugin con git pull.",
                "flags": [
                    {"flag": "--check", "type": "boolean", "description": "Comprueba si existen actualizaciones pendientes en el repositorio remoto."},
                    {"flag": "--update", "type": "boolean", "description": "Descarga e instala la última versión disponible de iafactory-qa-kit."},
                    {"flag": "--version", "type": "boolean", "description": "Muestra la versión actual instalada y commit HEAD."},
                    {"flag": "--json", "type": "boolean", "description": "Salida estructurada en JSON para procesamiento de agentes."}
                ],
                "examples": [
                    "python skills/qa-update/scripts/update_plugin.py --check",
                    "python skills/qa-update/scripts/update_plugin.py --check --json",
                    "python skills/qa-update/scripts/update_plugin.py --update",
                    "python skills/qa-update/scripts/update_plugin.py --version"
                ]
            }
        }
    }
}

def print_markdown(filter_skill=None):
    print("=" * 70)
    print("  📖 CATÁLOGO COMPLETO DE SKILLS, SCRIPTS Y FLAGS (`iafactory-qa-kit`)")
    print("=" * 70)
    print("Consulta rápida de capacidades operativas para agentes de IA y desarrolladores.\n")

    skills_to_show = {filter_skill: CATALOG[filter_skill]} if filter_skill and filter_skill in CATALOG else CATALOG

    for s_name, s_data in skills_to_show.items():
        print(f"### 📦 Skill: `{s_name}`")
        print(f"*{s_data['description']}*\n")
        
        for sc_name, sc_data in s_data["scripts"].items():
            print(f"#### 📄 Script: `{sc_name}` (`{sc_data['path']}`)")
            print(f"• **Propósito:** {sc_data['purpose']}")
            
            if sc_data["flags"]:
                print("• **Parámetros y Flags:**")
                for f in sc_data["flags"]:
                    def_str = f" (Por defecto: `{f['default']}`)" if "default" in f else ""
                    choice_str = f" [Opciones: {', '.join(f['choices'])}]" if "choices" in f else ""
                    print(f"  - `{f['flag']}` ({f['type']}){def_str}{choice_str}: {f['description']}")
            else:
                print("• **Parámetros y Flags:** Ninguno (ejecución directa)")

            if sc_data["examples"]:
                print("• **Ejemplos de Uso:**")
                for ex in sc_data["examples"]:
                    print(f"  ```bash\n  {ex}\n  ```")
            print()
        print("-" * 70)

def main():
    parser = argparse.ArgumentParser(description="IAFactory QA Kit Command & Flag Catalog.")
    parser.add_argument("--skill", type=str, default=None, help="Filtrar por skill específica")
    parser.add_argument("--json", action="store_true", help="Salida en JSON estructurado")
    args = parser.parse_args()

    if args.json:
        if args.skill and args.skill in CATALOG:
            print(json.dumps(CATALOG[args.skill], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(CATALOG, indent=2, ensure_ascii=False))
        return

    print_markdown(args.skill)

if __name__ == "__main__":
    main()
