#!/usr/bin/env python3
"""
IAFactory QA Kit - Welcome & Interactive Onboarding
---------------------------------------------------
Provides a unified guide, environment status, and command catalog
for new developers and AI assistants.
"""

import os
import sys
import json
import shutil
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SHARED_DIR = os.path.join(SKILLS_DIR, "shared")
PLUGIN_ROOT = os.path.dirname(SKILLS_DIR)

sys.path.append(SHARED_DIR)
try:
    import utils
except ImportError:
    utils = None

def get_status_data():
    data = {
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "workspace_root": utils.WORKSPACE_ROOT if utils else os.getcwd(),
        "reporter": "Desconocido",
        "gcloud_auth": False,
        "notion_token": False,
        "submodules": {}
    }
    
    if utils:
        data["reporter"] = utils.get_user_name()
        ntok = utils.get_notion_token()
        data["notion_token"] = bool(ntok)

    # Check gcloud
    if shutil.which("gcloud"):
        try:
            tok = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"],
                text=True,
                stderr=subprocess.PIPE,
                shell=(sys.platform == "win32")
            ).strip()
            if tok and not tok.startswith("ERROR"):
                data["gcloud_auth"] = True
        except Exception:
            data["gcloud_auth"] = False

    # Check submodules in workspace root
    ws = data["workspace_root"]
    repos = utils.get_product_repos() if utils else ["ai-factory-core", "ai-factory-agents", "ai-factory-frontend", "ai-factory-platform"]
    for repo in repos:
        repo_path = os.path.join(ws, repo)
        data["submodules"][repo] = os.path.exists(repo_path)

    return data

def main():
    if "--json" in sys.argv:
        print(json.dumps(get_status_data(), indent=2, ensure_ascii=False))
        return

    data = get_status_data()

    # Version check
    try:
        sys.path.append(os.path.join(SKILLS_DIR, "qa-update", "scripts"))
        import update_plugin
        data["plugin_info"] = update_plugin.get_local_version_info()
    except Exception:
        data["plugin_info"] = {"version": "1.1.1", "commit": "local"}

    print("=" * 65)
    print("  👋 BIENVENIDO AL PLUGIN IAFACTORY QA KIT (`iafactory-qa-kit`)")
    print("=" * 65)
    print("Kit autónomo y portable para Aseguramiento de Calidad y Observabilidad.")
    print(f"Plataforma: {data['platform']} | Python: {data['python_version']}")
    p_info = data.get("plugin_info", {})
    print(f"Plugin    : v{p_info.get('version', '1.0.0')} (Commit: `{p_info.get('commit', 'local')}`) | Workspace: {data['workspace_root']}")
    print(f"Usuario   : 👤 {data['reporter']}")
    print("-" * 65)
    
    print("\n🔍 ESTADO DE CONECTIVIDAD Y SERVICIOS:")
    print(f"  {'Google Cloud Auth (Sheets API)':<32}: {'✅ Activo' if data['gcloud_auth'] else '⚠️ No activo (corre: gcloud auth login --enable-gdrive-access)'}")
    print(f"  {'Notion API (NOTION_TOKEN)':<32}: {'✅ Configurado' if data['notion_token'] else '⚠️ No configurado'}")
    if not data['notion_token']:
        print(f"     👉 Configura NOTION_TOKEN en: {os.path.join(data['workspace_root'], '.env')}")
    
    print("\n📂 REPOSITORIOS PRODUCTO DETECTADOS:")
    for repo, exists in data["submodules"].items():
        print(f"  - {repo:<22}: {'✅ Presente' if exists else '❌ No encontrado (ejecuta git submodule update --init)'}")

    print("\n" + "=" * 65)
    print("  🚀 COMANDOS ESENCIALES (CHEATSHEET DE QA)")
    print("=" * 65)
    print("1. Revisar defectos pendientes en Google Sheets:")
    print("   python skills/qa-backlog/scripts/fetch_issues.py --status \"Pendiente,En Revisión\"\n")
    print("2. Auditar commits o cambios de código de un issue:")
    print("   python skills/qa-code-audit/scripts/audit_changes.py --issue \"AF-XXX\"\n")
    print("3. Pre-flight check (Túneles IAP, DB y puertos antes de probar):")
    print("   python skills/qa-preflight/scripts/check_env.py\n")
    print("4. Reportar un nuevo defecto formalmente:")
    print("   python skills/report-bug/scripts/gsheets_updater.py \"<Título>\" \"<Descripción>\" \"<Gravedad>\"\n")
    print("5. Cerrar y aprobar formalmente un ticket verificado:")
    print("   python skills/qa-finish/scripts/qa_finish_publisher.py \"AF-XXX\" \"<Resumen>\" \"<Evidencia>\"\n")
    print("6. Rechazar formalmente un fix fallido o incompleto:")
    print("   python skills/qa-rejection/scripts/qa_rejection_publisher.py \"AF-XXX\" \"<Motivo>\" \"<Detalle>\" \"<Diff>\"\n")
    print("=" * 65)
    print("📖 Consulta la metodología completa en: docs/METODOLOGIA_QA_IAFACTORY.md")
    print("🛡️ Reglas y gobernanza HHH en: rules/AGENTS.md\n")

if __name__ == "__main__":
    main()
