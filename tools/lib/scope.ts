// What each agent role may change. Checked with git, not with the agent's good will.
// The programmer owns tools/host/ (host-side test helpers of the firmware); the rest of tools/ is the architect's.
import { matchesAny } from "./glob.ts";

export type Role = "programmer" | "verifier" | "reviewer";

interface RoleRule {
  /** When set, only these paths may change. */
  allow?: readonly string[];
  /** These paths may never change. */
  deny: readonly string[];
}

const ARCHITECT_OWNED = [
  "docs/specs/**",
  "docs/adr/**",
  "docs/templates/**",
  "docs/reports/**",
  "docs/lessons.md",
  "docs/metrics.md",
  ".claude/**",
  "CLAUDE.md",
  "tools/*",
  "tools/lib/**",
  "tests/agents/**",
];

const RULES: ReadonlyMap<Role, RoleRule> = new Map<Role, RoleRule>([
  ["programmer", { deny: [...ARCHITECT_OWNED, "tests/acceptance/**"] }],
  ["verifier", { allow: ["tests/acceptance/**"], deny: [] }],
  ["reviewer", { allow: [], deny: [] }],
]);

export function isRole(value: string): value is Role {
  return RULES.has(value as Role);
}

/** Returns the files the role was not allowed to change. */
export function outOfScope(role: Role, files: readonly string[]): string[] {
  const rule = RULES.get(role) ?? { allow: [], deny: [] };
  return files.filter((file) => {
    if (matchesAny(file, rule.deny)) return true;
    return rule.allow !== undefined && !matchesAny(file, rule.allow);
  });
}
