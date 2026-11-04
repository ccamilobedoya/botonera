# Botonera

[English](README.md)

Un macropad de escritorio con RP2040 que Windows, iPadOS y macOS ven como un teclado más, sin driver ni app que instalar, y que manda un comando distinto según el sistema: la misma tecla copia con `Ctrl+C` en Windows y con `Cmd+C` en un iPad o un Mac. Nueve teclas, un encoder rotatorio y una OLED pequeña, primero en protoboard y después en una PCB propia. El firmware es [QMK](https://qmk.fm); el mapa de teclas se escribe en un archivo de configuración corto, no en C.

**Estado:** andamiaje. Todavía no hay firmware: siguen la ficha F-001 (un teclado USB HID escrito a mano, para aprender el protocolo) y la F-002 (el formato del keymap y la definición del teclado en QMK).

## Cómo va a funcionar

- El pad se declara como teclado USB HID y dispositivo de *consumer control*, así que cada sistema lo maneja con su driver de clase.
- Adivina el sistema del host por cómo lo enumera (la detección de sistema de QMK) y permite forzarlo con una tecla; la OLED muestra el sistema y el perfil activos.
- Las teclas, las macros, las variantes por sistema y los perfiles por aplicación viven en un solo `keymap.toml`; un generador lo convierte en el keymap de QMK y lo valida antes de compilar.

## Inicio rápido

<!-- smoke -->

```bash
scripts/setup
ls docs
```

<!-- /smoke -->

Después, `npm ci` para las herramientas de `tools/`, y `tools/build blink` para comprobar que el contenedor del SDK de la Pico funciona (necesita Docker; nada se instala en tu máquina). Las compilaciones quedan en `build/` como archivos `.uf2` que se arrastran a la placa con BOOTSEL apretado.

## Repositorio

| Carpeta | Qué tiene |
| ------- | --------- |
| `firmware/` | El firmware del producto como *userspace* externo de QMK, fijado a un commit de QMK (`qmk.lock`) |
| `experiments/` | Firmware desechable que enseña o mide algo y nunca se publica |
| `tools/` | Herramientas del proceso: lanzador de agentes, control de alcance, compilación en contenedores fijados |
| `docs/` | Fichas (`specs/`), registros de decisión (`adr/`), proceso, reglas de seguridad, lecciones |
| `docker/` | Las cadenas de herramientas fijadas |

## Desarrollo

Las reglas de trabajo están en [CLAUDE.md](CLAUDE.md). Las fichas, las decisiones y lo pendiente están en [docs/decisions.md](docs/decisions.md), [docs/pending.md](docs/pending.md) y [docs/specs/TEMPLATE.md](docs/specs/TEMPLATE.md). Las fichas, los registros de decisión y los documentos del proceso están en español; el código, los comentarios y todo lo demás, en inglés.

## Licencia

Publicado bajo la licencia MIT. Véase [LICENSE](LICENSE). La definición del teclado y los keymaps de `firmware/` se enlazan con QMK (GPL-2.0-or-later) y llevan esa licencia en sus cabeceras.
