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


# ---------------------------------------------------------------------------
# Claude Code plugin install. Claude Code installs the kit from its own clone of
# the repo (a "marketplace") and never refreshes that clone by itself, so a
# `git pull` of the workspace copy leaves the installed plugin on an old version.
# ---------------------------------------------------------------------------
PLUGIN_NAME = "iafactory-qa-kit"
CLAUDE_PLUGINS_DIR = os.path.join(os.path.expanduser("~"), ".claude", "plugins")


def _version_tuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except ValueError:
        return (0,)


def find_claude_cli():
    """The `claude` CLI: PATH first, then the copy bundled with the desktop app."""
    import glob
    import shutil
    found = shutil.which("claude")
    if found:
        return found
    candidates = []
    if sys.platform == "win32":
        candidates = glob.glob(os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude-code", "*", "claude.exe"))
    elif sys.platform == "darwin":
        candidates = glob.glob(os.path.expanduser("~/Library/Application Support/Claude/claude-code/*/claude"))
    candidates += glob.glob(os.path.expanduser("~/.local/bin/claude"))
    candidates.sort(key=lambda p: _version_tuple(os.path.basename(os.path.dirname(p))), reverse=True)
    return candidates[0] if candidates else None


def claude_plugin_status():
    """Installed version of the kit in Claude Code and the latest version on its marketplace remote."""
    try:
        with open(os.path.join(CLAUDE_PLUGINS_DIR, "installed_plugins.json"), encoding="utf-8") as f:
            plugins = json.load(f).get("plugins", {})
    except (OSError, ValueError):
        return None
    key = next((k for k in plugins if k.split("@")[0] == PLUGIN_NAME), None)
    if not key:
        return None
    installs = plugins[key] if isinstance(plugins[key], list) else [plugins[key]]
    installed = installs[0].get("version", "?") if installs else "?"
    marketplace = key.split("@", 1)[1] if "@" in key else ""

    # The repo is private, so the version is read through git in Claude Code's own
    # marketplace clone (it already has access). `fetch` only updates remote refs;
    # the installed plugin does not change until `claude plugin update`.
    remote_version = None
    try:
        with open(os.path.join(CLAUDE_PLUGINS_DIR, "known_marketplaces.json"), encoding="utf-8") as f:
            location = json.load(f).get(marketplace, {}).get("installLocation")
    except (OSError, ValueError):
        location = None
    if location and os.path.isdir(os.path.join(location, ".git")):
        rc, _, _ = run_git_cmd(["fetch", "--quiet", "origin"], cwd=location, timeout=45)
        if rc == 0:
            for ref in ("origin/HEAD", "origin/main"):
                rc, out, _ = run_git_cmd(["show", f"{ref}:.claude-plugin/plugin.json"], cwd=location)
                if rc == 0:
                    try:
                        remote_version = json.loads(out).get("version")
                    except ValueError:
                        pass
                    break
    return {
        "key": key, "marketplace": marketplace, "installed_version": installed,
        "remote_version": remote_version,
        "has_update": bool(remote_version) and _version_tuple(remote_version) > _version_tuple(installed),
    }


def update_claude_plugin(status):
    cli = find_claude_cli()
    if not cli:
        print("⚠️ No encontré el comando `claude`. Actualiza el plugin a mano en una terminal:")
        print(f"   claude plugin marketplace update {status['marketplace']}")
        print(f"   claude plugin update {status['key']}")
        return False
    for step in (["plugin", "marketplace", "update", status["marketplace"]], ["plugin", "update", status["key"]]):
        proc = subprocess.run([cli] + step, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
        print((proc.stdout or proc.stderr).strip())
        if proc.returncode != 0:
            print(f"❌ Falló: claude {' '.join(step)}")
            return False
    print("🔁 Reinicia Claude Code (o abre una sesión nueva) para que cargue la versión nueva del plugin.")
    return True


def is_git_repo():
    rc, out, _ = run_git_cmd(["rev-parse", "--is-inside-work-tree"])
    return rc == 0 and out == "true"


def perform_update():
    """Updates the workspace copy (git) and the Claude Code plugin install, whichever exist."""
    ok = True
    plugin = claude_plugin_status()
    if plugin and plugin["has_update"]:
        print(f"🚀 Plugin de Claude Code: {plugin['installed_version']} → {plugin['remote_version']}")
        ok = update_claude_plugin(plugin) and ok
    elif plugin:
        print(f"✅ Plugin de Claude Code al día (v{plugin['installed_version']}).")

    if not is_git_repo():
        if not plugin:
            print("⚠️ Esta copia del kit no es un repo git ni un plugin de Claude Code registrado: no sé cómo actualizarla.")
            return False
        return ok

    check_res = check_for_updates()
    if not check_res["success"]:
        print(f"❌ Error al comprobar actualizaciones: {check_res['error']}")
        return False

    if not check_res["has_update"]:
        print(f"✅ La copia del workspace ya está en su versión más reciente (Commit {check_res['local']['commit']} en {check_res['local']['branch']}).")
        return ok

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
    print(f"\n🎉 Copia del workspace actualizada a la versión {new_info['version']} (Commit: {new_info['commit']}).")
    print("💡 Si el kit es un submódulo del workspace, registra el nuevo commit del submódulo en el repo del workspace.")
    return ok


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
    plugin = claude_plugin_status()
    if not is_git_repo():
        # Corriendo desde el plugin instalado (sin git): solo aplica el estado del plugin.
        if args.json:
            print(json.dumps({"success": plugin is not None, "workspace_copy": None, "claude_plugin": plugin}, indent=2))
            return
        if not plugin:
            print("⚠️ Esta copia del kit no es un repo git ni un plugin de Claude Code registrado.")
        elif plugin["has_update"]:
            print(f"🔔 Plugin de Claude Code: v{plugin['installed_version']} instalada, v{plugin['remote_version']} disponible.")
            print("👉 Actualiza con: python <KIT>/skills/qa-update/scripts/update_plugin.py --update")
        else:
            print(f"🟢 Plugin de Claude Code al día (v{plugin['installed_version']}"
                  f"{'' if plugin['remote_version'] else '; no se pudo consultar la versión remota'}).")
        return

    status = check_for_updates()
    status["claude_plugin"] = plugin
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
        print("🟢 La copia del workspace está al día con origin/main.")
    if plugin:
        if plugin["has_update"]:
            print(f"🔔 Plugin de Claude Code: v{plugin['installed_version']} instalada, v{plugin['remote_version']} disponible "
                  f"(--update también lo actualiza).")
        else:
            print(f"🟢 Plugin de Claude Code: v{plugin['installed_version']}"
                  f"{'' if plugin['remote_version'] else ' (no se pudo consultar la versión remota)'}.")
    print("=" * 65)


if __name__ == "__main__":
    main()
