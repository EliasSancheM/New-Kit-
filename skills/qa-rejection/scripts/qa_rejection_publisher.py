"""
QA Rejection Publisher Script
-----------------------------
Rejects a defect whose fix failed verification (AF-XXX):
1. Generates the local report 'Reportes/rechazo/AF-XXX_reporte_rechazo_qa.md' with the AI warning banner.
2. Updates Google Sheets: ESTADO = 'Rechazada por QA', FECHA TERMINO = today,
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


def render_rejection_report(defect_id: str, reason: str, test_details: str, code_changes_found: str,
                            user_name: str, build: str) -> str:
    today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""> ⚠️ **ADVERTENCIA DE SEGURIDAD E INGENIERÍA**
> *Esta solución técnica y sus fragmentos de código fueron generados mediante Inteligencia Artificial. Los cambios sugeridos pueden tener implicaciones o consecuencias imprevistas en el entorno. Es imperativo que el equipo de desarrollo revise minuciosamente el código y se aplique con extrema precaución.*

# ❌ Reporte de Rechazo de QA: {defect_id}

**Estado:** ❌ **RECHAZADO POR QA**
**Fecha de Validación:** {today_str} (-04:00)
**Validado por:** {user_name} / QA Team
**Build / commit probado:** `{build}`

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


def generate_local_rejection_report(defect_id, reason, test_details, code_changes_found, user_name, build="") -> tuple:
    target_dir = os.path.join(utils.REPORTS_DIR, "rechazo")
    os.makedirs(target_dir, exist_ok=True)
    filepath = os.path.join(target_dir, f"{defect_id}_reporte_rechazo_qa.md")
    content = render_rejection_report(defect_id, reason, test_details, code_changes_found, user_name, build)
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
        print("Usage: python qa_rejection_publisher.py [--dry-run | --confirm <código>] --build <commit|imagen probada> "
              "<defect_id> <reason> <test_details> <code_changes_found>")
        print("--build es obligatorio: un rechazo sin la versión probada no se publica.")
        sys.exit(2)
    defect_id, reason, test_details, code_changes_found = args[0].upper(), args[1], args[2], args[3]

    gate = ["qa-rejection", [defect_id, reason, test_details, code_changes_found, build]]
    if not dry_run:
        utils.require_confirm(gate[0], gate[1], confirm)

    user_name = utils.get_user_name()
    content = render_rejection_report(defect_id, reason, test_details, code_changes_found, user_name, build)
    pre = utils.publish_qa_outcome(defect_id, "Rechazada por QA", reason, report_text=content, dry_run=True)
    if not pre:
        sys.exit(1)
    if dry_run:
        pre["build"] = build
        pre["sheet_updates"]["comentario_qa"] = f"<reporte de rechazo completo, {len(pre['sheet_updates']['comentario_qa'])} caracteres>"
        pre["confirm_code"] = utils.confirm_code(*gate)
        print(json.dumps(pre, indent=2, ensure_ascii=False))
        return

    utils.require_human_confirmation("Rechazar por QA", defect_id, [
        f"Fila: {pre['sheet_row']} (estado actual: {pre['estado_actual'] or 'vacío'})",
        f"Motivo: {reason}", f"Versión probada: {build}"])
    filepath, content = generate_local_rejection_report(defect_id, reason, test_details, code_changes_found, user_name, build)
    print(f"Reporte de rechazo local generado: {filepath}")
    res = utils.publish_qa_outcome(defect_id, "Rechazada por QA", reason, report_text=content,
                                   evidence=test_details, tech_details=code_changes_found)
    if not res:
        sys.exit(1)
    res["local_file"] = filepath
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
