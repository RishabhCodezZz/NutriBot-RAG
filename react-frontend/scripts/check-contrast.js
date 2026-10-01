// Asserts WCAG AA (4.5:1) for every text/background token pair, in both themes.
// Parses the RGB triplets straight out of src/index.css so it can't drift.
const fs = require('fs');
const path = require('path');

const css = fs.readFileSync(path.join(__dirname, '..', 'src', 'index.css'), 'utf8');

function readBlock(selector) {
  const escaped = selector.replace(/[.]/g, '\\.');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  if (!match) throw new Error(`token block not found: ${selector}`);
  const vars = {};
  for (const m of match[1].matchAll(/--([a-z0-9-]+):\s*(\d+)\s+(\d+)\s+(\d+)\s*;/g)) {
    vars[m[1]] = [Number(m[2]), Number(m[3]), Number(m[4])];
  }
  return vars;
}

function luminance([r, g, b]) {
  const lin = [r, g, b].map((v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2];
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const PAIRS = [
  ['ink', 'canvas'], ['ink', 'surface'], ['ink', 'surface-2'], ['ink', 'primary-soft'],
  ['muted', 'canvas'], ['muted', 'surface'], ['muted', 'surface-2'],
  ['primary', 'canvas'], ['primary', 'surface'], ['primary', 'primary-soft'],
  ['primary-fg', 'primary'],
  ['accent', 'canvas'], ['accent', 'surface'],
  ['danger', 'danger-soft'],
];

let failed = 0;
for (const [theme, selector] of [['light', ':root'], ['dark', '.dark']]) {
  const vars = readBlock(selector);
  for (const [fg, bg] of PAIRS) {
    if (!vars[fg] || !vars[bg]) throw new Error(`${theme}: missing token ${!vars[fg] ? fg : bg}`);
    const r = ratio(vars[fg], vars[bg]);
    const ok = r >= 4.5;
    if (!ok) failed += 1;
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${theme.padEnd(5)} ${fg} on ${bg}: ${r.toFixed(2)}`);
  }
}
if (failed) {
  console.error(`\n${failed} pair(s) below 4.5:1`);
  process.exit(1);
}
console.log('\nAll token pairs >= 4.5:1');
