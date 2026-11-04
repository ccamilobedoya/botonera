# tools

Process tooling kept by the architect: `launch-agent`, `integrator-brief`, `check-scope`, `publish-spec`, `map` and `build`, with their TypeScript in `lib/` (Node 24, no build step) and the host test helpers in `host/`.

| Tool                                                                 | What it does                                                                                                                                   |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `tools/launch-agent <role> <model> <folder> <brief> [cap-usd]`       | Runs one agent (`claude -p`) with a closed tool list, a clean context and a spend cap; logs to `.agents/`; exit 3 when the report says STOPPED |
| `tools/integrator-brief <folder> --phase … --spec F-NNN --summary …` | Builds the integrator's brief with the exact `git status` list                                                                                 |
| `tools/check-scope <role> [--base <ref>]`                            | Did the role change only what it owns?                                                                                                         |
| `tools/publish-spec docs/specs/F-NNN-*.md`                           | Copies a spec to the owner's knowledge base (local config, see `docs/local-config.md`)                                                         |
| `tools/map`                                                          | Regenerates `docs/MAP.md` from the README of each folder                                                                                       |
| `tools/build qmk \| hid-from-scratch \| blink`                       | Compiles in pinned containers; output in `build/`                                                                                              |
