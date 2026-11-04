# ADR-0006 · Comandos por sistema: capa manual manda sobre la huella de enumeración

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

Un teclado USB no puede preguntar al host qué sistema es. Hay tres mecanismos: capa manual, huella de enumeración (QMK OS Detection) y un ayudante instalado en el PC.

## Decisión

Se usan **capa manual** (siempre presente, con indicación en la OLED) y **huella** (automática al enumerar). La manual manda sobre la huella hasta la siguiente enumeración. El ayudante en el PC queda como plan B solo si la huella falla en la medición. Los perfiles por aplicación (Teams, Zoom…) también se cambian a mano.

## Consecuencias

La huella se valida con los registros de F-001. Con hubs, KVM o al volver de suspensión la huella puede dudar: la manual lo cubre.
