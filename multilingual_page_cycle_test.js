/* Contract for the multilingual TV cycle.
   A product set is three items displayed as ME+RU then EN+DE. Video follows
   each configured number of sets and after the final partial batch. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('apps/menu-display/Index.html', 'utf8');
const match = source.match(/function buildBilingualPages\(items, bundlesBeforeVideo, videoUrls\) \{[\s\S]*?\n    \}/);
assert(match, 'buildBilingualPages must exist in Index.html');
const sandbox = { CARDS_PER_PAGE: 3 };
vm.runInNewContext(match[0], sandbox);

const items = Array.from({ length: 23 }, (_, index) => ({ orderKey: String(index + 1) }));
const pages = sandbox.buildBilingualPages(items, 3, ['clip-a', 'clip-b', 'clip-c']);
const types = Array.from(pages, page => page.video ? 'V' : Array.from(page.pair).join('+'));

assert.deepStrictEqual(types, [
  'me+ru', 'en+de', 'me+ru', 'en+de', 'me+ru', 'en+de', 'V',
  'me+ru', 'en+de', 'me+ru', 'en+de', 'me+ru', 'en+de', 'V',
  'me+ru', 'en+de', 'me+ru', 'en+de', 'V'
]);
assert.strictEqual(pages.filter(page => page.video).length, 3);
assert(pages.every((page, index) => !(page.video && index > 0 && pages[index - 1].video)), 'fullscreen videos must be separated by card pages');
assert.deepStrictEqual(pages[0].items.map(item => item.orderKey), ['1', '2', '3']);
assert.deepStrictEqual(pages[1].items.map(item => item.orderKey), ['1', '2', '3']);
assert.deepStrictEqual(pages[16].items.map(item => item.orderKey), ['22', '23']);
console.log('PASS: three multilingual product sets are followed by one video');
