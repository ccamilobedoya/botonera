#!/bin/sh
# Process tooling (tools/): type check and unit tests with the Node devDependencies.
if ! command -v node >/dev/null 2>&1; then
  echo "tools cannot-run: node not found → install Node 24"
  exit 2
fi
if [ ! -x node_modules/.bin/tsc ] || [ ! -x node_modules/.bin/vitest ]; then
  echo "tools cannot-run: devDependencies missing → run npm ci"
  exit 2
fi
node_modules/.bin/tsc --noEmit || { echo "tools finding: type errors → fix them"; exit 1; }
node_modules/.bin/vitest run --passWithNoTests >/tmp/vitest.$$ 2>&1 || { cat /tmp/vitest.$$; rm -f /tmp/vitest.$$; echo "tools finding: failing tests → fix them"; exit 1; }
rm -f /tmp/vitest.$$
node_modules/.bin/prettier --check tools tests vitest.config.ts >/dev/null 2>&1 || { echo "tools finding: formatting → run npm run format"; exit 1; }
echo "tools pass"
exit 0
