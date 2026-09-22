---
title: API centralizada FastAPI
description: Mantener una única API centralizada en services y separar workers solo cuando sea estrictamente necesario.
scope: services/**
applyTo: services/**
---

## Regla

- Los endpoints y routers de la compañía deben implementarse en una API FastAPI centralizada dentro de `services/`.
- Organiza la API por routers o módulos de dominio, como ubicaciones, menús, ventas o telemetría.
- No crees un microservicio independiente por cada dominio durante la fase inicial.
- Solo separa un worker cuando tenga una necesidad real de ejecución independiente del API.

## Justificación

La guía raíz define `services/` como un único backend FastAPI centralizado y recomienda evitar dividirlo pronto en muchos microservicios. La evidencia está en `README.md`, en la sección `services/ — centralized company API (FastAPI)`. El README específico de servicios exige además que cada subcarpeta represente un servicio concreto y tenga documentación propia: `services/README.md`.

## Ámbito de aplicación

Aplica a todo código nuevo bajo `services/`, incluyendo APIs, routers, módulos de dominio, consumidores de colas y workers.