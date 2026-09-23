#!/usr/bin/env python3
"""
IAFactory QA Kit - Auto-Updater & Version Manager CLI
-----------------------------------------------------
Checks for new versions of the iafactory-qa-kit plugin from its remote Git
repository (https://github.com/AlonsoSalasApiux/iafactory-qa-kit.git).
Allows verifying update status, viewing new commits/changelog, and safely
updating the plugin with a single command.

Usage:
    python update_plugin.py --check [--json]
    python update_plugin.py --update
    python update_plugin.py --version
"""

import os
import sys
import json
import argparse
import subprocess

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))


def run_git_cmd(args, cwd=PLUGIN_ROOT, timeout=30):
    """Executes a git command inside the plugin repository safely."""
    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=(sys.platform == "win32"),
            encoding="utf-8",
            errors="replace",
            env=env
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def get_local_version_info():
    """Reads version from plugin.json and current git commit."""
    version = "1.0.0"
    plugin_json_path = os.path.join(PLUGIN_ROOT, "plugin.json")
    if os.path.exists(plugin_json_path):
        try:
            with open(plugin_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                version = data.get("version", "1.0.0")
        except Exception:
            pass

    rc, branch, _ = run_git_cmd(["branch", "--show-current"])
    rc, commit_hash, _ = run_git_cmd(["log", "-1", "--format=%h"])
    rc, commit_date, _ = run_git_cmd(["log", "-1", "--format=%cI"])
    rc, commit_msg, _ = run_git_cmd(["log", "-1", "--format=%s"])

    return {
        "version": version,
        "branch": branch or "main",
        "commit": commit_hash or "unknown",
        "commit_date": commit_date or "unknown",
        "commit_message": commit_msg or "unknown"
    }


def check_for_updates():
    """Fetches remote git origin and checks if there are new commits on main."""
    local_info = get_local_version_info()
    branch = local_info["branch"] or "main"

    # Fetch remote silently
    rc, _, err = run_git_cmd(["fetch", "origin", branch, "--quiet"], timeout=30)
    if rc != 0:
        return {
            "success": False,
            "error": f"No se pudo conectar al repositorio remoto para verificar actualizaciones: {err}",
            "local": local_info,
            "has_update": False,
            "behind_count": 0,
            "new_commits": []
        }

    # Count commits behind
    rc, behind_str, _ = run_git_cmd(["rev-list", "--count", f"HEAD..origin/{branch}"])
    behind_count = int(behind_str) if rc == 0 and behind_str.isdigit() else 0

    new_commits = []
    if behind_count > 0:
        rc, logs_str, _ = run_git_cmd(["log", f"HEAD..origin/{branch}", "--oneline", "-n", "10"])
        if rc == 0 and logs_str:
            new_commits = logs_str.splitlines()

    return {
        "success": True,
        "local": local_info,
        "has_update": behind_count > 0,
        "behind_count": behind_count,
        "new_commits": new_commits
    }


def perform_update():
    """Pulls the latest changes from origin and verifies environment."""
    check_res = check_for_updates()
    if not check_res["success"]:
        print(f"❌ Error al comprobar actualizaciones: {check_res['error']}")
        return False

    if not check_res["has_update"]:
        print(f"✅ El plugin ya se encuentra en su versión más reciente (Commit {check_res['local']['commit']} en {check_res['local']['branch']}).")
        return True

    print(f"🚀 Actualizando iafactory-qa-kit ({check_res['behind_count']} commits pendientes)...")
    branch = check_res["local"]["branch"] or "main"

    rc, out, err = run_git_cmd(["pull", "origin", branch])
    if rc != 0:
        print(f"❌ Error al ejecutar git pull: {err}")
        print("💡 Si tienes cambios locales sin confirmar en el plugin, guárdalos o haz stash antes de actualizar.")
        return False

    print("✅ Código del plugin actualizado correctamente:")
    print(out)

    # Re-read version
    new_info = get_local_version_info()
    print(f"\n🎉 Plugin actualizado exitosamente a la versión {new_info['version']} (Commit: {new_info['commit']}).")
    return True


def main():
    parser = argparse.ArgumentParser(description="Gestor de Versión y Actualizaciones para iafactory-qa-kit.")
    parser.add_argument("--check", action="store_true", help="Comprueba si existen actualizaciones en el repositorio remoto")
    parser.add_argument("--update", action="store_true", help="Descarga e instala la última versión disponible del plugin")
    parser.add_argument("--version", action="store_true", help="Muestra la versión local actual y el commit activo")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON para asistentes de IA")

    args = parser.parse_args()

    if args.version:
        info = get_local_version_info()
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print(f"iafactory-qa-kit v{info['version']} ({info['branch']} @ {info['commit']})")
        return

    if args.update:
        success = perform_update()
        sys.exit(0 if success else 1)

    # Por defecto o con --check
    status = check_for_updates()
    if args.json:
        print(json.dumps(status, indent=2))
        return

    print("=" * 65)
    print("  🔄 ESTADO DE ACTUALIZACIÓN: IAFACTORY QA KIT")
    print("=" * 65)
    loc = status["local"]
    print(f"Versión Local Instalada : v{loc['version']} (Rama: {loc['branch']})")
    print(f"Commit HEAD Activo      : {loc['commit']} ({loc['commit_date'][:10]})")
    print(f"Último Mensaje Local    : {loc['commit_message']}")
    print("-" * 65)

    if not status["success"]:
        print(f"⚠️ {status['error']}")
    elif status["has_update"]:
        print(f"🔔 ¡NUEVA ACTUALIZACIÓN DISPONIBLE! ({status['behind_count']} commits pendientes en remoto)")
        print("\n📋 Novedades pendientes:")
        for c in status["new_commits"]:
            print(f"   • {c}")
        print("\n👉 Para actualizar ahora ejecuta:")
        print("   python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --update\n")
    else:
        print("🟢 El plugin está 100% actualizado con origin/main. No hay cambios pendientes.")
    print("=" * 65)


if __name__ == "__main__":
    main()
