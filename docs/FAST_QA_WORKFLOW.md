# ⚡ Flujo de QA Acelerado: Guía Operativa y Protocolo

Esta guía documenta la optimización de latencia y velocidad del **Plugin IAFactory QA Kit**, diseñada para reducir tiempos muertos durante la auditoría, prueba en vivo y resolución de incidencias (`AF-XXX`), respetando estrictamente el marco ético y de gobernanza **HHH** (*Honest, Helpful, Harmless*).

---

## 1. Motivación y Diagnóstico de Cuellos de Botella

Durante las pruebas secuenciales se identificaron las principales causas de lentitud:
1. **Sobrecarga de comandos remotos sucesivos vía IAP (`~25s` cada uno):** Consultar ramas git, luego docker ps, luego logs generaba múltiples handshakes SSH redundantes.
2. **Arranque pesado de suites globales de test (`30-60s`):** Escanear monorepos completos o recompilar DOM en cada comprobación puntual incrementaba la latencia.
3. **Pausas por tareas en segundo plano (`background tasks`):** Comandos que superaban 10 segundos obligaban a pausas de turno y re-invocación de contexto.

---

## 2. Los 3 Pilares del Modo Acelerado (Validados con Claude Code)

### Pilar 1: Batching Remoto Consolidado (`remote_batch_inspect.py`)
En lugar de múltiples comandos remotos, una única llamada empaquetada en base64 extrae de la VM `iafactory-dev`:
- Rama, commit SHA, fecha y estado *dirty* de los 4 repositorios (`core`, `agents`, `frontend`, `platform`).
- Estado de los 42 contenedores Docker (health, estado, uptime, imagen).
- **Principio de Honestidad (Aporte de Claude):** Correlaciona la fecha de creación del contenedor con la fecha del commit para confirmar que el código en disco efectivamente fue desplegado en el contenedor y no permanece solo en el sistema de archivos del host.

```bash
# Ejecución consolidada:
python <PLUGIN_ROOT>/skills/qa-preflight/scripts/remote_batch_inspect.py
python <PLUGIN_ROOT>/skills/qa-preflight/scripts/remote_batch_inspect.py --json
```

### Pilar 2: Tests Quirúrgicos y Ligeros (`fast_test_runner.py` / `--run-tests`)
*Nota de Integración Continua:* La suite de pruebas unitarias ya es ejecutada automáticamente por el pipeline de Jenkins en cada build de CI/CD. Por lo tanto, en la auditoría de issues la ejecución de tests está **desactivada por defecto** para evitar reprocesos innecesarios, y solo se ejecuta localmente cuando se incluye el flag `--run-tests` en `audit_changes.py` o se invoca manualmente:
- **Frontend:** Ejecuta Vitest con `--no-threads` filtrando por archivo (`--file`) o por nombre de prueba (`--test`), reduciendo el tiempo de 45s a < 10s.
- **Agentes:** Ejecuta scripts de validación directamente sobre Python nativo (ej. suite anti-voseo sobre los 7 agentes en < 5s).
- **Advertencia Técnica de Rigor:** Útil cuando se necesita reproducir o validar quirúrgicamente un test específico en local antes del push.

```bash
# Frontend quirúrgico:
python <PLUGIN_ROOT>/skills/qa-code-audit/scripts/fast_test_runner.py --frontend --file "src/hooks/orchestrator/__tests__/eventId.test.ts"

# Suite anti-voseo en los 7 agentes:
python <PLUGIN_ROOT>/skills/qa-code-audit/scripts/fast_test_runner.py --agent all --test-voseo
```

### Pilar 3: Subagentes en Paralelo para Auditoría Estática
Para eliminar tiempos muertos:
- Mientras el agente interactivo valida en vivo con Puppeteer o prepara el cierre de la incidencia $AF_N$, se puede disparar un subagente de tipo `research` para auditar el código, commits y diffs de la siguiente incidencia $AF_{N+1}$.
- **Frontera de Seguridad Concurrente (Aporte de Claude):**
  - El subagente opera en modo **estricta solo lectura** sobre el filesystem y git local.
  - **Prohibido que los subagentes ejecuten mutaciones sobre Google Sheets o Notion en paralelo**, evitando colisiones de estado concurrente. Toda mutación se ejecuta secuencialmente en el hilo interactivo tras aprobación explícita del usuario.

---

## 3. Matriz de Velocidad vs. Cobertura

| Acción | Modo Tradicional | Modo Acelerado | Ahorro de Tiempo |
|---|---|---|---|
| Diagnóstico de VM remota | 3-4 comandos SSH (`~90s`) | 1 llamada consolidada (`~15s`) | **~83%** |
| Test unitario de frontend | Suite completa (`~50s`) | `fast_test_runner.py` (`~10s`) | **~80%** |
| Test anti-voseo 7 agentes | Pytest monorepo (`35s` + errores) | `fast_test_runner.py` (`~5s`) | **~85%** |
| Preparación siguiente issue | Secuencial tras cierre | Subagente paralelo en background | **~100% solapado** |

---

## 4. Estándar de Reportabilidad: Trazabilidad del Commit en GCP

A requerimiento expreso del equipo de QA, **todo reporte técnico de verificación exitosa (`qa-finish`) o de rechazo (`qa-rejection`) debe incluir de forma mandatoria**:

1. **Commit HEAD de la VM:** El hash SHA exacto verificado en caliente en la instancia de GCP (`iafactory-dev`).
2. **Rama Activa y Estado del Contenedor:** La rama de Git desplegada y el estado de salud del contenedor Docker correspondiente.
3. **Correlación Empírica:** Garantizar que la evidencia empírica se obtuvo sobre la compilación activa en GCP y no sobre supuestos locales no sincronizados.

