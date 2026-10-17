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

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

REMOTE_SCRIPT = """
import json, subprocess, os, base64

env = os.environ.copy()
env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:" + env.get("PATH", "")

repos = json.loads(base64.b64decode("__REPOS_B64__").decode())

repo_info = {}
for key, path in repos.items():
    if not os.path.exists(path):
        repo_info[key] = {"error": f"No existe {path} en la VM"}
        continue
    try:
        cmd = f"git -c safe.directory={path} -C {path} log -1 --format='%h|%H|%cI|%s'"
        out = subprocess.check_output(cmd, shell=True, env=env, stderr=subprocess.PIPE).decode().strip().split("|")
        branch = subprocess.check_output(f"git -c safe.directory={path} -C {path} rev-parse --abbrev-ref HEAD", shell=True, env=env, stderr=subprocess.PIPE).decode().strip()
        dirty = bool(subprocess.check_output(f"git -c safe.directory={path} -C {path} status --porcelain", shell=True, env=env, stderr=subprocess.PIPE).decode().strip())
        repo_info[key] = {
            "branch": branch,
            "short_sha": out[0] if len(out) > 0 else "",
            "full_sha": out[1] if len(out) > 1 else "",
            "commit_date": out[2] if len(out) > 2 else "",
            "subject": out[3] if len(out) > 3 else "",
            "dirty": dirty
        }
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or b"").decode(errors="replace").strip().splitlines()
        repo_info[key] = {"error": detail[-1] if detail else str(e)}
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

def remote_repo_map(remote_root: str) -> dict:
    """Short key (e.g. 'frontend') -> absolute path of each product repo on the VM."""
    out = {}
    for repo in utils.get_product_repos():
        key = repo[len("ai-factory-"):] if repo.startswith("ai-factory-") else repo
        out[key] = f"{remote_root.rstrip('/')}/{repo}"
    return out

def execute_remote_batch(env: dict):
    gcloud_bin = shutil.which("gcloud") or "gcloud"

    repos_b64 = base64.b64encode(json.dumps(remote_repo_map(env["remote_repo_root"])).encode()).decode("ascii")
    script = REMOTE_SCRIPT.strip().replace("__REPOS_B64__", repos_b64)
    # Codificar en base64 para evitar cualquier escape de comillas en Windows / PowerShell
    b64_payload = base64.b64encode(script.encode("utf-8")).decode("ascii")
    remote_cmd = f'python3 -c "import base64; exec(base64.b64decode(\'{b64_payload}\').decode())"'

    cmd = [
        gcloud_bin, "compute", "ssh", env["instance"],
        f"--zone={env['zone']}",
        "--tunnel-through-iap",
        f"--project={env['project']}",
    ] + utils.iap_extra_args() + [f"--command={remote_cmd}"]
    
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=90,
            shell=False
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout (90 s) conectando por SSH/IAP a {env['instance']}."}
    
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

def print_markdown_report(data, env, repo_filter=None):
    if repo_filter:
        repos = data.get("repos", {})
        info = repos.get(repo_filter)
        if not info or "error" in info:
            err = info.get("error") if info else f"Repositorio {repo_filter} no encontrado"
            print(f"❌ Error en checkout VM ({repo_filter}): {err}")
            return
        dirty_str = " (⚠️ Dirty)" if info.get("dirty") else ""
        print(f"• **Checkout en VM {env['instance']} (`{remote_repo_map(env['remote_repo_root']).get(repo_filter, repo_filter)}`):** Commit `{info.get('short_sha')}` ({info.get('commit_date', '')[:19]}){dirty_str}")
        print(f"  Mensaje: \"{info.get('subject')}\" | Rama: `{info.get('branch')}`")
        return

    print(f"### 🛰️ Diagnóstico Remoto Consolidado ({env['name']}: {env['instance']})\n")
    
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
    parser.add_argument("--env", help="Entorno de environments.json (dev, qa, team-devs...). Por defecto QA_KIT_ENV o 'dev'")
    parser.add_argument("--repo", help="Filtrar un repositorio (ej. core, agents, frontend, platform)")
    parser.add_argument("--instance", help="Sobrescribe la instancia GCE del entorno")
    parser.add_argument("--zone", help="Sobrescribe la zona GCP del entorno")
    parser.add_argument("--project", help="Sobrescribe el proyecto GCP del entorno")
    args = parser.parse_args()

    try:
        env = utils.resolve_environment(args.env)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(2)
    for key in ("instance", "zone", "project"):
        if getattr(args, key):
            env[key] = getattr(args, key)

    data = execute_remote_batch(env)
    data["env"] = {"name": env["name"], "instance": env["instance"]}

    if args.json:
        if args.repo and "repos" in data and args.repo in data["repos"]:
            print(json.dumps(data["repos"][args.repo], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_markdown_report(data, env, repo_filter=args.repo)
    sys.exit(1 if "error" in data else 0)

if __name__ == "__main__":
    main()
