# Configuración local (fuera del repo)

> Todo lo personal, de infraestructura o secreto vive **fuera del repo** (ADR-0008). Aquí solo están las instrucciones.

| Archivo (fuera del repo)                                     | Para qué                                                                                                                        | Formato                                                                                                                                               |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `~/.config/botonera/local.env` (o `$BOTONERA_LOCAL_ENV`)     | Dónde está la base de conocimiento y en qué nota se publican las fichas (`tools/publish-spec`)                                  | Tres líneas: `TRILIUM_ETAPI_URL=<url>`, `TRILIUM_TOKEN_FILE=<ruta>`, `TRILIUM_FICHAS_NOTE_ID=<id>`                                                    |
| El archivo que indique `TRILIUM_TOKEN_FILE`                  | El token de la API                                                                                                              | Una línea `TRILIUM_ETAPI_TOKEN=<token>`                                                                                                               |
| `~/.config/botonera/private-terms.txt`                       | Términos que **nunca** pueden llegar al repo: nombres, servidores, direcciones, ids de notas, rutas locales, nombres de empresa | Uno por línea; `#` para comentarios. Lo leen los hooks de git y `scripts/review`; se registra con `git config --local checks.privateTermsFile <ruta>` |
| `firmware/keymaps/local/` (ignorado con `.git/info/exclude`) | El keymap personal del dueño                                                                                                    | El mismo formato que `keymaps/default/`                                                                                                               |

Todos con permisos **600** y la carpeta con **700**. Para leer `/dev/input` sin `sudo` (pruebas con el pad en el servidor), el usuario tiene que estar en el grupo `input`: lo hace el dueño.

## Activar los hooks y las herramientas en una copia nueva

```bash
scripts/setup && npm ci
git config --local checks.privateTermsFile ~/.config/botonera/private-terms.txt
```
