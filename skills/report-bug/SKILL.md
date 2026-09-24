---
name: report-bug
description: Reporta un defecto nuevo. Asigna el siguiente ID AF-XXX, publica el reporte ejecutivo y el técnico como páginas anidadas en Notion e inserta la fila en Google Sheets. Úsala cuando el usuario encuentre un bug nuevo y quiera registrarlo, levantarlo o reportarlo. ESCRIBE en sistemas compartidos; requiere dry-run y confirmación. / Report a new defect to Notion and Google Sheets.
---

# Report Bug (`report-bug`)

Registra un defecto nuevo en Notion y en Google Sheets. Escribe en sistemas compartidos por todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Protocolo obligatorio

1. **Busca duplicados antes de reportar:** revisa el backlog (`qa-backlog`) y Notion por un defecto con el mismo síntoma. Si ya existe, avisa al usuario en vez de crear otro.
2. **Obtén el siguiente ID** (solo lectura):
   ```bash
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --audit
   ```
3. **Escribe los dos reportes locales** en `Reportes/`:
   - `Reportes/AF-XXX_<nombre_corto>.md`: resumen ejecutivo (qué falla, impacto, cómo reproducirlo).
   - `Reportes/AF-XXX_<nombre_corto>_tecnico.md`: análisis técnico. Debe empezar con el banner de advertencia de contenido generado por IA y separar hechos, inferencias y supuestos.
4. **Dry-run de ambos pasos** y muéstraselo al usuario:
   ```bash
   python <KIT>/skills/report-bug/scripts/notion_mcp_publisher.py --dry-run \
     "Reportes/AF-XXX_<nombre_corto>.md" "Reportes/AF-XXX_<nombre_corto>_tecnico.md" "AF-XXX" "<nombre_corto>"
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --dry-run \
     "<nombre del defecto>" "<descripción técnica>" "<Critica|Alta|Media|Baja>"
   ```
5. **Pide confirmación explícita.** Con un "sí" claro, ejecuta los mismos comandos sin `--dry-run`: primero Notion, y luego Sheets pasándole como 4.º argumento la `level1_url` que devolvió Notion.

## Códigos de salida

- `0`: ok.
- `1`: fallo.
- `2`: faltan argumentos.
- `3` (Notion): la página Nivel 1 se creó pero la técnica (Nivel 2) falló. Avisa al usuario antes de seguir con Sheets.

## Notas

- El ID que devuelve `--audit` se recalcula al insertar. Si otra persona reporta entre medio, el ID real puede cambiar: verifica el que imprime la inserción.
- El script no rellena la columna AGRUPACIÓN; el usuario la completa a mano.
