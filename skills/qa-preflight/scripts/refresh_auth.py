"""
QA Live Testing Session & Token Refresh Utility
-----------------------------------------------
Generates and maintains a clean, tool-agnostic 'storageState.json' containing
valid session cookies and localStorage authentication tokens for IAFactory frontend.

Enables any agent (Antigravity/Puppeteer, Claude Code/Playwright, ...) to launch
fresh, isolated browser sessions pre-authenticated without typing passwords in plain text.

The target environment (dev, qa, team-devs...) comes from environments.json.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import argparse
import datetime

# Ensure UTF-8 console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

AUTH_DIR = os.path.join(utils.PLUGIN_ROOT, "auth")

def default_output_path(env_name: str) -> str:
    return os.path.join(AUTH_DIR, f"storageState_{env_name}.json")

def generate_storage_state(access_token: str, refresh_token: str, user_role: str, frontend_origin: str) -> dict:
    host = urllib.parse.urlparse(frontend_origin).hostname or "localhost"
    secure = frontend_origin.startswith("https://")
    return {
        "generated_at": datetime.datetime.now().isoformat(),
        "cookies": [
            {
                "name": "ai_factory_access_token",
                "value": access_token,
                "domain": host,
                "path": "/",
                "expires": -1,
                "httpOnly": False,
                "secure": secure,
                "sameSite": "Lax"
            }
        ],
        "origins": [
            {
                "origin": frontend_origin.rstrip("/"),
                "localStorage": [
                    {"name": "refresh_token", "value": refresh_token or access_token},
                    {"name": "user_role", "value": user_role}
                ]
            }
        ]
    }

def resolve_targets(env: dict, api_url: str = None, frontend_origin: str = None) -> tuple:
    """API URL priority: --api-url > environment api_url > local tunnel (8000 + offset).
    Frontend origin: --frontend-origin > same origin as a remote API > local tunnel (3001 + offset)."""
    offset = env["port_offset"]
    api = api_url or env.get("api_url") or f"http://127.0.0.1:{8000 + offset}"
    if not frontend_origin:
        parsed = urllib.parse.urlparse(api)
        if parsed.hostname in ("127.0.0.1", "localhost"):
            frontend_origin = f"http://localhost:{3001 + offset}"
        else:
            frontend_origin = f"{parsed.scheme}://{parsed.netloc}"
    return api, frontend_origin

def login_and_refresh(env: dict, api_url: str = None, user: str = None, password: str = None,
                      output_path: str = None, frontend_origin: str = None) -> dict:
    utils.load_env_variables()

    api_url, frontend_origin = resolve_targets(env, api_url, frontend_origin)
    user = user or os.environ.get("QA_TEST_USER", "")
    password = password or os.environ.get("QA_TEST_PASSWORD", "")
    output_path = output_path or default_output_path(env["name"])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    endpoint = f"{api_url.rstrip('/')}/v1/auth/login"
    access_token, refresh_token, role = None, "", "admin"

    if user and password:
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps({"user": user, "password": password}).encode("utf-8"),
                # Cloudflare rejects default library user agents (error 1010)
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (iafactory-qa-kit)"},
                method="POST"
            )
            with urllib.request.urlopen(req, context=utils.get_ssl_context(), timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                access_token = data.get("access_token")
                refresh_token = data.get("refresh_token", "")
                role = data.get("role") or role
                print(f"✅ Autenticación exitosa en {endpoint} para {user} (rol: {role})", file=sys.stderr)
        except Exception as e:
            print(f"❌ No se pudo autenticar contra {endpoint}: {e}", file=sys.stderr)
            if "127.0.0.1" in api_url:
                print(f"   👉 ¿Está abierto el túnel IAP del entorno '{env['name']}'?", file=sys.stderr)
    else:
        print("⚠️ Faltan QA_TEST_USER / QA_TEST_PASSWORD en el .env: no se intentó login.", file=sys.stderr)

    if not access_token:
        dev_token = os.environ.get("QA_DEV_TOKEN")
        if not dev_token:
            print("❌ No se generó storageState: sin login válido y sin QA_DEV_TOKEN.", file=sys.stderr)
            return None
        access_token = dev_token
        print("ℹ️ Usando el token pre-configurado QA_DEV_TOKEN (no se verificó contra el backend).", file=sys.stderr)

    storage_state = generate_storage_state(access_token, refresh_token, role, frontend_origin)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(storage_state, f, indent=2)

    print(f"📁 Archivo de sesión generado: {output_path}", file=sys.stderr)
    return storage_state

def main():
    parser = argparse.ArgumentParser(description="Generate pre-authenticated storageState.json for QA live testing.")
    parser.add_argument("--env", help="Entorno de environments.json (dev, qa, team-devs...). Por defecto QA_KIT_ENV o 'dev'")
    parser.add_argument("--api-url", default=None, help="URL base de la API (por defecto, la del entorno)")
    parser.add_argument("--frontend-origin", default=None, help="Origen del frontend para el storageState")
    parser.add_argument("--user", default=None, help="Usuario de pruebas (por defecto QA_TEST_USER)")
    parser.add_argument("--output", default=None, help="Ruta destino (por defecto auth/storageState_<env>.json)")
    parser.add_argument("--json", action="store_true", help="Imprimir el storageState en stdout")
    args = parser.parse_args()

    try:
        env = utils.resolve_environment(args.env)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)

    state = login_and_refresh(env, api_url=args.api_url, user=args.user,
                              output_path=args.output, frontend_origin=args.frontend_origin)
    if not state:
        sys.exit(1)
    if args.json:
        print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
