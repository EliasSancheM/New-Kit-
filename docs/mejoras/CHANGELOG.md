# Registro de mejoras — IAFactory QA Kit

Cada versión explica **qué cambió**, **cómo** y **por qué**. La más reciente va primero. Las versiones anteriores a la 1.6.0 se resumen a partir de sus mensajes de commit.

Formato de cada entrada: **Nuevo** (capacidades nuevas), **Cambiado** (comportamiento distinto al anterior; revisa si afecta tu forma de trabajar), **Corregido** (errores).

---

## [1.9.0] — 2026-10-17 · El asistente verifica en vivo: veredictos y corridas con evidencia obligatoria

### Por qué

Las reglas decían qué mirar, pero no cuándo un fix se aprueba o se rechaza, y nada impedía cerrar un ticket "con alta confianza" sin ejecutar el caso del ticket (pasó con AF-227). En las corridas E2E, "qué artefactos generó el agente" era texto libre, así que se daba por bueno lo que el agente decía en el chat y dos corridas no se podían comparar. Desde esta versión el criterio es uno: la persona abre la instancia y **el asistente verifica por sí mismo** cada caso y cada artefacto, con evidencia observada; lo que no se observó se declara no probado.

### Nuevo

- **Plantilla de veredicto** (`skills/shared/templates/veredicto.md`) y **`verdict.py lint`**: versión probada, criterio del ticket, las tres preguntas sobre el cambio (¿toca la causa raíz?, ¿cubre todos los síntomas?, ¿trae test del caso?), tabla de casos ejecutados (ticket, control, límite) con pasos, resultado observado, evidencia `[R]`/`[DB]` y Pasa/Falla/No probado, y límites. Rechaza marcadores de plantilla y frases como "se asume", "debería funcionar" o "alta confianza".
- **Regla de veredicto en `AGENTS.md`:** Finalizada solo con versión desplegada identificada, caso del ticket y todos los síntomas pasando en vivo y control sin regresión; Rechazada si el caso falla, el cambio no toca la causa o rompe el control; Sin veredicto si no se pudo probar. Nueva **Fase 0** (qué pide el ticket, criterio de aceptación) y Fase 3 con los tres casos mínimos.
- **Corridas E2E:** tabla 📦 de **artefactos esperados por agente**, llena por `new_run.py` con lo que cada agente debe dejar y dónde; el asistente la verifica en el destino real (`[R]`/`[DB]`) con resultado Existe y coincide / Existe con diferencias / No existe. §9.1 pasa a **Resultado por agente** (artefactos, hallazgos por gravedad, bloqueos, síntesis). `validate_run.py --metrics` imprime los conteos para comparar corridas.

### Cambiado

- **`qa-finish` y `qa-rejection` reciben el archivo de veredicto** en lugar de cuatro argumentos de texto. Con errores de lint no publican ni entregan código. `qa-finish` rechaza un veredicto con un caso en Falla; `qa-rejection` exige al menos uno.
- **`validate_run.py` es más estricto:** son errores (antes advertencias o nada) una tabla 📦 vacía o sin verificación del asistente, un hallazgo sin etiqueta o con solo `[H]`, una gravedad fuera de escala o sin motivo entre paréntesis, y una fila de §9.1 ausente o incompleta para un agente que participó.

### Cómo actualizar

1. Escribe cierres y rechazos desde `veredicto.md` y pásalos por `verdict.py lint` antes del dry-run. Los comandos antiguos con `--build` y cuatro argumentos salen con código `2`.
2. Crea las corridas nuevas con `new_run.py`: trae la tabla 📦 por agente. Las corridas anteriores no pasan el validador nuevo sin esa tabla.

---

## [1.8.0] — 2026-10-17 · Solo Google Sheets, token pegado y publicación en un paso

### Por qué

El 15 de octubre las publicaciones del kit no se pudieron hacer con el kit: la confirmación humana leía el teclado con `msvcrt` y en Windows no recibía ninguna tecla; la resolución de la página Nivel 1 de Notion pasaba por `npx notion-mcp-server` con 12 s de tope y fallaba al azar, y el respaldo REST solo sabía crear páginas. Se publicaron 18 tickets y 8 veredictos con scripts improvisados y sin Notion. Además, si la sesión arrancaba dentro de la carpeta del kit, el kit se tomaba a sí mismo como workspace y escribía los reportes dentro del plugin. El equipo decidió dejar de usar Notion: Google Sheets pasa a ser el único registro compartido.

### Cambiado

- **Sin Notion.** Se eliminan `notion_mcp_publisher.py`, `mcp_config.json`, `NOTION_TOKEN` y todo el cliente MCP/REST. El reporte completo de cada defecto vive en la columna **Comentario QA** de su fila (tope 45.000 caracteres): ejecutivo + técnico al reportar, reporte de éxito o de rechazo al cerrar, y bloques "Ampliación (<origen>)" con evidencia posterior. Los markdown de `Reportes/` siguen siendo la copia local.
- **`report-bug` publica en un paso.** `gsheets_updater.py` recibe los dos reportes markdown, pasa `report_lint.py`, lee título, gravedad y síntoma del ejecutivo y escribe la fila. Ya no se copian título ni descripción como argumentos ni hay URL que trasladar. Si la planilla ya asignó el ID del reporte a otro defecto, sale con código `2` y dice a cuál renombrar.
- **`qa-finish` y `qa-rejection`** resuelven la fila y muestran su estado actual **antes** de pedir la confirmación, escriben también FECHA TERMINO y guardan el reporte completo en Comentario QA. Desaparecen el 5.º argumento `level1_page_id` y el código de salida `3`.
- **`qa-amplify`** agrega la evidencia al final de Comentario QA. Se eliminan `--level1` y `--link-in-sheet`.
- **Token de Google Sheets.** Nueva fuente principal: `SHEETS_ACCESS_TOKEN` en el `.env` del workspace, pegado desde el OAuth Playground (dura 60 minutos). Si venció, los scripts salen con código `6` y dicen qué pegar. También se admite un cliente OAuth propio (`SHEETS_CLIENT_ID`, `SHEETS_CLIENT_SECRET`, `SHEETS_REFRESH_TOKEN`) con renovación automática, y la sesión de gcloud sigue funcionando. Regla nueva en `AGENTS.md`: el asistente pide el token fresco antes de cada publicación o cambio de estado.
- **`qa-backlog`:** el filtro por defecto pasa a `Reportada,En Revisión,En curso` ("Pendiente" no existe en la planilla) y la tabla muestra el inicio de Comentario QA.

### Corregido

- **Confirmación humana con `input()`** (y un tiempo límite en un hilo) en lugar de `msvcrt.kbhit()`. Funciona en PowerShell, CMD, Windows Terminal y Git Bash. El bloqueo a asistentes y el registro en `Reportes/.publicaciones.log` siguen igual.
- **La carpeta del kit nunca se toma como workspace**, aunque contenga un `Reportes/` dejado por una corrida anterior. Antes, al arrancar dentro del kit, los reportes y el `.env` del workspace se buscaban en el lugar equivocado.
- **Corridas E2E:** `new_run.py` copia el bloque de Maya en las secciones 2, 3, 4, 5, 7 y 8 con su prefijo, así que el documento nuevo solo falla la validación por contenido vacío, no por estructura; la plantilla de 6.a incluye la línea de consulta con `--status all`; `validate_run.py` ignora los comentarios HTML de la plantilla.
- `report_lint.py` reconoce el reporte técnico por su encabezado, no solo por el sufijo del archivo.
- `QA_KIT_REPOS` admite subcarpetas (por ejemplo `ia-factory/ai-factory-core`).

### Cómo actualizar

1. Actualiza el kit (`qa-update`) y abre un chat nuevo con `qa-welcome`.
2. En el `.env` del workspace: quita `NOTION_TOKEN`; agrega `SHEETS_ACCESS_TOKEN=` cuando vayas a publicar (o el cliente OAuth propio); si tus repos no están en la raíz, `QA_KIT_REPOS` con sus rutas relativas.
3. `report-bug`: el comando ahora recibe los dos archivos markdown, no título/descripción/gravedad. `qa-finish` y `qa-rejection`: sin 5.º argumento. `qa-amplify`: sin `--level1` ni `--link-in-sheet`.
4. Los scripts improvisados de `Reportes/publicar/` ya no hacen falta.

---

## [1.7.1] — 2026-09-30 · `qa-update` también actualiza el plugin de Claude Code

### Por qué

Claude Code instala el kit desde su propio clon del repo (el "marketplace" `iafactory-qa`) y no lo refresca solo. `qa-update` hacía `git pull` en la copia del workspace, así que el plugin instalado se quedaba en una versión vieja aunque el workspace estuviera al día: con la 1.7.0 publicada, el plugin seguía en 1.5.1. Además, al correr desde el plugin instalado (una carpeta sin git), `--check` fallaba.

### Corregido

- **`qa-update` detecta y actualiza el plugin de Claude Code:** lee la versión instalada, consulta la disponible con `git fetch` en el clon del marketplace (el repo es privado) y, con `--update`, corre `claude plugin marketplace update` y `claude plugin update`. Busca `claude` en el PATH o el que trae la app de escritorio; si no lo encuentra, imprime los comandos.
- **`--check` funciona desde el plugin instalado** (sin git): informa el estado del plugin en vez de fallar.

### Cómo actualizar (solo esta vez)

El `qa-update` que tienes instalado todavía no sabe actualizar el plugin, así que esta vez corre en tu terminal:

```bash
claude plugin marketplace update iafactory-qa
claude plugin update iafactory-qa-kit@iafactory-qa
```

Si `claude` no está en tu PATH, usa el que trae la app de escritorio: `%APPDATA%\Claude\claude-code\<versión>\claude.exe` en Windows. Después reinicia Claude Code. Desde esta versión, `qa-update` lo hace por su cuenta.

---

## [1.7.0] — 2026-09-30 · La persona decide qué es un ticket

### Por qué

En una corrida E2E salieron 31 tickets de una vez. Revisando el chat, el asistente había descartado hallazgos "que consideró comportamiento normal", la lista final la armó él y se aprobó con una sola confirmación para todo el lote; los 31 técnicos se escribieron en un solo proceso en segundo plano. Varios eran síntomas de una misma causa y otros eran de plataforma sin relación con la corrida. Además, el análisis de calidad de reportes mostró que al equipo le faltan sobre todo los pasos para reproducir, la versión desplegada y la causa con archivo y línea. Esta versión deja la decisión en manos de la persona y da una estructura base a cada reporte.

### Nuevo

- **Confirmación humana en la terminal** para tickets nuevos (`report-bug`), cierres (`qa-finish`) y rechazos (`qa-rejection`). La persona ejecuta el último comando en una terminal abierta por ella, ve qué se va a publicar y escribe el AF-XXX para confirmar. Desde un asistente el script sale con código `5` sin esperar ni escribir nada. Cada publicación confirmada queda en `Reportes/.publicaciones.log`. Las ampliaciones siguen con el código del dry-run.
  *Límite conocido:* detiene errores y automatizaciones apuradas; no a alguien que quiera saltárselo a propósito.
- **Plantillas de reporte** en `report-bug/templates/` (ejecutivo y técnico) y **`report_lint.py`**, que revisa su estructura: síntoma observado contra esperado, impacto, pasos numerados, entorno y versión, evidencia etiquetada, causa raíz con `archivo:línea` (o "Causa no identificada"), corrección y lo no verificado. `notion_mcp_publisher.py` no publica con errores de estructura.
- **Corridas E2E (a partir del método de Elias Sanchez):**
  - §9.5 coherencia entre agentes: la misma decisión según cada agente y el código;
  - §9.6 documentación publicada, revisada en su destino real al cierre;
  - §9.7 bloqueos y fallas de la corrida con su causa en logs o código;
  - §9.8 fuera de alcance: problemas de plataforma que no afectaron la corrida, sin ticket automático.

### Cómo actualizar

1. Actualiza el kit (`qa-update`, o `git pull` en el submódulo) y abre un chat nuevo con `qa-welcome`.
2. Para publicar un ticket nuevo, cerrar o rechazar: el asistente te entrega el comando con `--confirm`; ejecútalo **tú** en una terminal abierta por ti (no la del asistente) y escribe el AF-XXX cuando lo pida.
3. Escribe los reportes nuevos desde las plantillas de `report-bug/templates/`; los reportes con el formato anterior no pasan `report_lint.py`.
4. En tu workspace, agrega `Reportes/.publicaciones.log` al `.gitignore`: es el registro local de tus confirmaciones.

### Cambiado

- **§9.2 de la corrida:** una fila por causa (agrupa los síntomas), con la propuesta del asistente y las columnas **Decisión**, **Motivo** y **Decidido por**, que llena la persona. `validate_run.py` falla si falta la decisión, si un descarte no tiene motivo o si "Decidido por" es el asistente.
- **Regla en `AGENTS.md`, `report-bug` y `qa-e2e-corrida`:** si la persona delega ("descarta los que consideres"), el asistente devuelve su propuesta y espera. Un ticket por causa, no por síntoma.

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
