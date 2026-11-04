# Proceso: de la ficha a `main`

> Aprobado por el dueño el 2026-11-04 (ADR-0007), calcado del de Tintero. Lo ejecuta el **arquitecto** (sesión principal), que **no** hace commits ni push. Hay **dos puertas del dueño**: la ficha y la integración. Los agentes **escriben el firmware**; el dueño graba el `.uf2` y prueba en Windows, iPad y Mac.

Carpetas de trabajo (_worktrees_), fuera del repo: `../botonera-wt/F-NNN-{acc,dev,ver}`. Cada una con `npm ci`.

**Lanzar un agente:** `tools/launch-agent <rol> <modelo> <carpeta> <encargo.md> [tope-usd]` (contexto limpio, tope de gasto, costo y tokens en `.agents/`). Roles: `programmer`, `verifier`, `reviewer`, `integrator`.

**Al final de cada fase** el arquitecto arma el encargo con **`tools/integrator-brief`** (lista exacta de archivos, primera línea ≤ 72 caracteres) y lanza al **integrador** (Haiku). Los informes de los agentes quedan en `.agents/` durante el ciclo y el arquitecto los consolida en `docs/reports/F-NNN/` **al cierre**.

## Reglas del arquitecto al orquestar (lecciones de Tintero)

1. **Encargos al integrador solo con `tools/integrator-brief`**: nunca escritos a mano.
2. **Lo que un agente necesita va primero a su rama:** si el arquitecto cambia una regla o herramienta que el agente va a usar, el integrador la guarda en `main` y se une a la rama **antes** de lanzar al agente.
3. **Aclaraciones de la ficha:** si después de la fase 1 se aclara un CA, el encargo de la verificación lo dice («el CA-N se aclaró: …»).
4. **Encargos completos:** el agente no ve esta conversación ni la de la base de conocimiento del dueño. El encargo trae la ruta de la ficha, la carpeta, la fase, los comandos y todo dato concreto. Otro modelo puede ser el que haga el trabajo.
5. **Esperar agentes:** cada `tools/launch-agent` en primer plano o en una tarea en segundo plano propia. **Nunca** bucles con `pgrep -f`.
6. **Cadenas de comandos:** cada paso con `|| exit 1`, `set -o pipefail`, `test -s <encargo>` antes de lanzar al integrador, y **nunca** pasar la salida de `tools/launch-agent` por un _pipe_ (tapa el código 3 de STOPPED).
7. **Si un agente termina con error** (`is_error`): revisar qué dejó a medias, esperar y relanzarlo con una nota de lo que ya existe.
8. **Datos concretos en la ficha:** nombres de archivos, rutas, funciones con firma, formatos y marcas que las pruebas necesiten.
9. **Lo que toca el aparato real** (grabar el `.uf2`, enchufar en Windows, iPad o Mac) lo hace el dueño con el guion «Pasos del dueño» de la ficha; los CA que dependen de eso se marcan «pendiente de Cris» y no bloquean el cierre del código.
10. **`main` es una copia compartida:** los encargos en `main` van con `tools/integrator-brief --only <ruta>`, y el arquitecto **lee la lista** antes de lanzar al integrador.
11. **Pruebas sin reintentos que tapen defectos:** si el verificador necesita reintentar algo que la ficha exige a la primera, lo reporta como hallazgo.
12. **Los contenedores no ven el USB:** compilar sí, grabar no. El pad de pruebas en el servidor se resuelve en F-002.

## 0 · Ficha

1. Escribir `docs/specs/F-NNN-<nombre>.md` desde `TEMPLATE.md`, con la sección **Para el arquitecto**, y marcar «Listo para programar».
2. `tools/publish-spec docs/specs/F-NNN-….md` → el dueño la lee en su base de conocimiento.
3. **Puerta 1:** el dueño aprueba. Estado `aprobada`.
4. **Integrador** en `main`, fase `spec`, con push.

## 1 · Pruebas primero

1. `git worktree add ../botonera-wt/F-NNN-acc -b acc/F-NNN main`
2. **Verificador**, fase `tests`, en esa carpeta. Solo recibe la ruta de la ficha.
3. Si marca algún CA **NO VERIFICABLE** → la ficha vuelve al arquitecto; si el cambio es de fondo, otra vez a la puerta 1.
4. **Integrador** en `acc/F-NNN`, fase `tests`, rol `verifier`, con push.

## 2 · Programar

1. `git worktree add ../botonera-wt/F-NNN-dev -b dev/F-NNN main` (sin las pruebas de aceptación).
2. **Programador** con el modelo que diga la ficha. Recibe la ficha y, en vueltas siguientes, solo el informe de lo que falló.
3. **Integrador** en `dev/F-NNN`, fase `code`, rol `programmer`, con push.

## 3 · Verificar

1. `git worktree add ../botonera-wt/F-NNN-ver -b ver/F-NNN dev/F-NNN`; el **integrador** une `acc/F-NNN` (`merge --no-ff`).
2. **Verificador nuevo**, fase `verification`. No recibe nada del programador.
3. **Integrador** en `ver/F-NNN`, fase `verification`, rol `verifier` con **`--base HEAD`**, con push.
4. **NO CUMPLE** → informe al programador (vuelta +1) → volver a 2; luego el integrador vuelve a unir `dev/F-NNN` en `ver/F-NNN`.
5. **3 vueltas sin cumplir → se detiene.** El arquitecto revisa si la ficha está mal.

## 4 · Revisar (herramientas primero)

En la carpeta `ver`: `scripts/review` (y `tools/build` del objetivo de la ficha). El arquitecto guarda la salida en `.review/review.txt` y el cambio en `.review/diff.patch` (`git diff main`): el revisor no corre comandos, solo lee.

- Sale **0** (limpio) → sin modelo, sigue a 5.
- Sale **1** (hallazgo) → **revisor** modo «findings» con **Haiku**, separando por dueño → lo de `tests/acceptance/` vuelve al **verificador** (rama `ver`) y lo demás al **programador** (rama `dev`; luego se une y se vuelve a 3).
- Toca zona sensible (`tools/`, `scripts/`, `review.d/`, `docker/`, ganchos de prueba, descriptores USB) o dependencia nueva → **revisor** modo «judgement» con **Sonnet**.
- **Integrador** en `ver/F-NNN`, fase `review` (informe), con push.

## 5 · Cierre

1. El arquitecto lee los informes, llena **Resultado obtenido** y **Resumen para aprobar**, y publica la ficha.
2. **Puerta 2:** el dueño aprueba integrar.
3. **Integrador:** une `ver/F-NNN` en `main` (`merge --no-ff`, fase `close`) y sube `main`.
4. El arquitecto borra los _worktrees_; actualiza `docs/metrics.md`, `docs/lessons.md` (y su sección «Para la plantilla»), `docs/pending.md` y la nota de estado (fuera del repo); `tools/map`; **integrador** fase `process` en `main`, con push.

## Regresión de los agentes

Cada vez que el arquitecto cambie un `.claude/agents/*.md`: correr `tests/agents/` (ver su README) y confirmar el resultado esperado.
