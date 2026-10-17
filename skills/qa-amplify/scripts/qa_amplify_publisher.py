"""
QA Amplify Publisher
--------------------
Adds new evidence to an existing defect (AF-XXX) WITHOUT changing its status:
appends a block "--- Ampliación (<origen>) ---" at the end of COMENTARIO QA in
the sheet and keeps a local copy in Reportes/ampliaciones/. ESTADO is never touched.

Usage:
  One ticket:
    qa_amplify_publisher.py [--dry-run] AF-XXX "<origen>" "<evidencia markdown>"
    qa_amplify_publisher.py [--dry-run] AF-XXX "<origen>" --body-file <evidencia.md>
  Several tickets from a file with sections separated by a '---' line:
    qa_amplify_publisher.py [--dry-run] --file <ampliaciones.md> --origin "<origen>" [--only AF-X,AF-Y]

  File format:
    ## AF-231 — <título>            -> one block with the section body
    ## AF-231 / AF-245 — <título>   -> same body appended to both tickets
    ## Evidencia adicional para duplicados
    - **AF-300** (<nota>): <texto>  -> one short block per bullet

Exit codes: 0 all ok (or dry-run) / 1 some ticket failed / 2 bad arguments /
4 missing or stale --confirm / 6 no Sheets token.
"""
import os
import re
import sys
import json
import argparse
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

SECTION_RE = re.compile(r"\s*## (AF-\d+(?:\s*/\s*AF-\d+)*)\s+[—-]\s+")
BULLET_RE = re.compile(r"- \*\*(AF-\d+(?:\s*/\s*AF-\d+)*)\*\*(?: \(([^)]*)\))?: (.*)")
SAFE_RE = re.compile(r"[^0-9A-Za-z._-]+")


def safe_origin(origin: str) -> str:
    return SAFE_RE.sub("_", origin.strip()).strip("_")


def parse_file(text: str) -> list[tuple[list[str], str]]:
    items = []
    for sec in re.split(r"\n---\s*\n", text):
        m = SECTION_RE.match(sec)
        if m:
            ids = re.findall(r"AF-\d+", m.group(1))
            parts = sec.strip().split("\n", 1)
            items.append((ids, parts[1].strip() if len(parts) > 1 else ""))
        elif re.search(r"^## Evidencia adicional para duplicados", sec, re.M):
            for line in sec.splitlines():
                mm = BULLET_RE.match(line.strip())
                if mm:
                    note = f" ({mm.group(2)})" if mm.group(2) else ""
                    items.append((re.findall(r"AF-\d+", mm.group(1)),
                                  f"**Qué se vio{note}**\n- {mm.group(3)}"))
    return items


def build_block(origin: str, body: str) -> str:
    today = datetime.date.today().isoformat()
    return (f"--- Ampliación ({origin}) ---\n{today}, {utils.get_user_name()}. Evidencia adicional; "
            f"el estado del ticket no cambia.\n\n{body.strip()}")


def process(defect_id: str, origin: str, body: str, dry_run: bool) -> dict:
    name = f"{defect_id}_ampliacion_{safe_origin(origin)}"
    rec = {"id": defect_id, "name": name}

    row_idx = utils.find_sheet_row_for_defect(defect_id)
    rec["sheet_row"] = row_idx
    if not row_idx:
        rec["error"] = "no está en el Sheet"
        return rec
    rec["estado_actual"] = utils.get_sheet_cell(row_idx, "estado")
    current = utils.get_sheet_cell(row_idx, "comentario_qa")
    header = f"--- Ampliación ({origin}) ---"
    if header in current:
        rec["error"] = "ya hay una ampliación con ese origen en Comentario QA; no se duplica (usa otro origen si es evidencia distinta)"
        rec["already_exists"] = True
        return rec

    block = build_block(origin, body)
    new_comment = utils.truncate_comment((current.rstrip() + "\n\n" if current.strip() else "") + block)
    rec["chars_agregados"] = len(block)
    rec["chars_total"] = len(new_comment)
    if dry_run:
        rec["preview"] = block[:600] + ("…" if len(block) > 600 else "")
        return rec

    utils.batch_update_sheet_row(row_idx, {"comentario_qa": new_comment})
    rec["sheet_updated"] = True

    target_dir = os.path.join(utils.REPORTS_DIR, "ampliaciones")
    os.makedirs(target_dir, exist_ok=True)
    local = os.path.join(target_dir, f"{name}.md")
    with open(local, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n\n{block}\n")
    rec["local_file"] = local
    return rec


@utils.exit_on_auth_error
def main():
    parser = argparse.ArgumentParser(description="Agrega evidencia a un AF-XXX existente sin cambiar su estado.")
    parser.add_argument("defect_id", nargs="?")
    parser.add_argument("origin_pos", nargs="?", metavar="origen")
    parser.add_argument("body", nargs="?", metavar="evidencia")
    parser.add_argument("--body-file")
    parser.add_argument("--file", help="Archivo con secciones '## AF-XXX — título'")
    parser.add_argument("--origin", help="Origen (con --file), p. ej. E2E_Apiux_2026-09-25")
    parser.add_argument("--only", help="Solo estos IDs, separados por coma")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", help="Código que imprime el --dry-run del mismo lote (obligatorio para publicar)")
    args = parser.parse_args()

    jobs = []  # (id, origin, body)
    if args.file:
        if not args.origin or args.defect_id:
            parser.error("con --file usa --origin y no pases un AF-XXX posicional")
        with open(args.file, encoding="utf-8") as f:
            items = parse_file(f.read())
        only = {x.strip().upper() for x in args.only.split(",")} if args.only else None
        for ids, body in items:
            jobs += [(i, args.origin, body) for i in ids if not only or i in only]
        if not jobs:
            parser.error("el archivo no tiene secciones reconocibles (o --only no coincide con ninguna)")
    else:
        body = args.body
        if args.body_file:
            with open(args.body_file, encoding="utf-8") as f:
                body = f.read()
        if not (args.defect_id and args.origin_pos and body):
            parser.error("uso: AF-XXX \"<origen>\" \"<evidencia>\" (o --body-file), o bien --file ... --origin ...")
        jobs = [(args.defect_id.upper(), args.origin_pos, body)]

    gate_parts = []
    for i, o, b in jobs:
        gate_parts += [i, o, b]
    if not args.dry_run:
        utils.require_confirm("qa-amplify", gate_parts, args.confirm)

    results = [process(i, o, b, args.dry_run) for i, o, b in jobs]
    out = {"dry_run": args.dry_run, "tickets": results}
    if args.dry_run:
        out["confirm_code"] = utils.confirm_code("qa-amplify", gate_parts)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    failed = [r for r in results if "error" in r]
    if failed:
        print(f"{len(failed)} de {len(results)} tickets con error: {', '.join(r['id'] for r in failed)}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
