---
name: qa-finish
description: Cierra formalmente un defecto AF-XXX verificado. Genera el reporte de éxito local y marca la fila de Google Sheets como 'Finalizada' con el reporte completo en Comentario QA. Úsala cuando el usuario diga que un AF-XXX pasó la prueba y quiera cerrarlo o finalizarlo. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y confirmación de una persona. / Close a verified defect in Google Sheets.
---

# QA Finish (`qa-finish`)

Cierra un defecto que **ya se verificó empíricamente**. Escribe en Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Protocolo obligatorio

1. **Confirma que hay evidencia real** de la prueba (qué se ejecutó, en qué entorno, qué salió) y **qué versión se probó** (commit o imagen desplegada). Si falta cualquiera de las dos, no cierres: pídela. "Alta confianza" sin prueba ejecutada no alcanza; el script exige `--build`.
2. **Dry-run:** ejecuta el comando con `--dry-run`. No escribe nada; muestra la fila de la hoja, su estado actual, los valores que se escribirán y un `confirm_code`.
3. **Muestra el dry-run al usuario y pide confirmación explícita.** La confirmación vale para este defecto y este turno, no para los siguientes.
4. **Pide el token de Sheets:** "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`.
5. Con un "sí" claro, entrégale a la persona el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. **La persona lo ejecuta en su propia terminal** y escribe el AF-XXX para confirmar; desde el asistente el script sale con código `5`. Si cambias cualquier argumento, el código deja de valer y hay que repetir el dry-run.

```bash
python <KIT>/skills/qa-finish/scripts/qa_finish_publisher.py --dry-run \
  --build "<commit o imagen probada, p. ej. ai-factory-agents@3f2a1c9 en iafactory-qa>" \
  "AF-XXX" \
  "<resumen: qué se verificó>" \
  "<detalle de la prueba: pasos, entorno, evidencia>" \
  "<conclusión de la verificación>"
```

## Argumentos

| # | Argumento | Contenido |
|---|---|---|
| 1 | `AF-XXX` | ID del defecto |
| 2 | resumen | Una frase: qué se probó y que pasó. |
| 3 | detalle | Pasos, entorno (local/dev), datos usados y evidencia observada |
| 4 | conclusión | **Obligatoria.** Por qué se considera resuelto, con el resultado observado. |
| — | `--build` | **Obligatorio.** Commit o imagen que se probó, y dónde. Queda escrito en el reporte de éxito. |
| — | `--confirm` | Código del dry-run. Obligatorio para publicar. |

## Qué escribe en la fila

ESTADO = `Finalizada`, FECHA TERMINO = hoy, CERRADA POR = quien confirma, COMENTARIO QA = el reporte de éxito completo (el mismo que queda en `Reportes/exito/AF-XXX_reporte_exito_qa.md`).

## Resultado y códigos de salida

- `0`: hoja actualizada. El JSON trae `sheet_row` y `local_file`.
- `1`: el defecto no está en la hoja o falló la escritura. No se publicó.
- `2`: faltan argumentos (incluye `--build` o la conclusión).
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.
