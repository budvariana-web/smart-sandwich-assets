import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildWaitForecast,
  createOrder,
  toKitchenOrder,
  toPublicWaitForecast,
} from '../src/order-core.js';

test('creates one canonical order for an external source with immutable price snapshot', () => {
  const order = createOrder({
    id: 'ord-3213',
    source: 'telegram_form',
    externalOrderId: 'tg-987',
    createdAt: '2026-08-09T10:00:00.000Z',
    items: [{ productId: 'burger-macho', name: 'Мачо Бургер', quantity: 2, unitPriceCents: 1000 }],
    service: { customerMessage: 'Без лука, пожалуйста' },
  });

  assert.equal(order.id, 'ord-3213');
  assert.equal(order.source, 'telegram_form');
  assert.equal(order.externalOrderId, 'tg-987');
  assert.equal(order.status, 'confirmed');
  assert.deepEqual(order.items, [{ productId: 'burger-macho', name: 'Мачо Бургер', quantity: 2, unitPriceCents: 1000 }]);
  assert.equal(order.totalCents, 2000);
});

test('kitchen projection contains preparation work but never contact, address, payment, tender, or change data', () => {
  const order = createOrder({
    id: 'ord-private', source: 'website', externalOrderId: 'web-11',
    items: [{ productId: 'sandwich', name: 'Сэндвич', quantity: 1, unitPriceCents: 450 }],
    service: {
      contactChannel: '@customer',
      deliveryLocation: { address: 'Bar, Secret Street 1', latitude: 42.1, longitude: 19.1 },
      payment: { method: 'cash', cashTenderedCents: 5000, changeRequired: true, changeAmountCents: 4550 },
      customerMessage: 'Домофон 15. Без лука.',
    },
  });

  const kitchen = toKitchenOrder(order);
  assert.deepEqual(kitchen, {
    id: 'ord-private', orderNumber: 'private', status: 'confirmed',
    items: [{ name: 'Сэндвич', quantity: 1 }], preparationNote: 'Без лука.',
  });
  assert.equal(JSON.stringify(kitchen).includes('Secret Street'), false);
  assert.equal(JSON.stringify(kitchen).includes('5000'), false);
});

test('public forecast includes hidden online workload but exposes only safe wait fields', () => {
  const now = new Date('2026-08-09T10:00:00.000Z');
  const active = [
    { id: 'ord-3213', orderNumber: '3213', status: 'preparing', estimatedFinishAt: '2026-08-09T10:11:23.000Z' },
    { id: 'ord-online', orderNumber: '3214', status: 'confirmed', estimatedPrepSeconds: 1800,
      source: 'ifood_telegram', service: { contactChannel: '@hidden', payment: { method: 'card' } } },
  ];

  const forecast = buildWaitForecast(active, now, {
    kitchenLanes: 1, defaultNewOrderSeconds: 0, safetyBufferSeconds: 0,
  });
  assert.equal(forecast.activeOrderNumber, '3213');
  assert.equal(forecast.activeOrderRemainingSeconds, 683);
  assert.equal(forecast.newOrderWaitSeconds, 2483);
  assert.deepEqual(toPublicWaitForecast(forecast), {
    activeOrderNumber: '3213', activeOrderRemainingSeconds: 683, newOrderWaitSeconds: 2483,
  });
});
