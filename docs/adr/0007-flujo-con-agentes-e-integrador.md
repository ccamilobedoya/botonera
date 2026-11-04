# ADR-0007 · Flujo de desarrollo con agentes; commits y push solo por el integrador

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

El proceso de Tintero (ficha → pruebas primero → código → verificación → revisión → integración, con dos puertas del dueño) funcionó en 19 fichas.

## Decisión

Se adopta el mismo ciclo (`docs/process.md`). Los agentes **escriben el firmware** (a diferencia de Tintero). El arquitecto no hace commits ni push: los hace el agente **integrador** al final de cada fase, con encargos de `tools/integrator-brief`. Nadie usa `--force`, `reset` ni `rebase`. Cada ficha lleva la sección **Para el arquitecto**, que el dueño lee y que se documenta en su curso.

## Consecuencias

Tres vueltas sin cumplir detienen la ficha. Los informes quedan en `docs/reports/F-NNN/` al cierre.
