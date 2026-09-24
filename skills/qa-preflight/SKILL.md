---
name: qa-preflight
description: Diagnóstico previo a probar en vivo contra una VM (dev, qa, team-devs u otra de environments.json). Revisa túneles IAP, puertos de PostgreSQL/Qdrant, credenciales de gcloud y Notion, y el estado de contenedores y repos en la VM. Úsala antes de cualquier prueba en vivo, cuando el usuario diga que algo no conecta o que el túnel no anda, o pregunte si un entorno está arriba. El diagnóstico es de solo lectura; abrir o cerrar túneles requiere confirmación. / Pre-flight connectivity and environment check.
---

# QA Preflight (`qa-preflight`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`. Ejecuta desde la raíz de tu workspace.

## Entornos (varias VMs en paralelo)

Las VMs están definidas en `<KIT>/environments.json`. Por defecto hay `dev`, `qa` y `team-devs`.
- Todos los scripts aceptan `--env <nombre>`. Sin `--env` se usa `QA_KIT_ENV` del `.env`, o `dev` si no está definido.
- Cada entorno tiene su propio **offset de puertos**, así que puedes tener varios túneles abiertos a la vez: **puerto local = puerto remoto + offset**. Por defecto: dev +0, qa +10000, team-devs +20000. Ejemplo: Postgres de qa en `127.0.0.1:15432`.
- **Pregunta siempre al usuario contra qué entorno quiere probar** si no lo dijo. No asumas `dev`.
- Un entorno con la instancia vacía da error hasta que alguien la complete en `environments.json`, o en `environments.local.json` para ajustes personales, que no se versiona.

## Solo lectura (se puede ejecutar sin confirmar)

```bash
# Entornos configurados y estado de todos los túneles
python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py envs
python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py status --all

# Conectividad local de un entorno: túnel, puertos, credenciales
python <KIT>/skills/qa-preflight/scripts/check_env.py --env qa --json

# Estado de contenedores y checkout de repos en la VM (un solo viaje SSH, solo lectura)
python <KIT>/skills/qa-preflight/scripts/remote_batch_inspect.py --env dev --json
python <KIT>/skills/qa-preflight/scripts/remote_batch_inspect.py --env qa --repo frontend

# Estado del túnel de un entorno
python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py status --env team-devs --json
```

## Cambian estado: pide confirmación antes

```bash
# Abrir o cerrar el túnel IAP local de un entorno
python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py start --env qa
python <KIT>/skills/qa-preflight/scripts/iap_tunnel.py stop --env qa

# storageState.json autenticado para pruebas de navegador. Hace login contra la API del
# entorno y guarda auth/storageState_<env>.json. Necesita QA_TEST_USER y QA_TEST_PASSWORD en el .env.
python <KIT>/skills/qa-preflight/scripts/refresh_auth.py --env qa
```

Si `refresh_auth.py` no logra autenticarse, termina con código 1 y no genera ningún archivo. Nunca generes ni uses un token inventado.

## Regla de las VMs remotas

Todas las VMs (dev, qa, team-devs) son **infraestructura compartida**. Si el diagnóstico muestra un contenedor o servicio caído:
1. Informa el estado exacto, el entorno y el comando que usaste.
2. Propón el comando para arreglarlo.
3. **No lo ejecutes.** Espera la autorización explícita del usuario. Nunca levantes ni reinicies nada para "poder terminar la prueba".

## Problemas comunes

- **`CERTIFICATE_VERIFY_FAILED` en gcloud o en los scripts** (antivirus como Avast o proxy corporativo que re-firma TLS). Solución recomendada, mantiene la verificación activa:
  ```bash
  python <KIT>/skills/qa-preflight/scripts/build_ca_bundle.py
  ```
  Luego agrega al `.env` del kit la línea `QA_KIT_CA_BUNDLE=...` que imprime, y `QA_KIT_TLS_RELAX_STRICT=1` si usas Python 3.13 o superior. No cambia la configuración global de gcloud: el kit se lo pasa solo a sus propios procesos.
- Solo si lo anterior no alcanza para el túnel IAP: `QA_KIT_IAP_INSECURE_WS=1` desactiva la verificación del websocket de IAP. Es un último recurso.
- **SSH con "dubious ownership" en git:** el script ya lo maneja por comando, sin tocar la configuración de la VM.
- **Fallos intermitentes de SSH/IAP** ("Remote side unexpectedly closed", "Updating project ssh metadata... failed"): reintenta una vez antes de concluir que la VM está caída.
- Sin sesión de gcloud: `gcloud auth login --enable-gdrive-access`.
- El túnel no levanta porque hay un Postgres local usando `5432`: cambia el `port_offset` de ese entorno en `environments.local.json`.
