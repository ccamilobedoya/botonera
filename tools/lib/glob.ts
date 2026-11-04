// Minimal glob matching for repo-relative paths: "**" spans folders, "*" stays inside one.

export function globToRegExp(pattern: string): RegExp {
  let source = "";
  for (let i = 0; i < pattern.length; i++) {
    const char = pattern.charAt(i);
    if (char === "*") {
      if (pattern.charAt(i + 1) === "*") {
        source += ".*";
        i++;
      } else {
        source += "[^/]*";
      }
    } else if ("\\^$+?.()|{}[]".includes(char)) {
      source += `\\${char}`;
    } else {
      source += char;
    }
  }
  return new RegExp(`^${source}$`);
}

export function parsePatterns(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line !== "" && !line.startsWith("#"));
}

export function matchesAny(path: string, patterns: readonly string[]): boolean {
  return patterns.some((pattern) => globToRegExp(pattern).test(path));
}
