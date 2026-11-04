#!/bin/sh
# Production firmware artifacts must not carry the test-hook markers (rule S2). Skips when nothing was built.
found=0
for f in build/*/*.uf2; do
  [ -f "$f" ] || continue
  case "$f" in *autotype*|*test*) continue ;; esac
  if strings "$f" | grep -q -e "autotype on" -e "BOTONERA_TEST_HOOK"; then
    echo "firmware-artifacts finding: $f contains a test-hook marker → rebuild without the test flags"
    found=1
  fi
done
[ "$found" -eq 0 ] || exit 1
ls build/*/*.uf2 >/dev/null 2>&1 || { echo "SKIP: no firmware artifacts built"; exit 0; }
echo "firmware-artifacts pass"
exit 0
