# ADR-0005 · Un ensayo con TinyUSB sin QMK, solo para aprender

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

QMK esconde el descriptor, la enumeración y los reports, que es lo que el dueño quiere entender como arquitecto (módulo M7 de su curso).

## Decisión

La ficha F-001 escribe un teclado HID mínimo con el SDK de la Pico y TinyUSB, con los descriptores a mano y un registro de la enumeración, probado en Windows, iPad y Mac. Vive en `experiments/` y **no se reutiliza** en el producto.

## Consecuencias

Dos cadenas de compilación (QMK y Pico SDK), las dos en Docker. El ensayo sirve además para medir la huella de enumeración real antes de confiar en la detección de QMK.
