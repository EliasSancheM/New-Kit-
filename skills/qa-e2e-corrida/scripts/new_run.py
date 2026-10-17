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

# What each agent must leave behind, and where the assistant has to open it to verify it.
# These rows fill the 📦 table of each section; add rows for things the project "Antes" asks for.
AGENT_ARTIFACTS = {
    "1": [("Proyecto creado en IAF con el nombre acordado", "UI de proyectos / base de datos (projects)"),
          ("Equipo asignado según la complejidad declarada", "workflow.agent_plan en base de datos"),
          ("Perfiles de agentes de la empresa leídos antes de empezar", "company_agent_profiles (§0.6)")],
    "2": [("Documento de requisitos (objetivos, alcance, RF, RN, exclusiones) sin duplicados", "Almacenamiento del proyecto y Wiki"),
          ("Backlog: épicas e historias que cubren cada RF del documento 'Antes'", "Boards (Jira / Azure Boards)"),
          ("Diagrama funcional embebido como imagen en el documento", "Documento de requisitos")],
    "3": [("HLD publicado y coherente con lo acordado en el chat", "Wiki (Confluence / Azure Wiki)"),
          ("LLD con modelo de datos que cubre las entidades del documento 'Antes'", "Wiki"),
          ("Diagramas de arquitectura actualizados con la última decisión", "Wiki / documento"),
          ("URLs del HLD y LLD guardadas en la sesión", "Base de datos de la sesión")],
    "4": [("Pantallas que cubren cada UI-n del documento 'Antes'", "Figma"),
          ("Contrato de API coherente con el LLD", "Repo / documento"),
          ("Enlace del diseño publicado en la Wiki apunta al diseño, no a otro documento", "Wiki")],
    "5": [("Plan de pruebas que cubre RF y RN del documento 'Antes'", "Wiki / documento"),
          ("Casos de prueba trazables a RF-n / RN-n / CA-n", "Wiki / Boards"),
          ("Veredicto del agente coherente con el estado real del proyecto", "Chat vs. repo / Boards")],
    "6": [("Repositorio publicado con código (no un repo vacío duplicado)", "GitHub / Azure Repos"),
          ("Commit final registrado y clonado para §6.b", "Repo publicado"),
          ("SPEC y plan de desarrollo con el nombre real del proyecto", "docs/ del repo"),
          ("Narración del agente coincide con lo que hay en el repo", "Chat vs. repo")],
    "7": [("Reporte de seguridad publicado y basado en el código revisado", "Wiki / almacenamiento del proyecto"),
          ("Plan de remediación ejecutado o entregado al Developer", "Chat / Boards / repo"),
          ("Veredicto en el chat coherente con su propio reporte", "Chat vs. reporte")],
    "8": [("Estrategia de infraestructura con los valores dados por el usuario (nube, ambientes, presupuesto, velocidad)", "Documento / Wiki"),
          ("Topología y diagramas finales coinciden con lo pedido y con el resumen del agente", "Documento / base de datos"),
          ("Pipelines o IaC si el plan los incluía", "Repo")],
}


def fill_artifacts(content: str) -> str:
    """Replaces {{ARTEFACTOS}} inside each '## N.' section with that agent's expected artifacts."""
    parts = re.split(r"(?m)^(?=## \d+\.)", content)
    out = []
    for part in parts:
        m = re.match(r"## (\d+)\.", part)
        rows = AGENT_ARTIFACTS.get(m.group(1), []) if m else []
        table = "\n".join(f"| {a} | {w} | | |" for a, w in rows) or "| | | | |"
        out.append(part.replace("{{ARTEFACTOS}}", table))
    return "".join(out)


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
        content = fill_artifacts(expand_agent_blocks(content))
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
