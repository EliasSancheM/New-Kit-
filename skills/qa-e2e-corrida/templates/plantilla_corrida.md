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
| Entorno (VM) | |
| Fechas | |
| Ejecutado por | |
| Modelo del asistente | |
| Versión del kit | {{KIT_VERSION}} (documento creado con `new_run.py` el {{CREATED_AT}}) |
| Autores del documento | (quién escribió cada parte; si otra herramienta o sesión lo completó, indicarlo aquí) |
| Quién responde a los agentes | Usuario / asistente, siempre según el documento "Antes" |
| Objetivo de la corrida | |
| Plan de revisión de issues | No / Sí — ver §0.3 |
| Convención de evidencia | [R] runtime observado, [DB] leído en Postgres/logs, [C] verificado en código, [C-sub] leído solo por subagente, [H] hipótesis. No se usan otras etiquetas. |
| Escala de gravedad | Crítica: bloquea el flujo sin alternativa o pierde/expone datos · Alta: bloquea una etapa o entrega un resultado incorrecto que el usuario no detecta · Media: hay alternativa o el error es visible y corregible · Baja: cosmético o de redacción |

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

### 0.6 Foto de la configuración de agentes de la empresa (al inicio)

Leída en solo lectura antes de escribirle a Maya (`company_agent_profiles` u otra fuente). Los perfiles no tienen historial: si no se guarda ahora, después no se puede saber si un comportamiento venía de la configuración.

| Agente | Instrucciones / tono | Largo de respuesta | Restricciones | Fuente y hora de lectura |
|---|---|---|---|---|
| | | | | |

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
| # | Hallazgo | Evidencia | Gravedad propuesta | ¿Lo explica la configuración (§0.6)? |
|---|---|---|---|---|
| MY-1 | | | | |

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

Método (obligatorio; si algún paso no se pudo hacer, esta sección lo dice como **revisión parcial**, no solo en §10):
1. Clonar el repo publicado (no el workspace del contenedor) y registrar repo, rama y **commit revisado**. Comprobar que no sea un repo vacío duplicado.
2. Instalar dependencias y compilar backend y frontend (`tsc --noEmit` o equivalente), incluidos los tests del repo.
3. Probar cada RN-x del documento "Antes" **ejecutando** el código: el servicio levantado en local, o un test contra la clase real con dependencias en memoria. Incluir **pruebas de control** que demuestren que el arnés sí puede rechazar (por ejemplo, un caso inválido que el código ya maneja).
4. Si la autenticación u otra dependencia externa impide levantar el servicio, se puede reemplazar solo esa pieza (stub) y se declara cuál.
5. Todo en local; nada en VMs compartidas.

| Dato del método | Valor |
|---|---|
| Repo / rama / commit revisado | |
| Cómo se ejecutaron las reglas (servicio local / test con dependencias en memoria / stub de …) | |
| Pruebas de control y su resultado | |
| ¿Revisión completa o parcial? (si es parcial, qué faltó y por qué) | |

**✅ Lo que funciona correctamente:**
-

**❌ Defectos del código entregado:**
| # | Defecto | Regla / requisito afectado | Evidencia | ¿Ejecutado o solo leído? |
|---|---|---|---|---|
| COD-1 | | | | |

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

### 9.2 Hallazgos consolidados: propuesta del asistente y decisión humana

Una fila por **causa**, no por síntoma: los hallazgos de la misma etapa con la misma raíz se agrupan en una fila (columna "Hallazgos"). El asistente llena hasta "Propuesta"; **las tres últimas columnas las llena la persona** (o el asistente las copia textualmente de lo que la persona escribió en el chat). El asistente nunca decide ni descarta por su cuenta, aunque se lo pidan ("descarta los que consideres"): en ese caso devuelve su propuesta con el motivo y espera la decisión.

| Causa | Hallazgos | Agente | Severidad | Relación con Sheet (de las tablas 🔍) | Propuesta del asistente (y por qué) | Decisión (Ticket / Ampliar AF-XXX / Descartar) | Motivo de la decisión | Decidido por |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

### 9.3 Discrepancias Planificado | Agente | Documentación | Código

Una fila por elemento del documento "Antes" que no llegó intacto al final. "Primera ruptura" = la primera arista donde el valor se desvía de lo planificado.

| Elemento (RF / RN / UI / CA) | Planificado (documento "Antes") | Agente (lo que dijo o decidió en el chat) | Documentación (Wiki/Confluence/Boards/Figma) | Código | Primera ruptura |
|---|---|---|---|---|---|
| | | | | | |

### 9.4 Resultado del plan de revisión de issues

| AF | Resultado | Acción propuesta (cerrar con `qa-finish` / rechazar con `qa-rejection` / ninguna, va a pendientes) |
|---|---|---|
| | | |

### 9.5 Coherencia entre agentes

La misma decisión según cada agente y el código. Una fila por decisión que se repite entre etapas (nube, ambientes, entidades del modelo, pantallas, integraciones, reglas). "—" si el agente no la trata; ❌ si contradice lo que dijo otro agente.

| Decisión | PO | Arquitecto | UI/UX | QA | DevOps | Código | ¿Coherente? |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

### 9.6 Documentación publicada

Revisada en su destino real (Confluence / Wiki / Boards / Figma) al cierre, no en el chat.

| Documento esperado | ¿Existe? | Enlace | ¿Refleja lo acordado? (qué falta o sobra) |
|---|---|---|---|
| | | | |

### 9.7 Bloqueos y fallas de la corrida

Momentos en que un agente se trabó, falló o hubo que reintentar, con su causa en los logs. Se separa de los hallazgos de conducta: aquí se explica qué detuvo la corrida.

| Cuándo (UTC) | Agente / servicio | Qué se vio | Cuánto duró | Causa en logs o código [DB]/[C] | Cómo se destrabó |
|---|---|---|---|---|---|
| | | | | | |

### 9.8 Fuera de alcance (sin ticket automático)

Problemas de plataforma o infraestructura vistos durante la corrida que **no la afectaron** (p. ej. alertas por correo, recolección de logs, cambios sin commit en la VM). Quedan anotados para revisión aparte; no entran en la §9.2.

| Qué se vio | Dónde | Por qué no afectó la corrida |
|---|---|---|
| | | |

---

## 10. Qué queda pendiente de esta corrida

1.

---

## 11. Validación del documento

Resultado de `validate_run.py` al cerrar (pegar la línea de resumen):


