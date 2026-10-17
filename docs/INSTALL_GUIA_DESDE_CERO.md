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

En un computador nuevo, asegúrate de contar con estas herramientas base instaladas:

| Herramienta | Versión Mínima | Propósito | Enlace de Descarga |
| :--- | :--- | :--- | :--- |
| **Python** | `>= 3.8` | Motor de ejecución de las skills del plugin | [python.org](https://www.python.org/downloads/) |
| **Git** | `>= 2.30` | Inspección de diffs, historial y versionamiento | [git-scm.com](https://git-scm.com/) |
| **Google Cloud SDK (`gcloud`)** | Última versión | Túneles IAP a las VMs; también sirve de token para Google Sheets si no pegas uno | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) |

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

El plugin solo escribe en **Google Sheets**. Necesita un token OAuth con el scope `spreadsheets`; el kit prueba estas fuentes en orden:

### A. Token pegado desde el OAuth Playground (el que usa el equipo)
1. Entra a [developers.google.com/oauthplayground](https://developers.google.com/oauthplayground), autoriza `https://www.googleapis.com/auth/spreadsheets` y copia el `access_token` (`ya29...`).
2. Pégalo en el `.env` de la **raíz del workspace**:
   ```env
   SHEETS_ACCESS_TOKEN=ya29.xxxxxxxx
   USER_NAME=Tu Nombre y Apellido
   ```
3. Dura 60 minutos. Cuando vence, los scripts salen con código `6` y el asistente te pide uno nuevo. Nunca pegues el token en el chat.

### B. Cliente OAuth propio (sin pegar nada cada hora)
Si creas un cliente OAuth en Google Cloud Console y lo autorizas una vez en el Playground, guarda en el `.env` `SHEETS_CLIENT_ID`, `SHEETS_CLIENT_SECRET` y `SHEETS_REFRESH_TOKEN`: el kit renueva el token solo.

### C. Sesión de gcloud
```bash
gcloud auth login --enable-gdrive-access
```
*Verificación:* `python .agents/plugins/iafactory-qa-kit/skills/qa-preflight/scripts/check_env.py` muestra qué fuente de token está activa.

---

## 4. Integración Multi-IA

El plugin está diseñado bajo la **especificación abierta de Agent Skills**, permitiendo que cualquier modelo o agente lo adopte instantáneamente:

### 4.1 Google Antigravity
* **Detección Automática:** Antigravity detecta por diseño cualquier plugin alojado en `.agents/plugins/<nombre>/`.
* **Carga Progresiva:** Las reglas en `rules/AGENTS.md` se aplican automáticamente, y las skills (`qa-backlog`, `qa-code-audit`, `qa-preflight`, `report-bug`, `qa-finish`, `qa-rejection`, `qa-amplify`, `qa-e2e-corrida`) quedan disponibles para el agente según las necesite.

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
python .agents/plugins/iafactory-qa-kit/skills/qa-backlog/scripts/fetch_issues.py --status "En Revisión"

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
