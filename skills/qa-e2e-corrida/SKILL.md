---
name: qa-e2e-corrida
description: Planifica y documenta corridas E2E de IAFactory (Maya → Product Owner → Arquitecto → UI/UX → QA → Developer, y DevSec/DevOps cuando participan). Úsala antes de una corrida nueva (documento de proyecto "Antes" y, si se pide, plan de revisión de issues pendientes), durante la corrida para llenar un único documento por agente, y para auditar una corrida ya terminada a partir de su ID de proyecto. Escribe solo archivos locales; publicar tickets sigue pasando por report-bug, qa-amplify, qa-finish y qa-rejection con confirmación. / Plan and document IAFactory end-to-end runs.
---

# Corridas E2E (`qa-e2e-corrida`)

> `<KIT>` es la carpeta raíz del kit: dos niveles por encima de este `SKILL.md`.

Define **cómo se planifica y documenta** una corrida end-to-end: un proyecto piloto que se lleva por todo el pipeline de agentes de IAFactory. Para un bug puntual ya conocido no uses esta skill: usa `qa-backlog`, `qa-code-audit` y la plantilla de 4 fases de `rules/AGENTS.md`.

**Plantillas** (en `<KIT>/skills/qa-e2e-corrida/templates/`):
- `plantilla_proyecto.md`: documento "Antes" del proyecto.
- `plantilla_corrida.md`: documento único de la corrida.

**Crear los documentos** (solo escribe archivos locales, nunca sobrescribe):

```bash
python <KIT>/skills/qa-e2e-corrida/scripts/new_run.py where
python <KIT>/skills/qa-e2e-corrida/scripts/new_run.py proyecto <slug-proyecto>
python <KIT>/skills/qa-e2e-corrida/scripts/new_run.py corrida <empresa> <slug-proyecto> [AAAA-MM-DD]
```

La carpeta de salida es `QA_KIT_E2E_DIR` del `.env` (ruta absoluta o relativa al workspace). Por defecto: `<workspace>/Reportes/E2E/`. Los documentos de proyecto van en su subcarpeta `proyectos/`.

**Validar el documento** (solo lectura, determinista):

```bash
python <KIT>/skills/qa-e2e-corrida/scripts/validate_run.py <documento_corrida.md> [--json] [--strict]
```

---

## Reglas de consistencia (valen para cualquier persona y cualquier asistente)

1. **El documento de corrida siempre se crea con `new_run.py`**, nunca copiando la plantilla a mano ni partiendo de un informe anterior. `new_run.py` escribe la versión del kit en los metadatos: así se sabe con qué método se hizo cada corrida.
2. **Esta skill manda sobre la memoria del asistente y sobre informes anteriores** en todo lo que es método: estructura, secciones, tablas, etiquetas, escala de gravedad y pasos. La memoria sirve para criterios del producto que cambian con el tiempo, no para cambiar el formato.
3. **Un solo documento, escrito durante la corrida.** No se lleva un registro paralelo con otro formato para "pasarlo después". Si otra sesión u otra herramienta completa el documento, se anota en "Autores del documento".
4. **Etiquetas de evidencia:** solo `[R]`, `[DB]`, `[C]`, `[C-sub]`, `[H]`. **Gravedad:** solo Crítica, Alta, Media o Baja, según la escala de los metadatos (el motivo va en otra columna o entre paréntesis después de la palabra).
5. **Antes de cerrar, `validate_run.py` debe dar 0 errores.** Su línea de resumen se pega en la §11.

---

## Modos

| Modo | Cuándo | Pasos |
|---|---|---|
| **En vivo** | El usuario va a correr un proyecto nuevo por el pipeline | 0 → 0.3 (opcional) → 1 → 2 → 3 → 4 |
| **Auditoría retroactiva** | La corrida ya terminó y el usuario da un ID o URL de proyecto | 0 (reconstruido) → A → 2 → 3 → 4 |

El modo se declara en los metadatos del documento de corrida.

---

## Paso 0: Documento de proyecto ("Antes")

Antes de abrir el chat con Maya hay que tener **claridad completa** del proyecto. El resultado es un documento que explica todo lo que se construirá en IAF y sirve de línea base para auditar después.

1. `new_run.py proyecto <slug>`.
2. Si el usuario trae un documento propio (.docx, PDF), transcríbelo a la plantilla **sin alterar su contenido**. Lo que falte va a "Preguntas abiertas"; no se inventa.
3. Si no hay documento, redáctalo con el usuario, preguntando hasta que no queden huecos: contexto, objetivos medibles, roles, requerimientos (RF-n), reglas de negocio verificables con ejemplo (RN-n), datos, pantallas (UI-n), restricciones, fuera de alcance y criterios de aceptación (CA-n).
4. Lo que el usuario deje abierto se escribe como "libre para el equipo", no como vacío.
5. **El usuario aprueba el documento antes de empezar la corrida.** Varias corridas pueden reutilizar el mismo archivo; cada corrida indica qué versión usó.
6. **Si el usuario pide que el asistente invente el proyecto o haga de cliente**, igual se escribe primero este documento y el usuario lo aprueba. Durante la corrida, las respuestas a los agentes salen de este documento; lo que no esté, se responde como "libre para el equipo" y se anota en el libro de decisiones. No se improvisan requisitos sobre la marcha.

## Paso 0.2: Foto de la configuración de agentes

Antes de escribirle a Maya, lee en solo lectura la personalización de los agentes de la empresa de prueba (instrucciones, tono, largo de respuesta, restricciones; en IAFactory, `company_agent_profiles`) y guárdala en la §0.6 del documento de corrida. Los perfiles no tienen historial de versiones: si no se guarda al inicio, después no se puede saber si un comportamiento venía de la configuración. Si no hay acceso, se declara en la §0.6.

Los IDs RF/RN/UI/CA alimentan la columna **Planificado** de la tabla de discrepancias (Paso 3).

## Paso 0.3: Plan de revisión de issues (opcional)

Pregunta al usuario si quiere aprovechar la corrida para revisar issues existentes. Si dice que sí:

1. Consulta el Sheet en vivo:
   ```bash
   python <KIT>/skills/qa-backlog/scripts/fetch_issues.py --status "Pendiente,En Revisión,Reportada" --limit 1000 --json
   ```
   Otros estados, si el usuario los pide, van en `--status`.
2. **Filtro por persona:** agrega `--responsable "<nombre>"` (varias personas separadas por coma). Si nadie coincide, el script lista los responsables existentes: muéstraselos al usuario y pregunta, no adivines.
3. Lee cada issue candidato (fila del Sheet y su página de Notion) y clasifícalo:
   - **Revisable en esta corrida:** el agente o la función afectada se ejercita con este proyecto, esta empresa y este entorno.
   - **Revisable ajustando el proyecto:** se dispara agregando algo al documento "Antes" (una regla, un rol). El ajuste se declara en su §11.
   - **No revisable:** requiere otra integración (Azure o Jira), otro entorno, un agente que no participará o accesos que no hay. Se dice el motivo.
4. Escribe el plan en la §0.3 del documento de corrida: para cada AF, en qué etapa se prueba, qué se hará y con qué criterio se da por corregido o persistente.
5. **Presenta el plan y espera la aprobación del usuario** antes de empezar.

Durante la corrida, el resultado de cada issue se registra en la subsección 🔁 del agente donde se probó, separado de los hallazgos nuevos.

## Paso 1: Documento de corrida

`new_run.py corrida <empresa> <slug>` y llena los metadatos. Todo lo de la corrida vive en este único archivo; no se crean reportes sueltos por agente ni por hallazgo.

## Paso 2: Una sección por agente, en cuanto termina su etapa

No esperes al final. Solo se documentan los agentes que participaron; los demás quedan con "No participó". Para cada agente, en este orden:

1. **Configuración, resumen de la conversación y artefactos generados.** Verifica los artefactos en su destino real (Wiki, Boards, Figma, repo), no solo lo que el agente dijo en el chat.
2. **Libro de decisiones**, si el usuario cambió algo en esa etapa.
3. **✅ Lo que funcionó bien.** Obligatorio, con evidencia concreta de qué se comprobó.
4. **❌ Hallazgos: registro limpio.** Lo que pasó, con evidencia `[R]` runtime / `[DB]` base de datos o logs / `[C]` código / `[C-sub]` leído solo por subagente / `[H]` hipótesis, y gravedad propuesta. **Aquí no se mencionan tickets ni AF-IDs.** Para hallazgos de conducta de un agente, indica si la configuración de la §0.6 lo explica.
   - **Descartar un hallazgo** (no llevarlo a ticket) solo se permite con una causa citada: lo explica la configuración de la §0.6, es un duplicado, o hay un criterio del producto vigente que lo declara normal (dilo con su fuente). "Parece comportamiento normal" sin fuente no es motivo; en la duda, se deja y se pregunta al usuario.
5. **🔁 Issues del plan** probados en esta etapa, si hay plan.
6. **🔍 Contraste con el Sheet en vivo**, al final de la sección: para cada hallazgo del punto 4, si ya estaba reportado.
   - Fuente única: el Sheet en vivo, consultado en ese momento con `fetch_issues.py --status all --limit 1000 --json`. No se compara contra tablas internas ni reportes previos, que quedan desactualizados.
   - Se revisan **todos** los estados; una coincidencia con un ticket `Finalizada` se marca como posible regresión.
   - Relación: duplicado / ampliación / relacionado / nuevo / posible regresión.

### Developer: dos frentes que no se mezclan

- **6.a Funcionamiento del agente:** mismo tratamiento que los demás (incluye 🔍). Candidato a ticket, porque describe la plataforma.
- **6.b Código entregado:** se prueba **solo en local** contra las RN y CA del documento "Antes". **No se reporta en ningún lado**: ni ticket, ni Notion, ni contraste con el Sheet. Solo se menciona en el documento, como referencia del rendimiento del Developer. Método obligatorio:
  1. Clonar el **repo publicado** (no leer el workspace del contenedor del Developer) y registrar repo, rama y **commit revisado**. Comprobar que no sea un repo vacío duplicado.
  2. Instalar dependencias y compilar backend y frontend, incluidos los tests del propio repo.
  3. **Ejecutar** cada RN: con el servicio levantado en local, o con un test contra la clase real y dependencias en memoria. Incluir **pruebas de control** que demuestren que el arnés sí rechaza lo que el código ya valida; sin controles, un "falla" puede ser culpa del arnés.
  4. Si una dependencia externa (login corporativo, servicios pagos) impide levantar el servicio, se reemplaza solo esa pieza con un stub y se declara.
  5. Cada defecto indica si fue **ejecutado** o **solo leído** en el código.
  6. Si algo de lo anterior no se pudo hacer, la §6.b lo dice en la misma sección como **revisión parcial**, con qué faltó y por qué (no solo en §10).
  - Llena siempre la tabla del método y la de **datos de rendimiento** con el mismo formato en todas las corridas, para construir métricas de calidad más adelante.
- Criterio: *¿es un bug del comportamiento de un agente de IAFactory (6.a) o de la calidad del código de la app piloto (6.b)?* Si hay duda, pregunta al usuario.

## Paso A: Auditoría retroactiva

Menos detalle que en vivo, misma estructura.

1. Pide el ID o URL del proyecto y el entorno. Abrir túneles (`qa-preflight`, `iap_tunnel.py start --env <env>`) requiere autorización del usuario.
2. Fuentes, todas en solo lectura: base de datos de la plataforma, transcripciones del chat, logs, artefactos publicados y repositorio.
   - **Base de datos:** el kit no trae un cliente de Postgres. Si el workspace tiene uno de solo lectura, úsalo y revisa primero el esquema real (las columnas cambian). Si no hay, trabaja con el resto de las fuentes y decláralo en la §0.4. No escribas consultas que modifiquen datos.
3. **Documento "Antes":** si existe el original, úsalo. Si no, reconstrúyelo desde el primer mensaje del usuario a Maya y márcalo como "Reconstruido" (línea base más débil; la tabla de discrepancias lo debe decir).
4. Llena la §0.4: qué fuentes había y qué no se puede ver en este modo (lo observado en pantalla, tiempos percibidos, configuración no persistida).
5. La evidencia leída en base de datos o logs se etiqueta `[DB]`, no `[R]`.
6. Sigue con los Pasos 2, 3 y 4. El plan de issues no aplica, salvo que el usuario pida contrastar issues concretos.

## Paso 3: Cierre

1. **Plan de proyecto (§0.5):** de la idea del documento "Antes" a lo publicado, con el libro de decisiones y enlaces reales.
2. **Lo bueno por agente (§9.1).**
3. **Hallazgos consolidados (§9.2):** salen de las tablas 🔍, con la acción propuesta (publicar nuevo / ampliar un AF existente / ninguna). No incluye 6.b.
4. **Discrepancias en cuatro aristas (§9.3):** `Planificado | Agente | Documentación | Código`, una fila por elemento RF/RN/UI/CA que no llegó intacto, con la **primera ruptura**.
5. **Resultado del plan de issues (§9.4):** corregido → proponer cierre con `qa-finish`; persiste → proponer rechazo con `qa-rejection`; no se pudo probar → ninguna acción, va a pendientes.
6. **Pendientes (§10):** qué quedó sin verificar y por qué.
7. **Estado final primero.** Repasa el documento completo, no solo las secciones que cambiaron: cada tabla, título y párrafo debe mostrar primero el estado final verificado. Lo que ya se resolvió deja de decir "(en curso)", "(pendiente)", "candidato" o `[H]` en el texto principal; esa historia pasa a una columna "Estado inicial" o a una nota en cursiva "*Registro en vivo: …*". No basta con agregar marcas de cierre al lado del texto viejo.
8. **Validación (§11):** corre `validate_run.py`. Con errores, el documento no está terminado. Las advertencias se corrigen o se justifican en la §11.

## Paso 4: Publicación (solo con confirmación)

Nada se publica solo. Para cada hallazgo de §9.2 o issue de §9.4 que el usuario quiera subir, ejecuta primero el script correspondiente con `--dry-run`: `report-bug` para hallazgos nuevos, `qa-amplify` para duplicados y ampliaciones de tickets existentes (se pueden publicar en lote con `--file`), `qa-finish` / `qa-rejection` para issues del plan re-verificados. Muestra el dry-run y espera la confirmación del usuario en ese turno. Una autorización cubre solo lo que mostraste.

Los scripts lo exigen: cada `--dry-run` imprime un `confirm_code` calculado sobre el contenido exacto, y la publicación real solo corre con `--confirm <confirm_code>` (si no, sale con código `4` sin escribir nada). Si editas el reporte después del dry-run, el código deja de valer y hay que repetirlo. `qa-finish` y `qa-rejection` exigen además `--build <commit o imagen probada>`: sin la versión probada no se cierra ni se rechaza un ticket, aunque haya "alta confianza".

---

## Reglas que esta skill no cambia

- **Nunca publicar de forma autónoma** en Google Sheets, Notion, Jira ni Confluence.
- **El texto principal muestra el estado final.** Lo que cambió durante la corrida queda como nota secundaria ("*Registro en vivo: …*").
- **Registro limpio primero, contraste después**, siempre contra el Sheet en vivo.
- **6.b no se reporta en ningún lado.**
- **No inventar rutas ni líneas de código.** Si una causa raíz la citó un subagente, re-verifica al menos una muestra leyendo el archivo real.
- **Sin commits, push ni mutaciones remotas** (Docker, servicios, VMs) sin permiso explícito en el turno actual.
- El resto de `rules/AGENTS.md` sigue vigente.
