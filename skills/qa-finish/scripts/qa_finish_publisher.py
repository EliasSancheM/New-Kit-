"""
QA Finish Publisher
-------------------
Closes a verified defect from its verdict file (skills/shared/templates/veredicto.md):
the verdict passes verdict lint (version tested, acceptance criterion, executed cases with
[R]/[DB] evidence, control case, limits), then the sheet row gets ESTADO = 'Finalizada',
FECHA TERMINO, CERRADA POR and the full verdict in COMENTARIO QA.

  qa_finish_publisher.py [--dry-run | --confirm <código>] Reportes/exito/AF-XXX_veredicto.md

Exit codes: 0 ok / 1 lint errors, defect not in sheet or write failure / 2 bad arguments or
verdict of another kind / 4 missing or stale --confirm / 5 no human confirmation / 6 no Sheets token.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import utils
import verdict


@utils.exit_on_auth_error
def main():
    verdict.publish_verdict("Finalizada", "Cerrar como Finalizada", sys.argv[1:])


if __name__ == "__main__":
    main()
