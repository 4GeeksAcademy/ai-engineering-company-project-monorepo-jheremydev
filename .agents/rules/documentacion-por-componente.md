---
title: Documentación por componente
description: Acompañar cada aplicación, servicio, agente o pipeline con una subcarpeta y un README propio.
scope: uis/**, services/**, agents/**, data/pipelines/**
alwaysApply: true
---

## Regla

- Cada aplicación, servicio, agente o pipeline nuevo debe tener una subcarpeta propia.
- Esa subcarpeta debe incluir un `README.md` que explique su objetivo, tecnología o dependencias relevantes y cómo ejecutarlo, probarlo o utilizarlo.
- Mantén la documentación específica junto al componente; reserva `docs/` para documentación transversal que abarque varias áreas.
- No añadas una pieza nueva como archivo suelto sin documentación local cuando pertenezca a una de esas categorías.

## Justificación

El procedimiento de inicio de `README.md` raíz indica que cada nueva app, servicio, agente o pipeline recibe una subcarpeta y un README. Los README de `uis/`, `services/`, `agents/` y `data/pipelines/` repiten la recomendación de documentar cada componente, su objetivo, tecnología, dependencias y forma de ejecución. `docs/README.md` reserva `docs/` para documentación global o transversal.

## Ámbito de aplicación

Aplica al crear o ampliar aplicaciones en `uis/`, servicios en `services/`, agentes en `agents/` y pipelines en `data/pipelines/`. No exige convertir los README de nivel superior ni los recursos compartidos en aplicaciones independientes.