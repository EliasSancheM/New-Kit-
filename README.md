# 📦 Plugin: IAFactory QA Kit (`iafactory-qa-kit`)
### Kit Autónomo, Portable y Multi-IA para Aseguramiento de Calidad y Observabilidad

El plugin **`iafactory-qa-kit`** empaqueta en una única unidad distribuible todo el ciclo de vida de defectos, publicación en Google Sheets y Notion (con espejo local opcional en Obsidian), auditoría de cambios Git y chequeos de conectividad para **IAFactory**.

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
├── mcp_config.json             # Configuración del servidor MCP de Notion
├── setup.py                    # Asistente interactivo de instalación y diagnóstico
├── requirements.txt            # Dependencias opcionales de desarrollo (ruff, mypy, pytest)
├── .env.example                # Plantilla de variables de entorno (Tokens, IDs)
├── rules/
│   └── AGENTS.md               # Reglas de conducta, seguridad y gobernanza para cualquier IA
├── docs/
│   ├── METODOLOGIA_QA_IAFACTORY.md # Marco metodológico, dualidad de verdad y ciclo de defectos
│   ├── INSTALL_GUIA_DESDE_CERO.md  # Guía de onboarding paso a paso en computadores nuevos
│   └── FAST_QA_WORKFLOW.md         # Protocolo de QA acelerado (Batching, tests quirúrgicos, subagentes)
└── skills/
    ├── shared/                 # Utilidades comunes (Tokens, dynamic mapping, Obsidian, Notion)
    │   └── utils.py
    ├── qa-help/                # [NUEVO] Catálogo interactivo de skills, scripts, sintaxis y flags
    │   ├── SKILL.md
    │   └── scripts/help.py
    ├── qa-welcome/             # Onboarding guiado y autodiagnóstico de bienvenida
    │   ├── SKILL.md
    │   └── scripts/welcome.py
    ├── qa-backlog/             # Consulta y filtrado de issues en Google Sheets
    │   ├── SKILL.md
    │   └── scripts/fetch_issues.py
    ├── qa-code-audit/          # Agregador de diffs, status y runner quirúrgico rápido
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── audit_changes.py
    │       └── fast_test_runner.py       # [ACELERADO] Vitest / Python targeted runner
    ├── qa-preflight/           # Chequeo de túneles IAP e inspección remota en lote
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── check_env.py              # Diagnóstico local de puertos y credenciales
    │       └── remote_batch_inspect.py   # [ACELERADO] Inspección consolidada en 1 viaje a la VM
    ├── report-bug/             # Reporte formal de nuevo defecto (MD + Notion + Sheets)
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── gsheets_updater.py
    │       └── notion_mcp_publisher.py
    ├── qa-finish/              # Aprobación y cierre formal (MD + Notion + 'Finalizada')
    │   ├── SKILL.md
    │   └── scripts/qa_finish_publisher.py
    ├── qa-rejection/           # Rechazo formal de QA (MD + Warning Banner + 'Rechazada por QA')
    │   ├── SKILL.md
    │   └── scripts/qa_rejection_publisher.py
    └── qa-update/              # Verificación de versiones y auto-actualización del plugin
        ├── SKILL.md
        └── scripts/update_plugin.py
```

---

## ⚡ Instalación

Las skills son carpetas con un `SKILL.md` y scripts en Python (solo biblioteca estándar), así que funcionan con cualquier asistente. En los `SKILL.md`, `<KIT>` significa la carpeta raíz del kit.

### Claude Code (recomendado para Claude)

Como plugin, desde una sesión interactiva de Claude Code:

```
/plugin marketplace add AlonsoSalasApiux/iafactory-qa-kit
/plugin install iafactory-qa-kit@iafactory-qa
```

Alternativa sin gestor de plugins: clona el kit en tu workspace y enlaza cada carpeta de `skills/` (menos `shared/`) dentro de `.claude/skills/` del workspace.

### Otros asistentes (Antigravity, Cursor, Windsurf, Codex...)

Clona el kit en tu workspace (por ejemplo, en `.agents/plugins/iafactory-qa-kit`) y agrega a las instrucciones del asistente (`AGENTS.md`, `.cursorrules`, etc.) una referencia a `rules/AGENTS.md` y a `skills/*/SKILL.md`. Prompt de instalación:

> *"Instala el IAFactory QA Kit desde `https://github.com/AlonsoSalasApiux/iafactory-qa-kit.git` en `.agents/plugins/iafactory-qa-kit`, ejecuta `python .agents/plugins/iafactory-qa-kit/skills/qa-welcome/scripts/welcome.py` y preséntame el estado del entorno."*

### Configuración

1. Copia `.env.example` a `.env` y completa `NOTION_TOKEN` y `USER_NAME`.
2. Ejecuta `gcloud auth login --enable-gdrive-access`.
3. **VMs (dev, qa, team-devs):** vienen definidas en `environments.json`. Usa `--env <nombre>` en los scripts de `qa-preflight`, o `QA_KIT_ENV` en el `.env` para fijar la VM por defecto.
4. **Si gcloud o los scripts fallan con `CERTIFICATE_VERIFY_FAILED`** (antivirus o proxy que intercepta TLS): ejecuta `python skills/qa-preflight/scripts/build_ca_bundle.py` y agrega al `.env` la línea que imprime.
5. **Obsidian (opcional):** `QA_KIT_OBSIDIAN=1` activa el espejo local `docs/vault/defectos/`.
6. **Si tu workspace no tiene la estructura de IAFactory:** define `QA_KIT_REPOS` (carpetas de los repos de producto) y, si la autodetección falla, `WORKSPACE_ROOT`. También puedes crear un archivo vacío `.qa-kit-root` en la raíz de tu workspace para marcarla.

### Seguridad al publicar

`report-bug`, `qa-finish` y `qa-rejection` escriben en Notion y Google Sheets compartidos. Todos aceptan `--dry-run`, que muestra lo que se escribiría sin tocar nada. Los `SKILL.md` obligan al asistente a hacer dry-run y pedir confirmación antes de publicar. Código de salida `3` = éxito parcial (por ejemplo, Notion publicado pero Sheets no actualizado).

---

## 🚀 Inicio Rápido (Quickstart)

### 1. Ayuda y Catálogo de Flags
```bash
# Ver todos los scripts, sintaxis y flags disponibles
python skills/qa-help/scripts/help.py

# Filtrar ayuda por skill puntual
python skills/qa-help/scripts/help.py --skill qa-code-audit
```

### 2. Setup y Bienvenida Interactiva
```bash
# Diagnóstico guiado con bienvenida
python skills/qa-welcome/scripts/welcome.py
```

### 3. Verificación de Actualizaciones
```bash
# Comprobar si hay una versión más reciente del plugin
python skills/qa-update/scripts/update_plugin.py --check

# Actualizar el plugin a la última versión disponible
python skills/qa-update/scripts/update_plugin.py --update
```

### 4. Comandos Principales para Asistentes de IA y Desarrolladores

```bash
# 1. Consultar Backlog activo (Issues en Revisión o Pendientes):
python skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente,En Revisión"

# 2. Auditar cambios de código de un commit o issue:
python skills/qa-code-audit/scripts/audit_changes.py --issue "AF-XXX"

# 3. Diagnóstico de túnel IAP antes de probar en vivo:
python skills/qa-preflight/scripts/check_env.py

# 4. Reportar un nuevo defecto:
python skills/report-bug/scripts/gsheets_updater.py "<Título>" "<Descripción>" "<Gravedad>"

# 5. Aceptar y cerrar defecto verificado:
python skills/qa-finish/scripts/qa_finish_publisher.py "AF-XXX" "<Resumen>" "<Evidencia>"

# 6. Rechazar defecto fallido:
python skills/qa-rejection/scripts/qa_rejection_publisher.py "AF-XXX" "<Motivo>" "<Detalle_Falla>" "<Cambios_Encontrados>"
```

Para instrucciones detalladas de integración con Claude Code, Cursor o Windsurf, consulta [INSTALL_GUIA_DESDE_CERO.md](docs/INSTALL_GUIA_DESDE_CERO.md). Para la metodología completa de testing, consulta [METODOLOGIA_QA_IAFACTORY.md](docs/METODOLOGIA_QA_IAFACTORY.md).

