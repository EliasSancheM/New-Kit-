---
name: qa-finish
description: Cierra formalmente un defecto AF-XXX verificado. Genera el reporte de éxito local, lo publica como subpágina en Notion y marca la fila de Google Sheets como 'Finalizada'. Úsala cuando el usuario diga que un AF-XXX pasó la prueba y quiera cerrarlo o finalizarlo. ESCRIBE en sistemas compartidos; requiere dry-run y confirmación. / Close a verified defect in Notion and Google Sheets.
---

# QA Finish (`qa-finish`)

Cierra un defecto que **ya se verificó empíricamente**. Escribe en Notion y Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Protocolo obligatorio

1. **Confirma que hay evidencia real** de la prueba (qué se ejecutó, en qué entorno, qué salió). Si no la hay, no cierres: pídela.
2. **Dry-run:** ejecuta el comando con `--dry-run`. No escribe nada; muestra la página Nivel 1 encontrada, la fila de la hoja y los valores que se escribirán.
3. **Muestra el dry-run al usuario y pide confirmación explícita.** La confirmación vale para este defecto y este turno, no para los siguientes.
4. Solo con un "sí" claro, ejecuta sin `--dry-run`.

```bash
python <KIT>/skills/qa-finish/scripts/qa_finish_publisher.py --dry-run \
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
| 4 | conclusión | Opcional. Por qué se considera resuelto. |
| 5 | level1_page_id | Opcional. ID de la página Nivel 1 en Notion, si la búsqueda automática no la encuentra |

## Resultado y códigos de salida

- `0`: publicado en Notion y hoja actualizada. El JSON trae `notion_url` y `local_file`.
- `1`: no se publicó. Lo más común es que no se encontró la página Nivel 1: el script **no crea una nueva** para no duplicar el defecto. Pide al usuario el ID de esa página y pásalo como argumento 5.
- `2`: faltan argumentos.
- `3`: **éxito parcial**. Notion se publicó, pero la hoja NO se actualizó (`sheet_updated: false`). Avísale al usuario; no lo des por cerrado.
