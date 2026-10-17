# 📦 Plugin: IAFactory QA Kit (`iafactory-qa-kit`)
### Kit Autónomo, Portable y Multi-IA para Aseguramiento de Calidad y Observabilidad

El plugin **`iafactory-qa-kit`** empaqueta en una única unidad distribuible todo el ciclo de vida de defectos, publicación en Google Sheets, auditoría de cambios Git, corridas E2E y chequeos de conectividad para **IAFactory**.

---

## 🆕 Últimas mejoras — v1.8.0 (2026-10-17)

- **Solo Google Sheets.** Notion queda fuera: el reporte completo de cada defecto (ejecutivo + técnico, cierre o rechazo, ampliaciones) vive en la columna **Comentario QA** de su fila. Los markdown de `Reportes/` son tu copia local.
- **Publicar en un paso.** `report-bug` recibe los dos reportes markdown y escribe la fila; no se copian título ni descripción ni se traslada ninguna URL.
- **Token de Sheets pegado.** `SHEETS_ACCESS_TOKEN` en el `.env` del workspace (OAuth Playground, dura 60 min). Cuando vence, los scripts salen con código `6` y el asistente te pide uno nuevo. Sigue funcionando la sesión de gcloud, y se admite un cliente OAuth propio con renovación automática.
- **Corregido:** la confirmación humana ahora usa `input()` (en Windows no recibía teclas); la carpeta del kit ya no se toma como workspace; `new_run.py` genera el documento de corrida con todas las secciones por agente.

Detalle, motivos y cómo actualizar: [docs/mejoras/CHANGELOG.md](docs/mejoras/CHANGELOG.md).

---

## 🌟 Características Principales

* 🌐 **Multiplataforma:** Ejecutable de forma transparente en **Windows**, **macOS** y **Linux**.
* 🤖 **Universal Multi-IA:** Compatible de fábrica con **Google Antigravity**, **Claude Code**, **Cursor**, **Windsurf**, **GitHub Copilot** y terminales CLI estándar.
* ⚡ **Zero External Python Dependencies:** El núcleo de scripts opera al 100% sobre la biblioteca estándar de Python (`urllib`, `json`, `subprocess`, `ssl`).
* 🔒 **Gobernanza Rigurosa:** Reglas HHH (Honest 36%, Helpful 36%, Harmless 28%), cero alucinación, protección estricta contra commits automáticos no autorizados y banners de advertencia en reportes técnicos.

---

## 📂 Estructura del Plugin

```text
iafactory-qa-kit/
├── plugin.json                 # Manifiesto oficial del plugin
├── setup.py                    # Asistente interactivo de instalación y diagnóstico
├── requirements.txt            # Dependencias opcionales de desarrollo (ruff, mypy, pytest)
├── .env.example                # Plantilla de variables de entorno (token de Sheets, repos, E2E)
├── environments.json           # VMs del equipo (dev, qa, team-devs)
├── rules/
│   └── AGENTS.md               # Reglas de conducta, seguridad y gobernanza para cualquier IA
├── docs/
│   ├── mejoras/CHANGELOG.md        # Registro de mejoras por versión: qué cambió, cómo y por qué
│   ├── METODOLOGIA_QA_IAFACTORY.md # Marco metodológico, fuentes de verdad y ciclo de defectos
│   ├── INSTALL_GUIA_DESDE_CERO.md  # Guía de onboarding paso a paso en computadores nuevos
│   └── FAST_QA_WORKFLOW.md         # Protocolo de QA acelerado (Batching, tests quirúrgicos, subagentes)
└── skills/
    ├── shared/                 # Utilidades comunes (token de Sheets, mapeo de columnas, candados)
    │   └── utils.py
    ├── qa-help/                # Catálogo interactivo de skills, scripts, sintaxis y flags
    ├── qa-welcome/             # Onboarding guiado, autodiagnóstico y carga de reglas
    ├── qa-backlog/             # Consulta y filtrado de issues en Google Sheets
    ├── qa-code-audit/          # Agregador de diffs, status y runner quirúrgico rápido
    ├── qa-preflight/           # Chequeo de túneles IAP e inspección remota en lote
    ├── report-bug/             # Reporte formal de nuevo defecto (plantillas + lint + fila en Sheets)
    ├── qa-finish/              # Aprobación y cierre formal ('Finalizada')
    ├── qa-rejection/           # Rechazo formal de QA ('Rechazada por QA')
    ├── qa-amplify/             # Evidencia adicional sobre un defecto existente (sin cambiar estado)
    ├── qa-e2e-corrida/         # Planificación, documentación y validación de corridas E2E
    └── qa-update/              # Verificación de versiones y auto-actualización del plugin
```

---

## ⚡ Instalación

Las skills son carpetas con un `SKILL.md` y scripts en Python (solo biblioteca estándar), así que funcionan con cualquier asistente. En los `SKILL.md`, `<KIT>` significa la carpeta raíz del kit.

### Claude Code (recomendado para Claude)

Como plugin, desde una sesión interactiva de Claude Code, apuntando a la copia local del kit (el repo se mantiene en local, sin remoto):

```
/plugin marketplace add C:/Users/<usuario>/Desktop/Repositorios/.agents/plugins/iafactory-qa-kit
/plugin install iafactory-qa-kit@iafactory-qa
```

Después de cada commit local nuevo: `claude plugin marketplace update iafactory-qa` y `claude plugin update iafactory-qa-kit@iafactory-qa`, y reinicia Claude Code.

Alternativa sin gestor de plugins: clona el kit en tu workspace y enlaza cada carpeta de `skills/` (menos `shared/`) dentro de `.claude/skills/` del workspace.

### Otros asistentes (Antigravity, Cursor, Windsurf, Codex...)

Clona el kit en tu workspace (por ejemplo, en `.agents/plugins/iafactory-qa-kit`) y agrega a las instrucciones del asistente (`AGENTS.md`, `.cursorrules`, etc.) una referencia a `rules/AGENTS.md` y a `skills/*/SKILL.md`. Prompt de instalación:

> *"Instala el IAFactory QA Kit (copia local del repo) en `.agents/plugins/iafactory-qa-kit`, ejecuta `python .agents/plugins/iafactory-qa-kit/skills/qa-welcome/scripts/welcome.py` y preséntame el estado del entorno."*

### Configuración

1. Copia `.env.example` a `.env` **en la raíz de tu workspace** y completa `USER_NAME`.
2. **Token de Google Sheets** (ver `.env.example`): pega `SHEETS_ACCESS_TOKEN` del OAuth Playground cuando vayas a publicar, o configura un cliente OAuth propio, o ejecuta `gcloud auth login --enable-gdrive-access`.
3. **Repos de producto:** si no están en la raíz del workspace, `QA_KIT_REPOS=ia-factory/ai-factory-core,...`.
4. **VMs (dev, qa, team-devs):** vienen definidas en `environments.json`. Usa `--env <nombre>` en los scripts de `qa-preflight`, o `QA_KIT_ENV` en el `.env` para fijar la VM por defecto.
5. **Si gcloud o los scripts fallan con `CERTIFICATE_VERIFY_FAILED`** (antivirus o proxy que intercepta TLS): ejecuta `python skills/qa-preflight/scripts/build_ca_bundle.py` y agrega al `.env` la línea que imprime.
6. **Corridas E2E:** `QA_KIT_E2E_DIR` fija dónde se guardan los documentos (por defecto `Reportes/E2E/` del workspace).
7. **Obsidian (opcional):** `QA_KIT_OBSIDIAN=1` activa el espejo local `docs/vault/defectos/`.

### Seguridad al publicar

`report-bug`, `qa-finish`, `qa-rejection` y `qa-amplify` escriben en la planilla compartida. Todos aceptan `--dry-run`, que muestra lo que se escribiría sin tocar nada e imprime un `confirm_code`. La publicación real exige `--confirm <confirm_code>` del dry-run del mismo contenido; sin él, el script sale con código `4` sin escribir. Tickets nuevos, cierres y rechazos se confirman además **en la terminal de la persona**, escribiendo el AF-XXX (desde un asistente, código `5`). `qa-finish` y `qa-rejection` exigen `--build` con la versión probada. Código `6` = falta el token de Sheets o venció.

---

## 🚀 Inicio Rápido (Quickstart)

El kit está pensado para usarse **conversando con tu asistente de IA**, no ejecutando scripts a mano. Tú le dices qué necesitas en lenguaje natural; el asistente elige la skill, corre sus scripts y te muestra el resultado. Los scripts y sus flags están documentados en cada `SKILL.md` y en `qa-help`, pero no necesitas memorizarlos.

### 1. Empieza cada chat de QA con `qa-welcome`

Pídele: *"Inicia el QA Kit"* o *"prepárate para QA"*. El asistente revisa tu entorno (Python, token de Sheets, repos) y carga las reglas del kit, que rigen toda la conversación: honestidad primero, dry-run y confirmación antes de escribir en la planilla, sin commits ni cambios en las VMs por iniciativa propia. Si falta configuración, te dirá qué hacer.

En Claude Code con el plugin instalado, el hook de inicio de sesión ya carga las reglas; igual conviene pedir el diagnóstico la primera vez.

### 2. Qué pedir y qué skill se usa

| Quieres… | Pídele algo como… | Skill |
|---|---|---|
| Ver qué hay pendiente | *"¿Qué defectos hay en revisión?"*, *"muéstrame los issues de Fabio"*, *"¿en qué estado está AF-259?"* | `qa-backlog` |
| Saber si el entorno está listo | *"¿Está arriba QA?"*, *"abre el túnel a dev"*, *"el túnel no conecta"* | `qa-preflight` |
| Revisar qué cambió un desarrollador | *"Revisa el fix de AF-231"*, *"¿qué cambió en el commit 2d6a677?"* | `qa-code-audit` |
| Registrar un bug nuevo | *"Encontré un bug: …, repórtalo"* | `report-bug` |
| Cerrar un ticket cuyo fix pasó | *"AF-228 pasó la prueba, ciérralo"* | `qa-finish` |
| Rechazar un fix que sigue fallando | *"AF-228 sigue fallando, recházalo"* | `qa-rejection` |
| Sumar evidencia a un ticket sin cambiar su estado | *"Esto ya estaba reportado en AF-259, agrégale la evidencia"*, *"amplía estos tickets con lo que vimos en la corrida"* | `qa-amplify` |
| Probar el pipeline completo con un proyecto piloto | *"Vamos a hacer una corrida E2E"*, *"audita la corrida del proyecto <ID>"* | `qa-e2e-corrida` |
| Saber qué puede hacer el kit | *"¿Qué puedo hacer con el kit?"*, *"¿qué flags tiene el backlog?"* | `qa-help` |
| Actualizar el kit | *"¿Está al día el kit?"*, *"actualízalo"* | `qa-update` |

### 3. Flujo típico para verificar un ticket

1. **Backlog:** *"¿Qué hay en revisión?"* → eliges un ticket. Su reporte completo está en Comentario QA.
2. **Entorno:** *"¿Está listo QA para probar?"* → el asistente revisa túneles y contenedores (solo lectura).
3. **Código:** *"Revisa qué cambió en AF-XXX"* → ves los commits y el diff.
4. **Prueba:** la haces tú, o le pides al asistente que te guíe con la plantilla de 4 fases de `rules/AGENTS.md`.
5. **Resultado:** *"pasó, ciérralo"* (`qa-finish`), *"sigue fallando, recházalo"* (`qa-rejection`), o *"no se está re-verificando, solo agrégale esta evidencia"* (`qa-amplify`). Si encontraste algo distinto: *"repórtalo como bug nuevo"* (`report-bug`). Antes del comando final, el asistente te pide el token de Sheets fresco: lo pegas en el `.env` y ejecutas el comando en tu terminal.

### 4. Corridas E2E

Pídele *"vamos a hacer una corrida E2E de <proyecto>"*. El asistente (`qa-e2e-corrida`):

1. **Antes:** redacta contigo el documento del proyecto (requerimientos, reglas de negocio, pantallas, criterios de aceptación) y, si quieres, un plan de qué issues pendientes revisar aprovechando la corrida (puede filtrarlos por responsable).
2. **Durante:** documenta cada agente en un único archivo creado por `new_run.py`, ya con todas las secciones: lo que funcionó, los hallazgos en limpio y, al final de cada sección, el contraste contra el Sheet en vivo.
3. **Cierre:** hallazgos consolidados con tu decisión fila por fila, discrepancias `Planificado | Agente | Documentación | Código`, `validate_run.py` sin errores, y luego te propone qué publicar: bugs nuevos con `report-bug`, duplicados y ampliaciones con `qa-amplify`, y tickets re-verificados con `qa-finish` o `qa-rejection`.

También sirve para auditar una corrida ya terminada: *"audita la corrida del proyecto <ID> en QA"*. El código que genera el agente Developer se evalúa solo como referencia de rendimiento; no se reporta como ticket. Los documentos quedan en `QA_KIT_E2E_DIR` (por defecto `Reportes/E2E/`).

### 5. Lo que el asistente nunca hace sin tu "sí"

- Escribir en Google Sheets: siempre te muestra antes un dry-run y te pide el token fresco.
- Hacer commit o push.
- Levantar, detener o reiniciar servicios en las VMs, o abrir túneles.

Para instrucciones detalladas de integración con Claude Code, Cursor o Windsurf, consulta [INSTALL_GUIA_DESDE_CERO.md](docs/INSTALL_GUIA_DESDE_CERO.md). Para la metodología completa de testing, consulta [METODOLOGIA_QA_IAFACTORY.md](docs/METODOLOGIA_QA_IAFACTORY.md). Si prefieres la terminal, `python skills/qa-help/scripts/help.py` lista todos los scripts y flags.
