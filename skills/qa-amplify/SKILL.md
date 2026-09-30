---
name: qa-amplify
description: Agrega evidencia nueva a un defecto AF-XXX existente sin cambiar su estado. Publica una subpágina 'AF-XXX_ampliacion_<origen>' bajo la página Nivel 1 de Notion y guarda una copia local; el estado del Sheet no se toca. Úsala cuando un hallazgo ya estaba reportado (duplicado o ampliación), o cuando hay evidencia nueva sobre un ticket que nadie está re-verificando. ESCRIBE en Notion; requiere dry-run y confirmación. / Add evidence to an existing defect without changing its status.
---

# QA Amplify (`qa-amplify`)

Suma evidencia a un ticket que ya existe. Escribe en Notion, que usa todo el equipo.

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
2. **Dry-run:** no escribe nada. Por cada ticket muestra la página Nivel 1 destino, el título, el estado actual en el Sheet y un extracto del contenido, y al final un `confirm_code` que cubre todo el lote.
3. **Muestra el dry-run al usuario y pide confirmación explícita** en este turno. Una confirmación cubre el lote que mostraste, no otros.
4. Solo con un "sí" claro, repite el mismo comando cambiando `--dry-run` por `--confirm <confirm_code>`. Si cambias el lote (otro `--only`, otro texto), el código no sirve: repite el dry-run.

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

Cada viñeta de la última sección se publica como una subpágina corta en su ticket.

## Opciones

| Opción | Efecto |
|---|---|
| `--dry-run` | No escribe nada. Úsala siempre primero; imprime el `confirm_code`. |
| `--confirm <código>` | Obligatorio para publicar: el código del dry-run del mismo lote. |
| `--only AF-X,AF-Y` | Publica solo esos tickets del archivo. |
| `--level1 <id>` | Página Nivel 1 explícita (solo con un ticket), si no se resuelve sola. |
| `--link-in-sheet` | Agrega la URL de la subpágina al final de COMENTARIO QA sin borrar lo que había. Apagado por defecto; úsalo solo si el usuario lo pide. |

## Qué hace

1. Busca el ticket en el Sheet y lee su estado actual (solo para mostrarlo).
2. Resuelve la página Nivel 1 desde la URL de Notion guardada en el Sheet; si no puede, la busca por título.
3. Si ya hay una subpágina con el mismo título, **no la duplica** y lo informa. Si la evidencia es distinta, usa otro origen.
4. Publica la subpágina con un encabezado estándar (origen, fecha, autor y "sin cambiar el estado del ticket") y guarda una copia en `Reportes/ampliaciones/`.
5. **No cambia el estado del Sheet.** Solo con `--link-in-sheet` agrega el enlace en COMENTARIO QA.

Un ticket con error no detiene el lote: el resultado indica el error de cada uno.

## Códigos de salida

- `0`: todo publicado (o dry-run sin errores).
- `1`: algún ticket falló o ya tenía esa subpágina. Revisa el campo `error` de cada uno en el JSON.
- `2`: argumentos inválidos.
- `4`: bloqueado. Falta `--confirm` o no coincide con el lote; no se escribió nada.

## Si falla

- **gcloud o token de Notion:** revisa con `qa-preflight`. Si gcloud da `CERTIFICATE_VERIFY_FAILED`, configura `QA_KIT_CA_BUNDLE` (ver README).
- **Sin página Nivel 1:** revisa que la columna COMENTARIO QA del Sheet tenga la URL de Notion del ticket, o pásala con `--level1`.
