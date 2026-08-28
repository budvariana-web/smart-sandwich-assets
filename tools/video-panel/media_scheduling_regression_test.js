/* Contract: independently shuffled media lanes and transition gates.
   This test intentionally extracts the pure scheduling helpers from the Apps
   Script template so the critical rotation rules remain regression-testable. */
const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const source = fs.readFileSync('apps/menu-display/Index.html', 'utf8');

function loadFunction(name, argsPattern) {
  const match = source.match(new RegExp(`function ${name}\\(${argsPattern}\\) \\{[\\s\\S]*?\\n    \\}`));
  assert(match, `${name} must exist in Index.html`);
  return match[0];
}

const sandbox = {
  Math: Object.create(Math),
  JSON,
  Date,
  Set,
  String,
  Array,
  Number,
  Boolean
};
// Deterministic Fisher-Yates choices: still exercises queue boundaries.
let randomValues = [0.71, 0.12, 0.94, 0.36, 0.58, 0.04, 0.82, 0.23, 0.67];
sandbox.Math.random = () => randomValues.shift() ?? 0.5;

vm.runInNewContext([
  loadFunction('createPlaylistManager', ''),
  loadFunction('shufflePlaylistItems', 'items, avoid'),
  loadFunction('syncPlaylistManager', 'manager, items'),
  loadFunction('nextPlaylistItem', 'manager'),
  loadFunction('takePlaylistItems', 'manager, count'),
  loadFunction('isMenuAdvanceReady', 'pageTimerElapsed, miniVideoFinished, rightBlockExposureReached'),
  loadFunction('isActiveMiniVideoEvent', 'activeUrl, sourceUrl'),
  loadFunction('rightBlockNeedsMinimumExposure', 'items')
].join('\n'), sandbox);

// A lane shows every item exactly once before its next shuffle begins.
const side = sandbox.createPlaylistManager();
sandbox.syncPlaylistManager(side, ['a', 'b', 'c']);
const firstCycle = sandbox.takePlaylistItems(side, 3);
assert.strictEqual(new Set(firstCycle).size, 3, 'side lane must not repeat before every clip appears');
assert.deepStrictEqual([...firstCycle].sort(), ['a', 'b', 'c']);
const prior = firstCycle[2];
const nextCycleFirst = sandbox.nextPlaylistItem(side);
assert.notStrictEqual(nextCycleFirst, prior, 'new cycle must avoid an immediate A → A repeat when alternatives exist');

// Refreshing an unchanged lane must preserve its queue; another lane is isolated.
const fullscreen = sandbox.createPlaylistManager();
sandbox.syncPlaylistManager(fullscreen, ['F1', 'F2', 'F3']);
const fullscreenFirst = sandbox.nextPlaylistItem(fullscreen);
const sidePendingBeforeRefresh = side.queue.slice();
sandbox.syncPlaylistManager(side, ['a', 'b', 'c']);
assert.deepStrictEqual(side.queue, sidePendingBeforeRefresh, 'same side playlist data must not reset its queue');
assert.strictEqual(fullscreen.current, fullscreenFirst, 'side refresh must not affect fullscreen lane state');
const fullscreenCycle = [fullscreenFirst].concat(sandbox.takePlaylistItems(fullscreen, 2));
assert.strictEqual(new Set(fullscreenCycle).size, 3, 'fullscreen lane must remain independently non-repeating');

// Duplicate source URLs are one media asset, not extra lottery tickets.
const duplicateSafe = sandbox.createPlaylistManager();
sandbox.syncPlaylistManager(duplicateSafe, ['same', 'same', 'other']);
assert.deepStrictEqual([...duplicateSafe.items].sort(), ['other', 'same']);

// A page may advance only when every explicit gate is true.
assert.strictEqual(sandbox.isMenuAdvanceReady(true, true, true), true);
assert.strictEqual(sandbox.isMenuAdvanceReady(false, true, true), false);
assert.strictEqual(sandbox.isMenuAdvanceReady(true, false, true), false);
assert.strictEqual(sandbox.isMenuAdvanceReady(true, true, false), false);

// A preload failure must never impersonate the currently visible mini-video.
assert.strictEqual(sandbox.isActiveMiniVideoEvent('active.mp4', 'preloaded.mp4'), false);
assert.strictEqual(sandbox.isActiveMiniVideoEvent('active.mp4', 'active.mp4'), true);

// Weather is a real right-hand block and must receive its minimum exposure.
assert.strictEqual(sandbox.rightBlockNeedsMinimumExposure(['__weather__']), true);
assert.strictEqual(sandbox.rightBlockNeedsMinimumExposure([]), false);

console.log('PASS: independent shuffled playlists and page transition gates');
