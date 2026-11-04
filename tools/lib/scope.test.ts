import { describe, expect, it } from "vitest";
import { isRole, outOfScope } from "./scope.ts";

describe("outOfScope", () => {
  it("lets the verifier touch only acceptance tests", () => {
    expect(outOfScope("verifier", ["tests/acceptance/f001.test.ts"])).toEqual([]);
    expect(outOfScope("verifier", ["server/src/index.ts"])).toEqual(["server/src/index.ts"]);
  });

  it("keeps the programmer out of specs, decisions, acceptance tests and agent files", () => {
    const files = [
      "server/src/index.ts",
      "docs/specs/F-001.md",
      "docs/adr/0001.md",
      "tests/acceptance/a.test.ts",
      ".claude/agents/programmer.md",
      "package.json",
    ];
    expect(outOfScope("programmer", files)).toEqual([
      "docs/specs/F-001.md",
      "docs/adr/0001.md",
      "tests/acceptance/a.test.ts",
      ".claude/agents/programmer.md",
    ]);
  });

  it("lets the reviewer change nothing", () => {
    expect(outOfScope("reviewer", ["docs/lessons.md"])).toEqual(["docs/lessons.md"]);
    expect(outOfScope("reviewer", [])).toEqual([]);
  });
});

describe("isRole", () => {
  it("accepts only known roles", () => {
    expect(isRole("verifier")).toBe(true);
    expect(isRole("architect")).toBe(false);
  });
});
