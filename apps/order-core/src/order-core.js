const VALID_SOURCES = new Set([
  'website', 'ifood_telegram', 'telegram_form', 'instagram', 'cashier', 'phone', 'partner_ptt',
]);

function orderNumberFromId(id) {
  const suffix = String(id).split('-').at(-1);
  return suffix || String(id);
}

function centsFor(items) {
  return items.reduce((total, item) => total + item.quantity * item.unitPriceCents, 0);
}

export function createOrder(input) {
  if (!input?.id) throw new Error('order id is required');
  if (!VALID_SOURCES.has(input.source)) throw new Error('known order source is required');
  if (!Array.isArray(input.items) || input.items.length === 0) throw new Error('at least one item is required');

  const items = input.items.map((item) => {
    if (!item.productId || !item.name || !Number.isInteger(item.quantity) || item.quantity < 1 ||
        !Number.isInteger(item.unitPriceCents) || item.unitPriceCents < 0) {
      throw new Error('valid item snapshot is required');
    }
    return { productId: item.productId, name: item.name, quantity: item.quantity, unitPriceCents: item.unitPriceCents };
  });

  return {
    id: input.id,
    orderNumber: input.orderNumber || orderNumberFromId(input.id),
    source: input.source,
    externalOrderId: input.externalOrderId || null,
    createdAt: input.createdAt || new Date().toISOString(),
    status: 'confirmed',
    estimatedPrepSeconds: Math.max(0, Number(input.estimatedPrepSeconds) || 0),
    items,
    totalCents: centsFor(items),
    service: input.service || {},
  };
}

function preparationNote(message) {
  if (!message) return '';
  // v1 deliberately keeps only food-preparation intent; delivery/contact/payment
  // clauses remain in the server-side service record and do not leave the API.
  return String(message)
    .split(/(?<=[.!?])\s+/)
    .filter((sentence) => /без\s|добав|убра|аллерг|остр|соус|лук|соль|перец/i.test(sentence))
    .join(' ')
    .trim();
}

export function toKitchenOrder(order) {
  return {
    id: order.id,
    orderNumber: order.orderNumber,
    status: order.status,
    items: order.items.map(({ name, quantity }) => ({ name, quantity })),
    preparationNote: preparationNote(order.service?.customerMessage),
  };
}

function remainingSeconds(order, nowMs) {
  if (order.status === 'preparing' && order.estimatedFinishAt) {
    return Math.max(0, Math.ceil((new Date(order.estimatedFinishAt).getTime() - nowMs) / 1000));
  }
  return Math.max(0, Number(order.estimatedPrepSeconds) || 0);
}

export function buildWaitForecast(activeOrders, now, settings) {
  const active = activeOrders.filter((order) => ['new', 'confirmed', 'preparing'].includes(order.status));
  const nowMs = new Date(now).getTime();
  const lanes = Math.max(1, Number(settings.kitchenLanes) || 1);
  const preparing = active.find((order) => order.status === 'preparing' && remainingSeconds(order, nowMs) > 0);
  const workload = active.reduce((sum, order) => sum + remainingSeconds(order, nowMs), 0);

  return {
    activeOrderNumber: preparing?.orderNumber || null,
    activeOrderRemainingSeconds: preparing ? remainingSeconds(preparing, nowMs) : 0,
    newOrderWaitSeconds: Math.ceil(workload / lanes) + Math.max(0, Number(settings.defaultNewOrderSeconds) || 0) + Math.max(0, Number(settings.safetyBufferSeconds) || 0),
  };
}

export function toPublicWaitForecast(forecast) {
  return {
    activeOrderNumber: forecast.activeOrderNumber,
    activeOrderRemainingSeconds: forecast.activeOrderRemainingSeconds,
    newOrderWaitSeconds: forecast.newOrderWaitSeconds,
  };
}
