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
        "sheets_token_source": None,
        "submodules": {}
    }

    if utils:
        data["reporter"] = utils.get_user_name()
        data["sheets_token_source"] = utils.sheets_token_source() or None

    # Check submodules in workspace root
    ws = data["workspace_root"]
    repos = utils.get_product_repos() if utils else ["ai-factory-core", "ai-factory-agents", "ai-factory-frontend", "ai-factory-platform"]
    for repo in repos:
        repo_path = os.path.join(ws, repo)
        data["submodules"][repo] = os.path.exists(repo_path)

    return data

def _read_version(plugin_json: str) -> str:
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "?")
    except (OSError, ValueError):
        return "?"


def _file_hash(path: str) -> str:
    import hashlib
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        return ""


def find_stale_copies() -> list:
    """Other copies of the kit's skills that an assistant could load instead of this one.

    Different teammates ended up running different methods because an old copy of a skill
    (in <workspace>/.claude/skills or an older installed plugin) was loaded silently.
    Returns one entry per copy whose content differs from this kit.
    """
    this_version = _read_version(os.path.join(PLUGIN_ROOT, "plugin.json"))
    this_root = os.path.realpath(PLUGIN_ROOT)
    stale = []

    ws = utils.WORKSPACE_ROOT if utils else os.getcwd()
    local_skills = os.path.join(ws, ".claude", "skills")
    if os.path.isdir(local_skills):
        for name in sorted(os.listdir(local_skills)):
            ours = os.path.join(SKILLS_DIR, name, "SKILL.md")
            theirs = os.path.join(local_skills, name, "SKILL.md")
            if not os.path.isfile(ours) or not os.path.isfile(theirs):
                continue
            if os.path.realpath(theirs) == os.path.realpath(ours):
                continue  # junction/symlink to this kit: always in sync
            if _file_hash(ours) != _file_hash(theirs):
                stale.append({"where": os.path.join(local_skills, name), "kind": "copia en .claude/skills",
                              "detail": "SKILL.md distinto al del kit"})

    # Claude Code keeps old versions in its cache but only loads what installed_plugins.json lists.
    registry = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "installed_plugins.json")
    try:
        with open(registry, "r", encoding="utf-8") as f:
            plugins = json.load(f).get("plugins", {})
    except (OSError, ValueError):
        plugins = {}
    for key, installs in plugins.items():
        if not key.startswith("iafactory-qa-kit"):
            continue
        for inst in installs if isinstance(installs, list) else [installs]:
            path = inst.get("installPath", "")
            if path and os.path.realpath(path) == this_root:
                continue
            v = inst.get("version") or _read_version(os.path.join(path, "plugin.json"))
            if v != this_version:
                stale.append({"where": path, "kind": f"plugin instalado en Claude Code ({inst.get('scope', '?')})",
                              "detail": f"versión {v} (este kit: {this_version})"})
    return stale


RULES_PATH = os.path.join(PLUGIN_ROOT, "rules", "AGENTS.md")

def read_rules() -> str:
    try:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""

def main():
    if "--json" in sys.argv:
        data = get_status_data()
        data["rules_path"] = RULES_PATH
        data["kit_root"] = PLUGIN_ROOT
        data["stale_copies"] = find_stale_copies()
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    data = get_status_data()

    # Version check
    try:
        sys.path.append(os.path.join(SKILLS_DIR, "qa-update", "scripts"))
        import update_plugin
        data["plugin_info"] = update_plugin.get_local_version_info()
    except Exception:
        try:
            with open(os.path.join(PLUGIN_ROOT, "plugin.json"), "r", encoding="utf-8") as f:
                data["plugin_info"] = {"version": json.load(f).get("version", "?"), "commit": "n/d"}
        except Exception:
            data["plugin_info"] = {"version": "?", "commit": "n/d"}

    print("=" * 65)
    print("  👋 BIENVENIDO AL PLUGIN IAFACTORY QA KIT (`iafactory-qa-kit`)")
    print("=" * 65)
    print("Kit autónomo y portable para Aseguramiento de Calidad y Observabilidad.")
    print(f"Plataforma: {data['platform']} | Python: {data['python_version']}")
    p_info = data.get("plugin_info", {})
    print(f"Plugin    : v{p_info.get('version', '1.0.0')} (Commit: `{p_info.get('commit', 'local')}`) | Workspace: {data['workspace_root']}")
    print(f"Usuario   : 👤 {data['reporter']}")
    print(f"Kit en uso: {PLUGIN_ROOT}")
    stale = find_stale_copies()
    if stale:
        print("\n⚠️ HAY OTRAS COPIAS DEL KIT QUE NO COINCIDEN CON ESTA (pueden cargarse en su lugar y aplicar un método viejo):")
        for s in stale:
            print(f"  - [{s['kind']}] {s['where']} → {s['detail']}")
        print("  👉 Actualízalas (qa-update) o elimínalas, y reinicia el chat. Avísale al usuario antes de seguir.")
    print("-" * 65)
    
    print("\n🔍 ESTADO DE CONECTIVIDAD Y SERVICIOS:")
    src = data["sheets_token_source"]
    print(f"  {'Google Sheets API (token)':<32}: {('✅ Activo, fuente: ' + src) if src else '⚠️ Sin token'}")
    if not src:
        print(f"     👉 {utils.SHEETS_TOKEN_HELP if utils else 'Configura SHEETS_ACCESS_TOKEN en el .env del workspace.'}")
    if src == "pegado":
        print("     ℹ️ El token pegado dura 60 min: antes de publicar o cambiar estados, pide uno nuevo y pégalo en el .env.")

    print("\n📂 REPOSITORIOS PRODUCTO DETECTADOS (QA_KIT_REPOS, relativos al workspace):")
    for repo, exists in data["submodules"].items():
        print(f"  - {repo:<34}: {'✅ Presente' if exists else '❌ No encontrado (clónalo o ajusta QA_KIT_REPOS en el .env)'}")

    print("\n" + "=" * 65)
    print("  🚀 COMANDOS ESENCIALES (CHEATSHEET DE QA)")
    print("=" * 65)
    kit = PLUGIN_ROOT
    print(f"(Rutas absolutas; el kit está en: {kit})\n")
    print("1. Revisar defectos pendientes en Google Sheets (usa --limit alto para no truncar):")
    print(f"   python \"{kit}/skills/qa-backlog/scripts/fetch_issues.py\" --status \"Reportada,En Revisión,En curso\" --limit 500\n")
    print("2. Auditar commits o cambios de código de un issue:")
    print(f"   python \"{kit}/skills/qa-code-audit/scripts/audit_changes.py\" --issue \"AF-XXX\"\n")
    print("3. Pre-flight check (túneles IAP, DB y puertos antes de probar; --env dev|qa|team-devs):")
    print(f"   python \"{kit}/skills/qa-preflight/scripts/check_env.py\" --env dev\n")
    print("4. Reportar un nuevo defecto desde sus dos reportes (siempre --dry-run primero):")
    print(f"   python \"{kit}/skills/report-bug/scripts/gsheets_updater.py\" --dry-run Reportes/AF-XXX_x.md Reportes/AF-XXX_x_tecnico.md\n")
    print("5. Cerrar y aprobar formalmente un ticket verificado (siempre --dry-run primero):")
    print(f"   python \"{kit}/skills/qa-finish/scripts/qa_finish_publisher.py\" --dry-run --build \"<commit probado>\" \"AF-XXX\" \"<Resumen>\" \"<Evidencia>\" \"<Conclusión>\"\n")
    print("6. Rechazar formalmente un fix fallido o incompleto (siempre --dry-run primero):")
    print(f"   python \"{kit}/skills/qa-rejection/scripts/qa_rejection_publisher.py\" --dry-run --build \"<commit probado>\" \"AF-XXX\" \"<Motivo>\" \"<Detalle>\" \"<Diff>\"\n")
    print("   Para publicar de verdad: el mismo comando con --confirm <confirm_code del dry-run> en vez de --dry-run.\n")
    print("7. Agregar evidencia a un ticket existente sin cambiar su estado (siempre --dry-run primero):")
    print(f"   python \"{kit}/skills/qa-amplify/scripts/qa_amplify_publisher.py\" --dry-run \"AF-XXX\" \"<Origen>\" \"<Evidencia>\"\n")
    print("8. Corrida E2E: crear el documento 'Antes' del proyecto y el de la corrida (método en skills/qa-e2e-corrida/SKILL.md):")
    print(f"   python \"{kit}/skills/qa-e2e-corrida/scripts/new_run.py\" proyecto <slug>")
    print(f"   python \"{kit}/skills/qa-e2e-corrida/scripts/new_run.py\" corrida <empresa> <slug>")
    print("   Al cerrar, validar el documento (0 errores para darlo por terminado):")
    print(f"   python \"{kit}/skills/qa-e2e-corrida/scripts/validate_run.py\" <documento_corrida.md>\n")
    print("=" * 65)
    print(f"📖 Metodología completa: {kit}/docs/METODOLOGIA_QA_IAFACTORY.md")

    if "--no-rules" in sys.argv:
        print(f"🛡️ Reglas de operación (no impresas por --no-rules): {RULES_PATH}\n")
        return

    rules = read_rules()
    print("\n" + "=" * 65)
    print("  🛡️ REGLAS DE OPERACIÓN DEL KIT: VIGENTES PARA TODA ESTA CONVERSACIÓN")
    print("=" * 65)
    print("(Contenido de rules/AGENTS.md. Aplícalas en cada tarea de QA de este chat.)\n")
    print(rules if rules else f"⚠️ No se pudo leer {RULES_PATH}. Léelo manualmente antes de continuar.")
    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    main()
