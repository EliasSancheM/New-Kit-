"""
QA Rejection Publisher & Synchronization Script
------------------------------------------------
Automates the QA rejection workflow for any defect (AF-XXX):
1. Generates local report 'Reportes/AF-XXX_reporte_rechazo_qa.md' with AI Warning Banner.
2. Uploads the rejection report to Notion MCP as a nested subpage inside the Level 1 defect page.
3. Updates Google Sheets (dynamic mapping):
   - Sets Column I (ESTADO) to 'Rechazada por QA'
   - Sets Column K (Cerrada / Rechazada Por) to the executing user's name.
   - Sets Column O (Comentario QA) to include failure details + public Notion URL.
4. Syncs the Obsidian vault note at 'docs/vault/defectos/AF-XXX.md' setting status to 'Rechazada por QA'.
"""
import os
import sys
import json
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

def generate_local_rejection_report(defect_id: str, reason: str, test_details: str, code_changes_found: str, user_name: str) -> tuple:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_dir = os.path.join(utils.REPORTS_DIR, "rechazo")
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, f"{defect_id}_reporte_rechazo_qa.md")
    
    content = f"""> ⚠️ **ADVERTENCIA DE SEGURIDAD E INGENIERÍA**
> *Esta solución técnica y sus fragmentos de código fueron generados mediante Inteligencia Artificial. Los cambios sugeridos pueden tener implicaciones o consecuencias imprevistas en el entorno. Es imperativo que el equipo de desarrollo revise minuciosamente el código y se aplique con extrema precaución.*

# ❌ Reporte de Rechazo de QA: {defect_id}

**Estado:** ❌ **RECHAZADO POR QA**  
**Fecha de Validación:** {today_str} (-04:00)  
**Validado por:** {user_name} / QA Team  

---

## 📌 Resumen del Rechazo
La revisión y prueba de replicación en vivo para el issue **{defect_id}** ha sido **RECHAZADA POR QA**.

**Motivo Principal:** {reason}

---

## 🔍 Cambios Encontrados en Código Fuente
{code_changes_found}

---

## 🧪 Resultado Empírico de la Replicación en Vivo
{test_details}

---

## 🛠️ Acciones Requeridas para Re-Apertura
1. Corregir la causa raíz identificada en el código fuente.
2. Realizar pruebas de verificación antes de solicitar nueva revisión a QA.
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath, content

def process_qa_rejection(defect_id: str, reason: str, test_details: str, code_changes_found: str, level1_page_id: str = None, dry_run: bool = False):
    user_name = utils.get_user_name()
    if dry_run:
        return utils.publish_qa_outcome(
            defect_id=defect_id, page_suffix="reporte_rechazo_qa", content="", status="Rechazada por QA",
            severity=None, summary_or_reason=reason, comment_label="Reporte de rechazo",
            evidence=test_details, tech_details=code_changes_found,
            level1_page_id=level1_page_id, dry_run=True,
        )
    filepath, content = generate_local_rejection_report(defect_id, reason, test_details, code_changes_found, user_name)
    print(f"Reporte de rechazo local generado: {filepath}")

    result = utils.publish_qa_outcome(
        defect_id=defect_id,
        page_suffix="reporte_rechazo_qa",
        content=content,
        status="Rechazada por QA",
        severity=None,  # read from the sheet's GRAVEDAD column
        summary_or_reason=reason,
        comment_label="Reporte de rechazo",
        evidence=test_details,
        tech_details=code_changes_found,
        level1_page_id=level1_page_id
    )
    if not result:
        return False

    return {
        "defect_id": defect_id,
        "local_file": filepath,
        "notion_url": result["notion_url"],
        "status": result["status"],
        "rechazada_por": result["user_name"],
        "sheet_updated": result["sheet_updated"]
    }

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    if len(args) < 4:
        print("Usage: python qa_rejection_publisher.py [--dry-run] <defect_id> <reason> <test_details> <code_changes_found> [level1_page_id]")
        sys.exit(2)

    res = process_qa_rejection(
        defect_id=args[0],
        reason=args[1],
        test_details=args[2],
        code_changes_found=args[3],
        level1_page_id=args[4] if len(args) > 4 else None,
        dry_run=dry_run
    )
    if not res:
        sys.exit(1)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    # Exit 3 = Notion published but Sheets not updated (partial success)
    sys.exit(0 if dry_run or res.get("sheet_updated") else 3)
