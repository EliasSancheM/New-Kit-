#!/usr/bin/env python3
"""
IAFactory QA Kit - IAP Tunnel Manager
-------------------------------------
Manages the Google Cloud Identity-Aware Proxy (IAP) tunnel to iafactory-dev.
Allows starting, stopping, and checking the status of port-forwarded services.

Usage:
    python iap_tunnel.py start [--background]
    python iap_tunnel.py status [--json]
    python iap_tunnel.py stop
"""

import os
import sys
import time
import socket
import argparse
import subprocess
import shutil
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Setup environment and paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "shared")
sys.path.append(SHARED_DIR)
try:
    import utils
    WORKSPACE_ROOT = utils.WORKSPACE_ROOT
except ImportError:
    WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

# Default GCP settings (can be overridden via environment variables)
GCP_INSTANCE = os.environ.get("GCP_INSTANCE", "iafactory-dev")
GCP_ZONE = os.environ.get("GCP_ZONE", "us-central1-a")
GCP_PROJECT = os.environ.get("GCP_PROJECT", "apiux-iafactory-nonprod")

# Ports to forward: (Port, Description)
FORWARD_PORTS = [
    (3000, "Grafana / Core"),
    (3001, "Frontend Next.js"),
    (3200, "Frontend Alt"),
    (5432, "PostgreSQL Database"),
    (6333, "Qdrant Vector DB"),
    (6379, "Redis Cache"),
    (8000, "Core REST API Gateway"),
    (8001, "Core Service 8001"),
    (8002, "Core Service 8002"),
    (8082, "Core Service 8082"),
    (8085, "Jenkins CI/CD"),
    (8091, "DevOps Service"),
    (8100, "Orchestrator FastAPI"),
    (8200, "Owner Agent"),
    (8201, "Architect Agent"),
    (8202, "QA Agent"),
    (8203, "Developer Agent"),
    (8204, "DevOps Agent"),
    (8206, "Storage Service"),
    (8207, "UI/UX Agent"),
    (8208, "TeamDevs Agent 1"),
    (8209, "TeamDevs Agent 2"),
    (8210, "Data Service 8210"),
    (8213, "Security Service 8213"),
    (8300, "Metrics Service 8300"),
    (9000, "MinIO S3 Storage"),
    (9090, "Prometheus Telemetry")
]

PID_FILE = os.path.join(os.path.expanduser("~"), ".iafactory_qa_cache", "iap_tunnel.pid")


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.2) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def get_gcloud_bin() -> str:
    path = shutil.which("gcloud")
    if not path and sys.platform == "win32":
        candidate = r"C:\Users\alonso.salas\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.CMD"
        if os.path.exists(candidate):
            return candidate
    return path or "gcloud"


def build_port_forward_args():
    args = []
    for port, _ in FORWARD_PORTS:
        args.extend(["-L", f"127.0.0.1:{port}:localhost:{port}"])
    return args


def get_tunnel_status():
    open_count = 0
    total_count = len(FORWARD_PORTS)
    ports_detail = {}
    
    # Check core key ports
    for port, desc in FORWARD_PORTS:
        reachable = is_port_open(port)
        if reachable:
            open_count += 1
        ports_detail[port] = {
            "description": desc,
            "reachable": reachable
        }

    # Check saved PID if exists
    saved_pid = None
    pid_running = False
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                saved_pid = int(f.read().strip())
            # Check if PID is alive
            if sys.platform == "win32":
                proc_chk = subprocess.run(["tasklist", "/FI", f"PID eq {saved_pid}"], capture_output=True, text=True)
                pid_running = str(saved_pid) in proc_chk.stdout
            else:
                os.kill(saved_pid, 0)
                pid_running = True
        except Exception:
            pid_running = False

    is_active = open_count > 0 or pid_running

    return {
        "active": is_active,
        "pid": saved_pid if pid_running else None,
        "open_ports": open_count,
        "total_ports": total_count,
        "instance": GCP_INSTANCE,
        "project": GCP_PROJECT,
        "zone": GCP_ZONE,
        "ports": ports_detail
    }


def start_tunnel(background: bool = True):
    status = get_tunnel_status()
    if status["open_ports"] >= 3:
        print(f"✅ El túnel IAP ya parece estar activo ({status['open_ports']}/{status['total_ports']} puertos respondiendo).")
        return True

    gcloud = get_gcloud_bin()
    base_cmd = [
        gcloud, "compute", "ssh", GCP_INSTANCE,
        f"--zone={GCP_ZONE}",
        "--tunnel-through-iap",
        f"--project={GCP_PROJECT}",
        "--",
        "-N"
    ] + build_port_forward_args()

    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)

    print(f"🚀 Conectando Túnel IAP a {GCP_INSTANCE} ({GCP_ZONE}) en {GCP_PROJECT}...")
    print(f"   Reenviando {len(FORWARD_PORTS)} puertos a localhost (127.0.0.1)...")

    if background:
        if sys.platform == "win32":
            # Usar start para lanzar ventana o proceso desacoplado
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            p = subprocess.Popen(
                base_cmd,
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            p = subprocess.Popen(
                base_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

        with open(PID_FILE, "w") as f:
            f.write(str(p.pid))

        print(f"⏳ Túnel lanzado en segundo plano (PID: {p.pid}). Verificando puertos...")
        for _ in range(10):
            time.sleep(1)
            if is_port_open(5432) or is_port_open(8000) or is_port_open(8100):
                print("✅ Túnel IAP establecido exitosamente.")
                return True

        # Check again
        st = get_tunnel_status()
        if st["open_ports"] > 0:
            print(f"✅ Túnel IAP conectado ({st['open_ports']} puertos respondiendo).")
            return True
        else:
            print("⚠️ El proceso se inició pero los puertos aún no responden. Dale unos segundos para autenticar.")
            return True
    else:
        # Foreground
        try:
            subprocess.run(base_cmd)
        except KeyboardInterrupt:
            print("\n🛑 Túnel detenido por el usuario.")


def stop_tunnel():
    st = get_tunnel_status()
    stopped = False

    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
            else:
                os.kill(pid, 9)
            stopped = True
            print(f"🛑 Proceso del túnel IAP (PID {pid}) terminado.")
        except Exception as e:
            print(f"⚠️ Error terminando proceso {pid}: {e}")
        finally:
            try:
                os.remove(PID_FILE)
            except Exception:
                pass

    if sys.platform == "win32":
        # Buscar procesos putty o gcloud que estén escuchando en 5432 o 6333
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
        pids_to_kill = set()
        for line in out.splitlines():
            if ("127.0.0.1:5432" in line or "127.0.0.1:6333" in line) and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pids_to_kill.add(parts[-1])
        for p in pids_to_kill:
            try:
                subprocess.run(["taskkill", "/PID", p, "/T", "/F"], capture_output=True)
                print(f"🛑 Proceso port-forward (PID {p}) cerrado.")
                stopped = True
            except Exception:
                pass

    if stopped:
        print("✅ Túnel IAP cerrado exitosamente.")
    else:
        print("ℹ️ No se detectó ningún túnel IAP activo para detener.")


def main():
    parser = argparse.ArgumentParser(description="Gestor de Túnel IAP para GCP IAFactory.")
    parser.add_argument("--instance", type=str, default=None, help="Instancia GCP destino (iafactory-qa, iafactory-dev)")
    subparsers = parser.add_subparsers(dest="action", help="Acción a ejecutar")

    # start
    start_p = subparsers.add_parser("start", help="Iniciar túnel IAP")
    start_p.add_argument("--foreground", action="store_true", help="Ejecutar en primer plano")
    start_p.add_argument("--instance", type=str, default=None, help="Instancia GCP destino")

    # stop
    stop_p = subparsers.add_parser("stop", help="Detener túnel IAP activo")

    # status
    status_p = subparsers.add_parser("status", help="Consultar estado del túnel")
    status_p.add_argument("--json", action="store_true", help="Salida en JSON")
    status_p.add_argument("--instance", type=str, default=None, help="Instancia GCP destino")

    args = parser.parse_args()

    global GCP_INSTANCE
    target_inst = getattr(args, "instance", None) or args.instance
    if target_inst:
        GCP_INSTANCE = target_inst

    if args.action == "start":
        start_tunnel(background=not args.foreground)
    elif args.action == "stop":
        stop_tunnel()
    elif args.action == "status" or args.action is None:
        status = get_tunnel_status()
        if getattr(args, "json", False):
            print(json.dumps(status, indent=2))
        else:
            print("\n" + "=" * 55)
            print("  🌐 ESTADO DEL TÚNEL IAP (GCP -> LOCALHOST)")
            print("=" * 55)
            print(f"Instancia Destino : {status['instance']} ({status['zone']})")
            print(f"Proyecto GCP      : {status['project']}")
            state_icon = "🟢 ACTIVO" if status["active"] else "🔴 INACTIVO"
            print(f"Estado Túnel      : {state_icon}")
            if status["pid"]:
                print(f"PID Proceso       : {status['pid']}")
            print(f"Puertos Conectados: {status['open_ports']} de {status['total_ports']}")
            print("-" * 55)
            # Resumen de puertos clave
            core_ports = [5432, 6333, 6379, 8000, 8100, 8202, 8203, 3000, 9090]
            for p in core_ports:
                p_data = status["ports"].get(p, {})
                icon = "✅" if p_data.get("reachable") else "❌"
                desc = p_data.get("description", "")
                print(f"  {icon} Puerto {p:<5} : {desc}")
            print("=" * 55)
            if not status["active"]:
                print("💡 Para iniciar el túnel ejecuta:")
                print("   python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/iap_tunnel.py start\n")


if __name__ == "__main__":
    main()
