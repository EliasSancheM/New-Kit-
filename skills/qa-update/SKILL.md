---
name: qa-update
description: Comprueba si hay una versión nueva del IAFactory QA Kit en origin/main, muestra los cambios y, si el usuario lo aprueba, actualiza el kit. Úsala cuando el usuario pregunte si el kit está al día, quiera ver qué cambió o pida actualizarlo. Consultar es solo lectura; actualizar requiere confirmación. / Check for and apply QA kit updates.
---

# QA Update (`qa-update`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.
>
> Si instalaste el kit como plugin de Claude Code (`/plugin install`), actualízalo desde el gestor de plugins en vez de usar esta skill.

## Solo lectura

```bash
python <KIT>/skills/qa-update/scripts/update_plugin.py --version
python <KIT>/skills/qa-update/scripts/update_plugin.py --check --json
```

## Actualizar: pide confirmación antes

Muestra al usuario los commits entrantes que listó `--check` y espera un "sí" explícito. Después:

```bash
python <KIT>/skills/qa-update/scripts/update_plugin.py --update
```

Si el kit está como submódulo git del workspace, avisa al usuario de que después tendrá que registrar el nuevo commit del submódulo en el repo del workspace. No hagas ese commit sin que te lo pida.
