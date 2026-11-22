import assert from 'node:assert/strict';
import { ShuffledQueue, normalizeUrls } from '../../assets/video-player/player-core.mjs';

const urls = ['https://x/a.mp4', 'https://x/b.mp4', 'https://x/c.mp4'];
assert.deepEqual(normalizeUrls([...urls, urls[1], '', '  ']), urls);

const queue = new ShuffledQueue(urls, () => 0);
const firstRound = [queue.next(), queue.next(), queue.next()];
assert.equal(new Set(firstRound).size, 3, 'every clip appears once in a round');
assert.notEqual(queue.next(), firstRound.at(-1), 'new round cannot start with the prior clip');

console.log('queue tests: PASS');
