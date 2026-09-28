"""
QA Backlog Fetcher & Triage CLI
-------------------------------
Queries Google Sheets API v4 using gcloud access token and outputs structured
backlog issues filtered by status, defect ID, or severity.
Supports both Markdown and JSON output.
"""
import sys
import os
import argparse
import json

# Add shared utils
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils
import unicodedata


def normalize(text: str) -> str:
    """Lowercase and strip accents so 'José' matches 'jose'."""
    return "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")


def main():
    parser = argparse.ArgumentParser(description="Fetch and triage IAFactory QA backlog from Google Sheets.")
    parser.add_argument("--status", type=str, default="Pendiente,En Revisión,Reportada",
                        help="Comma-separated status filter (e.g., 'Pendiente,En Revisión')")
    parser.add_argument("--id", type=str, default="", help="Filter by specific defect ID (e.g. AF-185)")
    parser.add_argument("--responsable", type=str, default="",
                        help="Filter by assignee; case- and accent-insensitive partial match, comma-separated for several people")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of issues to return")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of Markdown")

    args = parser.parse_args()

    status_filters = [s.strip() for s in args.status.split(",") if s.strip()] if args.status != "all" else []
    people = [normalize(p) for p in args.responsable.split(",") if p.strip()]

    if args.id:
        # A specific ID must be found whatever its status and row position
        defects = utils.list_defects_from_sheets(status_filter=None, limit=None)
        defects = [d for d in defects if d["id"].upper() == args.id.upper()]
    elif people:
        # Filter before applying the limit, otherwise the limit would cut rows of the requested people
        defects = utils.list_defects_from_sheets(status_filter=status_filters, limit=None)
        defects = [d for d in defects if any(p in normalize(d["responsable"] or "") for p in people)]
        if not defects:
            known = sorted({d["responsable"] for d in utils.list_defects_from_sheets(status_filter=status_filters, limit=None)
                            if d["responsable"]})
            print(f"AVISO: ningún responsable coincide con '{args.responsable}'. "
                  f"Responsables en estos estados: {', '.join(known) or '(ninguno)'}", file=sys.stderr)
        if len(defects) > args.limit:
            print(f"AVISO: {len(defects)} coincidencias; se muestran {args.limit}. Usa --limit más alto para verlas todas.",
                  file=sys.stderr)
            defects = defects[:args.limit]
    else:
        defects = utils.list_defects_from_sheets(status_filter=status_filters, limit=args.limit)
        if len(defects) >= args.limit:
            print(f"AVISO: se alcanzó el límite de {args.limit} resultados; pueden faltar defectos. "
                  f"Repite con --limit más alto (por ejemplo --limit 500) antes de contar o concluir.",
                  file=sys.stderr)

    if args.json:
        print(json.dumps(defects, indent=2, ensure_ascii=False))
        return

    if not defects:
        print(f"No se encontraron incidencias con el filtro de estado: '{args.status}'")
        return

    print(f"\n### 📋 Backlog de Incidencias QA ({len(defects)} encontradas)")
    print(f"**Filtro:** `{args.status}` | **Límite:** `{args.limit}`\n")
    print("| ID | Estado | Gravedad | Título / Nombre | Responsable | Commits | Notion / Comentarios |")
    print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for d in defects:
        n_url = d["comentario_qa"].replace("\n", " ").strip()
        link_str = f"[Notion]({n_url})" if "http" in n_url else n_url[:30]
        commits_str = d["id_commits"] or d["commits"] or "-"
        print(f"| **{d['id']}** | `{d['estado']}` | {d['gravedad'] or 'N/A'} | {d['nombre'][:40]} | {d['responsable'] or 'Sin asignar'} | `{commits_str[:15]}` | {link_str} |")

if __name__ == "__main__":
    main()
