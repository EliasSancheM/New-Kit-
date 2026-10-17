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
import re
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


# Sections that the template leaves as a one-line comment; each gets a copy of Maya's block.
AGENT_BLOCKS = [("2", "Product Owner", "PO"), ("3", "Arquitecto", "AR"), ("4", "UI/UX", "UX"),
                ("5", "QA", "QA"), ("7", "DevSec", "SEC"), ("8", "DevOps", "OPS")]


def expand_agent_blocks(content: str) -> str:
    """Copies the Maya block (## 1. ... up to the next '---') into the sections that the
    template marks with '<!-- mismo bloque ... -->', changing heading and finding prefix.
    A new document then only fails validation for empty content, never for structure."""
    m = re.search(r"^## 1\. Maya.*?(?=^---\s*$)", content, re.M | re.S)
    if not m:
        return content
    maya = m.group(0)
    for num, name, prefix in AGENT_BLOCKS:
        block = re.sub(r"^## 1\. Maya[^\n]*", f"## {num}. {name}", maya, count=1, flags=re.M)
        block = block.replace("MY-", f"{prefix}-")
        content = re.sub(rf"^## {num}\. {re.escape(name)}\s*\n<!--[^\n]*-->\s*\n", block.rstrip() + "\n\n", content,
                         count=1, flags=re.M)
    return content


def create(template: str, target: str) -> dict:
    if os.path.exists(target):
        return {"created": False, "path": target, "reason": "ya existe; no se sobrescribe"}
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(os.path.join(TEMPLATES_DIR, template), "r", encoding="utf-8") as f:
        content = f.read()
    content = (content.replace("{{KIT_VERSION}}", kit_version())
               .replace("{{CREATED_AT}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    if template == "plantilla_corrida.md":
        content = expand_agent_blocks(content)
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
