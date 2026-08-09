/* Regression: fullscreen clips must never occupy adjacent display pages.
   Current production shape: 46 menu items = 16 pages, 17 promo clips. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('apps/menu-display/Index.html', 'utf8');
const match = source.match(/function interleaveVideoPages\(pages, videoUrls\) \{[\s\S]*?\n    \}/);
assert(match, 'interleaveVideoPages must exist in Index.html');
const sandbox = {};
vm.runInNewContext(match[0], sandbox);

const menuPages = Array.from({ length: 16 }, (_, i) => [{ name: `menu-${i}` }]);
const videos = Array.from({ length: 17 }, (_, i) => `video-${i}.mp4`);
const result = sandbox.interleaveVideoPages(menuPages, videos);

const videoIndexes = result
  .map((page, index) => page && page.video ? index : -1)
  .filter(index => index >= 0);

assert(
  videoIndexes.every((index, position) => position === 0 || index - videoIndexes[position - 1] > 1),
  `fullscreen videos must be separated by menu pages; got video indexes ${videoIndexes.join(', ')}`
);
assert.strictEqual(
  videoIndexes.length,
  8,
  'one menu cycle may use only its eight RU+ME-pair video slots; surplus clips move to a later cycle'
);
console.log('PASS: no adjacent fullscreen video pages');
