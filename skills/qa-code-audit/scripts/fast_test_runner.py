#!/usr/bin/env python3
"""
Fast Surgical Test Runner
-------------------------
Optimización QA #2: Permite ejecutar pruebas unitarias dirigidas y quirúrgicas
sin la sobrecarga de escanear o recompilar todo el monorepo.

Soporta:
1. Frontend (Vitest): Ejecución rápida con --no-threads y filtrado por -t o archivo.
2. Agentes (Python): Ejecución directa de scripts de validación o módulos aislados.

Uso:
  python fast_test_runner.py --frontend --file "src/hooks/orchestrator/__tests__/eventId.test.ts"
  python fast_test_runner.py --frontend --test "resolves naive ISO as UTC"
  python fast_test_runner.py --agent owner-agent --test-voseo
  python fast_test_runner.py --agent all --test-voseo
"""

import sys
import os
import time
import subprocess
import argparse
import json

# Garantizar compatibilidad con Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

# Raíz y nombres de repos configurables (WORKSPACE_ROOT, QA_KIT_FRONTEND_REPO, QA_KIT_AGENTS_REPO)
WORKSPACE_ROOT = utils.WORKSPACE_ROOT
FRONTEND_REPO = utils._read_env_key("QA_KIT_FRONTEND_REPO") or "ai-factory-frontend"
AGENTS_REPO = utils._read_env_key("QA_KIT_AGENTS_REPO") or "ai-factory-agents"

def run_frontend_test(file_path=None, test_name=None):
    frontend_dir = os.path.join(WORKSPACE_ROOT, FRONTEND_REPO)
    if not os.path.isdir(frontend_dir):
        return {"success": False, "error": f"No se encontró el directorio frontend: {frontend_dir}"}

    cmd = ["npx", "vitest", "run"]
    if file_path:
        cmd.append(file_path)
    if test_name:
        cmd.extend(["-t", test_name])

    start_time = time.time()
    proc = subprocess.run(
        cmd,
        cwd=frontend_dir,
        capture_output=True,
        text=True,
        shell=(os.name == "nt")
    )
    duration_ms = int((time.time() - start_time) * 1000)

    return {
        "success": proc.returncode == 0,
        "target": file_path or test_name or "general",
        "duration_ms": duration_ms,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode
    }

def run_agent_voseo_tests(agent_target="all"):
    agents_dir = os.path.join(WORKSPACE_ROOT, AGENTS_REPO)
    base_layer = os.path.join(agents_dir, "services", "core", "agent-layer")
    
    available_agents = [
        "owner-agent", "devops-agent", "maya-agent",
        "architect-agent", "developer-agent", "qa-agent", "ui-ux-agent"
    ]
    
    targets = available_agents if agent_target == "all" else [agent_target]
    results = {}
    
    start_total = time.time()
    for ag in targets:
        script_path = os.path.join(base_layer, ag, "tests", "test_no_voseo.py")
        if not os.path.isfile(script_path):
            results[ag] = {"success": False, "duration_ms": 0, "error": "test_no_voseo.py no encontrado"}
            continue
            
        py_cmd = f"""
import importlib.util
spec = importlib.util.spec_from_file_location('{ag}.test_no_voseo', r'{script_path}')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.test_no_voseo_in_app_sources()
"""
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, "-c", py_cmd],
            cwd=agents_dir,
            capture_output=True,
            text=True
        )
        elapsed = int((time.time() - t0) * 1000)
        results[ag] = {
            "success": proc.returncode == 0,
            "duration_ms": elapsed,
            "error": proc.stderr.strip() if proc.returncode != 0 else None
        }

    total_duration_ms = int((time.time() - start_total) * 1000)
    all_passed = all(r.get("success") for r in results.values())
    
    return {
        "success": all_passed,
        "target": f"Agentes ({agent_target})",
        "total_duration_ms": total_duration_ms,
        "agents": results
    }

def main():
    parser = argparse.ArgumentParser(description="Ejecutor quirúrgico y ultrarrápido de pruebas unitarias QA.")
    parser.add_argument("--frontend", action="store_true", help="Ejecutar prueba en ai-factory-frontend")
    parser.add_argument("--file", help="Ruta relativa o nombre del archivo de prueba")
    parser.add_argument("--test", help="Nombre o patrón del test a filtrar (-t)")
    parser.add_argument("--agent", help="Nombre del agente (o 'all') para pruebas de agentes")
    parser.add_argument("--test-voseo", action="store_true", help="Ejecutar suite de regresión anti-voseo en agentes")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args()

    if args.frontend:
        res = run_frontend_test(args.file, args.test)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            status = "✅ PASÓ" if res["success"] else "❌ FALLÓ"
            print(f"\n[FAST TEST RUNNER - FRONTEND] {status} en {res['duration_ms']} ms")
            print(f"Target: {res['target']}")
            print("Alcance: Quirúrgico / Verificación puntual")
            if not res["success"]:
                print(f"\nSalida de error:\n{res['stderr'] or res['stdout']}")
    elif args.test_voseo or args.agent:
        target = args.agent or "all"
        res = run_agent_voseo_tests(target)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            status = "✅ TODOS PASARON" if res["success"] else "❌ AL MENOS UNO FALLÓ"
            print(f"\n[FAST TEST RUNNER - AGENTES VOSEO] {status} en {res['total_duration_ms']} ms")
            for ag, info in res["agents"].items():
                ag_status = "✅ OK" if info["success"] else "❌ ERROR"
                print(f"  - {ag}: {ag_status} ({info['duration_ms']} ms)")
                if not info["success"]:
                    print(f"    Detalle: {info['error']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
