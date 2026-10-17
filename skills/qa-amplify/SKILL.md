---
name: qa-amplify
description: Agrega evidencia nueva a un defecto AF-XXX existente sin cambiar su estado. Añade un bloque 'Ampliación (<origen>)' al final de Comentario QA en Google Sheets y guarda una copia local; el estado no se toca. Úsala cuando un hallazgo ya estaba reportado (duplicado o ampliación), o cuando hay evidencia nueva sobre un ticket que nadie está re-verificando. ESCRIBE en la planilla compartida; requiere dry-run, token de Sheets fresco y confirmación. / Add evidence to an existing defect without changing its status.
---

# QA Amplify (`qa-amplify`)

Suma evidencia a un ticket que ya existe. Escribe en Google Sheets, que usa todo el equipo.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Cuándo usarla y cuándo no

| Situación | Skill |
|---|---|
| Defecto nuevo, no está en el Sheet | `report-bug` |
| Ticket en revisión, re-probaste el fix y **pasó** | `qa-finish` |
| Ticket en revisión, re-probaste el fix y **sigue fallando** | `qa-rejection` |
| Evidencia nueva sobre un ticket que **no se está re-verificando** (`Reportada`, `En curso`…): otro proyecto, otra empresa, causa confirmada en logs | **`qa-amplify`** |
| Un hallazgo de una corrida E2E ya estaba reportado (duplicado o ampliación) | **`qa-amplify`** |

Si el ticket está `Finalizada` y el problema volvió a aparecer, es una posible regresión: pregúntale al usuario si prefiere ampliarlo o reportar uno nuevo que lo cite.

## Protocolo obligatorio

1. **Redacta la evidencia:** qué se vio, con su fuente (`[R]` observado, `[DB]` base de datos o logs, `archivo:línea`), y qué aporta respecto al ticket original. No repitas lo que el ticket ya dice.
2. **Dry-run:** no escribe nada. Por cada ticket muestra la fila, el estado actual, cuántos caracteres se agregan y un extracto, y al final un `confirm_code` que cubre todo el lote.
3. **Muestra el dry-run al usuario y pide confirmación explícita** en este turno. Una confirmación cubre el lote que mostraste, no otros.
4. **Pide el token de Sheets:** "necesito token fresco de Sheets". La persona lo pega en el `.env` del workspace como `SHEETS_ACCESS_TOKEN=`.
5. Solo con un "sí" claro, repite el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. Si cambias el lote (otro `--only`, otro texto), el código no sirve: repite el dry-run. Las ampliaciones no exigen la confirmación en terminal: el estado del ticket no cambia.

### Un ticket

```bash
python <KIT>/skills/qa-amplify/scripts/qa_amplify_publisher.py --dry-run \
  "AF-XXX" "<origen, p. ej. E2E_Apiux_2026-09-25>" "<evidencia en markdown>"

# Evidencia larga desde un archivo
python <KIT>/skills/qa-amplify/scripts/qa_amplify_publisher.py --dry-run \
  "AF-XXX" "<origen>" --body-file evidencia.md
```

### Varios tickets desde un archivo

```bash
python <KIT>/skills/qa-amplify/scripts/qa_amplify_publisher.py --dry-run \
  --file ampliaciones.md --origin "<origen>" [--only AF-231,AF-245]
```

Formato del archivo (secciones separadas por una línea `---`):

```markdown
## AF-231 — Título corto
Cuerpo de la evidencia para AF-231.

---

## AF-231 / AF-245 — Título corto
Este cuerpo se publica en los dos tickets.

---

## Evidencia adicional para duplicados
- **AF-300** (duplicado exacto): una línea con lo que se vio.
- **AF-236**: otra línea.
```

Cada viñeta de la última sección se agrega como un bloque corto en su ticket.

## Opciones

| Opción | Efecto |
|---|---|
| `--dry-run` | No escribe nada. Úsala siempre primero; imprime el `confirm_code`. |
| `--confirm <código>` | Obligatorio para publicar: el código del dry-run del mismo lote. |
| `--only AF-X,AF-Y` | Publica solo esos tickets del archivo. |

## Qué hace

1. Busca el ticket en el Sheet y lee su estado actual (solo para mostrarlo).
2. Si Comentario QA ya tiene una ampliación con el mismo origen, **no la duplica** y lo informa. Si la evidencia es distinta, usa otro origen.
3. Agrega al final de Comentario QA el bloque `--- Ampliación (<origen>) ---` con fecha, autor y la evidencia, respetando el tope de 45.000 caracteres, y guarda una copia en `Reportes/ampliaciones/`.
4. **No cambia el estado ni ninguna otra columna.**

Un ticket con error no detiene el lote: el resultado indica el error de cada uno.

## Códigos de salida

- `0`: todo publicado (o dry-run sin errores).
- `1`: algún ticket falló o ya tenía esa ampliación. Revisa el campo `error` de cada uno en el JSON.
- `2`: argumentos inválidos.
- `4`: bloqueado. Falta `--confirm` o no coincide con el lote; no se escribió nada.
- `6`: sin token de Sheets o token vencido. Pide uno nuevo y que lo pegue en el `.env`.
