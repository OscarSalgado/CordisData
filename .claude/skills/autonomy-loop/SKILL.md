---
name: autonomy-loop
description: Reglas del framework de programacion autonoma sobre OpenSpec. Consultar siempre que se trabaje con GOALS.yaml, cursor.json, el gate, o los comandos /goal-start, /goal-next, /goal-status. Tambien al decidir si una tarea esta terminada.
---

# Loop autonomo sobre OpenSpec

## Modelo mental
- `openspec/specs/` = lo que YA es verdad. Solo cambia al archivar.
- `openspec/changes/<id>/` = lo que se propone. Ahi vive el trabajo en curso.
- `autonomy/goals/GOALS.yaml` = por que se trabaja y como se sabe que termino.
- `autonomy/state/` = donde esta el loop ahora. Reanudable tras un corte.

## Los tres invariantes
1. **El gate manda.** Un checkbox de tasks.md solo se marca tras `gate.sh` en verde.
2. **Una tarea por subagente.** Contexto limpio. Nada de "ya que estoy, hago la siguiente".
3. **La repeticion escala.** Misma firma de fallo dos veces = problema de plan, no de codigo.
   Escalar al humano, no reintentar.

## Salidas del loop (solo estas tres)
- `success`: todos los `done_when` en verde -> archive.
- `exhausted`: presupuesto agotado -> informe y para.
- `stuck`: firma repetida o categoria `env` -> informe y para.

No existe "creo que ya esta".

## Anti-patrones que el sistema debe frenar
- Relajar un assert o borrar un test para pasar el gate.
- Reescribir el spec para que encaje con el codigo escrito.
- Ampliar blast_radius sin decision humana.
- Marcar varias tareas de golpe al final.

## Puntos de control humano
`human_gate` en el goal. Por defecto `proposal`: la decision cara es que se va a construir,
no como. Ponlo en `none` solo para cambios mecanicos de bajo riesgo.
