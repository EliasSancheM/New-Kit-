#!/usr/bin/env python3
"""
IAFactory QA Kit - Setup & Diagnostic Wizard
--------------------------------------------
Automates onboarding on any new machine (Windows, macOS, Linux):
1. Verifies Python version (>= 3.8) and OS.
2. Checks Node.js and npx (required for Notion MCP).
3. Checks Google Cloud CLI (`gcloud`).
4. Checks Git client.
5. Configures `.env` and `config.json`.
6. Executes a pre-flight test.
"""

import os
import sys
import subprocess
import shutil

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_command(cmd, name, install_hint=""):
    path = shutil.which(cmd)
    if path:
        print(f"  ✅ {name:<20}: Encontrado ({path})")
        return True
    else:
        print(f"  ❌ {name:<20}: NO ENCONTRADO.")
        if install_hint:
            print(f"     👉 Solución: {install_hint}")
        return False

def main():
    print_header("🚀 Setup e Instalación: IAFactory QA Kit")
    print(f"Plataforma: {sys.platform} | Python: {sys.version.split()[0]}")

    # 1. Prerequisitos de Software
    print("\n[1/4] Verificando dependencias del sistema...")
    ok_py = sys.version_info >= (3, 8)
    if ok_py:
        print("  ✅ Python              : Versión compatible (>= 3.8)")
    else:
        print("  ❌ Python              : Requiere Python 3.8 o superior")

    ok_git = check_command("git", "Git CLI", "Instala Git desde https://git-scm.com/")
    ok_node = check_command("node", "Node.js", "Instala Node.js (LTS) desde https://nodejs.org/")
    ok_npx = check_command("npx", "npx (MCP Runner)", "Viene incluido con Node.js")
    ok_gcloud = check_command("gcloud", "Google Cloud CLI", "Instala gcloud CLI desde https://cloud.google.com/sdk/docs/install")

    # 2. Configuración de Entorno e Identidad
    print("\n[2/4] Configurando variables de entorno e identidad...")
    sys.path.append(os.path.join(PLUGIN_DIR, "skills", "shared"))
    import utils

    ws_root = utils.WORKSPACE_ROOT
    ws_env = os.path.join(ws_root, ".env")
    ws_env_example = os.path.join(ws_root, ".env.example")
    plugin_env = os.path.join(PLUGIN_DIR, ".env")
    plugin_env_example = os.path.join(PLUGIN_DIR, ".env.example")

    # Asegurar .env en raíz de workspace
    if not os.path.exists(ws_env) and os.path.exists(ws_env_example):
        shutil.copy(ws_env_example, ws_env)
        print(f"  ℹ️ Archivo .env creado en raíz del workspace: {ws_env}")
    elif os.path.exists(ws_env):
        print(f"  ✅ Archivo .env presente en workspace: {ws_env}")

    # Asegurar .env en el plugin
    if not os.path.exists(plugin_env) and os.path.exists(plugin_env_example):
        shutil.copy(plugin_env_example, plugin_env)
        print(f"  ℹ️ Archivo .env creado en plugin: {plugin_env}")

    # Consultar identidad de reporte para nuevos usuarios
    try:
        user_name = utils.get_user_name()
        print(f"  👤 Identidad de reporte QA: {user_name}")
    except Exception as e:
        print(f"  ⚠️ No se pudo determinar identidad: {e}")

    # 3. Verificación de Autenticación y Conectividad GCP
    print("\n[3/4] Verificando autenticación de servicios y GCP...")
    
    # gcloud auth
    if ok_gcloud:
        try:
            tok = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True, stderr=subprocess.PIPE, shell=(sys.platform == "win32")).strip()
            if tok and not tok.startswith("ERROR"):
                print("  ✅ Google Cloud Auth   : Sesión activa y token OAuth2 válido")
            else:
                print("  ⚠️ Google Cloud Auth   : Sin sesión activa.")
                print("     👉 Ejecuta: gcloud auth login --enable-gdrive-access")
        except Exception:
            print("  ⚠️ Google Cloud Auth   : No se pudo verificar token.")
            print("     👉 Ejecuta: gcloud auth login --enable-gdrive-access")

        # Test de salud con Compute Engine / VM iafactory-dev
        try:
            gcp_inst = os.environ.get("GCP_INSTANCE", "iafactory-dev")
            gcp_zone = os.environ.get("GCP_ZONE", "us-central1-a")
            gcp_proj = os.environ.get("GCP_PROJECT", "apiux-iafactory-nonprod")
            cmd_vm = [
                "gcloud", "compute", "instances", "describe", gcp_inst,
                f"--zone={gcp_zone}",
                f"--project={gcp_proj}",
                "--format=value(status)"
            ]
            res_vm = subprocess.run(cmd_vm, capture_output=True, text=True, timeout=12, shell=(sys.platform == "win32"))
            if res_vm.returncode == 0 and res_vm.stdout.strip():
                vm_status = res_vm.stdout.strip()
                print(f"  ✅ GCP Compute VM      : {gcp_inst} estado `{vm_status}`")
            else:
                print(f"  ⚠️ GCP Compute VM      : No se pudo consultar {gcp_inst} ({res_vm.stderr.strip()[:60]}...)")
        except Exception as e:
            print(f"  ⚠️ GCP Compute Check   : Timeout o error conectando a GCP ({e})")

    # Notion Token
    try:
        ntok = utils.get_notion_token()
        if ntok and ntok.startswith("ntn_"):
            print("  ✅ Notion Token        : Configurado (ntn_****************)")
        else:
            print(f"  ⚠️ Notion Token        : NOTION_TOKEN no configurado en {ws_env}")
            print(f"     👉 Agrega tu token en: {ws_env} (ej: NOTION_TOKEN=ntn_xxxx...)")
    except Exception as e:
        print(f"  ⚠️ Verificación Notion : {e}")

    # 4. Pre-flight Check y Estado de Túneles
    print("\n[4/4] Ejecutando autodiagnóstico de Pre-flight y Túnel IAP...")
    sys.stdout.flush()
    try:
        preflight_script = os.path.join(PLUGIN_DIR, "skills", "qa-preflight", "scripts", "check_env.py")
        res_pf = subprocess.run([sys.executable, preflight_script], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res_pf.stdout:
            print(res_pf.stdout.rstrip())
        if res_pf.stderr:
            print(f"  ⚠️ Error en preflight: {res_pf.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"  Error ejecutando pre-flight: {e}")

    # Diagnóstico del túnel IAP
    sys.stdout.flush()
    try:
        tunnel_script = os.path.join(PLUGIN_DIR, "skills", "qa-preflight", "scripts", "iap_tunnel.py")
        res_tun = subprocess.run([sys.executable, tunnel_script, "status"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res_tun.stdout:
            print(res_tun.stdout.rstrip())
        if res_tun.stderr:
            print(f"  ⚠️ Error en túnel status: {res_tun.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        pass

    print_header("🎉 Setup Finalizado")
    print("El plugin está listo para ser utilizado en cualquier IA o terminal.")

    # Comprobación de actualizaciones del plugin
    try:
        updater_script = os.path.join(PLUGIN_DIR, "skills", "qa-update", "scripts", "update_plugin.py")
        res_up = subprocess.run([sys.executable, updater_script, "--check", "--json"], capture_output=True, text=True, timeout=8)
        if res_up.returncode == 0 and res_up.stdout:
            up_data = json.loads(res_up.stdout)
            if up_data.get("has_update"):
                print(f"\n🔔 ¡AVISO DE ACTUALIZACIÓN! Hay {up_data.get('behind_count')} commits nuevos disponibles en GitHub.")
                print("   👉 Para actualizar el plugin ejecuta:")
                print("      python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --update\n")
    except Exception:
        pass

    print("Comandos disponibles:")
    print("  - Actualizar Plugin : python .agents/plugins/iafactory-qa-kit/skills/qa-update/scripts/update_plugin.py --check")
    print("  - Túnel IAP (start) : python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py start")
    print("  - Túnel IAP (status): python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py status")
    print("  - Túnel IAP (stop)  : python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py stop")
    print("  - Pre-flight Check  : python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py")
    print("  - Backlog de Issues : python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py")
    print("  - Auditoría de Git  : python .agents/plugins/iafactory-qa-kit/skills/qa-code-audit/scripts/audit_changes.py")
    print("  - Cerrar Issue (QA) : python .agents/plugins/iafactory-qa-kit/skills/qa-finish/scripts/qa_finish_publisher.py")
    print("  - Rechazar Issue    : python .agents/plugins/iafactory-qa-kit/skills/qa-rejection/scripts/qa_rejection_publisher.py\n")

if __name__ == "__main__":
    main()
