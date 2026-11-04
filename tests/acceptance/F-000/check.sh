#!/bin/sh
# Acceptance checks for F-000. Run from anywhere inside the worktree.
cd "$(git rev-parse --show-toplevel)" || exit 2
FAILS=0
res() { # name ok evidence
  if [ "$2" = 0 ]; then echo "PASS $1: $3"; else echo "FAIL $1: $3"; FAILS=$((FAILS + 1)); fi
}

echo "PENDIENTE DEL ARQUITECTO CA6 (agent regression)"
# CA1 (partial, re-runnable parts)
git check-ignore -q CLAUDE.local.md; a=$?
res CA1-ignore $a "CLAUDE.local.md ignored (exit $a)"
echo "PENDIENTE DEL ARQUITECTO CA1 (template check tool outside repo; template-name grep is architect-run)"

# CA2
scripts/review >/tmp/f000-review.out 2>&1; rc=$?
res CA2 $rc "scripts/review exit $rc; tail: $(tail -n 2 /tmp/f000-review.out | tr '\n' ' ')"
rm -f /tmp/f000-review.out

# CA3
out=$(tools/build qmk 2>&1); rc=$?
v=$(printf '%s\n' "$out" | grep -c 'QMK CLI'); last=$(printf '%s\n' "$out" | tail -n 1)
ok=1; [ "$rc" = 1 ] && [ "$v" -ge 1 ] && [ "$last" = "build: no keyboard yet (see F-002)" ] && ok=0
res CA3 $ok "exit $rc; last line '$last'; version-ish lines $v"

# CA4
rm -rf build/blink
tools/build blink >/dev/null 2>&1; rc1=$?
size=$(wc -c <build/blink/blink.uf2 2>/dev/null || echo 0)
h1=$(sha256sum build/blink/blink.uf2 2>/dev/null | cut -d' ' -f1)
rm -rf build/blink
tools/build blink >/dev/null 2>&1; rc2=$?
h2=$(sha256sum build/blink/blink.uf2 2>/dev/null | cut -d' ' -f1)
ok=1; [ "$rc1" = 0 ] && [ "$rc2" = 0 ] && [ "$size" -gt 10240 ] && [ -n "$h1" ] && [ "$h1" = "$h2" ] && ok=0
res CA4 $ok "exits $rc1/$rc2; size $size; sha $h1 vs $h2"

# CA5
tools/map >/dev/null 2>&1; rc=$?
miss=""
for d in docs docs/adr docs/specs docs/templates docs/reports experiments experiments/blink experiments/hid-from-scratch firmware firmware/keyboards/botonera firmware/keymaps/default tools tools/host tests/agents tests/acceptance; do
  grep -q "$d" docs/MAP.md || miss="$miss $d"
done
ok=1; [ "$rc" = 0 ] && [ -z "$miss" ] && ok=0
res CA5 $ok "tools/map exit $rc; missing:${miss:- none}"

# CA7
echo x >docs/specs/zz-probe.md
tools/check-scope programmer --base HEAD >/dev/null 2>&1; p=$?
rm -f docs/specs/zz-probe.md
echo x >firmware/zz-probe.txt
tools/check-scope verifier --base HEAD >/dev/null 2>&1; v=$?
rm -f firmware/zz-probe.txt
ok=1; [ "$p" = 1 ] && [ "$v" = 1 ] && ok=0
res CA7 $ok "programmer-violation exit $p, verifier-violation exit $v (both expected 1)"

# CA8
o=$(tools/publish-spec docs/specs/F-000-andamiaje.md 2>&1); rc=$?
addr="127.0.0.1:80""87"
leak=$(git ls-files | xargs grep -l "$addr" 2>/dev/null)
ok=1; case "$o" in *"Updated: F-000"*) [ "$rc" = 0 ] && [ -z "$leak" ] && ok=0 ;; esac
res CA8 $ok "exit $rc; output '$(printf '%s' "$o" | head -n 1 | cut -c1-60)'; leaks: ${leak:-none}"

# CA9
printf '%s%s\n' almendr oso >docs/zz-probe.md
git add docs/zz-probe.md
o=$(scripts/hooks/pre-commit 2>&1); r1=$?
git restore --staged docs/zz-probe.md
printf 'clean probe\n' >docs/zz-probe.md
git add docs/zz-probe.md
scripts/hooks/pre-commit >/dev/null 2>&1; r2=$?
git restore --staged docs/zz-probe.md
rm -f docs/zz-probe.md
ok=1; [ "$r1" = 1 ] && [ "$r2" = 0 ] && printf '%s' "$o" | grep -q 'privacy finding' && ok=0
res CA9 $ok "dirty exit $r1 (expect 1, 'privacy finding' present: $(printf '%s' "$o" | grep -c 'privacy finding')), clean exit $r2 (expect 0)"

# CA10
ok=0; ev=""
for n in 1 2 3 4 5 6 7 8 9; do
  f=$(ls docs/adr/000$n-*.md 2>/dev/null | head -n 1)
  if [ -z "$f" ] || ! grep -q '\*\*Estado:\*\* aceptada' "$f"; then ok=1; ev="$ev 000$n"; fi
done
f3=$(ls docs/adr/0003-*.md 2>/dev/null | head -n 1)
grep -q 'GPL-2.0-or-later' "$f3" 2>/dev/null || { ok=1; ev="$ev 0003-license"; }
res CA10 $ok "bad:${ev:- none}; ADR-0003 coverage text needs human read (files section: $(grep -ci 'firmware' "$f3" 2>/dev/null) mentions of firmware)"

# CA11
git check-ignore -q build/blink/blink.uf2; a=$?
st=$(git status --short | grep -v 'tests/acceptance/F-000/')
ok=1; [ "$a" = 0 ] && [ -z "$st" ] && ok=0
res CA11 $ok "build ignored exit $a; stray status: ${st:-none}"

[ "$FAILS" = 0 ]
