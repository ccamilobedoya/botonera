# Botonera

[Español](README.es.md)

A desk macropad on an RP2040 that Windows, iPadOS and macOS see as a plain keyboard, with no driver or app to install, and that sends a different command per operating system: the same key copies with `Ctrl+C` on Windows and `Cmd+C` on an iPad or a Mac. Nine keys, a rotary encoder and a small OLED, first on a breadboard and later on a custom PCB. The firmware is [QMK](https://qmk.fm); the key map is written in a small configuration file, not in C.

**Status:** scaffolding. There is no firmware yet: spec F-001 (a hand-written USB HID keyboard, to learn the protocol) and F-002 (the keymap format and the QMK keyboard definition) come next.

## How it will work

- The pad declares itself as a USB HID keyboard and a consumer-control device, so every operating system drives it with its class driver.
- It guesses the host operating system from how the host enumerates it (QMK's OS detection) and lets you override that with a key; the OLED shows the active system and profile.
- Your keys, macros, per-system variants and per-application profiles live in one `keymap.toml`; a generator turns it into the QMK keymap and validates it before compiling.

## Quick start

<!-- smoke -->

```bash
scripts/setup
ls docs
```

<!-- /smoke -->

Then `npm ci` for the tooling under `tools/`, and `tools/build blink` to check that the Pico SDK container works (it needs Docker; nothing is installed on your machine). Firmware builds land in `build/` as `.uf2` files that you drag onto the board while holding BOOTSEL.

## Repository

| Folder | What it holds |
| ------ | ------------- |
| `firmware/` | The product firmware as a QMK external userspace, pinned to one QMK commit (`qmk.lock`) |
| `experiments/` | Throwaway firmware that teaches or measures something and is never shipped |
| `tools/` | Process tooling: agent launcher, scope checks, pinned container builds |
| `docs/` | Specs (`specs/`), decision records (`adr/`), process, security rules, lessons |
| `docker/` | The pinned toolchains |

## Development

Working rules are in [CLAUDE.md](CLAUDE.md). Specs, decisions and pending work are in [docs/decisions.md](docs/decisions.md), [docs/pending.md](docs/pending.md) and [docs/specs/TEMPLATE.md](docs/specs/TEMPLATE.md). Specs, decision records and the process documents are written in Spanish; code, comments and everything else in English.

## License

Released under the MIT license. See [LICENSE](LICENSE). The QMK keyboard definition and keymaps under `firmware/` link against QMK (GPL-2.0-or-later) and carry that licence in their headers.
