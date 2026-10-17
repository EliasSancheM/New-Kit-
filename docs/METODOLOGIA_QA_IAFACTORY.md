# 📐 Metodología y Protocolos Oficiales de QA: IAFactory

Este documento compila el marco metodológico, las fuentes de verdad y el ciclo de vida de defectos para el aseguramiento de calidad en **IAFactory**.

---

## 1. Fuentes de Verdad Operativa (Dualidad de Verdad)

El ecosistema IAFactory opera bajo una estricta separación de responsabilidades:

1. **Google Sheets Online (Fuente Única de Estado):**
   - Es la fuente de verdad **exclusiva y en tiempo real** para la lista de incidencias, estados (`Pendiente`, `En Revisión`, `Finalizada`, `Rechazada por QA`), severidad, desarrollador asignado y fechas.
   - **No existen matrices locales en CSV o Excel.** Toda consulta y mutación se realiza online vía la API oficial mediante las skills `qa-backlog`, `qa-finish`, `qa-rejection`, `qa-amplify` y `report-bug`. Toda escritura necesita un token de Sheets vigente (ver `.env.example`).

2. **Comentario QA (Evidencia Técnica en la misma fila):**
   - Desde la versión 1.8.0 no se usa Notion. La columna COMENTARIO QA de cada defecto guarda el reporte completo: ejecutivo + técnico al reportar (`report-bug`), el reporte de éxito o de rechazo al cerrar (`qa-finish`, `qa-rejection`) y bloques "Ampliación (<origen>)" con evidencia posterior (`qa-amplify`). Tope: 45.000 caracteres por celda.
   - Los archivos markdown de `Reportes/` en el workspace de cada QA son la copia local de trabajo.

3. **Obsidian Vault Local (`docs/vault/`), opcional:**
   - Espejo local de una sola dirección (el kit escribe, nada lo lee de vuelta). Desactivado por defecto; se activa con `QA_KIT_OBSIDIAN=1`. Cada publicación reescribe la nota completa del defecto con la gravedad real de la planilla.

---

## 2. Ciclo de Vida de Defectos (`AF-XXX`)

```text
[ Reportada ] ──> [ Pendiente ] ──> [ En Revisión ] ──┬──> [ Finalizada ] (Aprobado por QA)
                                                       │
                                                       └──> [ Rechazada por QA ] (Fix incompleto/regresión)
```

### Estados Permitidos:
- **`Reportada` / `Pendiente`:** El bug ha sido registrado con evidencia inicial, pero aún no tiene fix asignado o está en cola de desarrollo.
- **`En Revisión`:** El desarrollador implementó un commit de corrección y solicitó validación formal a QA.
- **`Finalizada`:** QA ejecutó pruebas empíricas en la VM de desarrollo (`iafactory-dev`) y comprobó que el bug está 100% resuelto sin regresiones.
- **`Rechazada por QA`:** El fix no solucionó la causa raíz, rompió otra funcionalidad o no está desplegado en la VM.

---

## 3. Matriz de Severidad

| Severidad | Criterio de Impacto Operativo | SLA Esperado |
| :--- | :--- | :--- |
| **`Crítica`** | Caída completa de un contenedor/servicio, bloqueo total de login o pérdida de datos. | Resolución inmediata |
| **`Alta`** | Falla de un flujo central del agente (ej. corte de streaming SSE, fallo en handoffs, timeouts persistentes). | < 24 horas |
| **`Media`** | Defecto visual mayor, discrepancia en métricas secundarias o error manejado con fallback degradado. | Sprint en curso |
| **`Baja`** | Detalle cosmético, tipografía, error tipográfico en prompt o inconsistencia menor de estilo. | Backlog regular |

---

## 4. Protocolo Mandatorio de Revisión de Incidencias (4 Fases)

Cualquier ingeniero o asistente de IA debe seguir estas 4 fases obligatorias al auditar una incidencia:

1. **Explicación del Issue:** Detalle del síntoma reportado, contexto operativo y causa raíz identificada a nivel de archivo y línea.
2. **Cambios Implementados:** Análisis técnico de los archivos modificados, commits del desarrollador asociados y diff concreto.
3. **Propuesta de Revisión en Vivo:** Plan detallado paso a paso para validar empíricamente la solución en caliente (endpoints, servicios, contenedores, logs de Docker o casos de prueba en navegador/API).
4. **🛑 Cero Mutaciones sin Autorización Previa:**
   - **Prohibido ejecutar `qa-finish` o `qa-rejection` de forma autónoma.**
   - No se alterará ninguna celda de estado en Google Sheets ni se escribirá el veredicto en Comentario QA sin visto bueno explícito del usuario ("Proceder", "Aprobado", "Rechazar ticket").

> 💡 **Excepción:** Si la consulta es puntual (*"revisa si está en checkout"*, *"¿está el commit en HEAD dev?"*), responder directamente con commit VM vs remoto y estado SÍ/NO sin disparar las 4 fases.
