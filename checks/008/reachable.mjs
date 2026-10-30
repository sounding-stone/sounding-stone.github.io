#!/usr/bin/env node
// Can a tap reach this element where the user first sees it, without anything scrolling?
//   node reachable.mjs <page.html|url> <css-selector> ["iPhone 13"]
// Verdicts: REACHABLE, COVERED (another element is on top of part of it),
// OFFSCREEN (part of it is outside the viewport, nothing on top), NO_BOX.
// Exits 0 REACHABLE, 1 any other verdict, 2 if the built-in controls fail, 3 on bad input.
// Limit: this is a hit test. An overlay with pointer-events:none hides the element
// from the eye but not from the hit test, so it reads REACHABLE.
import { chromium, webkit, devices } from 'playwright';
import { pathToFileURL } from 'node:url';
import { existsSync } from 'node:fs';

const GRID = 5;
function probe({ sel, grid }) {         // runs in the page
  const el = document.querySelector(sel);
  const r = el && el.getBoundingClientRect();
  if (!r || r.width === 0 || r.height === 0) return { verdict: 'NO_BOX' };
  let mine = 0, outside = 0; const others = new Set();
  for (let i = 0; i < grid; i++) for (let j = 0; j < grid; j++) {
    const x = r.left + r.width * (i + 0.5) / grid, y = r.top + r.height * (j + 0.5) / grid;
    if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) { outside++; continue; }
    const hit = document.elementFromPoint(x, y);
    if (hit && (hit === el || el.contains(hit))) mine++;
    else others.add(hit ? hit.tagName.toLowerCase() + (hit.id ? '#' + hit.id : '') : 'nothing');
  }
  const n = grid * grid, detail = `${mine}/${n} points reach it`;
  if (others.size) return { verdict: 'COVERED', detail: `${detail}; on top: ${[...others].join(', ')}` };
  if (outside) return { verdict: 'OFFSCREEN', detail: `${detail}; ${outside} outside the viewport` };
  return { verdict: 'REACHABLE', detail };
}
async function measure(page, sel) {
  await page.evaluate(() => window.scrollTo(0, 0));   // where the user lands; never scroll to it
  return page.evaluate(probe, { sel, grid: GRID });
}

const NAV = '<nav id="nav" style="position:fixed;left:0;right:0;bottom:0;height:48px;z-index:200;background:#ddd"></nav>';
const META = '<meta name="viewport" content="width=device-width,initial-scale=1">';
const FILL = '<div style="height:900px"></div>';
const sticky = (bottom, pad) => `<body style="margin:0;padding-bottom:${pad}px">${FILL}<div style="position:sticky;bottom:${bottom}px;padding:8px"><button id="b" style="width:100%;height:48px"><span>Start</span></button></div>${NAV}`;
const CONTROLS = [
  ['+', 'COVERED',   'sticky bar under a fixed nav', sticky(0, 48)],
  ['+', 'COVERED',   'nav over the bottom fifth, centre clear', `<body style="margin:0">${FILL}<button id="b" style="position:fixed;left:0;right:0;bottom:30px;height:90px">Start</button>${NAV}`],
  ['+', 'OFFSCREEN', 'plain button below the fold', `<body style="margin:0">${FILL}<button id="b" style="height:48px">Start</button>`],
  ['+', 'NO_BOX',    'button with display:none', `<body><button id="b" style="display:none">Start</button>`],
  ['-', 'REACHABLE', 'sticky bar above the nav', sticky(48, 48)],
  ['-', 'REACHABLE', 'label span inside the button', `<body style="margin:0"><button id="b" style="width:200px;height:80px"><span style="display:block;width:100%;height:100%">Start</span></button>${NAV}`],
];

const [target, sel, dev = 'iPhone 13'] = process.argv.slice(2);
if (!target || !sel || !devices[dev]) { console.error('usage: reachable.mjs <page|url> <selector> [device]'); process.exit(3); }
const url = /^https?:/.test(target) ? target : existsSync(target) ? pathToFileURL(target).href : null;
if (!url) { console.error(`cannot read ${target}`); process.exit(3); }

const browser = await (devices[dev].defaultBrowserType === 'webkit' ? webkit : chromium).launch();
const page = await (await browser.newContext({ ...devices[dev] })).newPage();
let bad = 0;
for (const [sign, want, label, html] of CONTROLS) {
  await page.setContent(META + html);
  const got = await measure(page, '#b');
  if (got.verdict !== want) bad++;
  console.log(`control ${sign}  ${got.verdict.padEnd(10)} ${label}${got.verdict === want ? '' : `  <- want ${want}`}`);
}
if (bad) { console.log(`\ncontrols failed (${bad}); not measuring ${target}`); await browser.close(); process.exit(2); }

try { await page.goto(url); } catch (e) { console.error(`cannot load ${url}: ${e.message.split('\n')[0]}`); await browser.close(); process.exit(3); }
const got = await measure(page, sel);
console.log(`\n${got.verdict.padEnd(10)} ${sel} on ${dev}${got.detail ? `  (${got.detail})` : ''}`);
await browser.close();
process.exit(got.verdict === 'REACHABLE' ? 0 : 1);
