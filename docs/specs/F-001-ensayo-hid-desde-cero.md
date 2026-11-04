# F-001 · Ensayo: USB HID desde cero en Windows y iPad

**Estado:** aprobada · puerta 1 el 2026-11-04 · arranca al cerrar F-000
**Modelo del programador:** Sonnet
**Dependencias nuevas permitidas:** ninguna fuera de la imagen `docker/pico-sdk.Dockerfile` (SDK de la Pico con TinyUSB incluido, CMake, `arm-none-eabi-gcc`). Nada de bibliotecas de Arduino ni de QMK.

## Listo para programar

- [x] Cada CA se comprueba con un comando o con un paso escrito para Cris, con valores.
- [x] Contrato escrito: archivos, nombres de funciones, formato del texto que escribe el pad.
- [x] Archivos listados; nombres, rutas y marcas fijados.
- [x] Presupuestos y reglas de seguridad nombrados.
- [x] Fuera de alcance escrito.

## Contexto

Decisión D6: antes de apoyarse en QMK, ver **una sola vez** la pila USB por dentro: el descriptor de dispositivo, el de configuración, el descriptor de reporte HID y la **enumeración** (la conversación inicial en la que el host pregunta y el dispositivo responde). Y, en el mismo ensayo, resolver las dos dudas que definen el diseño (documento 7): que Windows y el iPad aceptan la placa **sin instalar nada**, y cómo es la **huella de enumeración** real de cada uno, para saber si la detección de QMK la va a reconocer.

No se suelda nada: el firmware lee el botón **BOOTSEL** de la placa verde como entrada (truco de los ejemplos del SDK: se desactiva un instante el acceso a la flash, se lee el pin `QSPI_SS` y se restaura). Es también la sesión de M7 sobre USB y HID, que está 🔴 en el Mapa de dominio: se explica primero y se predice solo lo marcado abajo.

## Alcance

Un firmware en `experiments/hid-from-scratch/` que:

1. Se enumera como **un teclado HID y nada más** (una sola interfaz; sin CDC, sin almacenamiento), con cadenas `Botonera` / `HID from scratch`.
2. **Registra** en memoria cada petición de control que llega del host durante la enumeración (tipo, petición, `wValue`, `wIndex`, `wLength`), hasta llenar un búfer fijo.
3. Al apretar **BOOTSEL** (una pulsación, con antirrebote), **escribe como texto** por el propio teclado un resumen del registro, en una línea, con solo minúsculas, dígitos y espacios (para que salga igual en una distribución de teclado en español o en inglés).
4. En la compilación de prueba (`-DAUTO_TYPE=1`) escribe esa línea **sola, 3 s después de enumerar**, para que la aceptación corra en el servidor sin que nadie apriete el botón. La compilación normal **no** lo hace.
5. Suelta todas las teclas al terminar de escribir (report vacío) y nunca deja una pulsada.

**Fuera de alcance:** matriz, encoder, OLED, capas, QMK, detección de sistema propia (solo se **registra** la secuencia; interpretarla es trabajo del arquitecto con la tabla de QMK), Bluetooth, cualquier cosa que persista en flash.

## Requisitos

- **R1.** Solo SDK de la Pico y TinyUSB tal como vienen en el SDK: **sin parchar TinyUSB**. El registro de peticiones se obtiene por un mecanismo que el SDK ya ofrece (p. ej. redirigir el `printf` de depuración de TinyUSB a una función propia con `CFG_TUSB_DEBUG_PRINTF`, o un callback público). Si ningún mecanismo público da `wLength`, se registra lo que sí se pueda y el informe lo dice con claridad.
- **R2.** Los tres descriptores (dispositivo, configuración, reporte HID) se escriben **a mano** en `usb_descriptors.c`, byte a byte o con las macros de bajo nivel de `hid.h` (`HID_USAGE_PAGE`, `HID_USAGE`, …), **con un comentario por ítem** que diga qué significa. No se usa `TUD_HID_REPORT_DESC_KEYBOARD` ni ninguna macro que esconda el descriptor completo.
- **R3.** Report de teclado estándar de 8 bytes: modificadores, reservado, seis códigos. Tecla a tecla: report con el código, luego report vacío, con un intervalo fijo de 10 ms entre reports.
- **R4.** El texto que escribe el pad sale solo de la tabla fija de caracteres permitidos `[a-z0-9 ]`; cualquier otro byte se cambia por espacio.
- **R5.** Antirrebote de BOOTSEL: una pulsación produce exactamente **una** línea, aunque se mantenga apretado 2 s.
- **R6.** Ninguna entrada del host se interpreta salvo el report OUT estándar de LEDs del teclado (1 byte), que se acepta y se ignora; todo lo demás se rechaza con STALL (comportamiento por defecto de TinyUSB).
- **R7.** VID/PID: los de pruebas del SDK de la Pico (`0x2E8A`, PID de ejemplo), **documentado** en el README como «no registrado, solo para el ensayo».

## Contrato

### Archivos del contrato

```text
experiments/hid-from-scratch/
  CMakeLists.txt         objetivo hid_from_scratch; opción AUTO_TYPE (OFF por defecto)
  pico_sdk_import.cmake  del SDK
  tusb_config.h          CFG_TUD_HID=1, CFG_TUD_CDC=0, CFG_TUD_MSC=0, tamaño del endpoint 8
  usb_descriptors.c      descriptores a mano, comentados (R2); tud_descriptor_*_cb
  usb_descriptors.h      constantes compartidas (longitudes, índices de cadena)
  enum_log.c / .h        registro de peticiones: enum_log_add(...), enum_log_render(char *out, size_t n)
  keys.c / .h            texto → reports: keys_type_line(const char *s) (bloqueante, ≤ 5 s para 200 caracteres)
  keys_port.h            lo que keys.c necesita del exterior (dos funciones, abajo); las implementa main.c en el firmware y la prueba en el PC
  bootsel.c / .h         bootsel_pressed(void): lectura del botón, con antirrebote de 50 ms
  main.c                 tusb_init, bucle: tud_task(), botón, AUTO_TYPE
  README.md              qué es, cómo compilar (tools/build hid-from-scratch), cómo grabar, qué escribe
```

### Formato de la línea que escribe el pad

Una sola línea, terminada en Enter, con este formato (ejemplo inventado):

```text
botonera ensayo 1 n 7 r 80 06 0100 0000 0040 r 80 06 0200 0000 0009 r 80 06 0300 0000 00ff r 80 06 03ee 0000 00ff r 00 09 0001 0000 0000 r 21 0a 0000 0000 0000 r 81 06 2200 0000 003f
```

- `botonera ensayo 1`: marca fija y versión del formato.
- `n <k>`: cuántas peticiones se registraron, igual al número de grupos `r …` que siguen (el ejemplo tiene 7; si el búfer se llenó, `n 64 full`). _(Corregido el 2026-11-04: el ejemplo decía `n 11` con 7 peticiones.)_
- Por cada petición: `r <bmRequestType> <bRequest> <wValue> <wIndex> <wLength>`, todo en hexadecimal en minúsculas, sin `0x`, con el ancho fijo de arriba (2, 2, 4, 4, 4).
- Si no se pudo obtener `wLength` (R1), se escribe `xxxx` en su lugar y el README lo explica.

### Funciones con nombre y firma (lo que prueba el verificador)

- `void enum_log_reset(void);` vacía el registro y pone `dropped` en 0.
- `size_t enum_log_count(void);` cuántas entradas guardadas (0–64). `uint32_t enum_log_dropped(void);` cuántas no cupieron.

- `void enum_log_add(uint8_t bmRequestType, uint8_t bRequest, uint16_t wValue, uint16_t wIndex, uint16_t wLength);` guarda hasta `ENUM_LOG_MAX = 64` entradas; la 65 en adelante solo sube un contador `dropped`.
- `size_t enum_log_render(char *out, size_t n);` escribe la línea del formato de arriba, siempre terminada en `\0`, nunca más de `n - 1` caracteres, y devuelve cuántos escribió.
- `void keys_type_line(const char *s);` escribe `s` y un Enter; caracteres fuera de `[a-z0-9 ]` salen como espacio.
- `keys.c` no habla con TinyUSB directamente: usa dos funciones declaradas en `keys_port.h` y definidas fuera (en `main.c` en el firmware, en la prueba en el PC): `void keys_port_send(const uint8_t report[8]);` (entrega un report de teclado de 8 bytes y vuelve cuando el host lo aceptó) y `void keys_port_sleep_ms(uint32_t ms);` (espera). `keys_type_line` llama a `keys_port_send` una vez por report y a `keys_port_sleep_ms(10)` después de cada uno. En la prueba, `keys_port_send` guarda los reports en una lista y `keys_port_sleep_ms` no hace nada. _(Aclarado el 2026-11-04 tras la fase de pruebas: el contrato no nombraba estas funciones.)_
- `bool bootsel_pressed(void);` verdadero una sola vez por pulsación (flanco), con antirrebote de 50 ms.

Las tres primeras se prueban también **en el PC** (`tests/acceptance/F-001/host/`, compiladas con el `gcc` del contenedor, sin hardware): `enum_log` y `keys` no dependen del chip salvo por la función que envía el report, que se inyecta.

## Criterios de aceptación

**Sin hardware (verificador, en el servidor):**

- **CA1.** `tools/build hid-from-scratch` deja `build/hid-from-scratch/hid_from_scratch.uf2` y `hid_from_scratch_autotype.uf2`; cada uno pesa menos de 200 KB; dos compilaciones seguidas dan el mismo `sha256`.
- **CA2.** `grep -c TUD_HID_REPORT_DESC_KEYBOARD experiments/hid-from-scratch/*.c` da 0, y `usb_descriptors.c` tiene al menos **un comentario por línea de ítem** del descriptor de reporte (el verificador cuenta ítems y comentarios; si hay ítems sin comentario, no cumple).
- **CA3.** Pruebas de host de `enum_log`: 64 entradas se registran y la 65 incrementa `dropped`; `enum_log_render` con `n = 16` escribe 15 caracteres y `\0`; con el ejemplo del contrato produce exactamente la línea de arriba.
- **CA4.** Pruebas de host de `keys_type_line`: `"a1 Z!"` produce la secuencia de reports para `a`, `1`, espacio, espacio, espacio y Enter, cada tecla seguida de un report vacío; el último report enviado es vacío.
- **CA5.** El `.uf2` de producción **no contiene** la cadena `autotype on` y el de prueba sí (`strings | grep`).

**Con la placa conectada al servidor (verificador; Cris la enchufa en modo BOOTSEL y copia el `.uf2` de prueba, o la deja enchufada y el verificador avisa):**

- **CA6.** Con `hid_from_scratch_autotype.uf2`, enchufado (o reenchufado) justo antes de correr la prueba, en menos de 10 s desde que aparece, el servidor recibe por `evdev` (`/dev/input/by-id/*Botonera*`) una línea que empieza por `botonera ensayo 1 n` seguido de un espacio y termina con Enter; la herramienta `tools/host/read_line.py --timeout 10` la imprime y sale 0.
- **CA7.** La línea de CA6 contiene al menos una petición `r 80 06 0100` (descriptor de dispositivo), una `r 80 06 0200` (configuración) y una `r 81 06 2200` (descriptor de reporte HID), en ese orden relativo.
- **CA8.** Después de la línea, `evdev` no reporta ninguna tecla en estado presionado (`EVIOCGKEY` todo en cero), comprobado 1 s después.
- **CA9.** `lsusb -v -d 2e8a:` muestra una sola interfaz, clase HID (3), subclase 1 (boot), protocolo 1 (teclado), endpoint IN de 8 bytes; sin CDC ni MSC.
- **CA10.** La línea de CA6 se guarda en `tests/acceptance/F-001/fingerprints/linux.txt` como referencia (sin datos privados: solo hexadecimales).

**Pendiente de Cris (no bloquean el cierre del código; se anotan en la nota de estado con fecha):**

- **CA11 · Windows.** Con `hid_from_scratch.uf2`: al conectar, no aparece ningún diálogo de instalación; en el Administrador de dispositivos sale «Dispositivo de teclado HID» sin marca amarilla; en el Bloc de notas, una pulsación de BOOTSEL escribe **una** línea con el formato del contrato. Cris la copia a la nota de estado (`fingerprints/windows.txt` en el repo si no tiene nada privado: no lo tiene). Anotar cuántos segundos tardó en aparecer.
- **CA12 · iPad.** Conectado por USB-C: ningún aviso de alimentación ni de accesorio no compatible; en Ajustes → General → Teclado aparece _Teclado físico_; en Notas, una pulsación escribe una línea. Copiarla igual. Anotar el tiempo.
- **CA13 · iPhone.** Lo mismo si el cable o adaptador lo permite; si es de Lightning sin adaptador, se anota «no probado» y por qué.

## Presupuestos

- Flash: `.uf2` < 200 KB. RAM: búfer del registro 64 × 10 bytes más la línea de salida de 1 KB.
- Escribir la línea completa (≤ 700 caracteres): ≤ 15 s (dos reports por carácter con 10 ms entre reports, R3). _(Corregido el 2026-11-04: decía «< 2 s», incompatible con R3.)_
- Reacción a BOOTSEL: < 100 ms.

## Seguridad

- S1: el único OUT aceptado es el report de LEDs de 1 byte (R6). S2: el gancho `AUTO_TYPE` es una compilación aparte y la de producción no lo contiene (CA5). S3: el texto escrito nunca incluye nada que no sea el registro de peticiones. S5: compilación en contenedor sin red tras construir la imagen.
- `tools/host/read_line.py` lee `evdev` con tope de 4 KB por línea y descarta lo que no cumpla el formato. Acepta `--device <ruta>` opcional; sin él, usa la primera entrada `/dev/input/by-id/*Botonera*`.

## Archivos

Los del contrato, más `tools/build` (ya existe por F-000; aquí solo se usa), `tools/host/read_line.py` (nuevo, Python 3 estándar: lee `/dev/input/by-id/` sin `sudo` si el usuario está en el grupo `input`; **si no está, es un comando para Cris**, documentado en `docs/configuracion-local.md`), `tests/acceptance/F-001/`.

## Para el arquitecto

- **Flujo de información.** Al enchufar: el host da energía → el RP2040 arranca y TinyUSB se conecta al bus → el host **resetea** el bus y empieza a pedir: descriptor de dispositivo (quién eres), lo vuelve a pedir completo, asigna una dirección, pide la configuración (qué interfaces y endpoints tienes), las cadenas (nombres), y para una interfaz HID, el **descriptor de reporte** (qué vas a mandar y en qué orden de bytes). Windows mete además la cadena `0xEE`. Cuando termina, elige el driver de clase y el dispositivo queda «configurado». Desde ahí el pad manda **reports** por el endpoint de interrupción cuando tiene algo (y el host sondea cada N ms según `bInterval`).
- **Qué hace cada archivo.** `usb_descriptors.c` responde las preguntas de la enumeración; `enum_log.c` las anota; `keys.c` traduce texto a reports (tabla de `usage IDs`: `a` = `0x04`, `1` = `0x1E`, espacio = `0x2C`, Enter = `0x28`); `bootsel.c` lee el botón que normalmente solo sirve para grabar; `main.c` reparte el tiempo entre atender el USB (`tud_task`) y lo demás.
- **Límites.** El pad no sabe qué sistema lo enumeró; solo ve la secuencia. Un teclado manda posiciones, no letras: por eso la línea usa solo lo que coincide en las distribuciones en inglés y en español. 6 teclas a la vez como máximo en este report. Si el firmware se cuelga con un report no vacío enviado, la tecla queda pegada hasta desconectar: en este ensayo no hay watchdog (lo trae F-007), así que **no se deja el pad enchufado sin vigilar**.
- **Para predecir antes de ver el resultado** (🟡 solo después de la explicación de arriba; lo demás se explica directo):
  1. ¿Cuál de los dos sistemas hará **más** peticiones al enumerar, Windows o el iPad? ¿Por qué podría Windows pedir una cadena que ningún otro pide?
  2. Si el descriptor de reporte declara 8 bytes y el firmware mandara 7, ¿qué haría el host: escribir mal, ignorar o desconectar?
  3. ¿Qué pasa con una pulsación de BOOTSEL de 2 s sin antirrebote por flanco?
- **Qué se mide:** tiempo hasta aparecer en cada sistema; número de peticiones; si el iPad se queja de la alimentación (la placa sola consume muy poco; se mide en F-005 con la OLED).

## Pasos de Cris (guion)

1. Cable USB-C **de datos**. Mantener apretado BOOTSEL y conectar la placa verde al PC: aparece la unidad `RPI-RP2`.
2. Copiar `hid_from_scratch.uf2` desde la carpeta compartida del repo, `build\hid-from-scratch\` a esa unidad. La placa se reinicia sola.
3. Windows: abrir el Bloc de notas, apretar BOOTSEL **una vez**, copiar la línea a la nota de estado; abrir el Administrador de dispositivos y confirmar la entrada sin marca. Anotar los segundos entre conectar y que aparezca.
4. iPad: conectar, abrir Notas, apretar BOOTSEL una vez, copiar la línea; revisar Ajustes → General → Teclado. Anotar avisos y segundos.
5. iPhone: igual si se puede; si no, anotar por qué.
6. Para la aceptación del servidor: enchufar la placa al servidor con `hid_from_scratch_autotype.uf2` cuando el arquitecto lo pida, y desenchufarla al terminar.

## Resultado esperado

Tres líneas de huella (Linux, Windows, iPad) guardadas, los tres descriptores leídos y entendidos por Cris, y una respuesta clara a «¿hace falta instalar algo?» en los dos sistemas. Con eso, F-002 escribe el contrato y la decisión de confiar o no en la detección de QMK se toma con datos.

## Terminado

- [ ] CA1–CA10 en verde (informe del verificador); CA11–CA13 anotados con fecha o marcados «pendiente de Cris».
- [ ] `docs/lecciones.md` → «Para la plantilla»: cómo se probó un firmware con la placa en el servidor.
- [ ] Sesión de M7 documentada por el `documentador` (descriptor, enumeración, reports) con las tres predicciones y lo que salió.
- [ ] Cris aprobó integrar.

---

## Resultado obtenido

Al cerrar.

## Resumen para aprobar

Una pantalla.
