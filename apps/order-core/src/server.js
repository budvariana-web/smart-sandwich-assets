import http from 'node:http';
import { pathToFileURL } from 'node:url';

import {
  buildWaitForecast,
  createOrder,
  toKitchenOrder,
  toPublicWaitForecast,
} from './order-core.js';

function sendJson(response, status, body) {
  response.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  response.end(JSON.stringify(body));
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.setEncoding('utf8');
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      try { resolve(body ? JSON.parse(body) : {}); }
      catch { reject(new Error('invalid JSON')); }
    });
    request.on('error', reject);
  });
}

export async function startOrderApi({ port = 3000, clock = () => new Date(), settings = {} } = {}) {
  const orders = new Map();
  const forecastSettings = {
    kitchenLanes: settings.kitchenLanes ?? 1,
    defaultNewOrderSeconds: settings.defaultNewOrderSeconds ?? 0,
    safetyBufferSeconds: settings.safetyBufferSeconds ?? 0,
  };

  const server = http.createServer(async (request, response) => {
    const url = new URL(request.url, 'http://localhost');
    try {
      if (request.method === 'GET' && url.pathname === '/health') {
        return sendJson(response, 200, { ok: true, orderCount: orders.size });
      }
      if (request.method === 'POST' && url.pathname === '/orders') {
        const input = await readJson(request);
        if (orders.has(input.id)) return sendJson(response, 409, { error: 'duplicate order id' });
        const order = createOrder({ ...input, createdAt: input.createdAt || clock().toISOString() });
        orders.set(order.id, order);
        return sendJson(response, 201, { id: order.id, orderNumber: order.orderNumber, status: order.status });
      }
      const statusMatch = url.pathname.match(/^\/orders\/([^/]+)\/status$/);
      if (request.method === 'POST' && statusMatch) {
        const order = orders.get(decodeURIComponent(statusMatch[1]));
        if (!order) return sendJson(response, 404, { error: 'order not found' });
        const input = await readJson(request);
        const allowed = { confirmed: ['preparing', 'cancelled'], preparing: ['ready', 'cancelled'], ready: ['completed', 'cancelled'] };
        if (!allowed[order.status]?.includes(input.status)) {
          return sendJson(response, 409, { error: `invalid transition from ${order.status}` });
        }
        order.status = input.status;
        if (input.estimatedFinishAt) order.estimatedFinishAt = input.estimatedFinishAt;
        orders.set(order.id, order);
        return sendJson(response, 200, { id: order.id, orderNumber: order.orderNumber, status: order.status });
      }
      if (request.method === 'GET' && url.pathname === '/kitchen/orders') {
        return sendJson(response, 200, [...orders.values()]
          .filter((order) => ['new', 'confirmed', 'preparing'].includes(order.status))
          .map(toKitchenOrder));
      }
      if (request.method === 'GET' && url.pathname === '/public/wait-forecast') {
        const forecast = buildWaitForecast([...orders.values()], clock(), forecastSettings);
        return sendJson(response, 200, toPublicWaitForecast(forecast));
      }
      return sendJson(response, 404, { error: 'not found' });
    } catch (error) {
      return sendJson(response, 400, { error: error.message });
    }
  });

  await new Promise((resolve) => server.listen(port, '127.0.0.1', resolve));
  return {
    port: server.address().port,
    close: () => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())),
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const app = await startOrderApi({ port: Number(process.env.PORT) || 3000 });
  console.log(`order-core API listening on http://127.0.0.1:${app.port}`);
}
