"""
Google Sheets Defect Publisher (report-bug)
-------------------------------------------
Publishes a new defect from its two markdown reports (executive + technical):
1. Lints both reports against the report-bug templates (errors block the publish).
2. Reads ID, title, severity and symptom from the executive report.
3. Audits the sheet: next free AF-XXX and first empty row below the table. The ID
   in the report must be that next ID, otherwise nothing is written.
4. Writes the row: ID, NOMBRE, GRAVEDAD, DESCRIPCION, REPORTADA POR, FECHA INICIO,
   ESTADO=Reportada and the full executive + technical text in COMENTARIO QA.

  gsheets_updater.py --audit
  gsheets_updater.py [--dry-run | --confirm <código>] <ejecutivo.md> <tecnico.md> [--gravedad <Critica|Alta|Media|Baja>]

Exit codes: 0 ok / 1 lint or write failure / 2 bad arguments or ID mismatch /
4 missing or stale --confirm / 5 no human confirmation / 6 no Sheets token.
"""
import json
import urllib.request
import re
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_lint

H1_RE = re.compile(r"^#\s+(AF-\d+)\s*[—–-]+\s*(.+)$", re.M)
SEV_RE = re.compile(r"(?im)^\**\s*gravedad\**\s*:\**\s*([^\s*<>|]+)")


def parse_executive(text: str) -> tuple:
    """(defect_id, title, severity, description) from the executive report."""
    m = H1_RE.search(text)
    if not m:
        raise ValueError("El reporte ejecutivo debe empezar con '# AF-NNN — <título>' (con el ID real, no AF-XXX).")
    defect_id, title = m.group(1), m.group(2).strip().strip("*").strip()
    sev = SEV_RE.search(text)
    severity = sev.group(1) if sev else ""
    body = report_lint.section(text, ["qué falla", "que falla", "síntoma", "sintoma"])
    description = " ".join(l.strip().lstrip("-* ").replace("**", "").strip() for l in body.splitlines() if l.strip()).strip()
    return defect_id, title, severity, description or title


def build_comment(executive: str, technical: str) -> str:
    return f"REPORTE EJECUTIVO\n\n{executive.strip()}\n\n---\n\nREPORTE TÉCNICO\n\n{technical.strip()}"


def audit_and_get_next_id_and_target_row() -> tuple:
    token = utils.get_sheets_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{utils.SPREADSHEET_ID}/values/{utils.SHEET_NAME}!A:A"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

    af_ids = []
    last_occupied_row_idx = 1
    with utils.google_urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    for r_idx, row in enumerate(data.get("values", [])):
        if row and row[0].strip():
            last_occupied_row_idx = max(last_occupied_row_idx, r_idx + 1)
            match = re.search(r"AF-(\d+)", row[0].strip())
            if match:
                af_ids.append(int(match.group(1)))

    next_num = (max(af_ids) + 1) if af_ids else 1
    return f"AF-{next_num:03d}", last_occupied_row_idx + 1


def insert_defect_row(defect_id: str, target_row: int, name: str, description: str, severity: str, comment: str) -> None:
    token = utils.get_sheets_token()
    user_name = utils.get_user_name()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    mapping = utils.get_column_mapping()

    row_values = [""] * 15

    def set_col(key: str, val: str):
        letter = mapping.get(key, "")
        if letter and len(letter) == 1 and "A" <= letter <= "O":
            row_values[ord(letter) - ord("A")] = val

    set_col("id", defect_id)
    set_col("nombre", name)
    set_col("gravedad", severity)
    set_col("descripcion", description)
    set_col("reportada_por", user_name)
    set_col("fecha_inicio", today_str)
    set_col("estado", "Reportada")
    set_col("comentario_qa", comment)

    range_target = f"{utils.SHEET_NAME}!A{target_row}:O{target_row}"
    url_put = (f"https://sheets.googleapis.com/v4/spreadsheets/{utils.SPREADSHEET_ID}/values/{range_target}"
               f"?valueInputOption=USER_ENTERED")
    payload = {"range": range_target, "majorDimension": "ROWS", "values": [row_values]}
    req = urllib.request.Request(url_put, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                                 method="PUT")
    with utils.google_urlopen(req, timeout=20) as resp:
        json.loads(resp.read().decode("utf-8"))

    utils.sync_obsidian_note(defect_id=defect_id, title=name, status="Reportada", severity=severity,
                             evidence="Defecto reportado y registrado en Google Sheets.", tech_details=description)


def usage(code: int = 2):
    print("Uso: python gsheets_updater.py [--dry-run | --confirm <código>] <ejecutivo.md> <tecnico.md> "
          "[--gravedad <Critica|Alta|Media|Baja>]\n     python gsheets_updater.py --audit   (solo imprime el próximo ID y la fila)")
    sys.exit(code)


@utils.exit_on_auth_error
def main():
    dry_run = "--dry-run" in sys.argv
    confirm, args = utils.pop_option([a for a in sys.argv[1:] if a != "--dry-run"], "--confirm")
    gravedad_opt, args = utils.pop_option(args, "--gravedad")

    if args == ["--audit"]:
        nid, trow = audit_and_get_next_id_and_target_row()
        print(f"Next ID: {nid}\nTarget Row: {trow}")
        return
    if len(args) != 2:
        usage()
    eje_path, tec_path = args
    for p in (eje_path, tec_path):
        if not os.path.isfile(p):
            print(f"No existe: {p}", file=sys.stderr)
            sys.exit(2)
    with open(eje_path, encoding="utf-8", errors="replace") as fh:
        executive = fh.read()
    with open(tec_path, encoding="utf-8", errors="replace") as fh:
        technical = fh.read()

    # Structure (report-bug templates). With errors nothing is published and the dry-run gives no code.
    e1, w1 = report_lint.lint_executive(executive)
    e2, w2 = report_lint.lint_technical(technical)
    lint = {"ejecutivo": {"errors": e1, "warnings": w1}, "tecnico": {"errors": e2, "warnings": w2}}
    lint_errors = e1 + e2

    try:
        report_id, title, sev_in_report, description = parse_executive(executive)
        severity = utils.normalize_severity(gravedad_opt or sev_in_report)
    except ValueError as e:
        print(f"[ARGUMENTOS] {e}", file=sys.stderr)
        sys.exit(2)
    tec_h1 = H1_RE.search(technical)
    if tec_h1 and tec_h1.group(1) != report_id:
        print(f"[ARGUMENTOS] El técnico dice {tec_h1.group(1)} y el ejecutivo {report_id}.", file=sys.stderr)
        sys.exit(2)

    gate = ["report-bug", [utils.file_digest(eje_path), utils.file_digest(tec_path), severity]]
    if not dry_run:
        if lint_errors:
            print("[BLOQUEADO] Los reportes no cumplen la estructura de las plantillas de report-bug:", file=sys.stderr)
            for e in lint_errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(1)
        utils.require_confirm(gate[0], gate[1], confirm)

    nid, trow = audit_and_get_next_id_and_target_row()
    if nid != report_id:
        print(f"[ID] La planilla asignará {nid}, pero los reportes dicen {report_id}. Renombra los archivos y el "
              f"encabezado a {nid} (otra persona reportó entre medio) y repite el dry-run. No se escribió nada.",
              file=sys.stderr)
        sys.exit(2)

    comment = utils.truncate_comment(build_comment(executive, technical))
    if dry_run:
        print(json.dumps({
            "dry_run": True, "defect_id": nid, "target_row": trow, "nombre": title, "gravedad": severity,
            "descripcion": description, "estado": "Reportada", "reportada_por": utils.get_user_name(),
            "comentario_qa_chars": len(comment), "comentario_qa_inicio": comment[:300],
            "lint": lint,
            "confirm_code": utils.confirm_code(*gate) if not lint_errors else None,
            **({"bloqueado_por_lint": "Corrige los errores de estructura y repite el dry-run para obtener el código."}
               if lint_errors else {}),
        }, indent=2, ensure_ascii=False))
        return

    utils.require_human_confirmation("Nuevo defecto en Google Sheets", nid, [
        f"Fila: {trow}", f"Nombre: {title}", f"Gravedad: {severity}",
        f"Comentario QA: {len(comment)} caracteres (ejecutivo + técnico)"])
    insert_defect_row(nid, trow, title, description, severity, comment)
    print(json.dumps({"defect_id": nid, "row": trow, "nombre": title, "gravedad": severity, "sheet_updated": True},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
