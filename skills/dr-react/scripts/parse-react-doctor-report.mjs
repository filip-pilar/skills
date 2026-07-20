#!/usr/bin/env node

import { readFileSync } from "node:fs";

const inputPath = process.argv[2];
const raw = inputPath ? readFileSync(inputPath, "utf8") : readFileSync(0, "utf8");
const report = JSON.parse(raw);

function firstNumber(...values) {
  for (const value of values) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) {
      return Number(value);
    }
  }
  return null;
}

function getScore(root) {
  const candidates = [
    root?.summary?.score,
    root?.score?.score,
    root?.score?.value,
    root?.score,
    root?.healthScore,
    root?.overallScore,
    root?.meta?.score,
  ];
  return firstNumber(...candidates);
}

function getProjectScores(root) {
  if (!Array.isArray(root?.projects)) return [];
  return root.projects
    .map((project) => ({
      name: project?.name ?? project?.project ?? project?.path ?? null,
      score: getScore(project),
    }))
    .filter((project) => project.score !== null);
}

function looksLikeDiagnostic(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  return Boolean(
    value.fixGroupId ||
      value.ruleId ||
      value.rule ||
      value.category ||
      value.severity ||
      value.message ||
      value.file ||
      value.path ||
      value.location
  );
}

function collectDiagnostics(value, diagnostics = [], seen = new Set()) {
  if (!value || typeof value !== "object" || seen.has(value)) return diagnostics;
  seen.add(value);

  if (Array.isArray(value)) {
    if (value.some(looksLikeDiagnostic)) {
      for (const item of value) {
        if (looksLikeDiagnostic(item)) diagnostics.push(item);
      }
      return diagnostics;
    }
    for (const item of value) collectDiagnostics(item, diagnostics, seen);
    return diagnostics;
  }

  for (const item of Object.values(value)) collectDiagnostics(item, diagnostics, seen);
  return diagnostics;
}

function pick(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "") ?? null;
}

const projectScores = getProjectScores(report);
const ownScore = getScore(report);
const score = ownScore ?? (projectScores.length > 0 ? Math.min(...projectScores.map((project) => project.score)) : null);
const diagnostics = collectDiagnostics(report);
const severityCounts = {};
const categoryCounts = {};
const groups = new Map();

for (const diagnostic of diagnostics) {
  const severity = String(pick(diagnostic.severity, diagnostic.level, "unknown"));
  const category = String(pick(diagnostic.category, diagnostic.type, "unknown"));
  const ruleId = String(pick(diagnostic.ruleId, diagnostic.rule?.id, diagnostic.rule, "unknown"));
  const file = String(pick(diagnostic.file, diagnostic.path, diagnostic.location?.file, "unknown"));
  const key = String(pick(diagnostic.fixGroupId, `${ruleId}:${category}:${file}`));

  severityCounts[severity] = (severityCounts[severity] ?? 0) + 1;
  categoryCounts[category] = (categoryCounts[category] ?? 0) + 1;

  const group = groups.get(key) ?? {
    key,
    count: 0,
    severity,
    category,
    ruleId,
    files: new Set(),
  };
  group.count += 1;
  group.files.add(file);
  groups.set(key, group);
}

const topGroups = [...groups.values()]
  .sort((a, b) => b.count - a.count)
  .slice(0, 10)
  .map((group) => ({
    ...group,
    files: [...group.files].slice(0, 5),
  }));

console.log(
  JSON.stringify(
    {
      scoreAvailable: score !== null,
      score,
      scoreSource: ownScore !== null ? "report" : projectScores.length > 0 ? "worst-project" : null,
      projectScores,
      diagnosticCount: diagnostics.length,
      severityCounts,
      categoryCounts,
      topGroups,
    },
    null,
    2
  )
);
