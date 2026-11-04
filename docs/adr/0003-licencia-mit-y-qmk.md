# ADR-0003 · Licencia MIT; qué cubre y qué no frente a QMK

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

El dueño eligió MIT. QMK es GPL-2.0 (o posterior) y la definición del teclado y el keymap se compilan dentro de QMK.

## Decisión

El repo se publica bajo MIT: herramientas, documentación, experimentos (Pico SDK y TinyUSB son BSD-3 y MIT) y el generador de keymaps. **Los archivos del userspace de QMK** (`firmware/keyboards/botonera/` y `firmware/keymaps/`) se enlazan con QMK al compilar: el firmware resultante es GPL y esos archivos se distribuyen bajo GPL-2.0-or-later, con su cabecera SPDX, igual que hace la comunidad QMK con los teclados y keymaps que viven fuera del árbol principal. El `LICENSE` del repo lo dice en una nota.

## Consecuencias

Pendiente de F-002: la cabecera SPDX en cada archivo de `firmware/` y la nota en `LICENSE` y en el README. Esta decisión sale de leer la licencia de QMK; si el dueño quiere otra lectura, consulta a alguien de derecho antes de publicar.
