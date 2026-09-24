---
name: qa-help
description: Muestra el catálogo de skills, scripts y flags del IAFactory QA Kit. Úsala cuando el usuario pregunte qué puede hacer el kit, cómo se usa un script, qué flags tiene o pida ayuda con los comandos de QA. Solo lectura. / Command and flag catalog for the QA kit.
---

# QA Help (`qa-help`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.

```bash
# Catálogo completo
python <KIT>/skills/qa-help/scripts/help.py

# JSON para procesarlo tú
python <KIT>/skills/qa-help/scripts/help.py --json

# Solo una skill
python <KIT>/skills/qa-help/scripts/help.py --skill qa-code-audit
```

Si el usuario es nuevo en el kit, sugiere también `qa-welcome`.
