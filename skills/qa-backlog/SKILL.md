---
name: qa-backlog
description: Consulta el backlog de defectos QA (AF-XXX) en la planilla de Google Sheets. Úsala cuando el usuario pregunte qué defectos hay pendientes, en revisión o reportados, pida el estado o detalle de un AF-XXX, quiera priorizar el backlog o diga "qué hay para probar". Solo lectura. / Read-only QA defect backlog lookup from Google Sheets.
---

# QA Backlog (`qa-backlog`)

Lee la planilla de defectos y devuelve los AF-XXX filtrados por estado o ID. **Es de solo lectura**: se puede ejecutar sin pedir confirmación.

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md` (por ejemplo `.agents/plugins/iafactory-qa-kit`). Ejecuta los comandos desde la raíz de tu workspace.

## Comandos

```bash
# Defectos activos (usa --json para procesarlos tú; muéstrale al usuario una tabla Markdown)
python <KIT>/skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente,En Revisión,Reportada" --json

# Detalle de un defecto concreto
python <KIT>/skills/qa-backlog/scripts/fetch_issues.py --id "AF-185" --json

# Limitar resultados
python <KIT>/skills/qa-backlog/scripts/fetch_issues.py --status "En Revisión" --limit 10
```

**El límite por defecto es 20 y corta sin más aviso que un mensaje en stderr.** Si vas a contar defectos, filtrar por responsable o afirmar que "solo hay N", usa siempre `--limit 500`. Para filtrar por persona usa `--responsable "<nombre>"` (coincidencia parcial, sin distinguir mayúsculas ni tildes; varias personas separadas por coma). El filtro se aplica antes del límite. Si nadie coincide, el script lista en stderr los responsables que sí existen: muéstraselos al usuario en vez de adivinar.

## Campos del JSON

`id`, `nombre`, `estado`, `gravedad` (Critica/Alta/Media/Baja), `responsable`, `descripcion`, `reportada_por`, `fecha_inicio`, `commits`, `id_commits`, `comentario_dev`, `comentario_qa` (suele contener la URL de Notion), `row` (fila en la hoja).

## Si falla

- **"No se detectó sesión activa de gcloud"** o lista vacía: falta el login de Google con acceso a Drive. Dile al usuario que ejecute `gcloud auth login --enable-gdrive-access`.
- **`CERTIFICATE_VERIFY_FAILED`**: hay un proxy o antivirus que re-firma certificados. Sugiere definir `QA_KIT_TLS_RELAX_STRICT=1` en el `.env` del kit.
- No inventes defectos ni estados: si la consulta falla, dilo tal cual.

## Siguiente paso habitual

Para revisar el código de un defecto, usa `qa-code-audit --issue AF-XXX`.
