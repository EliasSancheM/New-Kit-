# Corrida E2E — <empresa> / <proyecto> (<fecha-inicio> → <fecha-cierre>)

Documento único de la corrida, según la skill `qa-e2e-corrida` del IAFactory QA Kit. El texto principal muestra el **estado final**; lo que cambió durante la corrida queda como nota secundaria ("*Registro en vivo: …*").

---

## 0. Metadatos, línea base y plan

| Campo | Valor |
|---|---|
| Modo | **En vivo** / **Auditoría retroactiva** (corrida ya terminada: menos detalle, ver §0.4) |
| Empresa | |
| Proyecto (nombre final en IAF) | |
| ID de proyecto IAF | |
| Documento de proyecto ("Antes") | [`proyectos/<slug>_requisitos.md`](proyectos/<slug>_requisitos.md) — versión usada: |
| Equipo asignado por Maya | (según `workflow.agent_plan`; indicar qué agentes **no** participaron) |
| Integraciones reales | Wiki: — Boards: — Repo: |
| Repo de código real | (verificar que no sea el repo vacío duplicado, ver AF-255, antes de asumir cuál es) |
| Entorno | |
| Fechas | |
| Ejecutado por | |
| Objetivo de la corrida | |
| Plan de revisión de issues | No / Sí — ver §0.3 |
| Convención de evidencia | [R] runtime observado, [DB] leído en Postgres/logs, [C] verificado en código, [C-sub] leído solo por subagente, [H] hipótesis |

### 0.1 Libro de decisiones (valor final = última fila de cada tema)

| Tema | Historial de cambios | Valor final vigente |
|---|---|---|
| | | |

### 0.2 Enlaces de la corrida

| Artefacto | Enlace |
|---|---|
| Wiki | |
| Backlog | |
| Repositorio de código | |
| Diseño (Figma) | |

### 0.3 Plan de revisión de issues (solo si se pidió)

Consulta: `fetch_issues.py --status "<estados>" --limit 1000 --json` el <fecha hora>, filtro de responsable: <nombre o "ninguno">.

| AF | Responsable | Estado en Sheet | Agente / etapa donde se prueba | Qué se hará | Criterio de verificación | ¿Requiere ajustar el proyecto? |
|---|---|---|---|---|---|---|
| | | | | | | |

**No revisables en esta corrida:**

| AF | Motivo (otro entorno, otra integración, agente que no participa, requiere acceso) |
|---|---|
| | |

Plan aprobado por el usuario: <fecha> / pendiente.

### 0.4 Alcance de la auditoría retroactiva (solo modo auditoría)

| Fuente | Disponible | Notas |
|---|---|---|
| Base de datos de la plataforma (solo lectura) | | |
| Transcripciones del chat | | |
| Logs (Loki) | | |
| Artefactos generados (Wiki/Boards/Figma) | | |
| Repositorio | | |
| Configuración de agentes/modelos | | |

**Lo que este modo no puede ver:** (lo observado en pantalla, tiempos percibidos, configuración que no quedó persistida, etc.)

### 0.5 Plan de proyecto: de la idea inicial a lo publicado

<!-- Completar al cierre: punto de partida (documento "Antes"), cómo se transformó etapa por etapa (referenciando el libro de decisiones), qué quedó finalmente publicado por IAF. -->

---

<!--
Bloque por agente. Repetir para cada agente que participó, en orden:
1 Maya · 2 Product Owner · 3 Arquitecto · 4 UI/UX · 5 QA · 6 Developer · 7 DevSec · 8 DevOps
Si un agente no participó, dejar su sección con una sola línea: "No participó (según workflow.agent_plan)".
-->

## 1. Maya (orquestador)

**Configuración usada:**
**Resumen de la conversación:**
**Artefactos generados y qué se verificó:**

### ✅ Lo que funcionó bien
-

### ❌ Hallazgos (registro limpio de la corrida)
| # | Hallazgo | Evidencia | Gravedad propuesta |
|---|---|---|---|
| MY-1 | | | |

### 🔁 Issues del plan revisados en esta etapa
| AF | Qué se probó | Resultado (corregido / persiste / no reproducible / no se pudo probar) | Evidencia |
|---|---|---|---|
| | | | |

### 🔍 Contraste con el Sheet en vivo
Consulta: `fetch_issues.py --status all --limit 1000 --json` el <fecha hora>.

| # | ¿Ya reportado? | AF-XXX | Estado actual en Sheet | Relación (duplicado / ampliación / relacionado / nuevo / posible regresión) | Nota |
|---|---|---|---|---|---|
| MY-1 | | | | | |

---

## 2. Product Owner
<!-- mismo bloque que Maya; prefijo PO- -->

## 3. Arquitecto
<!-- mismo bloque; prefijo AR- -->

## 4. UI/UX
<!-- mismo bloque; prefijo UX- -->

## 5. QA
<!-- mismo bloque; prefijo QA- -->

---

## 6. Developer — dos frentes que no se mezclan

### 6.a Funcionamiento del agente (candidato a ticket, igual que los demás agentes)

**Configuración usada:**
**Cómo se comportó el proceso:** (tiempos por ítem, reintentos, fidelidad, si abortó, si su narración coincide con lo que hizo)

#### ✅ Lo que funcionó bien (proceso)
-

#### ❌ Hallazgos del proceso (registro limpio)
| # | Hallazgo | Evidencia | Gravedad propuesta |
|---|---|---|---|
| DEV-1 | | | |

#### 🔁 Issues del plan revisados en esta etapa
| AF | Qué se probó | Resultado | Evidencia |
|---|---|---|---|
| | | | |

#### 🔍 Contraste con el Sheet en vivo (solo hallazgos de 6.a)
| # | ¿Ya reportado? | AF-XXX | Estado actual en Sheet | Relación | Nota |
|---|---|---|---|---|---|
| DEV-1 | | | | | |

### 6.b Código entregado — referencia de rendimiento del Developer (no se reporta en ningún lado)

Solo se menciona en este documento. Sin ticket, sin Notion, sin contraste con el Sheet.

Método: clonar, instalar dependencias, compilar (`tsc --noEmit` o equivalente) y, solo en local, levantar el servicio y probar las reglas RN-x del documento "Antes".

**✅ Lo que funciona correctamente:**
-

**❌ Defectos del código entregado:**
| # | Defecto | Regla / requisito afectado | Evidencia |
|---|---|---|---|
| COD-1 | | | |

**Datos de rendimiento (insumo para métricas futuras, no son métricas oficiales):**

| Dato | Valor |
|---|---|
| Archivos en el repo / commit final | |
| Compila (backend / frontend) | |
| Requerimientos RF implementados / totales | |
| Reglas RN probadas: correctas / parciales / fallidas / totales | |
| Pantallas UI presentes / planificadas | |
| Fidelidad reportada por el propio Developer | |

**Alcance no cubierto:**

---

## 7. DevSec
<!-- mismo bloque que Maya; prefijo SEC-. "No participó" si no aplica -->

## 8. DevOps
<!-- mismo bloque que Maya; prefijo OPS-. "No participó" si no aplica -->

---

## 9. Resumen ejecutivo

### 9.1 Lo bueno por agente

| Agente | Síntesis |
|---|---|
| | |

### 9.2 Hallazgos consolidados y relación con el Sheet

| # | Agente | Hallazgo | Severidad | Relación con Sheet (de las tablas 🔍) | Acción propuesta (publicar nuevo / ampliar AF-XXX / ninguna) |
|---|---|---|---|---|---|
| | | | | | |

### 9.3 Discrepancias Planificado | Agente | Documentación | Código

Una fila por elemento del documento "Antes" que no llegó intacto al final. "Primera ruptura" = la primera arista donde el valor se desvía de lo planificado.

| Elemento (RF / RN / UI / CA) | Planificado (documento "Antes") | Agente (lo que dijo o decidió en el chat) | Documentación (Wiki/Confluence/Boards/Figma) | Código | Primera ruptura |
|---|---|---|---|---|---|
| | | | | | |

### 9.4 Resultado del plan de revisión de issues

| AF | Resultado | Acción propuesta (cerrar con `qa-finish` / rechazar con `qa-rejection` / ninguna, va a pendientes) |
|---|---|---|
| | | |

---

## 10. Qué queda pendiente de esta corrida

1.
