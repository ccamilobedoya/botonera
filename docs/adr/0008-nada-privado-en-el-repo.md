# ADR-0008 · Nada privado en el repo; el keymap personal y la lista de términos, fuera

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

El repo es público desde el primer commit.

## Decisión

Nunca van al repo: datos personales, nombres de personas o empresas, hosts, rutas de la máquina del dueño, llaves ni nada generado con ellas, ni el **keymap personal** del dueño (vive en el pad y en un archivo local ignorado). Los hooks de git y `scripts/review` comparan contra una **lista de términos privados fuera del repo** (`docs/local-config.md`). Si la prueba falla, se reescribe el texto; nunca se aflojan los patrones. La configuración de publicación de fichas también vive fuera.

## Consecuencias

Las referencias privadas del proyecto se guardan en la base de conocimiento del dueño, no aquí. El repo publica un keymap de ejemplo genérico.
