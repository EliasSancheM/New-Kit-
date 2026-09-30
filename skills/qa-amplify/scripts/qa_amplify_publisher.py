"""
QA Amplify Publisher
--------------------
Adds new evidence to an existing defect (AF-XXX) WITHOUT changing its status:
publishes a subpage 'AF-XXX_ampliacion_<origen>' under the defect's Level-1
Notion page and keeps a local copy in Reportes/ampliaciones/.

The Sheet status is never touched. With --link-in-sheet, the subpage URL is
appended to the end of COMENTARIO QA (existing text is kept).

Usage:
  One ticket:
    qa_amplify_publisher.py [--dry-run] AF-XXX "<origen>" "<evidencia markdown>" [--level1 <page_id>]
    qa_amplify_publisher.py [--dry-run] AF-XXX "<origen>" --body-file <evidencia.md>
  Several tickets from a file with sections separated by a '---' line:
    qa_amplify_publisher.py [--dry-run] --file <ampliaciones.md> --origin "<origen>" [--only AF-X,AF-Y]

  File format:
    ## AF-231 — <título>            -> one subpage with the section body
    ## AF-231 / AF-245 — <título>   -> same body published on both tickets
    ## Evidencia adicional para duplicados
    - **AF-300** (<nota>): <texto>  -> one short subpage per bullet

Exit codes: 0 all ok (or dry-run) / 1 some ticket failed / 2 bad arguments.
"""
import os
import re
import sys
import json
import argparse
import datetime
import urllib.request

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


def list_child_titles(page_id: str) -> list[str] | None:
    """Titles of the child pages of a Notion page (REST). None if it can't be read."""
    token = utils.get_notion_token()
    if not token:
        return None
    titles, cursor = [], None
    try:
        while True:
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
            if cursor:
                url += f"&start_cursor={cursor}"
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"})
            with urllib.request.urlopen(req, context=utils.get_ssl_context(), timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            titles += [b["child_page"]["title"] for b in data.get("results", []) if b.get("type") == "child_page"]
            if not data.get("has_more"):
                return titles
            cursor = data.get("next_cursor")
    except Exception as e:
        print(f"Warning: no se pudieron leer las subpáginas de {page_id} ({e})", file=sys.stderr)
        return None


def build_markdown(defect_id: str, origin: str, body: str) -> str:
    today = datetime.date.today().isoformat()
    return (f"> Evidencia adicional ({origin}), agregada el {today} por {utils.get_user_name()}. "
            f"Se agrega sin cambiar el estado del ticket.\n\n{body.strip()}\n")


def process(defect_id: str, origin: str, body: str, dry_run: bool, link_in_sheet: bool, level1: str = None) -> dict:
    title = f"{defect_id}_ampliacion_{safe_origin(origin)}"
    rec = {"id": defect_id, "subpage_title": title}

    row_idx = utils.find_sheet_row_for_defect(defect_id)
    rec["sheet_row"] = row_idx
    if not row_idx:
        rec["error"] = "no está en el Sheet"
        return rec
    rec["estado_actual"] = utils.get_sheet_cell(row_idx, "estado")

    l1_id, l1_url = (level1, None) if level1 else utils.resolve_level1_from_sheet(defect_id)
    if not l1_id:
        l1_id, l1_url = utils.find_notion_level1_page_id(defect_id)
    rec["level1_page_id"] = l1_id
    if not l1_id:
        rec["error"] = "sin página Level-1 (revisa la URL de Notion en COMENTARIO QA o pasa --level1)"
        return rec

    children = list_child_titles(l1_id)
    if children is not None and title in children:
        rec["error"] = "ya existe una subpágina con ese título; no se duplica (usa otro origen si es evidencia distinta)"
        rec["already_exists"] = True
        return rec
    if children is None:
        rec["warning"] = "no se pudo comprobar si la subpágina ya existe"

    md = build_markdown(defect_id, origin, body)
    rec["chars"] = len(md)
    rec["link_in_sheet"] = link_in_sheet
    if dry_run:
        rec["preview"] = md[:600] + ("…" if len(md) > 600 else "")
        return rec

    page = utils.call_notion_mcp("create_page", {"parent": {"page_id": l1_id}, "title": title, "markdown": md})
    if not page:
        rec["error"] = "falló la creación en Notion"
        return rec
    rec["url"] = utils.notion_public_url(page.get("url", ""))

    target_dir = os.path.join(utils.REPORTS_DIR, "ampliaciones")
    os.makedirs(target_dir, exist_ok=True)
    local = os.path.join(target_dir, f"{title}.md")
    with open(local, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n{md}\n\nNotion: {rec['url']}\n")
    rec["local_file"] = local

    if link_in_sheet:
        try:
            current = utils.get_sheet_cell(row_idx, "comentario_qa")
            utils.batch_update_sheet_row(row_idx, {
                "comentario_qa": (current + "\n" if current else "") + f"Ampliación ({origin}): {rec['url']}"})
            rec["sheet_linked"] = True
        except Exception as e:
            rec["sheet_linked"] = False
            rec["error"] = f"Notion publicado, pero no se pudo agregar el enlace al Sheet ({e})"
    return rec


def main():
    parser = argparse.ArgumentParser(description="Agrega evidencia a un AF-XXX existente sin cambiar su estado.")
    parser.add_argument("defect_id", nargs="?")
    parser.add_argument("origin_pos", nargs="?", metavar="origen")
    parser.add_argument("body", nargs="?", metavar="evidencia")
    parser.add_argument("--body-file")
    parser.add_argument("--file", help="Archivo con secciones '## AF-XXX — título'")
    parser.add_argument("--origin", help="Origen (con --file), p. ej. E2E_Apiux_2026-09-25")
    parser.add_argument("--only", help="Solo estos IDs, separados por coma")
    parser.add_argument("--level1", help="ID de la página Level-1 (solo modo un ticket)")
    parser.add_argument("--link-in-sheet", action="store_true", help="Agrega la URL al final de COMENTARIO QA")
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

    gate_parts = [bool(args.link_in_sheet), args.level1 or ""]
    for i, o, b in jobs:
        gate_parts += [i, o, b]
    if not args.dry_run:
        utils.require_confirm("qa-amplify", gate_parts, args.confirm)

    results = [process(i, o, b, args.dry_run, args.link_in_sheet, args.level1 if not args.file else None)
               for i, o, b in jobs]
    out = {"dry_run": args.dry_run, "pages": results}
    if args.dry_run:
        out["confirm_code"] = utils.confirm_code("qa-amplify", gate_parts)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    failed = [r for r in results if "error" in r]
    if failed:
        print(f"{len(failed)} de {len(results)} tickets con error: {', '.join(r['id'] for r in failed)}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
