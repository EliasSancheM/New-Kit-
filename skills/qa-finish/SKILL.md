---
name: qa-finish
description: Cierra formalmente un defecto AF-XXX verificado en vivo. Publica el veredicto (plantilla veredicto.md, validado por verdict.py lint) en Google Sheets: ESTADO 'Finalizada', fecha de término, quién cerró y el veredicto completo en Comentario QA. Úsala cuando el asistente ya ejecutó los casos del ticket en la instancia abierta por la persona y todos pasaron. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y confirmación de una persona. / Close a verified defect in Google Sheets.
---

# QA Finish (`qa-finish`)

Cierra un defecto cuyo fix **el asistente verificó en vivo**: la persona abre la instancia y el asistente ejecuta los casos, observa y escribe. Escribe en Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Regla de veredicto

**Finalizada** solo si se cumplen las tres: la versión probada está identificada y desplegada en la VM; el caso del ticket y cada síntoma listado pasan en vivo con evidencia `[R]` o `[DB]`; el caso de control no regresó. Si falta cualquiera, no es un cierre: es `qa-rejection` (si algo falló) o queda `En Revisión` con la razón anotada vía `qa-amplify` (si no se pudo probar). "Alta confianza", "debería funcionar" o un test verde sin el caso del ticket no cierran nada.

## Protocolo obligatorio

1. **Revisión previa con las Fases 0 a 4** de `rules/AGENTS.md`: criterio del ticket, cambios del desarrollador con sus tres preguntas y los tres casos ejecutados en la instancia (ticket, control, límite).
2. **Escribe el veredicto** en `Reportes/exito/AF-XXX_veredicto.md` desde la plantilla `<KIT>/skills/shared/templates/veredicto.md`. Cada fila de "Casos probados" es un caso que ejecutaste, con pasos, resultado observado y evidencia.
3. **Valida el veredicto** (sin red):
   ```bash
   python <KIT>/skills/shared/verdict.py lint Reportes/exito/AF-XXX_veredicto.md
   ```
4. **Dry-run:** no escribe nada; muestra la fila, su estado actual, lo que se escribirá y un `confirm_code`. Con errores de lint no hay código.
   ```bash
   python <KIT>/skills/qa-finish/scripts/qa_finish_publisher.py --dry-run Reportes/exito/AF-XXX_veredicto.md
   ```
5. **Muestra el dry-run al usuario y pide confirmación explícita.** La confirmación vale para este defecto y este turno.
6. **Pide el token de Sheets:** "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`.
7. Con un "sí" claro, entrégale a la persona el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. **La persona lo ejecuta en su propia terminal** y escribe el AF-XXX para confirmar; desde el asistente el script sale con código `5`. Editar el veredicto después del dry-run invalida el código.

## Qué exige el lint

Encabezado `# AF-NNN — Veredicto QA: Finalizada`; Resumen, Versión probada (commit, imagen o fecha), Fecha y entorno y Criterio del ticket; las tres preguntas sobre el cambio; tabla de casos con al menos un `ticket` y un `control`, cada uno con pasos, resultado observado, evidencia `[R]`/`[DB]` y veredicto Pasa; sección de límites; sin marcadores `<...>` ni frases como "se asume" o "probablemente" fuera de los límites.

## Qué escribe en la fila

ESTADO = `Finalizada`, FECHA TERMINO = hoy, CERRADA POR = quien confirma, COMENTARIO QA = el veredicto completo.

## Códigos de salida

- `0`: hoja actualizada. El JSON trae `sheet_row` y `local_file`.
- `1`: errores de lint, el defecto no está en la hoja o falló la escritura. No se publicó.
- `2`: argumentos inválidos o el veredicto es de rechazo (usa `qa-rejection`).
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.
