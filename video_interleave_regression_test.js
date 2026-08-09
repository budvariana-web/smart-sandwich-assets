/* Regression: fullscreen clips must never occupy adjacent display pages.
   New production shape: one set is three products on ME+RU then EN+DE pages;
   with 23 products and bundlesBeforeVideo=3 there are three video slots. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('apps/menu-display/Index.html', 'utf8');
const match = source.match(/function buildBilingualPages\(items, bundlesBeforeVideo, videoUrls\) \{[\s\S]*?\n    \}/);
assert(match, 'buildBilingualPages must exist in Index.html');
const sandbox = { CARDS_PER_PAGE: 3 };
vm.runInNewContext(match[0], sandbox);

const items = Array.from({ length: 23 }, (_, index) => ({ orderKey: String(index + 1) }));
const videos = Array.from({ length: 17 }, (_, index) => `video-${index}.mp4`);
const result = sandbox.buildBilingualPages(items, 3, videos);
const videoIndexes = Array.from(result, (page, index) => page && page.video ? index : -1)
  .filter(index => index >= 0);

assert(videoIndexes.every((index, position) => position === 0 || index - videoIndexes[position - 1] > 1),
  `fullscreen videos must be separated by menu pages; got video indexes ${videoIndexes.join(', ')}`);
assert.strictEqual(videoIndexes.length, 3,
  '23 products form eight sets, producing 3 configured video slots at 3 sets per video');
assert.deepStrictEqual(videoIndexes, [6, 13, 18]);
console.log('PASS: no adjacent fullscreen video pages in multilingual cycle');
