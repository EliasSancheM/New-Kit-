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
                "purpose": "Verifica Python, Git, gcloud, Notion y presencia de los 4 repositorios.",
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
                    {"flag": "--status", "type": "string", "default": "Pendiente,En Revisión,Reportada", "description": "Filtro por estados separados por coma (ej. 'En Revisión' o 'all')."},
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
                "purpose": "Crea los documentos de la corrida desde las plantillas en QA_KIT_E2E_DIR (por defecto Reportes/E2E/). Solo archivos locales; nunca sobrescribe.",
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
                "purpose": "Verifica en <500ms los puertos del túnel del entorno (Postgres, Qdrant, Redis, Prometheus...) y las credenciales de gcloud/Notion.",
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
        "description": "Reporte formal de nuevos defectos (Notion 2 niveles + Google Sheets online).",
        "scripts": {
            "gsheets_updater.py": {
                "path": "skills/report-bug/scripts/gsheets_updater.py",
                "purpose": "Audita próximo ID disponible e inserta fila en Google Sheets.",
                "flags": [
                    {"flag": "--audit", "type": "boolean", "description": "Solo audita e imprime el próximo ID (AF-XXX) y fila destino sin escribir nada."},
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra qué se escribiría en Notion/Sheets sin escribir nada. Usarlo siempre antes de publicar."},
                    {"flag": "<nombre> <descripción> <gravedad> [notion_url]", "type": "positional", "description": "Parámetros posicionales para registrar el defecto."}
                ],
                "examples": [
                    "python skills/report-bug/scripts/gsheets_updater.py --audit",
                    "python skills/report-bug/scripts/gsheets_updater.py \"Error en login SSO\" \"Fallo al validar token\" \"Alta\" \"https://notion.so/...\""
                ]
            },
            "notion_mcp_publisher.py": {
                "path": "skills/report-bug/scripts/notion_mcp_publisher.py",
                "purpose": "Publica reportes markdown en Notion con arquitectura anidada de 2 niveles.",
                "flags": [
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra qué se escribiría en Notion/Sheets sin escribir nada. Usarlo siempre antes de publicar."},
                    {"flag": "<file_l1> <file_l2> <defect_id> <short_name>", "type": "positional", "description": "Archivos markdown de nivel 1 y 2 para publicar."}
                ],
                "examples": [
                    "python skills/report-bug/scripts/notion_mcp_publisher.py Reportes/AF-229.md Reportes/AF-229_tecnico.md AF-229 sso_bug"
                ]
            }
        }
    },
    "qa-finish": {
        "description": "Aprobación y resolución de defectos verificados empíricamente.",
        "scripts": {
            "qa_finish_publisher.py": {
                "path": "skills/qa-finish/scripts/qa_finish_publisher.py",
                "purpose": "Genera reporte local de éxito, subpágina en Notion y actualiza Google Sheets a 'Finalizada'.",
                "flags": [
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra qué se escribiría en Notion/Sheets sin escribir nada. Usarlo siempre antes de publicar."},
                    {"flag": "<defect_id>", "type": "string", "description": "Identificador del issue (AF-XXX)."},
                    {"flag": "<resumen_validacion>", "type": "string", "description": "Resumen ejecutivo de la verificación exitosa."},
                    {"flag": "<detalle_pruebas_evidencia>", "type": "string", "description": "Pasos ejecutados, logs o evidencia de prueba."},
                    {"flag": "[conclusion]", "type": "string", "default": "Aprobado", "description": "Conclusión final de QA."},
                    {"flag": "[level1_page_id]", "type": "string", "default": "Auto", "description": "ID de Notion padre si no se puede auto-resolver de Sheets."}
                ],
                "examples": [
                    "python skills/qa-finish/scripts/qa_finish_publisher.py \"AF-228\" \"SSO RBAC verificado sin fugas\" \"10 intentos con rol member bloqueados\" \"Aprobado\""
                ]
            }
        }
    },
    "qa-rejection": {
        "description": "Rechazo formal de tickets con soluciones incompletas o fallidas.",
        "scripts": {
            "qa_rejection_publisher.py": {
                "path": "skills/qa-rejection/scripts/qa_rejection_publisher.py",
                "purpose": "Genera reporte de rechazo con AI Warning Banner, subpágina en Notion y marca 'Rechazada por QA' en Google Sheets.",
                "flags": [
                    {"flag": "--dry-run", "type": "boolean", "description": "Muestra qué se escribiría en Notion/Sheets sin escribir nada. Usarlo siempre antes de publicar."},
                    {"flag": "<defect_id>", "type": "string", "description": "Identificador del issue (AF-XXX)."},
                    {"flag": "<motivo_rechazo>", "type": "string", "description": "Razón principal por la cual no se acepta el fix."},
                    {"flag": "<detalle_falla_empirica>", "type": "string", "description": "Evidencia de la replicación o error observado."},
                    {"flag": "<cambios_encontrados_diff>", "type": "string", "description": "Análisis del código del desarrollador o causa raíz pendiente."},
                    {"flag": "[level1_page_id]", "type": "string", "default": "Auto", "description": "ID de Notion padre si no se puede auto-resolver de Sheets."}
                ],
                "examples": [
                    "python skills/qa-rejection/scripts/qa_rejection_publisher.py \"AF-228\" \"Falta limpieza de listener\" \"Memory leak al cerrar tab\" \"useEffect sin return cleanup\""
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
