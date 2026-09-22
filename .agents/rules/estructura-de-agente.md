---
title: Estructura de cada agente
description: Crear cada agente como una subcarpeta documentada basada en la plantilla agent.py + README.md + tests/.
scope: agents/**
applyTo: agents/**
---

## Regla

- Cada agente concreto debe vivir en su propia subcarpeta dentro de `agents/`.
- Al crear un agente, copia o adapta la estructura de `agents/_template/`: `agent.py`, `README.md` y `tests/`.
- `README.md` debe documentar como mínimo el objetivo, capacidades, fuentes de conocimiento o memoria, herramientas y forma de probar el agente.
- `tests/` debe alojar pruebas funcionales, de regresión y de calidad, según corresponda.
- No coloques varios agentes concretos directamente como archivos sueltos en `agents/`.

## Justificación

`agents/README.md` establece una subcarpeta por agente y exige documentación sobre objetivo, capacidades, conocimiento/memoria, herramientas y pruebas. `agents/_template/README.md` identifica la plantilla como el estándar de estructura, y `agents/_template/tests/README.md` define el esqueleto de pruebas. La estructura verificable de referencia es `agents/_template/agent.py`, `agents/_template/README.md` y `agents/_template/tests/`.

## Ámbito de aplicación

Aplica a cualquier agente nuevo o modificado bajo `agents/`, excepto a la propia documentación general de `agents/` y a los archivos de soporte compartidos de `agents/tools/`.