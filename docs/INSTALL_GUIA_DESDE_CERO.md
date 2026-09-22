# 📘 Guía Maestra de Instalación e Integración desde Cero
## Plugin: `iafactory-qa-kit`
**Compatibilidad Universal:** Windows / macOS / Linux  
**Asistentes Soportados:** Antigravity, Claude Code, Cursor, Windsurf, Aider, GitHub Copilot Workspace, Terminal CLI.

---

## 📑 Tabla de Contenidos
1. [Requisitos Previos del Sistema](#1-requisitos-previos-del-sistema)
2. [Instalación y Setup en 3 Pasos](#2-instalación-y-setup-en-3-pasos)
3. [Configuración de Autenticación y Secretos](#3-configuración-de-autenticación-y-secretos)
4. [Integración Multi-IA](#4-integración-multi-ia)
   - [Google Antigravity](#41-google-antigravity)
   - [Claude Code](#42-claude-code)
   - [Cursor & Windsurf](#43-cursor--windsurf)
   - [Terminal / CI / Pipelines](#44-terminal--ci--pipelines)
5. [Comprobación y Verificación Rápida](#5-comprobación-y-verificación-rápida)

---

## 1. Requisitos Previos del Sistema

En un computador nuevo, asegúrate de contar con estas cuatro herramientas base instaladas:

| Herramienta | Versión Mínima | Propósito | Enlace de Descarga |
| :--- | :--- | :--- | :--- |
| **Python** | `>= 3.8` | Motor de ejecución de las skills del plugin | [python.org](https://www.python.org/downloads/) |
| **Node.js & npx** | `>= 18.0 (LTS)` | Servidor MCP de Notion (`npx notion-mcp-server`) | [nodejs.org](https://nodejs.org/) |
| **Git** | `>= 2.30` | Inspección de diffs, historial y versionamiento | [git-scm.com](https://git-scm.com/) |
| **Google Cloud SDK (`gcloud`)** | Última versión | Autenticación OAuth2 contra Google Sheets API | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |

---

## 2. Instalación y Setup en 3 Pasos

### Paso 1: Ubicación del Plugin
Coloca la carpeta `iafactory-qa-kit` dentro de la carpeta de plugins de tu workspace:
```text
tu-workspace/
├── .agents/
│   └── plugins/
│       └── iafactory-qa-kit/    <-- Aquí
```

### Paso 2: Instalar Dependencias Opcionales de Python (si aplica)
El núcleo de scripts utiliza la **biblioteca estándar de Python** para máxima portabilidad sin dependencias obligatorias. Sin embargo, para desarrollo y linters:
```bash
pip install -r .agents/plugins/iafactory-qa-kit/requirements.txt
```

### Paso 3: Ejecutar el Asistente de Setup
En la raíz de la carpeta del plugin ejecuta:
```bash
python .agents/plugins/iafactory-qa-kit/setup.py
```
Este script validará automáticamente que todas las herramientas estén en el `PATH`, creará tu `.env` a partir de la plantilla y correrá un chequeo inicial de puertos.

---

## 3. Configuración de Autenticación y Secretos

El plugin requiere acceso a **Google Sheets** y a **Notion**:

### A. Autenticación en Google Cloud (Google Sheets API)
Inicia sesión en la consola con tu cuenta corporativa autorizada:
```bash
gcloud auth login --enable-gdrive-access
```
*Verificación:* Ejecuta `gcloud auth print-access-token`. Si devuelve un token largo alfanumérico, la conexión con Google Sheets está lista.

### B. Configuración del Token de Notion
1. Obtén tu token de integración interna en [Notion Developers](https://www.notion.so/my-integrations).
2. Asegúrate de que la integración tenga permisos sobre la página contenedora de QA (`MDs pruebas`).
3. Abre el archivo `.env` en la raíz del workspace (o dentro del plugin) y asigna tu token:
   ```env
   NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   USER_NAME=Tu Nombre y Apellido
   ```

---

## 4. Integración Multi-IA

El plugin está diseñado bajo la **especificación abierta de Agent Skills**, permitiendo que cualquier modelo o agente lo adopte instantáneamente:

### 4.1 Google Antigravity
* **Detección Automática:** Antigravity detecta por diseño cualquier plugin alojado en `.agents/plugins/<nombre>/`.
* **Carga Progresiva:** Las reglas en `rules/AGENTS.md` se aplican automáticamente, y las 5 skills (`qa-backlog`, `qa-code-audit`, `qa-preflight`, `qa-finish`, `qa-rejection`) quedan disponibles para el agente según las necesite.

### 4.2 Claude Code
Para usar este kit con Claude Code:
1. En tu archivo `CLAUDE.md` o en las instrucciones del proyecto, agrega una referencia al plugin:
   ```markdown
   Para tareas de QA y revisión de defectos, utiliza los scripts empaquetados en:
   .agents/plugins/iafactory-qa-kit/skills/
   ```
2. Claude ejecutará de forma directa los comandos CLI (`fetch_issues.py`, `audit_changes.py`, etc.) vía `Bash`.

### 4.3 Cursor & Windsurf
1. Agrega a tu `.cursorrules` o `.windsurfrules`:
   ```markdown
   Always follow QA protocols from .agents/plugins/iafactory-qa-kit/rules/AGENTS.md.
   When asked to inspect or close issues, execute the corresponding CLI scripts under:
   .agents/plugins/iafactory-qa-kit/skills/<skill-name>/scripts/
   ```

### 4.4 Terminal / CI / Pipelines
Cualquier desarrollador o pipeline de CI/CD puede utilizar las herramientas directamente desde la consola sin depender de una IA:
```bash
# Ver backlog en formato Markdown o JSON
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente"

# Diagnóstico de puertos de túnel en 500 ms
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py
```

---

## 5. Comprobación y Verificación Rápida

Para comprobar que todo está 100% operativo en tu nuevo computador:

```bash
# 1. ¿Responde Google Sheets?
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --limit 3

# 2. ¿Responde el Pre-flight Check?
python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py
```

Si ambos comandos devuelven salidas limpias con checkmarks verdes o tablas formateadas, **tu entorno está completamente configurado y listo para operar QA de alto nivel.**
