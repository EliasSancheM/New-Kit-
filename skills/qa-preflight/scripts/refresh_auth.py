"""
QA Live Testing Session & Token Refresh Utility
-----------------------------------------------
Generates and maintains a clean, tool-agnostic 'storageState.json' containing
valid session cookies and localStorage authentication tokens for IAFactory frontend.

Enables both Antigravity (Puppeteer MCP) and Claude Code (CLI/Playwright) to launch
fresh, isolated browser sessions pre-authenticated without typing passwords in plain text.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import argparse
import datetime

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

AUTH_DIR = os.path.join(utils.PLUGIN_ROOT, "auth")
DEFAULT_STORAGE_STATE_PATH = os.path.join(AUTH_DIR, "storageState.json")

def generate_storage_state(access_token: str, refresh_token: str = "", user_role: str = "admin", frontend_host: str = "localhost", frontend_port: int = 3001) -> dict:
    origin_url = f"http://{frontend_host}:{frontend_port}"
    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "cookies": [
            {
                "name": "ai_factory_access_token",
                "value": access_token,
                "domain": frontend_host,
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": False,
                "sameSite": "Lax"
            }
        ],
        "origins": [
            {
                "origin": origin_url,
                "localStorage": [
                    {
                        "name": "refresh_token",
                        "value": refresh_token or access_token
                    },
                    {
                        "name": "user_role",
                        "value": user_role
                    }
                ]
            }
        ]
    }

def login_and_refresh(api_url: str = None, user: str = None, password: str = None, output_path: str = None) -> dict:
    utils.load_env_variables()
    
    api_url = api_url or os.environ.get("API_GATEWAY_URL", "http://127.0.0.1:8000")
    user = user or os.environ.get("QA_TEST_USER", "admin@iafactory.local")
    password = password or os.environ.get("QA_TEST_PASSWORD", "")
    output_path = output_path or DEFAULT_STORAGE_STATE_PATH
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    endpoint = f"{api_url.rstrip('/')}/v1/auth/login"
    login_payload = {"user": user, "password": password}

    access_token = None
    refresh_token = ""

    # 1. Attempt live login against backend
    if password:
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(login_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            ctx = utils.get_ssl_context()
            with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token", "")
                print(f"✅ Autenticación exitosa en backend ({endpoint}) para usuario: {user}")
        except Exception as e:
            print(f"⚠️ No se pudo autenticar contra {endpoint}: {e}", file=sys.stderr)
            print("   👉 Asegúrate de que el túnel IAP o el servicio Core esté activo.", file=sys.stderr)

    # 2. Fallback / Dev token if offline or mock testing
    if not access_token:
        dev_token = os.environ.get("QA_DEV_TOKEN")
        if dev_token:
            access_token = dev_token
            print("ℹ️ Utilizando token de desarrollo pre-configurado (QA_DEV_TOKEN).")
        else:
            access_token = f"dev-qa-session-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            print("ℹ️ Generando token temporal de desarrollo para pruebas locales.")

    storage_state = generate_storage_state(access_token, refresh_token)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, indent=2)

    print(f"📁 Archivo de sesión generado: {output_path}")
    return storage_state

def main():
    parser = argparse.ArgumentParser(description="Generate pre-authenticated storageState.json for QA live testing.")
    parser.add_argument("--api-url", type=str, default=None, help="Backend API base URL (default http://127.0.0.1:8000)")
    parser.add_argument("--user", type=str, default=None, help="QA test user email/username")
    parser.add_argument("--output", type=str, default=None, help="Destination path for storageState.json")
    parser.add_argument("--json", action="store_true", help="Output storageState JSON directly to stdout")

    args = parser.parse_args()
    state = login_and_refresh(api_url=args.api_url, user=args.user, output_path=args.output)

    if args.json:
        print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
