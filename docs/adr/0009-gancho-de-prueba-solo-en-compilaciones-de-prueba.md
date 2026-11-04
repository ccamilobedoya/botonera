# ADR-0009 · Gancho de prueba por Raw HID solo en compilaciones de prueba

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

Para que la aceptación corra en el servidor sin el dueño, el pad tiene que aceptar órdenes de prueba («simula la tecla 3», «escribe el registro»). Cualquiera con acceso al USB podría usarlas.

## Decisión

Los ganchos de prueba existen **solo** en compilaciones marcadas (`-DBOTONERA_TEST_HOOK`, `-DAUTO_TYPE`), que producen un artefacto aparte con una cadena marcadora. La compilación de producción no los contiene, y `scripts/review` falla si el artefacto de producción lleva la marca (regla S2).

## Consecuencias

Dos artefactos por ficha de firmware. Los ganchos nunca escriben en flash ni cambian el keymap.
