---
title: Estructura de cada skill
description: Mantener cada capacidad reutilizable como una carpeta con SKILL.md y recursos opcionales organizados.
scope: skills/**
applyTo: skills/**
---

## Regla

- Cada skill debe vivir en una carpeta propia bajo `skills/` y debe incluir un archivo `SKILL.md`.
- Usa `examples/`, `resources/` y `scripts/` como subcarpetas opcionales cuando la skill necesite ejemplos, referencias o automatización.
- Documenta en `SKILL.md` cuándo usar la skill, sus entradas y salidas esperadas y ejemplos relevantes.
- No trates una skill como una aplicación o librería independiente fuera de `skills/`.

## Justificación

`README.md` raíz describe `skills/` como instrucciones y scripts empaquetados, y especifica que cada skill tiene `SKILL.md` con scripts, recursos y ejemplos opcionales. `skills/README.md` exige documentar uso, entradas, salidas y ejemplos. La plantilla concreta muestra `skills/_template/SKILL.md`, `skills/_template/examples/`, `skills/_template/resources/` y `skills/_template/scripts/`.

## Ámbito de aplicación

Aplica a todas las skills bajo `skills/`, incluidas las nuevas skills de análisis, investigación, code review u otras capacidades reutilizables.