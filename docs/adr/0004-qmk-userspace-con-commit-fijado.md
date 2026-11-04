# ADR-0004 · Firmware en QMK como userspace externo con commit fijado

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

El dueño quiere aprovechar QMK con el menor roce ante sus cambios, poder migrar a mano a una versión posterior y que sea sencillo.

## Decisión

El firmware del producto es QMK. El repo es un **userspace externo**: QMK no vive en el repo; `firmware/qmk.lock` fija el commit exacto que `tools/build qmk` clona en caché y usa como `overlay_dir`. Migrar es cambiar ese commit, recompilar y correr las pruebas. Vial queda como extensión posterior (D10): si su fork no soporta userspace externo, no se usa.

## Consecuencias

F-002 verifica que la versión fijada compile el teclado desde el userspace. Si QMK cambia el mecanismo de userspace, se anota en `docs/lessons.md` y se decide si pasar a submódulo.
