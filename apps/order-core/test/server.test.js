import test from 'node:test';
import assert from 'node:assert/strict';

import { startOrderApi } from '../src/server.js';

test('HTTP API accepts an external order and serves safe kitchen and public projections', async (t) => {
  const app = await startOrderApi({ port: 0, clock: () => new Date('2026-08-09T10:00:00.000Z') });
  t.after(() => app.close());
  const base = `http://127.0.0.1:${app.port}`;

  const created = await fetch(`${base}/orders`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      id: 'ord-3213', source: 'ifood_telegram', externalOrderId: 'ifood-1',
      estimatedPrepSeconds: 1800,
      items: [{ productId: 'burger', name: 'Бургер', quantity: 1, unitPriceCents: 1000 }],
      service: {
        contactChannel: '@private',
        deliveryLocation: { address: 'Hidden address', latitude: 42.1, longitude: 19.1 },
        payment: { method: 'cash', cashTenderedCents: 5000, changeAmountCents: 4000 },
        customerMessage: 'Без лука. Позвоните в домофон.',
      },
    }),
  });
  assert.equal(created.status, 201);
  assert.deepEqual(await created.json(), { id: 'ord-3213', orderNumber: '3213', status: 'confirmed' });

  const kitchen = await (await fetch(`${base}/kitchen/orders`)).json();
  assert.equal(kitchen.length, 1);
  assert.deepEqual(kitchen[0].items, [{ name: 'Бургер', quantity: 1 }]);
  assert.equal(kitchen[0].preparationNote, 'Без лука.');
  assert.equal(JSON.stringify(kitchen).includes('Hidden address'), false);
  assert.equal(JSON.stringify(kitchen).includes('4000'), false);

  const publicForecast = await (await fetch(`${base}/public/wait-forecast`)).json();
  assert.deepEqual(publicForecast, {
    activeOrderNumber: null, activeOrderRemainingSeconds: 0, newOrderWaitSeconds: 1800,
  });
});
