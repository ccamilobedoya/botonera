# ADR-0010 · Los circuitos se dibujan y revisan con protoboard-iso

- **Estado:** aceptada
- **Fecha:** 2026-11-04 · **Decidió:** dueño del proyecto

## Contexto

Las fichas del protoboard (matriz, encoder, OLED) necesitan diagramas del circuito para que el dueño los monte y para la documentación pública. El dueño mantiene protoboard-iso, una herramienta abierta de diagramas isométricos de protoboard.

## Decisión

Todo diagrama de circuito del proyecto se hace con protoboard-iso. Si protoboard-iso todavía no puede dibujar lo que una ficha necesita, no se improvisa con otra herramienta: la ficha lo anota como pendiente, igual que `docs/pending.md`, y se dibuja cuando protoboard-iso lo permita. La carencia se le comunica a protoboard-iso como pedido.

## Consecuencias

Las fichas con circuito listan sus diagramas y su estado (hecho o pendiente de protoboard-iso). Lo que no se pueda dibujar no bloquea el firmware.
