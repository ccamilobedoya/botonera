# Reglas de seguridad

> Las fichas citan las que aplican; el revisor las usa en modo «judgement». **Estado:** _aprobada_ = decidida por el dueño (2026-11-04, con F-000).

| #   | Regla                                                                                                                                                                                        | Cómo se comprueba                                                                              | Estado   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------- |
| S1  | Toda entrada del host (reports OUT, Raw HID, texto que llega a una herramienta) se **limita en tamaño antes de leerla**; lo que no coincide con el contrato se descarta                      | Prueba de ataque en la ficha que la toque; revisor en modo juicio                              | aprobada |
| S2  | Los **ganchos de prueba no existen** en el firmware de producción (`#ifdef BOTONERA_TEST_HOOK`, `AUTO_TYPE`); `scripts/review` falla si el artefacto de producción lleva la cadena marcadora | `review.d/` cuando exista el artefacto (F-001)                                                 | aprobada |
| S3  | Ninguna macro, keymap de ejemplo ni registro escribe secretos ni términos privados; el escáner de privacidad corre también sobre `firmware/` y `experiments/`                                | `scripts/review` (privacy) y hooks de git                                                      | aprobada |
| S4  | Los hooks de git y de Claude Code **fallan cerrado**: ante un error o una entrada ilegible, bloquean                                                                                         | Casos de `.checks/`                                                                            | aprobada |
| S5  | `tools/build` compila en contenedores **sin red** (`--network none`) con imágenes fijadas por _digest_ o por `Dockerfile` con versiones fijas; nada se instala en el PC del dueño            | Lectura de `tools/build` y `docker/`; el revisor marca cualquier cambio ahí como zona sensible | aprobada |
| S6  | El firmware nunca deja una tecla presionada: todo envío de teclas termina con un report vacío, y desde F-007 hay watchdog                                                                    | Pruebas con el pad en el servidor (`EVIOCGKEY` en cero)                                        | aprobada |
| S7  | Nada se escribe en flash dentro del bucle de barrido; la EEPROM emulada se escribe solo al cambiar un ajuste                                                                                 | Revisor en modo juicio                                                                         | aprobada |

## Secretos del repo y de la máquina

- `.claude/settings.json` niega `Read` sobre `.env*`, `local.env`, llaves y `~/.config/**`; el hook `.checks/block_secrets.py` bloquea comandos de Bash que los nombren. Son barreras contra descuidos.
- Los agentes lanzados con `tools/launch-agent` solo tienen una **lista cerrada de comandos**: ese es el control real.
- La configuración local (publicación de fichas, lista de términos privados) vive fuera del repo: `docs/local-config.md`.

## Zonas sensibles (el revisor entra en modo juicio)

`tools/`, `scripts/`, `review.d/`, `.checks/`, `docker/`, `.claude/`, descriptores USB (`usb_descriptors.c`), ganchos de prueba, cualquier `package.json` o `qmk.lock`.
