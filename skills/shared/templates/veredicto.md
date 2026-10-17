# AF-XXX — Veredicto QA: <Finalizada | Rechazada por QA>

**Resumen:** <una frase: qué se probó y qué pasó>
**Versión probada:** <repo@commit o imagen, en qué VM, fecha de creación del contenedor>
**Fecha y entorno:** <fecha y hora, VM, usuario y rol con el que se probó>
**Criterio del ticket:** <lo que el ticket pide, en una frase que se pueda comprobar>

## Qué cambió el desarrollador
- <PR, commits y archivos, con archivo:línea>
- **¿Toca la causa raíz o solo el síntoma?** <respuesta con el porqué>
- **¿Cubre todos los síntomas del ticket?** <sí / no, cuáles faltan>
- **¿Trae un test del caso del ticket?** <sí: cuál / no>

## Casos probados
Cada fila la ejecutó el asistente en la instancia abierta por la persona. "Pasa" solo con lo observado ([R]) o leído en base de datos o logs ([DB]); un veredicto no se apoya en lectura de código ([C]) ni en hipótesis ([H]).

| # | Caso | Tipo (ticket / control / límite) | Pasos | Resultado observado | Evidencia | Veredicto (Pasa / Falla / No probado) |
|---|---|---|---|---|---|---|
| 1 | <el caso que describe el ticket> | ticket | | | [R] | |
| 2 | <algo que ya funcionaba y no debe romperse> | control | | | [R] | |
| 3 | <valor límite o variante del caso> | límite | | | [R] | |

## Límites y no verificado
- <qué no se pudo probar y por qué>

## Observaciones que no bloquean
- <opcional: lo que conviene mejorar sin cambiar el veredicto>
