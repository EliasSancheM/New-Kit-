#!/usr/bin/env python3
"""
IAFactory QA Kit - IAP Tunnel Manager
-------------------------------------
Manages Google Cloud Identity-Aware Proxy (IAP) tunnels to the remote VMs
defined in environments.json (dev, qa, team-devs, ...). Each environment
forwards its ports with its own local offset, so tunnels can run in parallel.

Usage:
    python iap_tunnel.py start  [--env dev] [--foreground]
    python iap_tunnel.py status [--env dev | --all] [--json]
    python iap_tunnel.py stop   [--env dev]
    python iap_tunnel.py envs   [--json]
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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SCRIPT_DIR, "..", "..", "shared"))
import utils

# Remote ports to forward: (Port, Description). Local port = port + env port_offset.
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

PID_DIR = os.path.join(utils.get_token_cache_dir(), "tunnels")


def pid_file(env_name: str) -> str:
    return os.path.join(PID_DIR, f"iap_tunnel_{env_name}.pid")


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
        candidate = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Cloud SDK",
                                 "google-cloud-sdk", "bin", "gcloud.cmd")
        if os.path.exists(candidate):
            return candidate
    return path or "gcloud"


def build_port_forward_args(offset: int):
    args = []
    for port, _ in FORWARD_PORTS:
        args.extend(["-L", f"127.0.0.1:{port + offset}:localhost:{port}"])
    return args


def _pid_alive(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
            return str(pid) in out
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def get_tunnel_status(env: dict):
    offset = env["port_offset"]
    open_count = 0
    ports_detail = {}
    for port, desc in FORWARD_PORTS:
        reachable = is_port_open(port + offset)
        if reachable:
            open_count += 1
        ports_detail[port] = {"local_port": port + offset, "description": desc, "reachable": reachable}

    saved_pid, pid_running = None, False
    pf = pid_file(env["name"])
    if os.path.exists(pf):
        try:
            with open(pf, "r") as f:
                saved_pid = int(f.read().strip())
            pid_running = _pid_alive(saved_pid)
        except Exception:
            pid_running = False

    return {
        "env": env["name"],
        "active": open_count > 0 or pid_running,
        "pid": saved_pid if pid_running else None,
        "open_ports": open_count,
        "total_ports": len(FORWARD_PORTS),
        "port_offset": offset,
        "instance": env["instance"],
        "project": env["project"],
        "zone": env["zone"],
        "ports": ports_detail
    }


def start_tunnel(env: dict, background: bool = True) -> bool:
    status = get_tunnel_status(env)
    if status["open_ports"] >= 3:
        print(f"✅ El túnel IAP de '{env['name']}' ya parece activo ({status['open_ports']}/{status['total_ports']} puertos respondiendo).")
        return True

    offset = env["port_offset"]
    base_cmd = [
        get_gcloud_bin(), "compute", "ssh", env["instance"],
        f"--zone={env['zone']}",
        "--tunnel-through-iap",
        f"--project={env['project']}",
    ] + utils.iap_extra_args() + ["--", "-N"] + build_port_forward_args(offset)

    os.makedirs(PID_DIR, exist_ok=True)
    print(f"🚀 Conectando túnel IAP '{env['name']}' a {env['instance']} ({env['zone']}) en {env['project']}...")
    print(f"   Reenviando {len(FORWARD_PORTS)} puertos a 127.0.0.1 con offset +{offset} (ej. Postgres en {5432 + offset}).")

    if not background:
        try:
            subprocess.run(base_cmd)
        except KeyboardInterrupt:
            print("\n🛑 Túnel detenido por el usuario.")
        return True

    if sys.platform == "win32":
        p = subprocess.Popen(base_cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        p = subprocess.Popen(base_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
    with open(pid_file(env["name"]), "w") as f:
        f.write(str(p.pid))

    print(f"⏳ Túnel lanzado en segundo plano (PID: {p.pid}). Verificando puertos...")
    key_ports = [5432 + offset, 8000 + offset, 8100 + offset]
    for _ in range(15):
        time.sleep(1)
        if any(is_port_open(kp) for kp in key_ports):
            print("✅ Túnel IAP establecido.")
            return True
        if p.poll() is not None:
            print(f"❌ El proceso gcloud terminó (código {p.returncode}) sin abrir el túnel. "
                  f"Prueba con --foreground para ver el error.")
            return False

    print("⚠️ El proceso sigue vivo pero los puertos aún no responden. Consulta 'status' en unos segundos.")
    return False


def stop_tunnel(env: dict):
    stopped = False
    pf = pid_file(env["name"])
    if os.path.exists(pf):
        pid = None
        try:
            with open(pf, "r") as f:
                pid = int(f.read().strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
            else:
                os.kill(pid, 9)
            stopped = True
            print(f"🛑 Proceso del túnel '{env['name']}' (PID {pid}) terminado.")
        except Exception as e:
            print(f"⚠️ Error terminando proceso {pid}: {e}")
        finally:
            try:
                os.remove(pf)
            except Exception:
                pass

    if sys.platform == "win32":
        # Tunnels started outside this script: kill whatever listens on this env's key ports
        offset = env["port_offset"]
        targets = (f"127.0.0.1:{5432 + offset}", f"127.0.0.1:{6333 + offset}")
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
        pids_to_kill = set()
        for line in out.splitlines():
            parts = line.strip().split()
            if "LISTENING" in line and len(parts) >= 5 and parts[1] in targets:
                pids_to_kill.add(parts[-1])
        for p in pids_to_kill:
            subprocess.run(["taskkill", "/PID", p, "/T", "/F"], capture_output=True)
            print(f"🛑 Proceso port-forward (PID {p}) cerrado.")
            stopped = True

    print("✅ Túnel IAP cerrado." if stopped else f"ℹ️ No se detectó ningún túnel activo para '{env['name']}'.")


def print_status(status: dict):
    print("\n" + "=" * 55)
    print(f"  🌐 TÚNEL IAP '{status['env']}' (GCP -> LOCALHOST)")
    print("=" * 55)
    print(f"Instancia Destino : {status['instance']} ({status['zone']})")
    print(f"Proyecto GCP      : {status['project']}")
    print(f"Offset de puertos : +{status['port_offset']}")
    print(f"Estado Túnel      : {'🟢 ACTIVO' if status['active'] else '🔴 INACTIVO'}")
    if status["pid"]:
        print(f"PID Proceso       : {status['pid']}")
    print(f"Puertos Conectados: {status['open_ports']} de {status['total_ports']}")
    print("-" * 55)
    for p in [5432, 6333, 6379, 8000, 8100, 8202, 8203, 3000, 9090]:
        d = status["ports"].get(p, {})
        print(f"  {'✅' if d.get('reachable') else '❌'} Puerto {d.get('local_port', p):<5} : {d.get('description', '')}")
    print("=" * 55)
    if not status["active"]:
        print(f"💡 Para iniciarlo: python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py start --env {status['env']}\n")


def main():
    parser = argparse.ArgumentParser(description="Gestor de túneles IAP hacia las VMs de IAFactory.")
    env_help = "Entorno de environments.json (por defecto QA_KIT_ENV o 'dev')"
    sub = parser.add_subparsers(dest="action")

    start_p = sub.add_parser("start", help="Iniciar túnel IAP")
    start_p.add_argument("--env", help=env_help)
    start_p.add_argument("--foreground", action="store_true", help="Ejecutar en primer plano")

    stop_p = sub.add_parser("stop", help="Detener túnel IAP")
    stop_p.add_argument("--env", help=env_help)

    status_p = sub.add_parser("status", help="Consultar estado del túnel")
    status_p.add_argument("--env", help=env_help)
    status_p.add_argument("--all", action="store_true", help="Estado de todos los entornos configurados")
    status_p.add_argument("--json", action="store_true", help="Salida en JSON")

    envs_p = sub.add_parser("envs", help="Listar entornos configurados")
    envs_p.add_argument("--json", action="store_true", help="Salida en JSON")

    args = parser.parse_args()
    action = args.action or "status"

    if action == "envs":
        envs = utils.get_environments()
        if getattr(args, "json", False):
            print(json.dumps(envs, indent=2, ensure_ascii=False))
        else:
            for name, cfg in envs.items():
                state = cfg.get("instance") or "⚠️ sin instancia configurada"
                print(f"  {name:<10} {state:<30} offset +{cfg.get('port_offset', 0)}")
        return

    if action == "status" and getattr(args, "all", False):
        results = []
        for name in utils.get_environments():
            try:
                results.append(get_tunnel_status(utils.resolve_environment(name)))
            except ValueError as e:
                results.append({"env": name, "error": str(e)})
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                if "error" in r:
                    print(f"  ⚠️ {r['env']}: {r['error']}")
                else:
                    print(f"  {'🟢' if r['active'] else '🔴'} {r['env']:<10} {r['instance']:<25} {r['open_ports']}/{r['total_ports']} puertos (offset +{r['port_offset']})")
        return

    try:
        env = utils.resolve_environment(getattr(args, "env", None))
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)

    if action == "start":
        sys.exit(0 if start_tunnel(env, background=not args.foreground) else 1)
    elif action == "stop":
        stop_tunnel(env)
    else:
        status = get_tunnel_status(env)
        if getattr(args, "json", False):
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print_status(status)


if __name__ == "__main__":
    main()
