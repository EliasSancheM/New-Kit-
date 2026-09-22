# 📦 Plugin: IAFactory QA Kit (`iafactory-qa-kit`)
### Kit Autónomo, Portable y Multi-IA para Aseguramiento de Calidad y Observabilidad

El plugin **`iafactory-qa-kit`** empaqueta en una única unidad distribuible todo el ciclo de vida de defectos, sincronización bidireccional (Google Sheets + Notion + Obsidian Vault), auditoría de cambios Git y chequeos de conectividad para **IAFactory**.

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
│   ├── INSTALL_GUIA_DESDE_CERO.md  # Guía de onboarding paso a paso en computadores nuevos
│   └── FAST_QA_WORKFLOW.md         # Protocolo de QA acelerado (Batching, tests quirúrgicos, subagentes)
└── skills/
    ├── shared/                 # Utilidades comunes (Tokens, dynamic mapping, Obsidian, Notion)
    │   └── utils.py
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
    └── qa-rejection/           # Rechazo formal de QA (MD + Warning Banner + 'Rechazada por QA')
        ├── SKILL.md
        └── scripts/qa_rejection_publisher.py
```

---

## 🚀 Inicio Rápido (Quickstart)

### 1. Setup en computador nuevo
```bash
python setup.py
```

### 2. Comandos Principales para Asistentes de IA y Desarrolladores

```bash
# 1. Consultar Backlog activo (Issues en Revisión o Pendientes):
python skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente,En Revisión"

# 2. Auditar cambios de código de un commit o issue:
python skills/qa-code-audit/scripts/audit_changes.py --commit "<hash>"

# 3. Diagnóstico de túnel IAP antes de probar en vivo:
python skills/qa-preflight/scripts/check_env.py

# 4. Reportar un nuevo defecto:
python skills/report-bug/scripts/gsheets_updater.py "<Título>" "<Descripción>" "<Gravedad>"

# 5. Aceptar y cerrar defecto verificado:
python skills/qa-finish/scripts/qa_finish_publisher.py "AF-XXX" "<Resumen>" "<Evidencia>"

# 6. Rechazar defecto fallido:
python skills/qa-rejection/scripts/qa_rejection_publisher.py "AF-XXX" "<Motivo>" "<Detalle_Falla>" "<Cambios_Encontrados>"
```

Para instrucciones detalladas de integración con Claude Code, Cursor o Windsurf, consulta [INSTALL_GUIA_DESDE_CERO.md](docs/INSTALL_GUIA_DESDE_CERO.md).
