---
name: backoffice-domain-module
description: Genera el scaffolding de un nuevo módulo de dominio para uis/backoffice (cliente API + vista + pestaña), siguiendo exactamente el patrón ya usado por Incidencias e Inventario.
---

# Backoffice Domain Module

## Objetivo

Cada vez que Brasaland Digital añade un dominio de negocio nuevo al backoffice (ej. "compras", "proveedores", "turnos"), el agente genera el scaffolding siguiendo el mismo patrón que ya usan `incidents.ts`/`inventory.ts` y `InventoryManager.tsx`, en vez de improvisar una estructura distinta cada vez.

## Input esperado

```
domain = {
  name: string,          // nombre del dominio, en minúsculas (ej: "compras")
  displayName: string,   // nombre visible en la pestaña (ej: "Compras")
  endpoints: [            // al menos "list"; "create" si el dominio permite alta
    { method: string, path: string, purpose: string }
  ],
  fields: [                // campos del recurso principal, para el formulario/tabla
    { name: string, type: string, required: boolean }
  ]
}
```

## Reglas

1. **Cliente API**: crear `uis/backoffice/src/api/<domain>.ts`, reutilizando el `client.ts` compartido (mismo wrapper de fetch, manejo de errores y base URL que ya usan `incidents.ts`/`inventory.ts`). Un archivo por dominio — conforme a `.agents/rules/separacion-por-dominio.md`.
2. **Vista**: crear `uis/backoffice/src/<DisplayName>Manager.tsx`, reutilizando únicamente las clases CSS ya existentes en `App.css` (`.panel`, `.panel-heading`, `.field`, `.primary-button`, `.table-wrap`, `.summary-grid`, etc.). No crear ni modificar estilos salvo que el dominio lo requiera explícitamente — y en ese caso, justificarlo.
3. **Registro de pestaña**: añadir el nuevo dominio al `activeView`/navegación de `App.tsx`, sin alterar el comportamiento de las pestañas existentes (Incidencias, Inventario).
4. **Tipos compartidos**: si el dominio necesita tipos nuevos, añadirlos a `packages/shared/types`, no duplicarlos localmente en el backoffice.
5. **Documentación**: si el módulo introduce lógica de negocio relevante, anotarlo en `memory-bank/progress.md`.

## Criterios de aceptación (verificables)

- Existe `uis/backoffice/src/api/<domain>.ts` y expone al menos una función `list` (y `create` si el input lo pide).
- Existe `uis/backoffice/src/<DisplayName>Manager.tsx` y compila sin errores de TypeScript (`npm run build` en `uis/backoffice`).
- Aparece una pestaña nueva en la navegación de `App.tsx` que renderiza el componente sin errores en `npm run dev`.
- Las pestañas Incidencias e Inventario siguen funcionando exactamente igual que antes del cambio.
- No se introduce ninguna clase CSS nueva sin justificación explícita en el commit.

## Salida

- `uis/backoffice/src/api/<domain>.ts`
- `uis/backoffice/src/<DisplayName>Manager.tsx`
- Diff mínimo en `uis/backoffice/src/App.tsx` (import + entrada de navegación + render condicional), sin tocar el resto de vistas.
