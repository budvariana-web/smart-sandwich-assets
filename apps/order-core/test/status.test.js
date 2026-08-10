import test from 'node:test';
import assert from 'node:assert/strict';

import { startOrderApi } from '../src/server.js';

test('kitchen can start a confirmed order and public forecast exposes only its number and remaining time', async (t) => {
  const now = new Date('2026-08-09T10:00:00.000Z');
  const app = await startOrderApi({ port: 0, clock: () => now });
  t.after(() => app.close());
  const base = `http://127.0.0.1:${app.port}`;

  await fetch(`${base}/orders`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      id: 'ord-3213', source: 'cashier', estimatedPrepSeconds: 1200,
      items: [{ productId: 'burger', name: 'Бургер', quantity: 1, unitPriceCents: 1000 }],
    }),
  });

  const status = await fetch(`${base}/orders/ord-3213/status`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ status: 'preparing', estimatedFinishAt: '2026-08-09T10:11:23.000Z' }),
  });
  assert.equal(status.status, 200);
  assert.deepEqual(await status.json(), { id: 'ord-3213', orderNumber: '3213', status: 'preparing' });

  const forecast = await (await fetch(`${base}/public/wait-forecast`)).json();
  assert.deepEqual(forecast, {
    activeOrderNumber: '3213', activeOrderRemainingSeconds: 683, newOrderWaitSeconds: 683,
  });
});
