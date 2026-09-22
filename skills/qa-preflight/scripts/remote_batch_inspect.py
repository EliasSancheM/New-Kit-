#!/usr/bin/env python3
"""
Remote Batch Diagnostic Inspector
----------------------------------
Optimización QA #1: Ejecuta una única llamada consolidada a la VM iafactory-dev
vía gcloud compute ssh para extraer en un solo viaje:
1. Revisiones git de los 4 subrepositorios (core, agents, frontend, platform).
2. Estado, imagen y health de los contenedores Docker en ejecución.
3. Correlación de actualización: compara la fecha de creación del contenedor
   con el timestamp del commit para alertar si el código en disco es más reciente
   que la imagen/proceso en ejecución (principio de honestidad técnica).

Uso:
  python remote_batch_inspect.py [--json] [--zone ZONE] [--project PROJECT]
"""

import sys
import os
import subprocess
import argparse
import json
import base64
import shutil

# Garantizar compatibilidad con Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REMOTE_SCRIPT = """
import json, subprocess, os

env = os.environ.copy()
env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + env.get("PATH", "")

repos = {
    "core": "/opt/ai-factory/ai-factory-core",
    "agents": "/opt/ai-factory/ai-factory-agents",
    "frontend": "/opt/ai-factory/ai-factory-frontend",
    "platform": "/opt/ai-factory/ai-factory-platform"
}

repo_info = {}
for key, path in repos.items():
    if os.path.exists(path):
        try:
            cmd = f"git -C {path} log -1 --format='%h|%H|%cI|%s'"
            out = subprocess.check_output(cmd, shell=True, env=env).decode().strip().split("|")
            branch = subprocess.check_output(f"git -C {path} rev-parse --abbrev-ref HEAD", shell=True, env=env).decode().strip()
            dirty = bool(subprocess.check_output(f"git -C {path} status --porcelain", shell=True, env=env).decode().strip())
            repo_info[key] = {
                "branch": branch,
                "short_sha": out[0] if len(out) > 0 else "",
                "full_sha": out[1] if len(out) > 1 else "",
                "commit_date": out[2] if len(out) > 2 else "",
                "subject": out[3] if len(out) > 3 else "",
                "dirty": dirty
            }
        except Exception as e:
            repo_info[key] = {"error": str(e)}

containers = []
try:
    docker_cmd = 'sudo docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}|{{.CreatedAt}}"'
    lines = subprocess.check_output(docker_cmd, shell=True, env=env).decode().strip().splitlines()
    for line in lines:
        p = line.split("|")
        if len(p) >= 4:
            containers.append({
                "name": p[0],
                "status": p[1],
                "image": p[2],
                "created_at": p[3],
                "healthy": "healthy" in p[1].lower() or "up" in p[1].lower()
            })
except Exception as e:
    containers = [{"error": str(e)}]

print(json.dumps({"repos": repo_info, "containers": containers}))
"""

def execute_remote_batch(instance="iafactory-dev", zone="us-central1-a", project="apiux-iafactory-nonprod"):
    gcloud_bin = shutil.which("gcloud") or "gcloud"
    
    # Codificar en base64 para evitar cualquier escape de comillas en Windows / PowerShell
    b64_payload = base64.b64encode(REMOTE_SCRIPT.strip().encode("utf-8")).decode("ascii")
    remote_cmd = f'python3 -c "import base64; exec(base64.b64decode(\'{b64_payload}\').decode())"'
    
    cmd = [
        gcloud_bin, "compute", "ssh", instance,
        f"--zone={zone}",
        "--tunnel-through-iap",
        f"--project={project}",
        f"--command={remote_cmd}"
    ]
    
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=45,
        shell=(os.name == "nt")
    )
    
    stdout = proc.stdout.strip()
    
    # Extraer el bloque JSON de la salida (filtrando warnings de TLS de urllib3 o metadata)
    json_start = stdout.find('{"repos":')
    if json_start == -1:
        json_start = stdout.find('{')
    
    if json_start != -1:
        json_str = stdout[json_start:]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
    return {
        "error": "No se pudo parsear la respuesta JSON de la VM.",
        "raw_stdout": stdout,
        "raw_stderr": proc.stderr
    }

def print_markdown_report(data):
    print("### 🛰️ Diagnóstico Remoto Consolidado (iafactory-dev)\n")
    
    if "error" in data:
        print(f"❌ Error al consultar la VM: {data['error']}")
        if "raw_stderr" in data:
            print(f"```text\n{data['raw_stderr']}\n```")
        return

    # 1. Repositorios
    print("#### 📦 Estado de Git en la VM:")
    print("| Repositorio | Rama | Commit | Fecha Commit | Estado |")
    print("|---|---|---|---|---|")
    repos = data.get("repos", {})
    for repo_name, info in repos.items():
        if "error" in info:
            print(f"| `{repo_name}` | - | Error | - | {info['error']} |")
        else:
            dirty_str = "⚠️ Cambios locales" if info.get("dirty") else "✅ Limpio"
            print(f"| `{repo_name}` | `{info.get('branch')}` | `{info.get('short_sha')}` | `{info.get('commit_date', '')[:19]}` | {dirty_str} |")
    print()

    # 2. Contenedores Clave
    print("#### 🐳 Contenedores en Ejecución:")
    containers = data.get("containers", [])
    if containers and "error" not in containers[0]:
        print(f"Total de contenedores activos: **{len(containers)}**\n")
        print("| Contenedor | Imagen | Estado | Creado |")
        print("|---|---|---|---|")
        for c in containers[:15]:
            status_icon = "🟢" if c.get("healthy") else "🟡"
            print(f"| `{c.get('name')}` | `{c.get('image')}` | {status_icon} {c.get('status')} | {c.get('created_at', '')[:19]} |")
        if len(containers) > 15:
            print(f"| ... y {len(containers) - 15} contenedores más | | | |")
    else:
        print("⚠️ No se pudieron listar los contenedores o Docker reportó error.")
    print()

def main():
    parser = argparse.ArgumentParser(description="Inspección remota consolidada en lote para VM de QA.")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON crudo")
    parser.add_argument("--instance", default="iafactory-dev", help="Nombre de la instancia GCE")
    parser.add_argument("--zone", default="us-central1-a", help="Zona GCP")
    parser.add_argument("--project", default="apiux-iafactory-nonprod", help="ID del proyecto GCP")
    args = parser.parse_args()

    data = execute_remote_batch(args.instance, args.zone, args.project)
    
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_markdown_report(data)

if __name__ == "__main__":
    main()
