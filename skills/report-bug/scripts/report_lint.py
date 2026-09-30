#!/usr/bin/env python3
"""
Report lint - structure check for defect reports (read-only, deterministic, standard library).

Checks that an executive (Level 1) and a technical (Level 2) report contain the sections of
the report-bug templates. It does not judge whether the analysis is right; it only makes sure
the parts a developer needs are there (symptom, steps, environment and version, evidence,
root cause at file:line or an explicit "not identified", fix, and what was not verified).

  report_lint.py <ejecutivo.md> [<tecnico.md>] [--json]
  report_lint.py --tecnico <tecnico.md>          # only the technical report

Exit codes: 0 no errors (warnings allowed), 1 errors, 2 bad arguments.
"""
import os
import re
import sys
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_LINE = re.compile(r"[\w./\-]+\.(?:py|ts|tsx|js|jsx|sql|ya?ml|json|go|java|sh|toml|ini|cfg)(?::\d+(?:-\d+)?|\s*\(l[íi]neas?\s*\d+)", re.I)
TAG = re.compile(r"\[(?:R|DB|C|C-sub|H)\]")
NOT_IDENTIFIED = re.compile(r"causa no identificada", re.I)

# (label, heading keywords (any), required)
EXECUTIVE = [
    ("Qué falla / síntoma", ["qué falla", "que falla", "síntoma", "sintoma"], True),
    ("Impacto", ["impacto"], True),
    ("Cómo reproducirlo", ["cómo reproducir", "como reproducir", "pasos", "reproducción", "reproduccion"], True),
    ("Relacionados", ["relacionad"], False),
]
TECHNICAL = [
    ("Entorno y versión", ["entorno", "versión", "version"], True),
    ("Evidencia", ["evidencia", "hechos"], True),
    ("Causa raíz", ["causa raíz", "causa raiz", "causa"], True),
    ("Corrección sugerida", ["corrección", "correccion", "fix"], True),
    ("Cómo verificar el fix", ["cómo verificar", "como verificar", "verificar el fix"], False),
    ("No verificado", ["no verificado", "sin verificar", "pendiente de verificar"], False),
]


def headings(text: str) -> list:
    return [h.strip().lower() for h in re.findall(r"^#{2,4}\s+(.+)$", text, re.M)]


def section(text: str, keywords: list) -> str:
    """Body of the first heading that contains one of the keywords."""
    parts = re.split(r"^(#{2,4}\s+.+)$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        if any(k in parts[i].lower() for k in keywords):
            return parts[i + 1] if i + 1 < len(parts) else ""
    return ""


def check(text: str, spec: list, kind: str) -> tuple:
    errors, warnings = [], []
    hs = headings(text)
    for label, keys, required in spec:
        if not any(any(k in h for k in keys) for h in hs):
            (errors if required else warnings).append(f"{kind}: falta la sección '{label}'.")
    return errors, warnings


def lint_executive(text: str) -> tuple:
    errors, warnings = check(text, EXECUTIVE, "Ejecutivo")
    steps = section(text, ["cómo reproducir", "como reproducir", "pasos", "reproducción", "reproduccion"])
    if steps and len(re.findall(r"^\s*\d+[.)]\s+\S", steps, re.M)) < 2:
        errors.append("Ejecutivo: 'Cómo reproducirlo' necesita al menos 2 pasos numerados.")
    if not re.search(r"(?im)^\**\s*(gravedad|severidad)\**\s*:", text):
        warnings.append("Ejecutivo: no indica la gravedad.")
    if not re.search(r"(?im)^\**\s*contexto\**\s*:", text):
        warnings.append("Ejecutivo: no indica el contexto (entorno, proyecto, fecha o corrida).")
    return errors, warnings


def lint_technical(text: str) -> tuple:
    errors, warnings = check(text, TECHNICAL, "Técnico")
    cause = section(text, ["causa raíz", "causa raiz", "causa"])
    if cause and not FILE_LINE.search(cause) and not NOT_IDENTIFIED.search(cause):
        errors.append("Técnico: la causa raíz no cita ningún archivo:línea. Si no se encontró, escribe 'Causa no identificada' "
                      "y qué se revisó, en vez de describirla sin ubicación.")
    evidence = section(text, ["evidencia", "hechos"])
    if evidence and not TAG.search(evidence) and "```" not in evidence:
        warnings.append("Técnico: la evidencia no tiene etiquetas [R]/[DB]/[C]/[C-sub]/[H] ni extractos literales.")
    env = section(text, ["entorno", "versión", "version"])
    if env and not re.search(r"\b[0-9a-f]{7,40}\b|imagen|image|creado|created|\d{4}-\d{2}-\d{2}", env, re.I):
        warnings.append("Técnico: 'Entorno y versión' no identifica la versión (commit, imagen o fecha del contenedor).")
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Revisa la estructura de los reportes de un defecto.")
    parser.add_argument("files", nargs="*")
    parser.add_argument("--tecnico", help="Revisa solo este reporte técnico")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    jobs = []
    if args.tecnico:
        jobs.append(("tecnico", args.tecnico))
    for f in args.files:
        jobs.append(("tecnico" if os.path.basename(f).lower().endswith("_tecnico.md") else "ejecutivo", f))
    if not jobs:
        parser.print_help()
        sys.exit(2)

    result = {"files": [], "errors": [], "warnings": []}
    for kind, path in jobs:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        e, w = (lint_technical if kind == "tecnico" else lint_executive)(text)
        result["files"].append({"file": path, "kind": kind, "errors": e, "warnings": w})
        result["errors"] += e
        result["warnings"] += w
    result["ok"] = not result["errors"]

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for f in result["files"]:
            for e in f["errors"]:
                print(f"ERROR  {os.path.basename(f['file'])}: {e}")
            for w in f["warnings"]:
                print(f"AVISO  {os.path.basename(f['file'])}: {w}")
        print(f"report_lint: {'OK' if result['ok'] else 'FALLA'} — {len(result['errors'])} errores, {len(result['warnings'])} advertencias")
    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
