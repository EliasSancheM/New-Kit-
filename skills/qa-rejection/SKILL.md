---
name: qa-rejection
description: Rechaza formalmente un defecto AF-XXX cuyo fix no pasó la verificación. Genera el reporte de rechazo local, lo publica como subpágina en Notion y marca la fila de Google Sheets como 'Rechazada por QA'. Úsala cuando el usuario diga que un AF-XXX sigue fallando, que el fix no corrige la causa raíz o que introdujo una regresión, y quiera rechazarlo. ESCRIBE en sistemas compartidos; requiere dry-run y confirmación. / Reject a defect whose fix failed verification.
---

# QA Rejection (`qa-rejection`)

Rechaza un defecto cuyo fix no funcionó. Escribe en Notion y Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

> Si tu equipo documenta las re-verificaciones fallidas ampliando el reporte existente en vez de rechazar el ticket, no uses esta skill: sigue el proceso de tu equipo.

## Protocolo obligatorio

1. **Reúne la evidencia del fallo:** pasos para reproducirlo, entorno y resultado observado frente al esperado. Revisa también qué cambió en el código (`qa-code-audit --issue AF-XXX`).
2. **Dry-run:** ejecuta con `--dry-run`. No escribe nada; muestra la página Nivel 1, la fila y los valores a escribir.
3. **Muestra el dry-run al usuario y pide confirmación explícita** para este defecto, en este turno.
4. Solo con un "sí" claro, ejecuta sin `--dry-run`.

```bash
python <KIT>/skills/qa-rejection/scripts/qa_rejection_publisher.py --dry-run \
  "AF-XXX" \
  "<motivo del rechazo, en una frase>" \
  "<detalle de la prueba que falló: pasos, entorno, resultado vs esperado>" \
  "<cambios de código encontrados y por qué no resuelven el problema>" \
  "[level1_page_id opcional]"
```

## Argumentos

| # | Argumento | Contenido |
|---|---|---|
| 1 | `AF-XXX` | ID del defecto |
| 2 | motivo | Una frase. Va también al Comentario QA de la hoja. |
| 3 | detalle de la falla | Reproducción concreta y evidencia |
| 4 | cambios encontrados | Qué commits/archivos cambió el dev y qué les falta |
| 5 | level1_page_id | Opcional. ID de la página Nivel 1 en Notion |

## Resultado y códigos de salida

- `0`: publicado en Notion y hoja actualizada.
- `1`: no se publicó. Si no se encontró la página Nivel 1, el script **no crea una nueva**: pide su ID al usuario y pásalo como argumento 5.
- `2`: faltan argumentos.
- `3`: **éxito parcial**. Notion se publicó, pero la hoja NO se actualizó. Avísale al usuario.
