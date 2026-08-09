/* Regression: surplus fullscreen clips move to subsequent menu cycles without repeats. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('apps/menu-display/Index.html', 'utf8');
const match = source.match(/function fullscreenVideoBatch\(order, slots, offset\) \{[\s\S]*?\n    \}/);
assert(match, 'fullscreenVideoBatch must exist in Index.html');
const sandbox = {};
vm.runInNewContext(match[0], sandbox);

const order = Array.from({ length: 17 }, (_, i) => `video-${i}`);
const first = sandbox.fullscreenVideoBatch(order, 8, 0);
const second = sandbox.fullscreenVideoBatch(order, 8, first.nextOffset);
const third = sandbox.fullscreenVideoBatch(order, 8, second.nextOffset);

assert.deepStrictEqual(first.urls, order.slice(0, 8));
assert.deepStrictEqual(second.urls, order.slice(8, 16));
assert.deepStrictEqual(third.urls, order.slice(16));
assert.strictEqual(third.nextOffset, 0, 'cursor resets only after every clip has been scheduled once');
assert.strictEqual(new Set([...first.urls, ...second.urls, ...third.urls]).size, 17);
console.log('PASS: surplus fullscreen videos rotate into later menu cycles');
