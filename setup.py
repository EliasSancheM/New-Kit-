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
    env_target = os.path.join(PLUGIN_DIR, ".env")
    env_example = os.path.join(PLUGIN_DIR, ".env.example")
    
    if not os.path.exists(env_target) and os.path.exists(env_example):
        shutil.copy(env_example, env_target)
        print(f"  ℹ️ Archivo .env creado desde .env.example en {env_target}")
    else:
        print(f"  ✅ Archivo .env ya presente en {env_target}")

    # Consultar identidad de reporte para nuevos usuarios
    sys.path.append(os.path.join(PLUGIN_DIR, "skills", "shared"))
    try:
        import utils
        user_name = utils.get_user_name()
        print(f"  👤 Identidad de reporte QA: {user_name}")
    except Exception as e:
        print(f"  ⚠️ No se pudo determinar identidad: {e}")

    # 3. Verificación de Autenticación
    print("\n[3/4] Verificando autenticación de servicios...")
    
    # gcloud auth
    if ok_gcloud:
        try:
            tok = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True, stderr=subprocess.PIPE, shell=(sys.platform == "win32")).strip()
            if tok and not tok.startswith("ERROR"):
                print("  ✅ Google Cloud Auth   : Sesión activa y token válido")
            else:
                print("  ⚠️ Google Cloud Auth   : Sin sesión activa.")
                print("     👉 Ejecuta: gcloud auth login --enable-gdrive-access")
        except Exception:
            print("  ⚠️ Google Cloud Auth   : No se pudo verificar token.")
            print("     👉 Ejecuta: gcloud auth login --enable-gdrive-access")

    # Notion Token
    sys.path.append(os.path.join(PLUGIN_DIR, "skills", "shared"))
    try:
        import utils
        ntok = utils.get_notion_token()
        if ntok:
            print("  ✅ Notion Token        : Configurado (ntn_****************)")
        else:
            print("  ⚠️ Notion Token        : No configurado en .env (NOTION_TOKEN)")
            print("     👉 AVISO: Solicita el token de integración de Notion a tu líder técnico / superior a cargo del workspace.")
            print("     👉 Una vez recibido, agrégalo a tu archivo .env: NOTION_TOKEN=ntn_xxxx...")
    except Exception as e:
        print(f"  ⚠️ Verificación Notion : {e}")

    # 4. Pre-flight Check
    print("\n[4/4] Ejecutando autodiagnóstico de Pre-flight...")
    try:
        preflight_script = os.path.join(PLUGIN_DIR, "skills", "qa-preflight", "scripts", "check_env.py")
        subprocess.run([sys.executable, preflight_script])
    except Exception as e:
        print(f"  Error ejecutando pre-flight: {e}")

    print_header("🎉 Setup Finalizado")
    print("El plugin está listo para ser utilizado en cualquier IA o terminal.")
    print("Comandos disponibles:")
    print("  - Backlog de Issues : python skills/qa-backlog/scripts/fetch_issues.py")
    print("  - Auditoría de Git  : python skills/qa-code-audit/scripts/audit_changes.py")
    print("  - Pre-flight Check  : python skills/qa-preflight/scripts/check_env.py")
    print("  - Cerrar Issue (QA) : python skills/qa-finish/scripts/qa_finish_publisher.py")
    print("  - Rechazar Issue    : python skills/qa-rejection/scripts/qa_rejection_publisher.py\n")

if __name__ == "__main__":
    main()
