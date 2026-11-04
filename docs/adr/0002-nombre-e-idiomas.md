# ADR-0002 · Nombre Botonera; inglés para lo público, español para el proceso

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

El repo es público y el dueño quiere que cualquiera lo use; el dueño lee las fichas en el celular en español.

## Decisión

El proyecto se llama **Botonera** (nombre en español, no se traduce). Código, identificadores, comentarios, README, CONTRIBUTING, SECURITY, mensajes de commit, issues, `CLAUDE.md` y los agentes van en **inglés**. Las fichas (`docs/specs/`), los ADR, los informes y los documentos del proceso van en **español** con ortografía completa.

## Consecuencias

`README.es.md` es el par en español del README; la paridad de encabezados la comprueba `scripts/review`.
