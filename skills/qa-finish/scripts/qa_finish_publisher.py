"""
QA Finish & Resolution Publisher Script
---------------------------------------
Closes a verified defect (AF-XXX):
1. Generates the local report 'Reportes/exito/AF-XXX_reporte_exito_qa.md'.
2. Updates Google Sheets: ESTADO = 'Finalizada', FECHA TERMINO = today,
   CERRADA POR = the executing user, COMENTARIO QA = the full report.
3. Optional Obsidian mirror (QA_KIT_OBSIDIAN=1).

Exit codes: 0 ok / 1 defect not in the sheet or write failure / 2 bad arguments /
4 missing or stale --confirm / 5 no human confirmation / 6 no Sheets token.
"""
import os
import sys
import json
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils


def render_success_report(defect_id: str, summary: str, test_details: str, verification_result: str,
                          user_name: str, build: str) -> str:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# ✅ Reporte de Verificación de QA — Prueba Exitosa: {defect_id}

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


def generate_local_success_report(defect_id, summary, test_details, verification_result, user_name, build="") -> tuple:
    target_dir = os.path.join(utils.REPORTS_DIR, "exito")
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, f"{defect_id}_reporte_exito_qa.md")
    content = render_success_report(defect_id, summary, test_details, verification_result, user_name, build)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath, content


@utils.exit_on_auth_error
def main():
    dry_run = "--dry-run" in sys.argv
    argv = [a for a in sys.argv[1:] if a != "--dry-run"]
    confirm, argv = utils.pop_option(argv, "--confirm")
    build, args = utils.pop_option(argv, "--build")
    if len(args) != 4 or not (build or "").strip():
        print("Usage: python qa_finish_publisher.py [--dry-run | --confirm <código>] --build <commit|imagen probada> "
              "<defect_id> <summary> <test_details> <verification_result>")
        print("--build y verification_result son obligatorios: un cierre sin la versión probada ni la evidencia "
              "observada no se publica.")
        sys.exit(2)
    defect_id, summary, test_details, verification_result = args[0].upper(), args[1], args[2], args[3]

    gate = ["qa-finish", [defect_id, summary, test_details, verification_result, build]]
    if not dry_run:
        utils.require_confirm(gate[0], gate[1], confirm)

    user_name = utils.get_user_name()
    content = render_success_report(defect_id, summary, test_details, verification_result, user_name, build)
    pre = utils.publish_qa_outcome(defect_id, "Finalizada", summary, report_text=content, dry_run=True)
    if not pre:
        sys.exit(1)
    if dry_run:
        pre["build"] = build
        pre["sheet_updates"]["comentario_qa"] = f"<reporte de éxito completo, {len(pre['sheet_updates']['comentario_qa'])} caracteres>"
        pre["confirm_code"] = utils.confirm_code(*gate)
        print(json.dumps(pre, indent=2, ensure_ascii=False))
        return

    utils.require_human_confirmation("Cerrar como Finalizada", defect_id, [
        f"Fila: {pre['sheet_row']} (estado actual: {pre['estado_actual'] or 'vacío'})",
        f"Resumen: {summary}", f"Versión probada: {build}", f"Conclusión: {verification_result[:200]}"])
    filepath, content = generate_local_success_report(defect_id, summary, test_details, verification_result, user_name, build)
    print(f"Reporte de éxito local generado: {filepath}")
    res = utils.publish_qa_outcome(defect_id, "Finalizada", summary, report_text=content,
                                   evidence=test_details, tech_details=verification_result)
    if not res:
        sys.exit(1)
    res["local_file"] = filepath
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
