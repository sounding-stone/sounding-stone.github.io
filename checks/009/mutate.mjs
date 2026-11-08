// Break written.mjs one way at a time; a mutant is caught if its controls refuse
// or it gives a different verdict or exit status on either target call.
import { readFileSync, writeFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

const SRC = readFileSync('written.mjs', 'utf8');
const MUTANTS = [
  ['compare the argument with itself',  'const got = entry[field];', 'const got = passed;'],
  ['build the entry from the arguments', 'const entry = written(call);', "const entry = { message: call.msg, severity: 'X', ...(call.fields || {}) };"],
  ['substring match (the : operator)',   'JSON.stringify(got) === JSON.stringify(passed)', "(typeof got === 'string' ? got.includes(passed) : JSON.stringify(got) === JSON.stringify(passed))"],
  ['read stdout only',                   '(r.stdout + r.stderr)', 'r.stdout'],
  ['first line of the message only',     'const got = entry[field];', "const got = typeof entry[field] === 'string' ? entry[field].split('\\n')[0] : entry[field];"],
  ['a missing field counts as same',     "if (!(field in entry)) return { verdict: 'MISSING', passed };", ''],
  ['every verdict exits 0',              'process.exit(allSame ? 0 : 1);', 'process.exit(0);'],
  ['controls are not enforced',          'if (bad) {', 'if (false) {'],
];
const TARGETS = [['error', 'nightly job failed', '{"category":"nightly"}', 'message'],
                 ['error', 'nightly job failed', '{"category":"nightly"}', 'category']];
const run = (file, t) => {
  const r = spawnSync('node', [file, ...t], { encoding: 'utf8' });
  return `${r.status} ${(r.stdout.trim().split('\n').pop() || '').split(/\s+/)[0]}`;
};
const base = TARGETS.map((t) => run('written.mjs', t));
console.log(`original: ${base.join(' | ')}`);
let caught = 0;
for (const [name, from, to] of MUTANTS) {
  if (!SRC.includes(from)) { console.log(`NOT APPLIED  ${name}`); continue; }
  writeFileSync('mutant.mjs', SRC.replace(from, to));
  const got = TARGETS.map((t) => run('mutant.mjs', t));
  const hit = got.some((g, i) => g !== base[i]);
  caught += hit;
  console.log(`${hit ? 'caught  ' : 'SURVIVED'}  ${name.padEnd(36)} ${got.join(' | ')}`);
}
rmSync('mutant.mjs');
console.log(`\n${MUTANTS.length} mutants, ${caught} caught, ${MUTANTS.length - caught} survived`);
