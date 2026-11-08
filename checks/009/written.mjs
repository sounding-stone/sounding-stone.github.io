#!/usr/bin/env node
// Does the entry firebase-functions' logger actually writes still carry the values you passed?
//   node written.mjs <debug|info|warn|error> <message> '<json fields>' <field> [field ...]
// Runs the real logger in a child process (from the current directory's node_modules) and,
// for each field you name, compares what you passed with what was written.
// Verdicts per field: SAME, CHANGED, MISSING (not in the written entry).
// Exits 0 if every named field is SAME, 1 otherwise, 2 if the built-in controls fail, 3 on bad input.
// Limit: this checks the entry as the library writes it to stdout/stderr, not what Cloud Logging
// stores or what a filter matches there.
import { spawnSync } from 'node:child_process';

function written({ sev, msg, fields, withError }) {
  const code = `const l = require('firebase-functions/logger'); const a = JSON.parse(process.argv[1]);
    const args = [a.msg]; if (a.withError) args.push(new Error('cause')); if (a.fields) args.push(a.fields);
    l[a.sev](...args);`;
  const r = spawnSync(process.execPath, ['-e', code, JSON.stringify({ sev, msg, fields, withError })],
    { encoding: 'utf8' });
  const line = (r.stdout + r.stderr).trim().split('\n').pop();
  try { return JSON.parse(line); } catch { return null; }
}
function compare(call, field) {
  const entry = written(call);
  if (!entry) return { verdict: 'NO_ENTRY' };
  const passed = field === 'message' ? call.msg : (call.fields || {})[field];
  if (!(field in entry)) return { verdict: 'MISSING', passed };
  const got = entry[field];
  return { verdict: JSON.stringify(got) === JSON.stringify(passed) ? 'SAME' : 'CHANGED', passed, got };
}

const CONTROLS = [
  ['+', 'CHANGED', 'message',  'error("x")',            { sev: 'error', msg: 'x' }],
  ['+', 'CHANGED', 'message',  'error("x", err)',       { sev: 'error', msg: 'x', withError: true }],
  ['+', 'MISSING', 'category', 'error("x"), no fields', { sev: 'error', msg: 'x' }],
  ['-', 'SAME',    'message',  'info("x")',             { sev: 'info', msg: 'x' }],
  ['-', 'SAME',    'message',  'warn("x")',             { sev: 'warn', msg: 'x' }],
  ['-', 'SAME',    'message',  'info("two\\nlines")',    { sev: 'info', msg: 'two\nlines' }],
  ['-', 'SAME',    'category', 'error("x", {category})', { sev: 'error', msg: 'x', fields: { category: 'c' } }],
];

const [sev, msg, json, ...names] = process.argv.slice(2);
let fields;
try { fields = JSON.parse(json || 'null'); } catch { fields = undefined; }
if (!['debug', 'info', 'warn', 'error'].includes(sev) || msg === undefined || fields === undefined || !names.length) {
  console.error("usage: written.mjs <debug|info|warn|error> <message> '<json fields>' <field> [field ...]");
  process.exit(3);
}
let bad = 0;
for (const [sign, want, field, label, call] of CONTROLS) {
  const { verdict } = compare(call, field);
  if (verdict !== want) bad++;
  console.log(`control ${sign}  ${verdict.padEnd(8)} ${field.padEnd(9)} ${label}${verdict === want ? '' : `  <- want ${want}`}`);
}
if (bad) { console.log(`\ncontrols failed (${bad}); not checking your call`); process.exit(bad === CONTROLS.length ? 3 : 2); }

console.log('');
let allSame = true;
for (const field of names) {
  const r = compare({ sev, msg, fields }, field);
  if (r.verdict === 'NO_ENTRY') { console.log('the logger wrote nothing parseable'); process.exit(3); }
  allSame &&= r.verdict === 'SAME';
  const show = (v) => { const s = JSON.stringify(v); return s && s.length > 48 ? s.slice(0, 45) + '..."' : s; };
  console.log(`${r.verdict.padEnd(8)} ${field.padEnd(9)} passed ${show(r.passed)}` + (r.verdict === 'CHANGED' ? `  written ${show(r.got)}` : ''));
}
process.exit(allSame ? 0 : 1);
