---
name: qa-update
description: Comprueba si hay una versión nueva del IAFactory QA Kit, muestra los cambios y, si el usuario lo aprueba, actualiza tanto la copia del workspace (git) como el plugin instalado en Claude Code. Úsala cuando el usuario pregunte si el kit está al día, quiera ver qué cambió o pida actualizarlo. Consultar es solo lectura; actualizar requiere confirmación. / Check for and apply QA kit updates.
---

# QA Update (`qa-update`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.

El kit puede estar en dos lugares a la vez, y los dos se actualizan por separado:

| Dónde | Cómo se actualiza |
|---|---|
| **Copia del workspace** (por ejemplo `.agents/plugins/iafactory-qa-kit`, un repo git o submódulo) | `git pull` |
| **Plugin instalado en Claude Code** (`~/.claude/plugins/…`) | `claude plugin marketplace update` + `claude plugin update`. Claude Code instala desde su propio clon del repo y **no lo refresca solo**: sin este paso, el plugin se queda en una versión vieja aunque el workspace esté al día. |

El script detecta cuáles existen y trabaja con los dos.

## Solo lectura

```bash
python <KIT>/skills/qa-update/scripts/update_plugin.py --version
python <KIT>/skills/qa-update/scripts/update_plugin.py --check [--json]
```

`--check` muestra los commits pendientes de la copia del workspace y la versión instalada del plugin frente a la disponible. Para consultar la versión remota del plugin hace `git fetch` en el clon de Claude Code: solo actualiza referencias, no cambia lo instalado.

## Actualizar: pide confirmación antes

Muestra al usuario lo que listó `--check` y espera un "sí" explícito. Después:

```bash
python <KIT>/skills/qa-update/scripts/update_plugin.py --update
```

- Actualiza el plugin de Claude Code si hay versión nueva (busca `claude` en el PATH o el que trae la app de escritorio) y hace `git pull` en la copia del workspace si está atrasada.
- **Después hay que reiniciar Claude Code** (o abrir una sesión nueva) para que cargue la versión nueva del plugin. Díselo al usuario.
- Si no encuentra el comando `claude`, imprime los dos comandos para que el usuario los corra en su terminal.
- Si el kit es un submódulo del workspace, avisa al usuario de que tendrá que registrar el nuevo commit del submódulo en el repo del workspace. No hagas ese commit sin que te lo pida.
