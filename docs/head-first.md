# HEAD-first: a price check that costs the seller nothing

An x402 seller is checked by catalogues, hubs and monitors that want to know its price. Each
check is a request to a paid route. If the route has a free tier or a trial, every check spends
one of the seller's free calls; if it has none, the handler may still run before the `402` is
decided. The rule below makes a check free for the seller and exact for the checker:

> On every paid route, answer `HEAD` with `402 Payment Required` and the x402 V2
> `PAYMENT-REQUIRED` header — **before** the free-tier or trial check, and without running the
> handler.

`HEAD` has no body, so the terms go in the V2 header (base64 of the same JSON a V2 `402` body
would carry: `x402Version`, `resource`, `accepts[]` with `scheme`, `network`, `amount`, `asset`,
`payTo`). A `GET` or `POST` with a payment is served as before; a `GET` or `POST` without one
follows the seller's own free-tier logic as before. Only `HEAD` changes.

Why it is needed: by default most stacks do not do this. Express routes `HEAD` to the `GET`
handler, Starlette/FastAPI add `HEAD` to every `GET` route and run the endpoint, and a
`POST`-only route answers `HEAD` with `404`/`405` and no price.

## Express

```js
// Before the routes and before any free-tier middleware.
app.use((req, res, next) => {
  const route = PAID_ROUTES[req.path];            // { amount, payTo, description } per paid path
  if (req.method !== "HEAD" || !route) return next();
  const required = {
    x402Version: 2,
    resource: { url: `https://${req.headers.host}${req.path}`, description: route.description },
    accepts: [{ scheme: "exact", network: "eip155:8453", amount: route.amount,
                asset: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", payTo: route.payTo }],
  };
  res.set("PAYMENT-REQUIRED", Buffer.from(JSON.stringify(required)).toString("base64"));
  res.status(402).end();
});
```

## FastAPI / Starlette

```python
import base64, json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class HeadFirst(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        route = PAID_ROUTES.get(request.url.path)  # {"amount", "payTo", "description"} per paid path
        if request.method != "HEAD" or route is None:
            return await call_next(request)
        required = {
            "x402Version": 2,
            "resource": {"url": str(request.url), "description": route["description"]},
            "accepts": [{"scheme": "exact", "network": "eip155:8453", "amount": route["amount"],
                         "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "payTo": route["payTo"]}],
        }
        header = base64.b64encode(json.dumps(required).encode()).decode()
        return Response(status_code=402, headers={"PAYMENT-REQUIRED": header})

app.add_middleware(HeadFirst)  # added last = runs first, before any trial middleware
```

## Check it

```bash
curl -sI https://your-seller.example/your/paid/route | head -5
# HTTP/2 402 … and a payment-required: … header; your request log shows no handler run,
# your trial counter did not move.
```

## Who uses it

AIMarket hubs' observed-seller tier (spec §2.7) sends `HEAD` first since 2026-10-31 and sends
its single unpaid request only when `HEAD` gives no terms. A seller that follows this rule is
checked with one `HEAD` per route per cycle (at least an hour apart), and never pays for it in
free calls.
