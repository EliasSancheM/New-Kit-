---
name: qa-rejection
description: Rechaza formalmente un defecto AF-XXX cuyo fix no pasó la verificación. Genera el reporte de rechazo local y marca la fila de Google Sheets como 'Rechazada por QA' con el reporte completo en Comentario QA. Úsala cuando el usuario diga que un AF-XXX sigue fallando, que el fix no corrige la causa raíz o que introdujo una regresión, y quiera rechazarlo. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y confirmación de una persona. / Reject a defect whose fix failed verification.
---

# QA Rejection (`qa-rejection`)

Rechaza un defecto cuyo fix no funcionó. Escribe en Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

> Si el ticket no se está re-verificando y solo quieres sumarle evidencia sin cambiar su estado, usa `qa-amplify`.

## Protocolo obligatorio

1. **Reúne la evidencia del fallo:** pasos para reproducirlo, entorno y resultado observado frente al esperado. Revisa también qué cambió en el código (`qa-code-audit --issue AF-XXX`).
2. **Dry-run:** ejecuta con `--dry-run` y `--build` (commit o imagen probada). No escribe nada; muestra la fila, su estado actual, los valores a escribir y un `confirm_code`.
3. **Muestra el dry-run al usuario y pide confirmación explícita** para este defecto, en este turno.
4. **Pide el token de Sheets:** "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`.
5. Con un "sí" claro, entrégale a la persona el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. **La persona lo ejecuta en su propia terminal** y escribe el AF-XXX para confirmar; desde el asistente el script sale con código `5`.

```bash
python <KIT>/skills/qa-rejection/scripts/qa_rejection_publisher.py --dry-run \
  --build "<commit o imagen probada, y dónde>" \
  "AF-XXX" \
  "<motivo del rechazo, en una frase>" \
  "<detalle de la prueba que falló: pasos, entorno, resultado vs esperado>" \
  "<cambios de código encontrados y por qué no resuelven el problema>"
```

## Argumentos

| # | Argumento | Contenido |
|---|---|---|
| 1 | `AF-XXX` | ID del defecto |
| 2 | motivo | Una frase. |
| 3 | detalle de la falla | Reproducción concreta y evidencia |
| 4 | cambios encontrados | Qué commits/archivos cambió el dev y qué les falta |
| — | `--build` | **Obligatorio.** Commit o imagen que se probó, y dónde. Queda escrito en el reporte de rechazo. |
| — | `--confirm` | Código del dry-run. Obligatorio para publicar. |

## Qué escribe en la fila

ESTADO = `Rechazada por QA`, FECHA TERMINO = hoy, CERRADA POR = quien confirma, COMENTARIO QA = el reporte de rechazo completo (el mismo que queda en `Reportes/rechazo/AF-XXX_reporte_rechazo_qa.md`).

## Resultado y códigos de salida

- `0`: hoja actualizada.
- `1`: el defecto no está en la hoja o falló la escritura. No se publicó.
- `2`: faltan argumentos (incluye `--build`).
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.
