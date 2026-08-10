# Smart Sandwich Bar — Order Core

Independent prototype API for the future ordering, kitchen queue, customer displays, cashier/admin and partner clients.

## What works in this first vertical slice

- Canonical order creation for `website`, `ifood_telegram`, `telegram_form`, `instagram`, `cashier`, `phone`, and `partner_ptt`.
- Immutable item/price snapshots and an external order reference.
- Kitchen-safe projection: items and food-preparation note only; contact, delivery location, payment, tender and change are excluded.
- Public wait forecast that includes all active workload, including online orders, without revealing their details.
- Status transition `confirmed → preparing → ready → completed` (and cancellation where permitted).

## Run locally

```bash
cd apps/order-core
npm test
PORT=3910 npm start
```

## API currently implemented

- `GET /health`
- `POST /orders`
- `POST /orders/:id/status`
- `GET /kitchen/orders`
- `GET /public/wait-forecast`

## Current limitation

This is an intentionally small, tested foundation. It holds data in memory and is **not deployed or connected to the public menu yet**. The next implementation step is durable storage plus authenticated role-based access before connecting real order channels or staff devices.
