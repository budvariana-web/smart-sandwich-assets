import assert from 'node:assert/strict';
import { getBarStatus } from '../../assets/video-player/opening-hours.mjs';

const tz = 'Europe/Podgorica';
function at(iso) { return new Date(iso); }

let status = getBarStatus(at('2026-11-22T09:30:00Z'), tz); // Saturday, 10:30 local
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'00:30:00', nextOpen:'11:00' });

status = getBarStatus(at('2026-11-22T13:30:00Z'), tz); // Saturday, 14:30 local
assert.deepEqual(status, { kind:'open', label:'Открыто до:', value:'00:30:00', nextOpen:'15:00' });

status = getBarStatus(at('2026-11-22T14:20:00Z'), tz); // Saturday, 15:20 local break
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'01:40:00', nextOpen:'17:00' });

status = getBarStatus(at('2026-11-22T21:15:00Z'), tz); // Saturday, 22:15 local
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'36:45:00', nextOpen:'11:00' });

status = getBarStatus(at('2026-11-23T12:00:00Z'), tz); // Monday, 13:00 local
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'22:00:00', nextOpen:'11:00' });
console.log('opening-hours tests: PASS');
