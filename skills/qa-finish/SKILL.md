---
name: qa-finish
description: Cierra formalmente un defecto AF-XXX verificado. Genera el reporte de éxito local, lo publica como subpágina en Notion y marca la fila de Google Sheets como 'Finalizada'. Úsala cuando el usuario diga que un AF-XXX pasó la prueba y quiera cerrarlo o finalizarlo. ESCRIBE en sistemas compartidos; requiere dry-run y confirmación. / Close a verified defect in Notion and Google Sheets.
---

# QA Finish (`qa-finish`)

Cierra un defecto que **ya se verificó empíricamente**. Escribe en Notion y Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Protocolo obligatorio

1. **Confirma que hay evidencia real** de la prueba (qué se ejecutó, en qué entorno, qué salió) y **qué versión se probó** (commit o imagen desplegada). Si falta cualquiera de las dos, no cierres: pídela. "Alta confianza" sin prueba ejecutada no alcanza; el script exige `--build`.
2. **Dry-run:** ejecuta el comando con `--dry-run`. No escribe nada; muestra la página Nivel 1 encontrada, la fila de la hoja, los valores que se escribirán y un `confirm_code`.
3. **Muestra el dry-run al usuario y pide confirmación explícita.** La confirmación vale para este defecto y este turno, no para los siguientes.
4. Solo con un "sí" claro, repite el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. Si cambias cualquier argumento, el código deja de valer y hay que repetir el dry-run.

```bash
python <KIT>/skills/qa-finish/scripts/qa_finish_publisher.py --dry-run \
  --build "<commit o imagen probada, p. ej. ai-factory-agents@3f2a1c9 en iafactory-qa>" \
  "AF-XXX" \
  "<resumen: qué se verificó>" \
  "<detalle de la prueba: pasos, entorno, evidencia>" \
  "<conclusión de la verificación>" \
  "[level1_page_id opcional]"
```

## Argumentos

| # | Argumento | Contenido |
|---|---|---|
| 1 | `AF-XXX` | ID del defecto |
| 2 | resumen | Una frase: qué se probó y que pasó. Va también al Comentario QA de la hoja. |
| 3 | detalle | Pasos, entorno (local/dev), datos usados y evidencia observada |
| 4 | conclusión | **Obligatoria.** Por qué se considera resuelto, con el resultado observado. |
| 5 | level1_page_id | Opcional. ID de la página Nivel 1 en Notion, si la búsqueda automática no la encuentra |
| — | `--build` | **Obligatorio.** Commit o imagen que se probó, y dónde. Queda escrito en el reporte de éxito. |
| — | `--confirm` | Código del dry-run. Obligatorio para publicar. |

## Resultado y códigos de salida

- `0`: publicado en Notion y hoja actualizada. El JSON trae `notion_url` y `local_file`.
- `1`: no se publicó. Lo más común es que no se encontró la página Nivel 1: el script **no crea una nueva** para no duplicar el defecto. Pide al usuario el ID de esa página y pásalo como argumento 5.
- `2`: faltan argumentos (incluye `--build` o la conclusión).
- `3`: **éxito parcial**. Notion se publicó, pero la hoja NO se actualizó (`sheet_updated: false`). Avísale al usuario; no lo des por cerrado.
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
