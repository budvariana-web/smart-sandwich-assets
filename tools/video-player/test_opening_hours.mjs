import assert from 'node:assert/strict';
import { getBarStatus } from '../../assets/video-player/opening-hours.mjs';

const tz = 'Europe/Podgorica';
function at(iso) { return new Date(iso); }

let status = getBarStatus(at('2026-11-22T09:30:00Z'), tz); // Saturday, 10:30 local
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'00:30:00', nextOpen:'11:00' });

status = getBarStatus(at('2026-11-22T13:30:00Z'), tz); // Saturday, 14:30 local: first service period
assert.deepEqual(status, { kind:'break', label:'До перерыва осталось:', value:'00:30:00', nextOpen:'15:00' });

status = getBarStatus(at('2026-11-22T14:20:00Z'), tz); // Saturday, 15:20 local lunch break
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'01:40:00', nextOpen:'17:00' });

status = getBarStatus(at('2026-11-22T19:30:00Z'), tz); // Saturday, 20:30 local: final service period
assert.deepEqual(status, { kind:'closes', label:'До закрытия осталось:', value:'01:30:00', nextOpen:'22:00' });

status = getBarStatus(at('2026-11-23T12:00:00Z'), tz); // Monday, 13:00 local
assert.deepEqual(status, { kind:'opens', label:'До открытия осталось:', value:'22:00:00', nextOpen:'11:00' });
console.log('opening-hours tests: PASS');
