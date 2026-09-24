"""
Google Sheets Defect Matrix Updater
-----------------------------------
Queries Google Sheets API v4 using gcloud print-access-token:
1. Audits all current AF-XXX IDs in sheet 'Ai-Factory'.
2. Calculates the next correlative ID (e.g., AF-196).
3. Locates the exact first contiguous empty row immediately below the active table.
4. Writes the 14 columns dynamically based on sheet headers.
5. Syncs the Obsidian vault note at 'docs/vault/defectos/AF-XXX.md'.
"""
import json
import urllib.request
import re
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

def audit_and_get_next_id_and_target_row() -> tuple:
    token = utils.get_gcloud_token()
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{utils.SPREADSHEET_ID}/values/{utils.SHEET_NAME}!A:A"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    
    af_ids = []
    last_occupied_row_idx = 1
    
    try:
        with utils.google_urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            values = data.get("values", [])
            for r_idx, row in enumerate(values):
                if row and row[0].strip():
                    last_occupied_row_idx = max(last_occupied_row_idx, r_idx + 1)
                    match = re.search(r"AF-(\d+)", row[0].strip())
                    if match:
                        af_ids.append(int(match.group(1)))
    except Exception as e:
        print(f"Error fetching sheets: {e}", file=sys.stderr)
        sys.exit(1)
        
    next_num = (max(af_ids) + 1) if af_ids else 1
    next_id = f"AF-{next_num:03d}"
    target_row = last_occupied_row_idx + 1
    return next_id, target_row

def insert_defect_row(defect_id: str, target_row: int, name: str, description: str, severity: str, notion_url: str) -> bool:
    token = utils.get_gcloud_token()
    user_name = utils.get_user_name()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    mapping = utils.get_column_mapping()
    
    qa_comment = f"\n{notion_url}" if notion_url else ""
    
    row_values = [""] * 15
    def set_col(key: str, val: str):
        letter = mapping.get(key, "")
        if letter and len(letter) == 1 and "A" <= letter <= "O":
            idx = ord(letter) - ord("A")
            if idx < len(row_values):
                row_values[idx] = val

    set_col("id", defect_id)
    set_col("nombre", name)
    set_col("gravedad", severity)
    set_col("descripcion", description)
    set_col("reportada_por", user_name)
    set_col("fecha_inicio", today_str)
    set_col("estado", "Reportada")
    set_col("comentario_qa", qa_comment)
    
    range_target = f"{utils.SHEET_NAME}!A{target_row}:O{target_row}"
    url_put = f"https://sheets.googleapis.com/v4/spreadsheets/{utils.SPREADSHEET_ID}/values/{range_target}?valueInputOption=USER_ENTERED"
    
    payload = {
        "range": range_target,
        "majorDimension": "ROWS",
        "values": [row_values]
    }
    
    req = urllib.request.Request(
        url_put,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    
    with utils.google_urlopen(req, timeout=20) as resp:
        json.loads(resp.read().decode("utf-8"))
        print(f"Successfully inserted {defect_id} at row {target_row} in Google Sheets!")
        
    utils.sync_obsidian_note(
        defect_id=defect_id,
        title=name,
        status="Reportada",
        severity=severity,
        level1_url=notion_url,
        subpage_url=notion_url,
        evidence="Defecto reportado y registrado en Google Sheets.",
        tech_details=description
    )

    return True

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]

    if args == ["--audit"]:
        nid, trow = audit_and_get_next_id_and_target_row()
        print(f"Next ID: {nid}\nTarget Row: {trow}")
        sys.exit(0)

    if len(args) < 3:
        print("Usage: python gsheets_updater.py [--dry-run] <defect_name> <description> <severity> [notion_url]")
        print("Or run --audit to print next ID and target row.")
        sys.exit(2)

    d_name, d_desc, d_severity = args[0], args[1], args[2]
    n_url = args[3] if len(args) > 3 else ""

    nid, trow = audit_and_get_next_id_and_target_row()
    if dry_run:
        print(json.dumps({
            "dry_run": True, "defect_id": nid, "target_row": trow, "nombre": d_name,
            "gravedad": d_severity, "descripcion": d_desc, "estado": "Reportada",
            "reportada_por": utils.get_user_name(), "comentario_qa": n_url,
        }, indent=2, ensure_ascii=False))
        sys.exit(0)
    insert_defect_row(nid, trow, d_name, d_desc, d_severity, n_url)
