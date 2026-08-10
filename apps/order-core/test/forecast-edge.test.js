import test from 'node:test';
import assert from 'node:assert/strict';

import { buildWaitForecast } from '../src/order-core.js';

test('public forecast skips a stale preparing order when selecting the currently cooking order', () => {
  const forecast = buildWaitForecast([
    { orderNumber: '3213', status: 'preparing', estimatedFinishAt: '2026-08-09T09:59:00.000Z' },
    { orderNumber: '3214', status: 'preparing', estimatedFinishAt: '2026-08-09T10:11:23.000Z' },
  ], new Date('2026-08-09T10:00:00.000Z'), {
    kitchenLanes: 1, defaultNewOrderSeconds: 0, safetyBufferSeconds: 0,
  });

  assert.equal(forecast.activeOrderNumber, '3214');
  assert.equal(forecast.activeOrderRemainingSeconds, 683);
});
