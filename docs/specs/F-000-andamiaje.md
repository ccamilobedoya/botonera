# F-000 · Andamiaje del repositorio

**Estado:** aprobada · puerta 1 el 2026-11-04 · en curso
**Quién la hace:** el **arquitecto**, como excepción de arranque (el ciclo necesita que esto exista). Al final la revisa un **verificador nuevo** y se corre la regresión de los agentes.
**Modelo del programador:** no aplica (arquitecto). Las copias y adaptaciones mecánicas pueden ir a un agente Haiku con encargo completo.
**Dependencias nuevas permitidas:** `copier` ya instalado con `uv tool` (para `new` de la plantilla); imagen Docker de la CLI de QMK fijada por _digest_; imagen Docker propia para el SDK de la Pico (ensayo F-001), construida desde un `Dockerfile` del repo con versiones fijadas. Nada en el PC de Cris.

## Listo para programar (se marca antes de pedir aprobación)

- [x] Cada CA se puede comprobar con un comando, con valores concretos.
- [x] Los archivos a crear están listados.
- [x] Lo que queda fuera de alcance, escrito.
- [ ] Cris decidió las tres cosas abiertas del final.

## Contexto

Ya están decididos (nota raíz, D1–D9): nombre Botonera, repo público MIT, inglés para lo público y español para fichas y proceso, placa verde, QMK con Vial, ensayo con TinyUSB, manual más huella, gancho Raw HID, roles. La plantilla de proyectos del dueño genera la base de cualquier proyecto (hooks, revisión, privacidad, agentes, CI, CHANGELOG), pero **no sabe de firmware**: lo que falte se construye aquí y se anota para la plantilla (R7). El proceso con agentes ya existe en Tintero: se copia y se adapta, no se reinventa.

## Alcance

### 1. Generar el repo con la plantilla

`new` de la plantilla de proyectos (herramienta local del arquitecto, fuera del repo) sobre la carpeta del repo con estas respuestas (se guardan en `.la plantilla de proyectos/`, sin versionar):

| Pregunta          | Valor                                          | Por qué                                                                                 |
| ----------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| `project_name`    | `botonera`                                     | D1                                                                                      |
| `visibility`      | `public`                                       | D2                                                                                      |
| `stack`           | `docs`                                         | No hay stack de firmware; el código C y el userspace de QMK se agregan a mano (punto 3) |
| `license`         | `MIT`                                          | D2                                                                                      |
| `docs_language`   | `en+es` (paridad `README.md` ↔ `README.es.md`) | D3                                                                                      |
| `ui_i18n`         | `no`                                           | No hay interfaz de texto                                                                |
| `agents`          | `subagents`                                    | Se reemplazan por los cuatro roles de Tintero (punto 4)                                 |
| `ci`              | `github`                                       |                                                                                         |
| `claude_language` | `es`                                           | Los documentos del proceso son en español; **Cris decide** (abierto 1)                  |
| `github_owner`    | `ccamilobedoya`                                |                                                                                         |

Después de generar: `git check-ignore -v CLAUDE.local.md` tiene que decir que está ignorado. En `CLAUDE.local.md` van los punteros a la base de conocimiento del dueño (nota de estado y Principios). **Ni el nombre de la plantilla ni rutas de la máquina del dueño en lo versionado** (lo comprueba el escáner).

### 2. Estructura (lo que se suma a lo generado)

```text
firmware/                 userspace de QMK (documento 4, opción a; abierto 2)
  keyboards/botonera/     info.json, config.h, rules.mk, botonera.c (vacíos hasta F-002, con README)
  keymaps/default/        keymap.c de ejemplo (vacío hasta F-002)
  qmk.lock                commit de Vial/QMK fijado; lo lee tools/build
experiments/
  hid-from-scratch/       el ensayo F-001 (vacío, con README que apunta a la ficha)
tools/
  build                   compila en Docker (QMK o el ensayo); deja build/*.uf2
  lanzar-agente, encargo-integrador, check-scope, publicar-ficha, mapa, revisar
                          copiados de Tintero y adaptados (rutas, nombres, sin Node donde no haga falta)
  host/                   herramienta de host (vacía hasta F-002, con README)
  lib/                    lo que necesiten los de arriba
docs/
  fichas/                 PLANTILLA.md (la de Tintero + sección «Para el arquitecto»), README.md, F-000, F-001
  decisiones/             ADR-0000 plantilla y ADR-0001 a ADR-0009 (abajo)
  plantillas/             informes del programador, verificador, revisor; resumen de aprobación
  PROCESO.md              el de Tintero, adaptado: fases, worktrees en ../botonera-wt/, roles
  seguridad.md            reglas S (abajo)
  lecciones.md            tabla de lecciones + sección «Para la plantilla»
  metricas.md             vueltas, hallazgos y costo por ficha
  MAPA.md                 generado por tools/mapa
  configuracion-local.md  qué archivos locales existen y qué formato tienen (sin valores)
tests/
  agents/                 ficha de juguete y README de la regresión (de Tintero)
  acceptance/             vacío; una carpeta por ficha
.claude/agents/           programador.md, verificador.md, revisor.md, integrador.md (de Tintero, adaptados)
.claude/settings.json     deny y hooks (lo generado + los de Tintero que apliquen)
docker/
  qmk.digest              digest de la imagen de la CLI de QMK
  pico-sdk.Dockerfile     imagen del ensayo: toolchain ARM + pico-sdk en una etiqueta fija
CLAUDE.md                 convenciones para todos los agentes (reglas de abajo)
```

### 3. QMK como userspace (abierto 2)

- `tools/build qmk` clona QMK/Vial en `~/.cache/botonera/qmk` en el commit de `firmware/qmk.lock` (si no está), monta `firmware/` como userspace y corre `qmk compile -kb botonera -km default` dentro de la imagen de la CLI de QMK. En F-000 solo tiene que **fallar con un mensaje claro** («no keyboard yet, see F-002») y dejar probada la imagen (`qmk --version`).
- `tools/build hid-from-scratch` construye la imagen de `docker/pico-sdk.Dockerfile` y compila `experiments/hid-from-scratch/` con CMake. En F-000 compila el ejemplo `blink` del SDK como prueba de la cadena.
- Ninguna de las dos escribe fuera de `build/` y de `~/.cache/botonera/`.

### 4. Agentes y proceso (de Tintero)

- Copiar `.claude/agents/{programador,verificador,revisor,integrador}.md`, `tools/lanzar-agente`, `tools/encargo-integrador`, `tools/check-scope`, `tools/publicar-ficha`, `tools/mapa`, `docs/PROCESO.md`, `docs/plantillas/`, `tests/agents/` de el repo público de Tintero y adaptar: nombre del repo, carpetas de trabajo `../botonera-wt/`, comandos de prueba (`tools/build`, `scripts/review` en vez de `npm`), y **quitar lo que dependa de Node** o reescribirlo en Python 3 con biblioteca estándar (abierto 3).
- `tools/check-scope`: programador toca `firmware/`, `experiments/`, `tools/host/` y pruebas unitarias; verificador solo `tests/acceptance/`; revisor nada; integrador solo git.
- Hooks: lo que generó la plantilla (privacidad, never-commit, secretos) más el de Tintero que bloquea `git` con `--force`, `--no-verify`, `reset`, `rebase`.
- `tools/publicar-ficha` publica a la nota _Fichas_ de la base de conocimiento del dueño usando `~/.config/botonera/local.env` (URL del ETAPI, archivo del token, id de la nota). Nada de eso en el repo.

### 5. ADR iniciales (`docs/decisiones/`)

| ADR  | Título                                                                                                            |
| ---- | ----------------------------------------------------------------------------------------------------------------- |
| 0001 | El dueño aprueba stack, arquitectura y tecnología                                                                 |
| 0002 | Nombre Botonera; inglés para lo público, español para el proceso                                                  |
| 0003 | Licencia MIT; qué licencia tienen los archivos del userspace de QMK (se investiga aquí y se escribe la respuesta) |
| 0004 | Firmware en QMK con Vial, como userspace externo con commit fijado                                                |
| 0005 | Un ensayo con TinyUSB sin QMK, solo para aprender; no se reutiliza en el producto                                 |
| 0006 | Comandos por sistema: capa manual manda sobre la huella de enumeración                                            |
| 0007 | Flujo de desarrollo con agentes; commits y push solo por el integrador                                            |
| 0008 | Nada privado en el repo; el keymap personal fuera; lista de términos privados fuera                               |
| 0009 | Gancho de prueba por Raw HID solo en compilaciones de prueba                                                      |

### 6. Reglas de seguridad (`docs/seguridad.md`)

- **S1.** Toda entrada del host (reports OUT, Raw HID) se limita en tamaño antes de leerla; lo que no coincide con el contrato se descarta.
- **S2.** El gancho de prueba **no existe** en el firmware de producción (`#ifdef BOTONERA_TEST_HOOK`); `scripts/review` falla si el `.uf2` de producción lo contiene (se busca una cadena marcadora).
- **S3.** Ninguna macro escribe secretos; el escáner de privacidad corre también sobre los keymaps.
- **S4.** Los hooks fallan cerrado.
- **S5.** `tools/build` corre en contenedores sin red después de bajar las dependencias fijadas.

### 7. `CLAUDE.md` del repo (reglas para todos, en español, abierto 1)

La ficha manda; los ADR obligan; idioma (inglés código y público, español proceso); commits solo el integrador; nada privado; sin archivos temporales; entrada externa con tope; hooks fallan cerrado; comandos (`tools/build`, `scripts/review`, `tools/revisar`, `tools/check-scope`); quién toca qué; y «cómo orientarse sin explorar» (`docs/MAPA.md`, `docs/PROCESO.md`).

**Fuera de alcance:** cualquier línea de firmware real (F-001 y F-002), la definición del teclado en QMK, la herramienta de host, publicar en GitHub (lo pide Cris), el pad de pruebas en el servidor.

## Criterios de aceptación

- **CA1.** la comprobación `check` de la plantilla de proyectos sobre la carpeta del repo sale 0 (sin `missing`); `grep -ri` del nombre de la plantilla sobre `git ls-files` no devuelve nada; `git check-ignore -v CLAUDE.local.md` lo marca ignorado.
- **CA2.** `scripts/review` sale 0 en el repo recién generado, con todo en verde: privacidad, never-commit, paridad `README.md`/`README.es.md`, enlaces, markdownlint.
- **CA3.** `tools/build qmk` termina con «no keyboard yet (see F-002)» y código 1, **después** de imprimir la versión de la CLI de QMK desde la imagen fijada (`qmk --version` muestra una versión).
- **CA4.** `tools/build hid-from-scratch` compila `blink` del SDK de la Pico y deja `build/hid-from-scratch/blink.uf2` de más de 10 KB; corrido dos veces, el `.uf2` es idéntico (`sha256sum`).
- **CA5.** `tools/mapa` genera `docs/MAPA.md` con todas las carpetas del punto 2.
- **CA6.** Regresión de los agentes (`tests/agents/README.md`): el verificador marca la ambigüedad plantada; el integrador se detiene ante un encargo que no coincide con `git status`.
- **CA7.** `tools/check-scope programador --base main` falla si el programador toca `docs/fichas/`; `tools/check-scope verificador` falla si toca `firmware/`.
- **CA8.** `tools/publicar-ficha docs/fichas/F-000-andamiaje.md` crea o actualiza la nota de fichas de la base de conocimiento del dueño (se comprueba leyendo la nota) sin que ningún archivo del repo contenga la URL ni el id.
- **CA9.** Un commit con la cadena de prueba de la lista privada es rechazado por el hook; el mismo texto sin ella pasa.
- **CA10.** `docs/decisiones/` tiene ADR-0001 a ADR-0009 con estado «aceptada» y ADR-0003 responde con fuentes qué licencia aplica a `firmware/keyboards/botonera/`.
- **CA11.** El `.uf2` de CA4 **no** se versiona (`build/` ignorado) y `git status` queda limpio tras CA1–CA10.

## Presupuestos

- `new` de la plantilla + adaptaciones: una sesión del arquitecto. Copias mecánicas a Haiku si se delega: tope 2 USD.
- Imagen del SDK de la Pico: construirse en menos de 10 min en el servidor; tamaño anotado en la nota de estado.

## Seguridad

Reglas S1–S5 escritas en `docs/seguridad.md` (sin código todavía); hooks fallan cerrado (CA9).

## Archivos

Todo el punto 2. Fuera del repo: `~/.config/botonera/local.env`, `~/.config/botonera/private-terms.txt` (600; los crea Cris con el contenido que diga `docs/configuracion-local.md`).

## Para el arquitecto

- **Flujo:** `new` de la plantilla → repo con piezas → se suman firmware, experimentos, herramientas y proceso → `scripts/review` y la comprobación `check` de la plantilla dicen qué falta → cada ficha siguiente trabaja dentro de ese marco.
- **Piezas que entran en juego:** la plantilla de copier (genera), el escáner de privacidad (bloquea), `scripts/review` (agrega), la CLI de QMK en Docker (compila), el SDK de la Pico en Docker (compila el ensayo), los cuatro agentes (ejecutan), `check-scope` (vigila quién tocó qué).
- **Límites:** la plantilla no sabe de firmware; lo que se agregue a mano es lo que vuelve a la plantilla. QMK se fija por commit, no por versión. Los contenedores no tienen acceso al USB: nada de aquí graba la placa.
- **Qué se puede predecir:** nada eléctrico. Sí una pregunta de método: ¿qué pasa si el escáner de privacidad encuentra la palabra «botonera» en otro repo del dueño? (Nada: es pública. Al revés sí: el nombre de la plantilla en este repo lo bloquea).

## Abierto (decide Cris)

1. ¿`CLAUDE.md` y los agentes en español (como Tintero) o en inglés (como la plantilla de proyectos)?
2. ¿QMK como userspace externo con commit fijado (propuesta) o como submódulo?
3. ¿Las herramientas de Tintero que dependen de Node se reescriben en Python (sin Node en el repo) o se acepta Node solo para `tools/`?

## Resultado esperado

Un repo en la carpeta del repo donde la próxima ficha (F-001) puede lanzarse con `tools/lanzar-agente` sin preparar nada más, y donde `scripts/review` y los hooks ya protegen lo privado.

## Terminado (se marca al cerrar)

- [ ] CA1–CA11 en verde (informe del verificador).
- [ ] Nota de estado al día; `docs/lecciones.md` con las primeras filas de «Para la plantilla».
- [ ] Integrador: commit inicial en `main`. Push cuando Cris lo pida.

---

## Resultado obtenido

Hecho por el arquitecto el 2026-11-04, con el verificador y el integrador como agentes.

- **Repo generado** con `new` de la plantilla (stack `docs`, público, MIT, `en+es`, agentes, CI, `claude_language` en inglés) y adaptado: proceso de Tintero (`docs/process.md`), cuatro agentes en inglés (`programmer`, `verifier`, `reviewer`, `integrator`), herramientas `tools/launch-agent`, `integrator-brief`, `check-scope`, `publish-spec`, `map`, `build` y `acceptance` (Node 24, TypeScript directo, pruebas con Vitest), `docker/` con la CLI de QMK fijada por _digest_ y una imagen propia del SDK de la Pico 2.3.1 con TinyUSB y picotool, ADR-0001 a ADR-0009, reglas S1–S7, plantillas de informes, regresión de agentes y las fichas F-000 y F-001.
- **Desviaciones de la ficha:** nombres de carpetas y herramientas en inglés (D3): `docs/specs/` en vez de `docs/fichas/`, `docs/adr/`, `docs/templates/`, `docs/reports/`, `docs/process.md`, `docs/security.md`, `docs/lessons.md`, `docs/metrics.md`, `docs/MAP.md`, `docs/local-config.md`; `docs/decisions.md` se mantiene como índice con estado (pieza de la plantilla) y apunta a los ADR; el humo de la cadena del SDK es `experiments/blink/` propio, no el `blink` del SDK (los ejemplos viven en otro repo); exención `N13` en `project.toml` porque la plantilla de ficha está en español; `tools/acceptance F-NNN` como punto de entrada único de las pruebas de aceptación (no estaba en la ficha; salió de la vuelta 2).
- **Hallazgos de camino:** el SDK de la Pico 2.x baja picotool por red al configurar, así que la imagen lo compila e instala (4 GB); prettier reformatea los JSON de la plantilla (excluidos en `.prettierignore`); markdownlint exige H1 en los agentes y lenguaje en cada cerca; un patrón de permiso `Bash(prefijo:*)` solo coincide con un token completo.
- **Vueltas de verificación:** 3. Vuelta 1: CA2 (faltaban los binarios de `.checks/bin/` en el _worktree_), CA5 (`tools/map` omitía `docs/reports`) y CA9 (sin permiso para el hook) → corregidos en `9b4b18f`. Vuelta 2: sin evidencia, el patrón de permiso no cubría el `check.sh` → `tools/acceptance` en `8f44a4f`. Vuelta 3: ver el informe en `docs/reports/F-000/`.
- **Regresión de agentes:** los tres pasos dieron lo esperado (CA1 NO VERIFICABLE con la pregunta del rango; CA2 FALLA con −478; el integrador se detiene ante `extra.txt`).
- **Licencia (ADR-0003):** los archivos del userspace de QMK van bajo GPL-2.0-or-later con cabecera SPDX (pendiente para F-002); el resto MIT; nota en `LICENSE`.
- **Fuera del repo, creado por el arquitecto:** `~/.config/botonera/local.env` (URL del ETAPI, archivo del token, nota de fichas) y `private-terms.txt` (lista inicial; el dueño la revisa), ambos 600; `git config --local checks.privateTermsFile`.
- **Costo de agentes:** verificador USD 0,23 + 0,05 + vuelta 3; regresión USD 0,18; integrador USD 0,01.

## Resumen para aprobar

Una pantalla.
