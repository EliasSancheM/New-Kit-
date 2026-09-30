#!/usr/bin/env python3
"""
E2E Run Documents - scaffolding
-------------------------------
Creates the documents of an E2E run from the skill templates, in the folder
set by QA_KIT_E2E_DIR (default: <WORKSPACE_ROOT>/Reportes/E2E). Never
overwrites an existing file. Only writes local files.

  new_run.py proyecto <slug>                    -> <E2E_DIR>/proyectos/<slug>_requisitos.md
  new_run.py corrida <empresa> <slug> [fecha]   -> <E2E_DIR>/<empresa>_<slug>_<fecha>.md
  new_run.py where                              -> prints the resolved folder
"""
import os
import sys
import json
import argparse
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


def e2e_dir() -> str:
    configured = utils._read_env_key("QA_KIT_E2E_DIR")
    if configured:
        return configured if os.path.isabs(configured) else os.path.join(utils.WORKSPACE_ROOT, configured)
    return os.path.join(utils.REPORTS_DIR, "E2E")


def kit_version() -> str:
    try:
        with open(os.path.join(utils.PLUGIN_ROOT, "plugin.json"), encoding="utf-8") as f:
            return json.load(f).get("version", "desconocida")
    except (OSError, ValueError):
        return "desconocida"


def create(template: str, target: str) -> dict:
    if os.path.exists(target):
        return {"created": False, "path": target, "reason": "ya existe; no se sobrescribe"}
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(os.path.join(TEMPLATES_DIR, template), "r", encoding="utf-8") as f:
        content = f.read()
    content = (content.replace("{{KIT_VERSION}}", kit_version())
               .replace("{{CREATED_AT}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return {"created": True, "path": target}


def main():
    parser = argparse.ArgumentParser(description="Crea los documentos de una corrida E2E desde las plantillas.")
    parser.add_argument("--json", action="store_true", help="Salida en JSON")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("proyecto", help="Documento 'Antes' del proyecto")
    p.add_argument("slug")
    c = sub.add_parser("corrida", help="Documento de la corrida")
    c.add_argument("empresa")
    c.add_argument("slug")
    c.add_argument("fecha", nargs="?", default=datetime.date.today().isoformat())
    sub.add_parser("where", help="Muestra la carpeta de salida resuelta")
    args = parser.parse_args()

    base = e2e_dir()
    if args.cmd == "where":
        result = {"e2e_dir": base, "exists": os.path.isdir(base)}
    elif args.cmd == "proyecto":
        result = create("plantilla_proyecto.md", os.path.join(base, "proyectos", f"{args.slug}_requisitos.md"))
    else:
        result = create("plantilla_corrida.md", os.path.join(base, f"{args.empresa}_{args.slug}_{args.fecha}.md"))

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif "e2e_dir" in result:
        print(f"Carpeta E2E: {result['e2e_dir']} ({'existe' if result['exists'] else 'se creará al generar el primer documento'})")
    elif result["created"]:
        print(f"Creado: {result['path']}")
    else:
        print(f"No creado: {result['path']} ({result['reason']})")
        sys.exit(1)


if __name__ == "__main__":
    main()
