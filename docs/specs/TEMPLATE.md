# F-NNN · Título

**Estado:** borrador | aprobada | en curso | verificada | cerrada
**Modelo del programador:** sonnet | haiku (ficha mecánica)
**Dependencias nuevas permitidas:** ninguna | `paquete` (por qué)

## Listo para programar (se marca antes de pedir aprobación)

- [ ] Cada CA se puede comprobar con una prueba o un paso escrito para el dueño, con valores concretos.
- [ ] El contrato (archivos, funciones con firma, formatos, errores) está escrito.
- [ ] Los archivos a crear o tocar están listados.
- [ ] Presupuestos (flash, RAM, tiempos) y reglas de seguridad que aplican, nombrados.
- [ ] Lo que queda fuera de alcance, escrito.
- [ ] Los criterios que solo el dueño puede probar están marcados «pendiente de Cris» con su guion.
- [ ] La sección **Para el arquitecto** está escrita.

## Contexto

Por qué existe; ADR que aplica.

## Alcance

Qué entra. **Fuera de alcance:** qué no.

## Requisitos

- R1.

## Contrato

Archivos, funciones con nombre y firma, formatos, errores, nombres y rutas que las pruebas necesiten.

## Criterios de aceptación

- **CA1.** Dado …, cuando …, entonces … (con valores). Check: `comando`.

## Presupuestos

Flash, RAM, tiempos.

## Seguridad

Reglas de `docs/security.md` que aplican y cómo se comprueban. Siempre:

- [ ] Toda entrada del host con **límite de tamaño antes de parsear** (S1).
- [ ] El gancho de prueba no existe en la compilación de producción (S2).
- [ ] Dependencias nuevas nombradas arriba (o ninguna).

## Archivos

A crear / a tocar.

## Para el arquitecto (lo que el dueño tiene que entender de esta ficha)

- Flujo de información: de dónde sale, por dónde pasa, dónde termina.
- Funciones o piezas de QMK que entran en juego y qué hace cada una.
- Límites y supuestos.
- Qué se puede predecir antes de probar y qué se mide.

## Pasos del dueño (si hay criterios pendientes de Cris)

1.

## Resultado esperado

Cómo se ve cuando está listo.

## Terminado (se marca al cerrar)

- [ ] Todos los CA pasan en la verificación (informe adjunto); los pendientes del dueño, anotados con fecha.
- [ ] `scripts/review` limpio, o hallazgos resueltos o anotados como mejora.
- [ ] `tools/check-scope` limpio para cada rol.
- [ ] Resultado obtenido y resumen para aprobar escritos; métricas y lecciones actualizadas; «Para la plantilla» si aplica.
- [ ] El dueño aprobó integrar.

---

## Resultado obtenido

Lo llena el arquitecto al cerrar: qué se hizo, vueltas, hallazgos, desviaciones.

## Resumen para aprobar

Una pantalla, con `docs/templates/approval-summary.md`.
