"""
QA Finish & Resolution Publisher Script
---------------------------------------
Automates the QA resolution & acceptance workflow for any defect (AF-XXX):
1. Generates local report 'Reportes/AF-XXX_reporte_exito_qa.md'.
2. Uploads the success report to Notion MCP as a nested subpage inside the Level 1 defect page.
3. Updates Google Sheets (dynamic mapping):
   - Sets Column I (ESTADO) to 'Finalizada'
   - Sets Column K (Cerrada Por) to the executing user's name.
   - Sets Column O (Comentario QA) to include test resolution details + public Notion URL.
4. Syncs the Obsidian vault note at 'docs/vault/defectos/AF-XXX.md' setting status to 'Finalizada'.
"""
import os
import sys
import json
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils

def generate_local_success_report(defect_id: str, summary: str, test_details: str, verification_result: str, user_name: str, build: str = "") -> tuple:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_dir = os.path.join(utils.REPORTS_DIR, "exito")
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, f"{defect_id}_reporte_exito_qa.md")
    
    content = f"""# ✅ Reporte de Verificación de QA — Prueba Exitosa: {defect_id}

**ID:** `{defect_id}`  
**Fecha de Verificación:** {today_str} (-04:00)  
**Validado por:** {user_name} / QA Team  
**Resultado:** **PRUEBA EXITOSA / ISSUE FINALIZADA**
**Build / commit probado:** `{build}`

---

## 🎯 Objetivo de la Prueba
{summary}

---

## 🧪 Resumen de la Ejecución y Evidencia

1. **Escenario Probado y Resultado:**
   {test_details}

2. **Verificación y Conclusión de QA:**
   {verification_result}
   - La prueba se considera **Completada con Éxito** y la issue **Finalizada**.
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath, content

def process_qa_finish(defect_id: str, summary: str, test_details: str, verification_result: str, level1_page_id: str = None, dry_run: bool = False, build: str = ""):
    user_name = utils.get_user_name()
    if dry_run:
        return utils.publish_qa_outcome(
            defect_id=defect_id, page_suffix="reporte_exito_qa", content="", status="Finalizada",
            severity=None, summary_or_reason=summary, comment_label="Reporte de éxito",
            evidence=test_details, tech_details=verification_result,
            level1_page_id=level1_page_id, dry_run=True,
        )
    filepath, content = generate_local_success_report(defect_id, summary, test_details, verification_result, user_name, build)
    print(f"Reporte de éxito local generado: {filepath}")

    result = utils.publish_qa_outcome(
        defect_id=defect_id,
        page_suffix="reporte_exito_qa",
        content=content,
        status="Finalizada",
        severity=None,  # read from the sheet's GRAVEDAD column
        summary_or_reason=summary,
        comment_label="Reporte de éxito",
        evidence=test_details,
        tech_details=verification_result,
        level1_page_id=level1_page_id
    )
    if not result:
        return False

    return {
        "defect_id": defect_id,
        "local_file": filepath,
        "notion_url": result["notion_url"],
        "status": result["status"],
        "cerrada_por": result["user_name"],
        "sheet_updated": result["sheet_updated"]
    }

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--dry-run"]
    confirm, argv = utils.pop_option(argv, "--confirm")
    build, args = utils.pop_option(argv, "--build")
    if len(args) < 4 or not (build or "").strip():
        print("Usage: python qa_finish_publisher.py [--dry-run | --confirm <código>] --build <commit|imagen probada> "
              "<defect_id> <summary> <test_details> <verification_result> [level1_page_id]")
        print("--build y verification_result son obligatorios: un cierre sin la versión probada ni la evidencia "
              "observada no se publica.")
        sys.exit(2)

    gate = ["qa-finish", [args[0], args[1], args[2], args[3], build, args[4] if len(args) > 4 else ""]]
    if not dry_run:
        utils.require_confirm(gate[0], gate[1], confirm)

    res = process_qa_finish(
        defect_id=args[0],
        summary=args[1],
        test_details=args[2],
        verification_result=args[3],
        level1_page_id=args[4] if len(args) > 4 else None,
        dry_run=dry_run,
        build=build,
    )
    if not res:
        sys.exit(1)
    if dry_run and isinstance(res, dict):
        res["build"] = build
        res["confirm_code"] = utils.confirm_code(*gate)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    # Exit 3 = Notion published but Sheets not updated (partial success)
    sys.exit(0 if dry_run or res.get("sheet_updated") else 3)
