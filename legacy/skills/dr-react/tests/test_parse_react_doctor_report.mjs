import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";


const HERE = dirname(fileURLToPath(import.meta.url));
const PARSER = resolve(HERE, "../scripts/parse-react-doctor-report.mjs");


function parse(report) {
  const result = spawnSync(process.execPath, [PARSER], {
    input: JSON.stringify(report),
    encoding: "utf8",
  });
  assert.equal(result.status, 0, result.stderr);
  return JSON.parse(result.stdout);
}


test("extracts the report score and groups diagnostics", () => {
  const output = parse({
    summary: { score: 92 },
    results: {
      diagnostics: [
        {
          fixGroupId: "hooks",
          ruleId: "react-hooks",
          severity: "warning",
          category: "correctness",
          file: "src/A.tsx",
        },
        {
          fixGroupId: "hooks",
          ruleId: "react-hooks",
          severity: "warning",
          category: "correctness",
          path: "src/B.tsx",
        },
        {
          rule: "no-img",
          level: "error",
          type: "accessibility",
          location: { file: "src/C.tsx" },
        },
      ],
    },
  });

  assert.equal(output.scoreAvailable, true);
  assert.equal(output.score, 92);
  assert.equal(output.scoreSource, "report");
  assert.equal(output.diagnosticCount, 3);
  assert.deepEqual(output.severityCounts, { warning: 2, error: 1 });
  assert.deepEqual(output.categoryCounts, { correctness: 2, accessibility: 1 });
  assert.deepEqual(output.topGroups[0], {
    key: "hooks",
    count: 2,
    severity: "warning",
    category: "correctness",
    ruleId: "react-hooks",
    files: ["src/A.tsx", "src/B.tsx"],
  });
});


test("uses the lowest project score when the report has no score", () => {
  const output = parse({
    projects: [
      { name: "app", score: { value: "87" } },
      { path: "admin", healthScore: 72 },
    ],
  });

  assert.equal(output.scoreAvailable, true);
  assert.equal(output.score, 72);
  assert.equal(output.scoreSource, "worst-project");
  assert.deepEqual(output.projectScores, [
    { name: "app", score: 87 },
    { name: "admin", score: 72 },
  ]);
});


test("finds diagnostics inside nested containers", () => {
  const output = parse({
    sections: [{ entries: [[{ ruleId: "nested", severity: "info", file: "src/N.tsx" }]] }],
  });

  assert.equal(output.diagnosticCount, 1);
  assert.deepEqual(output.severityCounts, { info: 1 });
  assert.equal(output.topGroups[0].ruleId, "nested");
});


test("reports a missing numeric score as unavailable", () => {
  const output = parse({ summary: { score: "not-a-number" } });

  assert.equal(output.scoreAvailable, false);
  assert.equal(output.score, null);
  assert.equal(output.scoreSource, null);
  assert.equal(output.diagnosticCount, 0);
});


test("rejects malformed JSON", () => {
  const result = spawnSync(process.execPath, [PARSER], {
    input: "{",
    encoding: "utf8",
  });

  assert.notEqual(result.status, 0);
});
