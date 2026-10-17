---
name: qa-rejection
description: Rechaza formalmente un defecto AF-XXX cuyo fix falló en la verificación en vivo. Publica el veredicto (plantilla veredicto.md, validado por verdict.py lint) en Google Sheets: ESTADO 'Rechazada por QA', fecha de término, quién rechazó y el veredicto completo en Comentario QA. Úsala cuando el asistente ejecutó los casos en la instancia y el del ticket sigue fallando, el fix no toca la causa raíz o rompió el control. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y confirmación de una persona. / Reject a defect whose fix failed verification.
---

# QA Rejection (`qa-rejection`)

Rechaza un defecto cuyo fix **el asistente probó en vivo y falló**. Escribe en Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

> Si el ticket no se está re-verificando y solo quieres sumarle evidencia sin cambiar su estado, usa `qa-amplify`. Si no se pudo probar (fix sin desplegar, entorno caído), tampoco es un rechazo: queda `En Revisión` con la razón anotada.

## Regla de veredicto

**Rechazada por QA** si, con la versión desplegada identificada, el caso del ticket sigue fallando, el cambio no toca la causa raíz, deja síntomas del ticket sin cubrir, o el caso de control regresó. El rechazo cita el caso que falló con su evidencia `[R]`/`[DB]` y lo que le falta al cambio.

## Protocolo obligatorio

1. **Revisión previa con las Fases 0 a 4** de `rules/AGENTS.md`, con los casos ejecutados en la instancia abierta por la persona.
2. **Escribe el veredicto** en `Reportes/rechazo/AF-XXX_veredicto.md` desde `<KIT>/skills/shared/templates/veredicto.md`, con encabezado `# AF-XXX — Veredicto QA: Rechazada por QA`. Al menos un caso en `Falla`.
3. **Valida el veredicto:**
   ```bash
   python <KIT>/skills/shared/verdict.py lint Reportes/rechazo/AF-XXX_veredicto.md
   ```
4. **Dry-run:**
   ```bash
   python <KIT>/skills/qa-rejection/scripts/qa_rejection_publisher.py --dry-run Reportes/rechazo/AF-XXX_veredicto.md
   ```
5. **Muestra el dry-run al usuario y pide confirmación explícita** para este defecto, en este turno.
6. **Pide el token de Sheets:** "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`.
7. Con un "sí" claro, entrégale a la persona el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. **La persona lo ejecuta en su propia terminal** y escribe el AF-XXX para confirmar; desde el asistente el script sale con código `5`.

## Qué exige el lint

Lo mismo que en `qa-finish` (versión probada, criterio del ticket, tres preguntas, casos con evidencia `[R]`/`[DB]`, control, límites, sin frases de suposición), y además al menos un caso con veredicto `Falla`.

## Qué escribe en la fila

ESTADO = `Rechazada por QA`, FECHA TERMINO = hoy, CERRADA POR = quien confirma, COMENTARIO QA = el veredicto completo.

## Códigos de salida

- `0`: hoja actualizada.
- `1`: errores de lint, el defecto no está en la hoja o falló la escritura. No se publicó.
- `2`: argumentos inválidos o el veredicto es de cierre (usa `qa-finish`).
- `4`: bloqueado. Falta `--confirm` o no coincide con el contenido; no se escribió nada.
- `5`: falta la confirmación de una persona en su terminal (o se canceló). No se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.
