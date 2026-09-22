"""
QA Pre-flight Connectivity & Environment Check CLI
--------------------------------------------------
Checks local TCP ports (IAP tunnel), cloud credentials, Notion MCP, and directories.
Runs in less than 500 ms and outputs structured diagnostic status.
"""
import sys
import os
import socket
import argparse
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

SERVICES = {
    "PostgreSQL (IAP)": ("127.0.0.1", 5432),
    "Qdrant Vector DB (IAP)": ("127.0.0.1", 6333),
    "Redis Cache (IAP)": ("127.0.0.1", 6379),
    "Prometheus Telemetry (IAP)": ("127.0.0.1", 9090),
    "Grafana Dashboards (IAP)": ("127.0.0.1", 3000),
    "Core API Gateway Local": ("127.0.0.1", 8000),
    "Frontend Next.js Local": ("127.0.0.1", 3001)
}

def check_tcp_port(host, port, timeout=0.2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser(description="Pre-flight check for QA testing environment.")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = {
        "ports": {},
        "credentials": {},
        "directories": {}
    }

    # 1. Ports
    for name, (host, port) in SERVICES.items():
        open_status = check_tcp_port(host, port)
        results["ports"][name] = {"port": port, "reachable": open_status}

    # 2. Credentials
    gcloud_tok = utils.get_gcloud_token()
    results["credentials"]["gcloud_auth"] = bool(gcloud_tok and not gcloud_tok.startswith("ERROR"))

    notion_tok = utils.get_notion_token()
    results["credentials"]["notion_token"] = bool(notion_tok)

    # 3. Directories
    results["directories"]["reports_dir"] = os.path.exists(utils.REPORTS_DIR)
    results["directories"]["obsidian_vault"] = os.path.exists(utils.OBSIDIAN_VAULT_DIR)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    print("\n### 🚀 Diagnóstico de Pre-Flight (Entorno QA)")
    print("\n**1. Conectividad de Red y Túneles IAP:**")
    for name, data in results["ports"].items():
        icon = "✅" if data["reachable"] else "❌"
        status_txt = "CONECTADO" if data["reachable"] else "CERRADO / NO DISPONIBLE"
        print(f"  {icon} {name} (Puerto {data['port']}): `{status_txt}`")

    print("\n**2. Credenciales y Autenticación:**")
    print(f"  {'✅' if results['credentials']['gcloud_auth'] else '❌'} Google Cloud API: `{'OK' if results['credentials']['gcloud_auth'] else 'Sin sesión gcloud'}`")
    print(f"  {'✅' if results['credentials']['notion_token'] else '❌'} Notion API Token: `{'OK' if results['credentials']['notion_token'] else 'Falta NOTION_TOKEN en .env'}`")

    print("\n**3. Directorios de Almacenamiento:**")
    print(f"  {'✅' if results['directories']['reports_dir'] else '⚠️'} Carpeta Reportes/: `{utils.REPORTS_DIR}`")
    print(f"  {'✅' if results['directories']['obsidian_vault'] else '⚠️'} Obsidian Vault: `{utils.OBSIDIAN_VAULT_DIR}`")

if __name__ == "__main__":
    main()
