---
name: qa-rejection
description: Rechaza formalmente un defecto AF-XXX cuyo fix no pasó la verificación. Genera el reporte de rechazo local, lo publica como subpágina en Notion y marca la fila de Google Sheets como 'Rechazada por QA'. Úsala cuando el usuario diga que un AF-XXX sigue fallando, que el fix no corrige la causa raíz o que introdujo una regresión, y quiera rechazarlo. ESCRIBE en sistemas compartidos; requiere dry-run y confirmación. / Reject a defect whose fix failed verification.
---

# QA Rejection (`qa-rejection`)

Rechaza un defecto cuyo fix no funcionó. Escribe en Notion y Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

> Si el ticket no se está re-verificando y solo quieres sumarle evidencia sin cambiar su estado, usa `qa-amplify`.

## Protocolo obligatorio

1. **Reúne la evidencia del fallo:** pasos para reproducirlo, entorno y resultado observado frente al esperado. Revisa también qué cambió en el código (`qa-code-audit --issue AF-XXX`).
2. **Dry-run:** ejecuta con `--dry-run` y `--build` (commit o imagen probada). No escribe nada; muestra la página Nivel 1, la fila, los valores a escribir y un `confirm_code`.
3. **Muestra el dry-run al usuario y pide confirmación explícita** para este defecto, en este turno.
4. Solo con un "sí" claro, repite el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`.

```bash
python <KIT>/skills/qa-rejection/scripts/qa_rejection_publisher.py --dry-run \
  --build "<commit o imagen probada, y dónde>" \
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
| — | `--build` | **Obligatorio.** Commit o imagen que se probó, y dónde. Queda escrito en el reporte de rechazo. |
| — | `--confirm` | Código del dry-run. Obligatorio para publicar. |

## Resultado y códigos de salida

- `0`: publicado en Notion y hoja actualizada.
- `1`: no se publicó. Si no se encontró la página Nivel 1, el script **no crea una nueva**: pide su ID al usuario y pásalo como argumento 5.
- `2`: faltan argumentos (incluye `--build`).
- `3`: **éxito parcial**. Notion se publicó, pero la hoja NO se actualizó. Avísale al usuario.
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
