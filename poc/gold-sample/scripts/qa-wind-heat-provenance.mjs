import {readFile, readdir, mkdir, writeFile} from 'node:fs/promises';
import {dirname, extname, relative, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDir, '../../..');
const outputPath = resolve(
  repositoryRoot,
  'production-library/validation/revideo-editability/wind-heat-v2/provenance-qa.json',
);

const sourceRoots = [
  'poc/gold-sample/src/wind-heat-editable-project.tsx',
  'poc/gold-sample/src/reference-native-intro-project.tsx',
  'poc/gold-sample/src/reference-replica-project.tsx',
  'poc/gold-sample/src/reference-mechanism-gap-project.tsx',
  'poc/gold-sample/src/reference-symptoms-project.tsx',
  'poc/gold-sample/src/reference-treatment-project.tsx',
  'poc/gold-sample/src/reference-medication-advice-project.tsx',
  'poc/gold-sample/src/reference-summary-outro-project.tsx',
  'poc/gold-sample/src/components/reference-medical-tech-master.tsx',
  'poc/gold-sample/src/components/reference-courseware-cards.tsx',
  'poc/gold-sample/src/components/reference-mechanism-gap.tsx',
  'poc/gold-sample/src/components/reference-summary-outro.tsx',
  'production-library/examples/wind-heat-full-frame-assembly.json',
  'production-library/examples/wind-heat-mechanism-gap.json',
  'production-library/examples/wind-heat-medication-advice.json',
  'production-library/examples/wind-heat-summary-outro.json',
];

const allowedExtensions = new Set(['.ts', '.tsx', '.js', '.mjs', '.json']);
const forbidden = [
  {
    id: 'forbidden.title-reference',
    pattern: /title-reference\.png/gi,
    reason: 'Full-frame title pixels from the reference video are prohibited.',
  },
  {
    id: 'forbidden.master-clean',
    pattern: /master-clean\.png/gi,
    reason: 'The flattened reference-derived master is prohibited.',
  },
  {
    id: 'forbidden.master-frame',
    pattern: /master-frame(?:-[^"'`\s/\\]*)?\.(?:png|jpe?g|webp)/gi,
    reason: 'Reference master-frame stills and crops are prohibited.',
  },
  {
    id: 'forbidden.reference-analysis-frame-path',
    pattern: /reference-analysis[\\/]+frames[\\/][^"'`\s)]+/gi,
    reason: 'Files from the reference frame-analysis directory are analysis-only.',
  },
  {
    id: 'forbidden.reference-frame-or-crop-file',
    pattern: /(?:reference|ref)[-_](?:frame|crop)[-_a-z0-9.]*\.(?:png|jpe?g|webp)/gi,
    reason: 'Reference frame or crop files cannot enter a production model.',
  },
  {
    id: 'forbidden.reference-replica-asset-path',
    pattern: /(?:\/|['"`])reference-replica\/[^'"`\s)]+/gi,
    reason: 'The legacy reference-replica asset namespace contains extracted reference pixels and is prohibited in v2 production.',
  },
];

async function collectFiles(entry) {
  const absolute = resolve(repositoryRoot, entry);
  const extension = extname(absolute).toLowerCase();
  if (extension) {
    return allowedExtensions.has(extension) ? [absolute] : [];
  }

  const children = await readdir(absolute, {withFileTypes: true});
  const files = [];
  for (const child of children) {
    if (child.name === 'node_modules' || child.name === 'dist') continue;
    const childPath = resolve(absolute, child.name);
    if (child.isDirectory()) {
      files.push(...(await collectFiles(relative(repositoryRoot, childPath))));
    } else if (allowedExtensions.has(extname(child.name).toLowerCase())) {
      files.push(childPath);
    }
  }
  return files;
}

function lineAndColumn(content, index) {
  const before = content.slice(0, index);
  const lines = before.split('\n');
  return {line: lines.length, column: lines.at(-1).length + 1};
}

const files = [
  ...new Set((await Promise.all(sourceRoots.map(collectFiles))).flat()),
].sort();
const findings = [];

for (const file of files) {
  const content = await readFile(file, 'utf8');
  for (const rule of forbidden) {
    rule.pattern.lastIndex = 0;
    for (const match of content.matchAll(rule.pattern)) {
      const location = lineAndColumn(content, match.index ?? 0);
      findings.push({
        rule_id: rule.id,
        file: relative(repositoryRoot, file),
        line: location.line,
        column: location.column,
        match: match[0],
        reason: rule.reason,
      });
    }
  }
}

const report = {
  schema_version: '1.0.0',
  check_id: 'qa.wind-heat-v2.provenance',
  checked_at: new Date().toISOString(),
  repository_root: repositoryRoot,
  status: findings.length === 0 ? 'passed' : 'failed',
  policy: {
    reference_pixels_allowed_in_production: false,
    forbidden_rule_ids: forbidden.map(rule => rule.id),
  },
  scanned_file_count: files.length,
  scanned_files: files.map(file => relative(repositoryRoot, file)),
  finding_count: findings.length,
  findings,
};

await mkdir(dirname(outputPath), {recursive: true});
await writeFile(outputPath, `${JSON.stringify(report, null, 2)}\n`, 'utf8');
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
process.exitCode = findings.length === 0 ? 0 : 1;
