// Break reachable.mjs one way at a time; a mutant is caught if its controls refuse (exit 2)
// or it gives a different verdict or exit status on either toy page.
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const SRC = readFileSync('reachable.mjs', 'utf8');
const MUTANTS = [
  ['centre point only',             'const GRID = 5;', 'const GRID = 1;'],
  ['label span counts as cover',    'hit === el || el.contains(hit)', 'hit === el'],
  ['scroll to the end first',       'window.scrollTo(0, 0)', 'window.scrollTo(0, document.body.scrollHeight)'],
  ['box only, no hit test',         'const hit = document.elementFromPoint(x, y);', 'const hit = el;'],
  ['outside the viewport is fine',  'outside++; continue;', 'mine++; continue;'],
  ['half reachable is enough',      'if (others.size)', 'if (others.size && mine < n / 2)'],
  ['zero-size box is measured',     "r.width === 0 || r.height === 0", 'false'],
  ['every verdict exits 0',         "process.exit(got.verdict === 'REACHABLE' ? 0 : 1)", 'process.exit(0)'],
  ['controls are not enforced',     'if (bad) {', 'if (false) {'],
];
const run = (file, page) => {
  const r = spawnSync('node', [file, page, '#start'], { encoding: 'utf8' });
  return `${r.status} ${(r.stdout.trim().split('\n').pop() || '').split(/\s+/)[0]}`;
};
const base = ['page.html', 'page-fixed.html'].map((p) => run('reachable.mjs', p));
console.log(`original: ${base.join(' | ')}`);
let caught = 0;
for (const [name, from, to] of MUTANTS) {
  if (!SRC.includes(from)) { console.log(`NOT APPLIED  ${name}`); continue; }
  writeFileSync('mutant.mjs', SRC.replace(from, to));
  const got = ['page.html', 'page-fixed.html'].map((p) => run('mutant.mjs', p));
  const hit = got.some((g, i) => g !== base[i]);
  caught += hit;
  console.log(`${hit ? 'caught  ' : 'SURVIVED'}  ${name.padEnd(30)} ${got.join(' | ')}`);
}
rmSync('mutant.mjs');
console.log(`\n${MUTANTS.length} mutants, ${caught} caught, ${MUTANTS.length - caught} survived`);
