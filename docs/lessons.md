# Lecciones

Hallazgos que se repitieron y en qué regla automática se convirtieron, más lo que la plantilla de proyectos no tenía y aquí hubo que construir.

## Reglas nuevas

| Fecha      | Ficha               | Hallazgo repetido                                                                                                                                       | Regla nueva                                                                                              | Dónde                       |
| ---------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------- |
| 2026-11-04 | F-000 (verificador) | `scripts/review` salía 2 en un _worktree_ nuevo: faltaban los binarios de `.checks/bin/` (no versionados)                                               | Toda carpeta de trabajo arranca con `scripts/setup && npm ci`                                            | `docs/process.md`           |
| 2026-11-04 | F-000 (verificador) | `tools/map` omitía `docs/reports/` por una lista de carpetas heredada                                                                                   | Lista de exclusión solo con lo generado (`.review`, `.agents`, `build`)                                  | `tools/lib/map.ts`          |
| 2026-11-04 | F-000 (verificador) | El verificador no pudo correr el hook `pre-commit` ni su propio `check.sh`: el patrón `Bash(sh scripts/hooks/:*)` no cubre un comando pegado al prefijo | Patrones con el comando completo (`Bash(sh scripts/hooks/pre-commit:*)`, `Bash(sh tests/acceptance/:*)`) | `tools/launch-agent`        |
| 2026-11-04 | F-000               | (heredadas de Tintero: encargos con lista exacta, estado OK/STOPPED, sin `pgrep -f`, sin _pipes_ sobre el lanzador)                                     | Ya aplicadas desde el inicio                                                                             | `docs/process.md`, `tools/` |

## Para la plantilla

Lo que un proyecto de firmware necesita y la plantilla de proyectos no trae. Cuando haya tres o cuatro filas, el arquitecto arma la ficha para la plantilla.

| Fecha      | Ficha | Qué le falta a la plantilla                                                                                          | Cómo se resolvió aquí                                                                                                           | Pieza o pregunta propuesta                                                              |
| ---------- | ----- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| 2026-11-04 | F-000 | Un stack de firmware: no hay opción para C embebido, ni compilación en contenedor como control, ni artefactos `.uf2` | `tools/build` con imágenes fijadas (digest y Dockerfile con etiqueta), `build/` ignorado, `docker/` como zona sensible          | Opción de stack `firmware` con `tools/build` y una comprobación de `review` que compile |
| 2026-11-04 | F-000 | Criterios de aceptación que solo el dueño puede probar (hardware real)                                               | Marca «pendiente de Cris» en la ficha y en el informe del verificador (`PENDIENTE DEL DUEÑO`); no bloquean el cierre del código | Campo de la plantilla de ficha y del informe                                            |
| 2026-11-04 | F-000 | Herramientas de proceso en Node dentro de un stack `docs` (`package.json` solo para `tools/`)                        | `review.d/35-tools.sh` propio que corre `tsc` y `vitest` sobre `tools/`; `npm ci` en la CI                                      | Que `review.d/30-tests.sh` acepte un `package.json` en un stack `docs`                  |
| 2026-11-04 | F-000 | Fichas y ADR con nombres y carpetas propios (`docs/specs/` en español, `docs/adr/`) además de `docs/decisions.md`    | `decisions.md` como índice con estado que apunta a los ADR                                                                      | Que `N09` acepte ADR en archivos aparte                                                 |
