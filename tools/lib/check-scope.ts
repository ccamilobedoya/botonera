// CLI: tools/check-scope <rol> [--base <ref>]. Exit 1 when the role changed files outside its scope.
import { changedFiles, defaultBase } from "./git.ts";
import { isRole, outOfScope } from "./scope.ts";

function main(): number {
  const [role, flag, baseArg] = process.argv.slice(2);
  if (role === undefined || !isRole(role)) {
    process.stderr.write(
      "Usage: tools/check-scope <programmer|verifier|reviewer> [--base <ref>]\n",
    );
    return 2;
  }
  const base = flag === "--base" && baseArg !== undefined ? baseArg : defaultBase();
  const bad = outOfScope(role, changedFiles(base));
  if (bad.length === 0) {
    process.stdout.write(`✅ ${role}: all changes are within scope (base ${base}).\n`);
    return 0;
  }
  process.stdout.write(`❌ ${role}: changes outside its scope (base ${base}):\n`);
  for (const file of bad) process.stdout.write(`  - ${file}\n`);
  return 1;
}

process.exitCode = main();
