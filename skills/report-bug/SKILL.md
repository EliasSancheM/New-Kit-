---
name: report-bug
description: Reporta un defecto nuevo. Asigna el siguiente ID AF-XXX e inserta la fila en Google Sheets con el reporte ejecutivo y el técnico completos en Comentario QA. Úsala cuando el usuario encuentre un bug nuevo y quiera registrarlo, levantarlo o reportarlo. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y la confirmación de una persona en su terminal. / Report a new defect to Google Sheets.
---

# Report Bug (`report-bug`)

Registra un defecto nuevo en Google Sheets, la única fuente compartida del equipo. No hay Notion: el reporte completo va en la columna Comentario QA de la fila.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Quién decide

**Que algo sea un ticket lo decide una persona, no el asistente.** El asistente propone (qué es, por qué y con qué evidencia) y la persona decide ticket, ampliar un AF existente o descartar. Si la persona delega ("sube los que creas", "descarta los que consideres"), el asistente devuelve su propuesta y espera; no publica ni descarta por su cuenta.

**Un ticket por causa, no por síntoma.** Si varios hallazgos tienen la misma raíz (o no se sabe todavía si la tienen), se proponen como un solo ticket que los menciona a todos.

## Protocolo obligatorio

1. **Busca duplicados antes de reportar:** revisa el backlog (`qa-backlog`, con `--status all`) por un defecto con el mismo síntoma o la misma causa. Si ya existe, propone ampliarlo (`qa-amplify`) en vez de crear otro.
2. **Obtén el siguiente ID** (solo lectura):
   ```bash
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --audit
   ```
3. **Escribe los dos reportes con las plantillas** de `<KIT>/skills/report-bug/templates/`, usando ese ID en el nombre del archivo y en el encabezado `# AF-NNN — <título>`:
   - `Reportes/AF-NNN_<nombre_corto>.md` desde `ejecutivo.md`: qué falla (acción, observado, esperado), impacto, pasos de usuario numerados, gravedad y contexto.
   - `Reportes/AF-NNN_<nombre_corto>_tecnico.md` desde `tecnico.md`: entorno y versión, evidencia etiquetada, causa raíz con `archivo:línea`, corrección, cómo verificarla y qué no se verificó.
   - **Evidencia antes que redacción:** sin una línea de código leída o un log citado, la causa raíz dice "Causa no identificada" y qué se revisó. No se completa con suposiciones.
4. **Revisa la estructura** (determinista, sin red):
   ```bash
   python <KIT>/skills/report-bug/scripts/report_lint.py "Reportes/AF-NNN_<nombre_corto>.md" "Reportes/AF-NNN_<nombre_corto>_tecnico.md"
   ```
   Con errores, el publicador no escribe y el dry-run no entrega código.
5. **Dry-run** y muéstraselo al usuario. El script lee título, gravedad y síntoma del reporte ejecutivo; no hay que copiarlos como argumentos.
   ```bash
   python <KIT>/skills/report-bug/scripts/gsheets_updater.py --dry-run \
     "Reportes/AF-NNN_<nombre_corto>.md" "Reportes/AF-NNN_<nombre_corto>_tecnico.md"
   ```
   Si la planilla ya asignó ese ID a otro defecto (alguien reportó entre medio), el script sale con código `2` y dice a qué ID renombrar.
6. **Pide el token de Sheets.** Antes de entregar el comando final, dile a la persona: "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`. Nunca en el chat.
7. **La persona publica desde su propia terminal.** Con su "sí", entrégale el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. La persona lo ejecuta en una terminal abierta por ella; el script muestra qué va a escribir y le pide escribir el AF-NNN para confirmar. **El asistente no puede hacer este paso**: si lo intenta, el script sale con código `5` sin escribir nada. Un ticket por vez.

## Qué escribe en la fila

ID, NOMBRE (título del ejecutivo), GRAVEDAD (del ejecutivo, o `--gravedad`), DESCRIPCIÓN (sección "Qué falla" en una línea), REPORTADA POR, FECHA INICIO, ESTADO = `Reportada` y COMENTARIO QA = reporte ejecutivo + reporte técnico (tope 45.000 caracteres; si se recorta, lo dice al final). AGRUPACIÓN y RESPONSABLE los completa el equipo a mano.

## Códigos de salida

- `0`: ok.
- `1`: errores de estructura (lint) o fallo al escribir.
- `2`: argumentos inválidos, gravedad desconocida o el ID del reporte ya no es el siguiente de la planilla.
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.

## Notas

- Cada publicación confirmada queda en `Reportes/.publicaciones.log` (fecha, quién confirmó, acción, ID).
- Editar un reporte después del dry-run invalida el `confirm_code`: repite el dry-run.
