#!/usr/bin/env python3
"""
E2E Run Document - validator
----------------------------
Checks that an E2E run document follows the qa-e2e-corrida template, so every
run report has the same structure no matter which person or assistant wrote it.
Deterministic, read-only, standard library only.

  validate_run.py <documento.md> [--json] [--strict]

Exit codes: 0 = no errors (warnings allowed unless --strict), 1 = errors, 2 = bad arguments.
"""
import os
import re
import sys
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REQUIRED_HEADINGS = [
    (r"^## 0\.", "## 0. Metadatos, línea base y plan"),
    (r"^### 0\.1", "### 0.1 Libro de decisiones"),
    (r"^### 0\.2", "### 0.2 Enlaces de la corrida"),
    (r"^### 0\.5", "### 0.5 Plan de proyecto"),
    (r"^### 0\.6", "### 0.6 Foto de la configuración de agentes"),
    (r"^## 1\. Maya", "## 1. Maya"),
    (r"^## 2\. Product Owner", "## 2. Product Owner"),
    (r"^## 3\. Arquitecto", "## 3. Arquitecto"),
    (r"^## 4\. UI/UX", "## 4. UI/UX"),
    (r"^## 5\. QA", "## 5. QA"),
    (r"^## 6\. Developer", "## 6. Developer"),
    (r"^### 6\.a", "### 6.a Funcionamiento del agente"),
    (r"^### 6\.b", "### 6.b Código entregado"),
    (r"^## 7\. DevSec", "## 7. DevSec"),
    (r"^## 8\. DevOps", "## 8. DevOps"),
    (r"^## 9\.", "## 9. Resumen ejecutivo"),
    (r"^### 9\.1", "### 9.1 Lo bueno por agente"),
    (r"^### 9\.2", "### 9.2 Hallazgos consolidados"),
    (r"^### 9\.3", "### 9.3 Discrepancias"),
    (r"^### 9\.4", "### 9.4 Resultado del plan de issues"),
    (r"^### 9\.5", "### 9.5 Coherencia entre agentes"),
    (r"^### 9\.6", "### 9.6 Documentación publicada"),
    (r"^### 9\.7", "### 9.7 Bloqueos y fallas de la corrida"),
    (r"^## 10\.", "## 10. Pendientes"),
    (r"^## 11\.", "## 11. Validación del documento"),
]

REQUIRED_METADATA = ["Modo", "Empresa", "ID de proyecto IAF", "Documento de proyecto", "Entorno", "Fechas",
                     "Ejecutado por", "Modelo del asistente", "Versión del kit", "Quién responde a los agentes",
                     "Objetivo de la corrida"]

AGENT_SECTIONS = [("1", "Maya"), ("2", "Product Owner"), ("3", "Arquitecto"), ("4", "UI/UX"), ("5", "QA"),
                  ("6", "Developer"), ("7", "DevSec"), ("8", "DevOps")]

ALLOWED_TAGS = {"R", "DB", "C", "C-sub", "H"}
SEVERITIES = {"crítica", "critica", "alta", "media", "baja"}
# (regex, case-insensitive). "En curso" alone is also a Sheet status, so only the parenthesised form counts.
STALE_MARKERS = [(r"\(en curso\)", True), (r"\bTODO\b", False), (r"\{\{", False), (r"<fecha", True),
                 (r"\bcandidat[oa]s?\b", True), (r"\(pendiente\)", True)]


def split_sections(text: str) -> dict:
    """Maps '## N.' agent sections to their text."""
    out, current, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^## (\d+)\.", line)
        if m:
            if current:
                out[current] = "\n".join(buf)
            current, buf = m.group(1), [line]
        elif current:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf)
    return out


def table_rows_after(text: str, heading_regex: str) -> list:
    """Data rows of the first markdown table after a heading matching heading_regex."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.search(heading_regex, line):
            rows, in_table = [], False
            for nxt in lines[i + 1:]:
                if nxt.startswith("#"):
                    break
                if nxt.strip().startswith("|"):
                    in_table = True
                    if re.match(r"^\|\s*:?-{3,}", nxt.strip()):
                        continue
                    rows.append([c.strip() for c in nxt.strip().strip("|").split("|")])
                elif in_table and nxt.strip():
                    break
            return rows[1:] if rows else []  # drop header row
    return []


def is_empty_row(row: list) -> bool:
    return all(not c or c in ("-", "—") for c in row[1:]) if row else True


def validate(path: str) -> dict:
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # Template comments are instructions, not content ("No participó" inside one must not skip a section).
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    errors, warnings = [], []

    for rx, label in REQUIRED_HEADINGS:
        if not re.search(rx, text, re.M):
            errors.append(f"Falta la sección '{label}'.")

    meta = {}
    for row in table_rows_after(text, r"^## 0\."):
        if len(row) >= 2:
            meta[row[0]] = row[1]
    for field in REQUIRED_METADATA:
        key = next((k for k in meta if k.startswith(field)), None)
        if key is None:
            errors.append(f"Metadatos: falta el campo '{field}'.")
        elif not meta[key] or "{{" in meta[key] or meta[key].startswith("("):
            errors.append(f"Metadatos: el campo '{field}' está vacío o sin reemplazar.")

    antes = re.search(r"\]\(([^)]*proyectos/[^)]+\.md)\)", meta.get(next((k for k in meta if k.startswith("Documento de proyecto")), ""), "") or "")
    if antes:
        target = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(path)), antes.group(1)))
        if not os.path.exists(target):
            errors.append(f"El documento 'Antes' enlazado no existe: {antes.group(1)}")
    else:
        errors.append("Metadatos: el documento 'Antes' no está enlazado (proyectos/<slug>_requisitos.md).")

    if not [r for r in table_rows_after(text, r"^### 0\.6") if not is_empty_row(r)]:
        warnings.append("§0.6: no hay foto de la configuración de agentes (o la tabla está vacía).")

    sections = split_sections(text)
    for num, name in AGENT_SECTIONS:
        body = sections.get(num, "")
        if not body or re.search(r"No particip", body):
            continue
        if "✅" not in body:
            errors.append(f"§{num} {name}: falta '✅ Lo que funcionó bien'.")
        if "❌" not in body:
            errors.append(f"§{num} {name}: falta la tabla '❌ Hallazgos'.")
        if "🔍" not in body:
            errors.append(f"§{num} {name}: falta el contraste '🔍' con el Sheet en vivo.")
        elif "--status all" not in body:
            errors.append(f"§{num} {name}: el contraste 🔍 no cita la consulta con '--status all'.")
        for row in table_rows_after(body, r"❌"):
            if is_empty_row(row):
                continue
            joined = " | ".join(row[:3])
            if re.search(r"\bAF-\d+", joined):
                errors.append(f"§{num} {name}: la fila '{row[0]}' de ❌ menciona un AF-ID (va solo en 🔍).")
            sev = next((c for c in row[3:4]), "")
            sev_word = re.split(r"[\s(]", sev.strip("* "), maxsplit=1)[0].lower() if sev else ""
            if sev and sev_word not in SEVERITIES:
                warnings.append(f"§{num} {name}: gravedad '{sev}' en '{row[0]}' fuera de la escala (Crítica/Alta/Media/Baja).")

    dev = sections.get("6", "")
    if dev and not re.search(r"No particip", dev):
        sixb = dev.split("### 6.b", 1)[1] if "### 6.b" in dev else ""
        method = table_rows_after(sixb, r"Dato del método|^Método")
        if not method or any(len(r) < 2 or not r[1] for r in method):
            errors.append("§6.b: la tabla del método (repo/commit, cómo se ejecutaron las reglas, controles, completa o parcial) está incompleta.")
        perf = table_rows_after(sixb, r"Datos de rendimiento")
        if not perf or any(len(r) < 2 or not r[1] for r in perf):
            errors.append("§6.b: la tabla de datos de rendimiento está incompleta (usa 'No aplica' si no hubo código).")

    # §9.2: la decisión de qué es ticket la toma una persona, fila por fila.
    decisions = [r for r in table_rows_after(text, r"^### 9\.2") if not is_empty_row(r)]
    for r in decisions:
        if len(r) < 9:
            errors.append("§9.2: la tabla no tiene las columnas de decisión humana (Decisión, Motivo, Decidido por); "
                          "usa la plantilla actual.")
            break
        cause, decision, reason, who = r[0] or r[1], r[6], r[7], r[8]
        if not re.match(r"(?i)^\**\s*(ticket|ampliar\s+AF-\d+|descartar)\b", decision):
            errors.append(f"§9.2 '{cause[:40]}': falta la decisión humana (Ticket / Ampliar AF-XXX / Descartar).")
        if not who.strip(" -—"):
            errors.append(f"§9.2 '{cause[:40]}': falta quién decidió.")
        if re.match(r"(?i)^\**\s*descartar", decision) and not reason.strip(" -—"):
            errors.append(f"§9.2 '{cause[:40]}': un descarte necesita motivo.")
        if re.search(r"(?i)\b(claude|asistente|ia|agy|gemini|gpt)\b", who):
            errors.append(f"§9.2 '{cause[:40]}': 'Decidido por' debe ser una persona, no el asistente.")

    discrepancies = table_rows_after(text, r"^### 9\.3")
    if not [r for r in discrepancies if not is_empty_row(r)] and not re.search(r"(?is)### 9\.3.*?sin discrepancias", text):
        warnings.append("§9.3: la tabla de discrepancias está vacía (si no hubo, escribir 'Sin discrepancias').")

    bad_tags = sorted({t for t in re.findall(r"\[([A-Za-z][A-Za-z\-]{0,6})\](?!\()", text)
                       if t not in ALLOWED_TAGS and not t.isdigit() and t.lower() not in ("x", "ok")})
    if bad_tags:
        errors.append(f"Etiquetas de evidencia fuera de la convención: {', '.join('[' + t + ']' for t in bad_tags)} "
                      f"(permitidas: [R] [DB] [C] [C-sub] [H]).")

    primary = "\n".join(l for l in text.splitlines()
                        if not re.match(r"^\s*[*_>]*\s*\*?Registro en vivo", l)
                        and not l.strip().startswith(("<!--", "#")))
    for rx, icase in STALE_MARKERS:
        hits = len(re.findall(rx, primary, re.I if icase else 0))
        if hits:
            warnings.append(f"Texto principal con marca de estado no final '{rx}' ({hits} vez/veces): muévela a 'Registro en vivo' si ya se resolvió.")

    return {"file": path, "ok": not errors, "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description="Valida un documento de corrida E2E contra la plantilla del kit.")
    parser.add_argument("document")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Las advertencias también hacen fallar")
    args = parser.parse_args()
    if not os.path.isfile(args.document):
        print(f"No existe: {args.document}", file=sys.stderr)
        sys.exit(2)

    res = validate(args.document)
    failed = bool(res["errors"]) or (args.strict and bool(res["warnings"]))
    res["summary"] = (f"validate_run: {'OK' if not failed else 'FALLA'} — {len(res['errors'])} errores, "
                      f"{len(res['warnings'])} advertencias{' (modo estricto)' if args.strict else ''}")
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        for e in res["errors"]:
            print(f"ERROR  {e}")
        for w in res["warnings"]:
            print(f"AVISO  {w}")
        print(res["summary"])
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
