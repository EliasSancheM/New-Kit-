---
name: report-bug
description: Reporta un defecto nuevo. Asigna el siguiente ID AF-XXX, publica el reporte ejecutivo y el técnico como páginas anidadas en Notion e inserta la fila en Google Sheets. Úsala cuando el usuario encuentre un bug nuevo y quiera registrarlo, levantarlo o reportarlo. ESCRIBE en sistemas compartidos; requiere dry-run y la confirmación de una persona en su terminal. / Report a new defect to Notion and Google Sheets.
---

# Report Bug (`report-bug`)

Registra un defecto nuevo en Notion y en Google Sheets. Escribe en sistemas compartidos por todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Quién decide

**Que algo sea un ticket lo decide una persona, no el asistente.** El asistente propone (qué es, por qué y con qué evidencia) y la persona decide ticket, ampliar un AF existente o descartar. Si la persona delega ("sube los que creas", "descarta los que consideres"), el asistente devuelve su propuesta y espera; no publica ni descarta por su cuenta.

**Un ticket por causa, no por síntoma.** Si varios hallazgos tienen la misma raíz (o no se sabe todavía si la tienen), se proponen como un solo ticket que los menciona a todos.

## Protocolo obligatorio

1. **Busca duplicados antes de reportar:** revisa el backlog (`qa-backlog`, con `--status all`) y Notion por un defecto con el mismo síntoma o la misma causa. Si ya existe, propone ampliarlo (`qa-amplify`) en vez de crear otro.
2. **Obtén el siguiente ID** (solo lectura):
   ```bash
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --audit
   ```
3. **Escribe los dos reportes con las plantillas** de `<KIT>/skills/report-bug/templates/`:
   - `Reportes/AF-XXX_<nombre_corto>.md` desde `ejecutivo.md`: qué falla (acción, observado, esperado), impacto, pasos de usuario numerados.
   - `Reportes/AF-XXX_<nombre_corto>_tecnico.md` desde `tecnico.md`: entorno y versión, evidencia etiquetada, causa raíz con `archivo:línea`, corrección, cómo verificarla y qué no se verificó.
   - **Evidencia antes que redacción:** sin una línea de código leída o un log citado, la causa raíz dice "Causa no identificada" y qué se revisó. No se completa con suposiciones.
4. **Revisa la estructura** (determinista, sin red):
   ```bash
   python <KIT>/skills/report-bug/scripts/report_lint.py "Reportes/AF-XXX_<nombre_corto>.md" "Reportes/AF-XXX_<nombre_corto>_tecnico.md"
   ```
   Con errores, `notion_mcp_publisher.py` no publica y el dry-run no entrega código.
5. **Dry-run de ambos pasos** y muéstraselo al usuario:
   ```bash
   python <KIT>/skills/report-bug/scripts/notion_mcp_publisher.py --dry-run \
     "Reportes/AF-XXX_<nombre_corto>.md" "Reportes/AF-XXX_<nombre_corto>_tecnico.md" "AF-XXX" "<nombre_corto>"
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --dry-run \
     "<nombre del defecto>" "<descripción técnica>" "<Critica|Alta|Media|Baja>"
   ```
6. **La persona publica desde su propia terminal.** Con su "sí", entrégale los dos comandos listos, cambiando `--dry-run` por `--confirm <confirm_code>` (cada dry-run imprime el suyo): primero Notion, y luego Sheets con la `level1_url` que devolvió Notion como 4.º argumento. La persona los ejecuta en una terminal abierta por ella; cada script muestra qué va a publicar y le pide escribir el AF-XXX para confirmar. **El asistente no puede hacer este paso**: si lo intenta, el script sale con código `5` sin escribir nada. Un ticket por vez.

## Códigos de salida

- `0`: ok.
- `1`: fallo (incluye errores de estructura en `notion_mcp_publisher.py`).
- `2`: faltan argumentos.
- `3` (Notion): la página Nivel 1 se creó pero la técnica (Nivel 2) falló. Avisa al usuario antes de seguir con Sheets.
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.

## Notas

- Cada publicación confirmada queda en `Reportes/.publicaciones.log` (fecha, quién confirmó, acción, ID).
- El ID que devuelve `--audit` se recalcula al insertar. Si otra persona reporta entre medio, el ID real puede cambiar: verifica el que imprime la inserción.
- El script no rellena la columna AGRUPACIÓN; el usuario la completa a mano.
