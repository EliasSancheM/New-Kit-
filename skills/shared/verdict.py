#!/usr/bin/env python3
"""
Verdict lint and publisher (shared by qa-finish and qa-rejection).

A verdict is a markdown file written from skills/shared/templates/veredicto.md. The lint
checks that it carries what a verdict needs to be trusted: the version that was tested,
the ticket's acceptance criterion, the three questions about the developer's change, a
table of executed cases with runtime evidence ([R]/[DB]) and a result per case, the
limits, and no placeholders or hedging ("se asume", "debería funcionar").

  verdict.py lint <veredicto.md> [--json]

Exit codes: 0 no errors / 1 errors / 2 bad arguments.
"""
import os
import re
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import utils

H1_RE = re.compile(r"^#\s+(AF-\d+)\s*[—–-]+\s*Veredicto QA:\s*(Finalizada|Rechazada por QA)\s*$", re.M)
FIELD_RE = r"(?im)^\**\s*{name}\s*:\**\s*(.*)$"
PLACEHOLDER_RE = re.compile(r"<[^>\n]{3,}>")
HEDGING = ["se asume", "debería funcionar", "deberia funcionar", "probablemente", "parece funcionar",
           "no se probó pero", "no se probo pero", "en teoría", "en teoria", "alta confianza"]
TYPES = {"ticket", "control", "límite", "limite"}
RESULTS = {"pasa", "falla", "no probado"}


def field(text: str, name: str) -> str:
    m = re.search(FIELD_RE.format(name=name), text)
    return m.group(1).strip() if m else ""


def section(text: str, keywords: list) -> str:
    parts = re.split(r"^(#{2,4}\s+.+)$", text, flags=re.M)
    for i in range(1, len(parts), 2):
        if any(k in parts[i].lower() for k in keywords):
            return parts[i + 1] if i + 1 < len(parts) else ""
    return ""


def table_rows(body: str) -> list:
    rows = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|") or re.match(r"^\|\s*:?-{3,}", s):
            continue
        rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows[1:] if rows else []


def parse_header(text: str) -> tuple:
    """(defect_id, status) or (None, None)."""
    m = H1_RE.search(text)
    return (m.group(1), m.group(2)) if m else (None, None)


def lint_verdict(text: str) -> tuple:
    errors, warnings = [], []
    defect_id, status = parse_header(text)
    if not defect_id:
        errors.append("El encabezado debe ser '# AF-NNN — Veredicto QA: Finalizada' o '... Rechazada por QA'.")

    for name in ("Resumen", "Versión probada", "Fecha y entorno", "Criterio del ticket"):
        val = field(text, name)
        if not val or PLACEHOLDER_RE.search(val):
            errors.append(f"Falta el campo '{name}' (o sigue con el texto de la plantilla).")
    build = field(text, "Versión probada")
    if build and not re.search(r"\b[0-9a-f]{7,40}\b|imagen|image|\d{4}-\d{2}-\d{2}", build, re.I):
        errors.append("'Versión probada' no identifica la versión: commit, imagen o fecha de creación del contenedor.")

    changes = section(text, ["qué cambió", "que cambio", "cambios del desarrollador"])
    if not changes.strip():
        errors.append("Falta la sección 'Qué cambió el desarrollador'.")
    else:
        for q in ("causa raíz", "todos los síntomas", "test del caso"):
            if q not in changes.lower():
                errors.append(f"'Qué cambió el desarrollador' no responde la pregunta sobre '{q}'.")

    cases = section(text, ["casos probados"])
    rows = [r for r in table_rows(cases) if any(c for c in r[1:])]
    if not rows:
        errors.append("'Casos probados' no tiene ninguna fila ejecutada.")
    types_seen, results = set(), []
    for r in rows:
        if len(r) < 7:
            errors.append(f"Caso '{r[1] if len(r) > 1 else r[0]}': la fila no tiene las 7 columnas de la plantilla.")
            continue
        _, case, ctype, steps, observed, evidence, result = r[:7]
        ctype_word = ctype.strip("* ").lower()
        result_word = result.strip("* ").lower()
        label = case[:40] or f"fila {r[0]}"
        if ctype_word not in TYPES:
            errors.append(f"Caso '{label}': tipo '{ctype}' no es ticket, control ni límite.")
        types_seen.add("límite" if ctype_word == "limite" else ctype_word)
        if result_word not in RESULTS:
            errors.append(f"Caso '{label}': veredicto '{result}' debe ser Pasa, Falla o No probado.")
        results.append((ctype_word, result_word, label))
        if result_word != "no probado":
            if not steps or not observed:
                errors.append(f"Caso '{label}': faltan los pasos o el resultado observado.")
            if not re.search(r"\[(R|DB)\]", evidence):
                errors.append(f"Caso '{label}': la evidencia debe ser observada [R] o leída en datos/logs [DB]; "
                              f"'{evidence or 'vacía'}' no sirve para un veredicto.")
        if PLACEHOLDER_RE.search(" ".join(r)):
            errors.append(f"Caso '{label}': quedan marcadores '<...>' de la plantilla.")
    if rows and "ticket" not in types_seen:
        errors.append("Falta el caso de tipo 'ticket' (el que describe el defecto).")
    if rows and "control" not in types_seen:
        errors.append("Falta el caso de tipo 'control' (algo que ya funcionaba y no debe romperse).")

    if status == "Finalizada":
        for ctype, result, label in results:
            if ctype in ("ticket", "control") and result != "pasa":
                errors.append(f"Finalizada exige que el caso {ctype} '{label}' pase; está en '{result}'.")
        if any(res == "falla" for _, res, _ in results):
            errors.append("Finalizada con un caso en 'Falla': o es rechazo, o el caso no corresponde a este ticket.")
    elif status == "Rechazada por QA":
        if results and not any(res == "falla" for _, res, _ in results):
            errors.append("Rechazada por QA exige al menos un caso en 'Falla' con evidencia; si nada falló, no es un rechazo.")

    limits = section(text, ["límites", "limites", "no verificado"])
    if not limits.strip() or PLACEHOLDER_RE.search(limits):
        errors.append("Falta 'Límites y no verificado' (escribe 'Ninguno' si se probó todo).")

    outside_limits = text.replace(limits, "")
    for phrase in HEDGING:
        if phrase in outside_limits.lower():
            errors.append(f"Frase '{phrase}' fuera de 'Límites': un veredicto afirma lo observado o lo declara no verificado.")
    leftovers = PLACEHOLDER_RE.findall(text)
    if leftovers:
        warnings.append(f"Quedan {len(leftovers)} marcadores '<...>' de la plantilla en el documento.")
    return errors, warnings


def publish_verdict(expected_status: str, action: str, argv: list) -> None:
    """CLI shared by qa_finish_publisher and qa_rejection_publisher.

      <script> [--dry-run | --confirm <código>] <veredicto.md>
    """
    dry_run = "--dry-run" in argv
    confirm, args = utils.pop_option([a for a in argv if a != "--dry-run"], "--confirm")
    if len(args) != 1 or not os.path.isfile(args[0]):
        print(f"Uso: [--dry-run | --confirm <código>] <veredicto.md>   (plantilla: skills/shared/templates/veredicto.md)")
        sys.exit(2)
    path = args[0]
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    defect_id, status = parse_header(text)
    errors, warnings = lint_verdict(text)
    if defect_id and status != expected_status:
        print(f"[ARGUMENTOS] El veredicto dice '{status}' y este script publica '{expected_status}'. "
              f"Usa el script que corresponde.", file=sys.stderr)
        sys.exit(2)
    if not dry_run and errors:
        print("[BLOQUEADO] El veredicto no cumple la plantilla:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    gate = [action, [utils.file_digest(path), defect_id or "", expected_status]]
    if not dry_run:
        utils.require_confirm(gate[0], gate[1], confirm)
    summary = field(text, "Resumen")
    build = field(text, "Versión probada")
    if dry_run:
        pre = utils.publish_qa_outcome(defect_id or "AF-000", expected_status, summary, report_text=text, dry_run=True) \
            if defect_id else None
        out = pre or {"dry_run": True, "defect_id": defect_id}
        out["lint"] = {"errors": errors, "warnings": warnings}
        if "sheet_updates" in out:
            out["sheet_updates"]["comentario_qa"] = f"<veredicto completo, {len(utils.truncate_comment(text))} caracteres>"
        out["build"] = build
        out["confirm_code"] = utils.confirm_code(*gate) if not errors else None
        if errors:
            out["bloqueado_por_lint"] = "Corrige el veredicto y repite el dry-run para obtener el código."
        print(json.dumps(out, indent=2, ensure_ascii=False))
        sys.exit(0 if pre or errors else 1)

    pre = utils.publish_qa_outcome(defect_id, expected_status, summary, report_text=text, dry_run=True)
    if not pre:
        sys.exit(1)
    utils.require_human_confirmation(action, defect_id, [
        f"Fila: {pre['sheet_row']} (estado actual: {pre['estado_actual'] or 'vacío'})",
        f"Resumen: {summary}", f"Versión probada: {build}", f"Veredicto: {path}"])
    res = utils.publish_qa_outcome(defect_id, expected_status, summary, report_text=text, evidence=section(text, ["casos probados"]),
                                   tech_details=section(text, ["qué cambió", "que cambio"]))
    if not res:
        sys.exit(1)
    res["local_file"] = os.path.abspath(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "lint":
        print(__doc__)
        sys.exit(2)
    path = sys.argv[2]
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    errors, warnings = lint_verdict(text)
    if "--json" in sys.argv:
        print(json.dumps({"file": path, "ok": not errors, "errors": errors, "warnings": warnings}, indent=2, ensure_ascii=False))
    else:
        for e in errors:
            print(f"ERROR  {e}")
        for w in warnings:
            print(f"AVISO  {w}")
        print(f"verdict_lint: {'OK' if not errors else 'FALLA'} — {len(errors)} errores, {len(warnings)} advertencias")
    sys.exit(0 if not errors else 1)


if __name__ == "__main__":
    main()
