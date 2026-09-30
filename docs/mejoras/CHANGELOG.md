# Registro de mejoras — IAFactory QA Kit

Cada versión explica **qué cambió**, **cómo** y **por qué**. La más reciente va primero. Las versiones anteriores a la 1.6.0 se resumen a partir de sus mensajes de commit.

Formato de cada entrada: **Nuevo** (capacidades nuevas), **Cambiado** (comportamiento distinto al anterior; revisa si afecta tu forma de trabajar), **Corregido** (errores).

---

## [1.6.0] — 2026-09-30 · Corridas E2E consistentes y publicación con candado

### Por qué

Comparamos las corridas E2E de tres integrantes del equipo y los informes salieron con al menos cinco estructuras distintas: secciones con otra numeración, etiquetas de evidencia propias, contrastes con el Sheet hechos solo con algunos estados, documentos terminados por otra herramienta sin decirlo y cierres de tickets sin la versión probada. La causa no era la persona, sino que el método dependía de que el asistente de cada uno recordara la plantilla (o cargara una copia vieja de la skill). Esta versión mueve esas reglas a scripts que se comportan igual para cualquier persona y cualquier asistente.

### Nuevo

- **`validate_run.py` (qa-e2e-corrida).** Valida un documento de corrida contra la plantilla y devuelve errores y advertencias (`--json`, `--strict`). Revisa:
  - secciones y metadatos obligatorios, y que exista el documento "Antes" enlazado;
  - que cada agente que participó tenga ✅, ❌ y 🔍, y que el 🔍 cite la consulta con `--status all`;
  - que las tablas ❌ no mencionen AF-IDs;
  - etiquetas de evidencia (`[R]`, `[DB]`, `[C]`, `[C-sub]`, `[H]`) y escala de gravedad (Crítica, Alta, Media, Baja);
  - la tabla del método y la de rendimiento de la §6.b;
  - texto principal que todavía no muestra el estado final ("(en curso)", "candidato", `TODO`).

  *Por qué:* un documento se da por terminado cuando el validador no reporta errores, sin depender de que alguien revise la estructura a mano.

- **Candado de publicación en `report-bug`, `qa-amplify`, `qa-finish` y `qa-rejection`.** El `--dry-run` imprime un `confirm_code` calculado sobre el contenido exacto a publicar; la publicación real exige `--confirm <confirm_code>`. Sin el código, o si el contenido cambió después del dry-run (incluido editar el reporte), el script sale con código `4` sin escribir nada.
  *Por qué:* en una corrida se publicaron tickets en Sheets y Notion sin mostrar antes el dry-run. La regla existía, pero solo como instrucción al asistente.

- **Detección de copias desactualizadas en `qa-welcome`.** Avisa si hay copias de las skills en `.claude/skills/` distintas a las del kit, o un plugin instalado en Claude Code con otra versión. Las junctions y enlaces al kit se reconocen como sincronizados.
  *Por qué:* una copia vieja de `qa-e2e-corrida` produjo un informe con la estructura antigua sin que nadie lo notara.

- **Plantilla de corrida:** metadatos nuevos (modelo del asistente, versión del kit, autores del documento, quién responde a los agentes), escala de gravedad definida, §0.6 con la foto de la configuración de agentes de la empresa, tabla del método de revisión de código en la §6.b y §11 para el resultado de la validación.

### Cambiado

- **`qa-finish` y `qa-rejection` exigen `--build <commit o imagen probada>`**, que queda escrito en el reporte. En `qa-finish`, la conclusión (4.º argumento) pasó a ser obligatoria.
  *Por qué:* se cerró un ticket "con alta confianza" sin prueba ejecutada; sin la versión probada no se puede saber qué se verificó.
  **Si tienes comandos o prompts guardados con estos scripts, agrega `--build`; sin él salen con código `2`.**

- **`new_run.py`** escribe la versión del kit y la fecha de creación en los metadatos del documento de corrida.

- **`qa-e2e-corrida` (SKILL.md)** incorpora reglas de consistencia:
  - la skill manda sobre la memoria del asistente y sobre informes anteriores en todo lo que es método;
  - un solo documento, escrito durante la corrida; si otra herramienta lo completa, se anota;
  - documento "Antes" obligatorio aunque el asistente invente el proyecto o haga de cliente;
  - foto de los perfiles de agentes antes de hablar con Maya;
  - descartar un hallazgo solo con una causa citada (configuración, duplicado o criterio vigente con fuente);
  - método completo para revisar el código del Developer: clonar el repo publicado, registrar el commit, compilar, **ejecutar** las reglas con pruebas de control, marcar qué se ejecutó y qué solo se leyó, y declarar una revisión parcial en su propia sección;
  - detalle de "estado final primero": repasar todo el documento y mover lo resuelto a notas de registro en vivo.

- **Hook de inicio y `rules/AGENTS.md`** incluyen las corridas E2E entre las tareas en que se cargan las reglas del kit, y documentan el código de salida `4`.

- **`qa-help` y README** documentan las opciones nuevas.

### Cómo actualizar

1. Actualiza el kit (`qa-update`, o `git pull` en el submódulo).
2. Abre un chat nuevo y corre `qa-welcome`: si avisa de copias o plugins desactualizados, actualízalos o elimínalos y reinicia el chat.
3. En tus comandos de publicación, reemplaza el segundo paso "sin `--dry-run`" por "`--confirm <código del dry-run>`", y agrega `--build` en `qa-finish` y `qa-rejection`.

---

## [1.5.1] — 2026-09-28
- Inicio rápido del README en modo agéntico: qué pedirle al asistente y qué skill se usa.

## [1.5.0] — 2026-09-28
- **Nuevo:** skill `qa-amplify`, para agregar evidencia a un defecto existente sin cambiar su estado.

## [1.4.0] — 2026-09-28
- **Nuevo:** skill `qa-e2e-corrida` (documento "Antes", plan de issues, auditoría retroactiva).
- **Nuevo:** filtro `--responsable` en `qa-backlog`.

## [1.3.0] — 2026-09-24
- `qa-welcome` carga las reglas del kit en el chat; hook de inicio de sesión.
- Lectura del `.env` del workspace y aviso de truncado en `qa-backlog`.

## [1.2.0] — 2026-09-24
- Varias VMs (dev, qa, team-devs), bundle de CA para TLS interceptado, Obsidian opcional, gravedad real y soporte para varios asistentes.

## [1.1.1] — 2026-09-23
- **Corregido:** respaldo a la columna O (Comentario QA).

## [1.1.0] — 2026-09-23
- Tests opcionales con `--run-tests`, skill `qa-update` y varios túneles IAP a la vez.
