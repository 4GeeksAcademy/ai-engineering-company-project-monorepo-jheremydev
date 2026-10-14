---
title: docker-compose en la raíz
description: Mantener la orquestación local global en docker-compose.yml en la raíz y el resto de infraestructura en infra/.
scope: repository
alwaysApply: true
---

## Regla

- El archivo de orquestación local global debe llamarse `docker-compose.yml` y vivir en la raíz del repositorio.
- Usa ese archivo para conectar `services/`, bases de datos y otros contenedores del stack local.
- Coloca Dockerfiles auxiliares, Terraform, manifiestos Kubernetes, Nginx y configuración de despliegue en `infra/`.
- No muevas el `docker-compose.yml` global dentro de `infra/` ni repartas su orquestación principal entre varias ubicaciones.

## Justificación

`README.md` raíz define `docker-compose.yml` como el archivo de orquestación local de todo el stack y ordena mantenerlo en la raíz. La sección `infra/` coloca allí Docker, Terraform y configuración de despliegue, y `infra/README.md` identifica esa carpeta como el lugar para la infraestructura del monorepo.

## Ámbito de aplicación

Aplica a la orquestación local de todo el repositorio y a cualquier cambio en `infra/`. No impide que un componente tenga archivos auxiliares propios si siguen siendo compatibles con la orquestación global.