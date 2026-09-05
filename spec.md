# AIMarket Protocol v2 — Federation Specification

**Version:** 2.0.0-draft  
**License:** Apache-2.0 OR MIT  
**Last Updated:** 2026-08-28

---

## Abstract

The AIMarket Protocol defines a standard for AI capability marketplaces to federate. Any hub implementing this spec can discover capabilities from other hubs, index them in a unified catalog, route invocations with transparent commission, and aggregate reputation across the network. The protocol extends HTTP 402-based AI payments (v1) with cross-hub discovery and routing.

## Status of This Memo

This document is an open standard, dual-licensed **Apache-2.0 OR MIT** at the implementer's option. Apache-2.0 is offered because it carries an express patent grant, which a specification implemented by independent parties needs and MIT does not provide; taking either licence is sufficient. It is NOT an IETF RFC, but follows RFC style for clarity. Implementation experience is sought — see `GOVERNANCE.md` for how to report it and `IPR.md` for the full policy. Comments to the AIMarket Protocol repository.

---

## 1. Introduction

### 1.1. Motivation

AI-Factory Protocol v1 defined a single-marketplace model: one server exposes capabilities via `.well-known/ai-market.json`, handles HTTP 402 payments, and executes invocations. This works for a single operator but creates silos.

Protocol v2 adds **federation**: multiple hubs form a network where:
- Any hub can crawl any other hub's `.well-known`
- Capabilities are indexed across the network
- Invocations route transparently with opt-in commission
- Reputation aggregates across hubs
- Users see a unified catalog regardless of which hub they connect to

### 1.2. Design Principles

1. **Decentralized discovery** — No central registry. Hubs discover each other via `.well-known` + seed lists.
2. **Transparent routing** — Client pays provider; hub may add opt-in commission.
3. **Verifiable reputation** — Signed reputation events verified independently.
4. **Compatible with v1** — A v2 hub also implements v1 endpoints for backward compatibility.
5. **No custody** — The protocol never holds funds; payment channels are on-chain constructs.

### 1.3. Terminology

| Term | Definition |
|------|-----------|
| **Hub** | An instance implementing this protocol |
| **Provider** | A hub that hosts capabilities (can execute them) |
| **Consumer** | A hub or agent that invokes capabilities |
| **Seed list** | Initial set of `.well-known` URLs for a hub to crawl |
| **Federated catalog** | Union of all capabilities discovered across all crawled hubs |
| **Routing fee** | Opt-in percentage a hub takes for forwarding an invocation |
| **Reputation event** | Signed attestation about a provider or capability |

### 1.4. Ecosystem architecture (visual)

For a single map of how Factory, Hub, Mesh, clients, plugins, and on-chain settlement connect under this protocol, see **[ecosystem.md](ecosystem.md)** (Mermaid diagrams: topology, invoke paths, federation mesh, plugin pipeline, persistence).

---

## 2. Discovery

### 2.1. Root Well-Known (v2 extended)

```
GET /.well-known/ai-market.json
```

Response (v2 adds `hub_version`, `federation` and `peers`):

```json
{
  "name": "AI-Factory Hub",
  "protocol_versions": ["v1", "v2"],
  "hub_version": "2.0.0",
  "mcp_endpoint": "https://hub.example.com/ai-market/mcp",
  "manifest_url": "https://hub.example.com/ai-market/manifest",
  "products_count": 12,
  "capabilities_count": 47,
  "federated_capabilities_count": 234,
  "supported_chains": ["base", "ethereum", "solana"],
  "supported_tokens": ["USDT", "USDC"],
  "signer_public_key": "AbCdEf1234...",
  "federation": {
    "crawl_interval_s": 3600,
    "routing_fee_bps": 100,
    "min_trust_score": 0.3,
    "seed_list": [
      "https://hub2.example.com/.well-known/ai-market.json",
      "https://hub3.example.com/.well-known/ai-market.json"
    ]
  },
  "peers": [
    {
      "url": "https://hub2.example.com",
      "name": "Legal AI Hub",
      "capabilities_count": 34,
      "last_crawl": "2026-05-21T10:00:00Z",
      "trust_score": 0.85
    }
  ]
}
```

**New v2 fields:**

| Field | Type | Description |
|-------|------|-------------|
| `hub_version` | string | Semver of hub software |
| `federated_capabilities_count` | int | Total capabilities including federated |
| `federation` | object | Federation configuration |
| `federation.crawl_interval_s` | int | How often this hub crawls peers |
| `federation.routing_fee_bps` | int | Fee in basis points (100 = 1%) |
| `federation.min_trust_score` | float | Minimum trust to list a peer |
| `federation.seed_list` | string[] | Initial peer URLs |
| `peers` | object[] | Known peer hubs (discovered + seeded) |

### 2.2. Crawl Protocol

A hub crawler follows this algorithm:

```
1. Load seed_list from config
2. For each seed URL:
   a. GET {seed_url}  (/.well-known/ai-market.json)
   b. Verify response structure
   c. Extract manifest_url
   d. GET {manifest_url}  (full capability catalog)
   e. Verify Ed25519 manifest signature
   f. Validate each capability against JSON Schema
   g. Store in local index
   h. Discover new peer URLs from response.peers
   i. Add new peers to crawl queue (BFS, max depth 3)
3. Repeat on crawl_interval_s
```

**Crawl headers:**

| Header | Value | Purpose |
|--------|-------|---------|
| `User-Agent` | `AIMarketHub/2.0.0` | Identifies crawler |
| `X-AIMarket-Crawler` | `{hub_url}` | Source hub URL |
| `If-None-Match` | `{etag}` | Conditional GET (304 support) |

### 2.3. Federation Announce Endpoint

When a hub starts up or discovers a new peer, it MAY announce itself:

```
POST /ai-market/v2/federation/announce
Content-Type: application/json

{
  "hub_url": "https://newhub.example.com",
  "well_known_url": "https://newhub.example.com/.well-known/ai-market.json",
  "capabilities_count": 23,
  "signer_public_key": "...",
  "signature": "..."
}
```

Response: `200 OK` with `{"acknowledged": true, "peer_added": true}`

Whether this endpoint requires operator authorization is a deployment choice, and the two
choices produce materially different networks. §2.4 defines both.

### 2.4. Admission: who may knock, and who is trusted

These are two different questions, and a hub MUST keep them separate. Conflating them
produces either a network nobody can join or a network anyone can poison.

A hub MUST classify every peer it knows into exactly one of:

| State | Meaning |
|---|---|
| `pending` | Known to exist. Nothing it publishes has any effect on this hub. |
| `active` | Operator-admitted. Subject to the trust rules of §5. |

A hub MUST support **closed admission**, in which a peer becomes `pending` only through
operator action (a seed list entry, or an authorized announce). A hub MAY additionally
support **open admission**, in which an unauthenticated party can cause a `pending` record
to exist.

Under open admission all of the following MUST hold:

1. An unauthenticated announce results in `pending`, never `active`, and never `trusted`.
2. An announcement for an already-known peer MUST NOT modify any stored field of that
   peer — not its name, not its pinned key, not its trust state. A stranger's claim about
   a peer this hub already knows is evidence of nothing.
3. A hub MUST bound the number of `pending` peers it will accept, and MUST refuse further
   unauthenticated announcements when that bound is reached (`429`).
4. An announced URL MUST pass the URL safety requirements of §7.4 before the hub records it.
5. A `pending` peer MUST NOT appear in the `peers` array of this hub's published
   `.well-known` document. Republishing unverified hubs would let any party use a hub's
   reputation to inject a URL into the network's crawl graph.

Open admission changes **who may knock**. It MUST NOT change **who is trusted**.

### 2.5. Reciprocal discovery

A crawler MUST identify the hub it acts for:

```
GET /.well-known/ai-market.json
X-AIMarket-Crawler: https://crawler-hub.example
User-Agent: AIMarketHub/2.0.0
```

Without this header, discovery is one-directional: a hub can read, index and route to a
peer that never learns it exists. Federation built that way grows blind spots by design —
an operator can be part of somebody's network and have no way to find out.

A hub receiving the header:

- SHOULD record the self-declared crawler URL, so its operator can see who reads it.
- MUST treat the value as an unauthenticated claim. It is a hint about where to look, not
  an identity, and MUST NOT confer trust.
- MAY, under open admission (§2.4), record the crawler as a `pending` peer.
- MUST validate the value syntactically before storing it, and MUST apply §7.4 before
  treating it as a URL to fetch.
- SHOULD bound the size of this record set, for the same reason as §2.4 (3).

Implementations SHOULD keep the receiving side of this off the request path. The discovery
document is fetched on a timer by every peer in the network, and a hub that resolves DNS
while answering it has made its most-requested endpoint as slow as its slowest lookup.

### 2.6. Catalogue preview of a pending peer

An operator deciding whether to admit a stranger benefits from seeing what it offers. A
hub MAY fetch and display a `pending` peer's manifest for that purpose, subject to:

1. The manifest MUST be validated and its signature verified exactly as in §3.1 before
   anything from it is displayed.
2. Previewed capabilities MUST NOT be searchable, routable, invocable, or present in this
   hub's published manifest. Implementations SHOULD achieve this **structurally** — by
   storing preview records outside the catalogue the serving paths read — rather than by
   filtering, so that a query which forgets the filter cannot expose them.
3. Any surface presenting them MUST mark them as unapproved.

What a signature proves here is narrow and MUST NOT be overstated in any UI: the manifest
was signed by the key the peer advertises and was not altered in transit. It says nothing
about that key belonging to a party worth trusting.

---

## 3. Federated Catalog

### 3.1. Federated Manifest

```
GET /ai-market/v2/manifest
```

Returns the manifest with ALL capabilities from ALL crawled hubs:

```json
{
  "protocol_version": "v2",
  "generated_at": "2026-05-21T12:00:00Z",
  "total_capabilities": 234,
  "local_capabilities": 47,
  "federated_capabilities": 187,
  "hubs_indexed": 4,
  "tools": [...],
  "by_hub": {
    "https://hub.example.com": {"capabilities_count": 47, "trust_score": 0.95},
    "https://hub2.example.com": {"capabilities_count": 34, "trust_score": 0.85}
  }
}
```

### 3.2. Federated Search

```
GET /ai-market/v2/search
  ?intent=translate+to+5+languages
  &budget=3.00
  &max_latency_ms=15000
  &min_trust=0.5
  &hub=any
  &limit=20
```

Response includes `source_hub` for each result:

```json
{
  "query": "translate to 5 languages",
  "matches": [
    {
      "product_id": "prod-xxx",
      "capability_id": "translate.multi@v2",
      "source_hub": "https://hub2.example.com",
      "source_hub_name": "Legal AI Hub",
      "score": 0.92,
      "price_per_call_usd": 0.40,
      "routed_price_usd": 0.404,
      "routing_fee_bps": 100,
      "trust_score": 0.85
    }
  ],
  "total_hubs_searched": 4,
  "protocol_version": "v2"
}
```

---

## 4. Federated Invocation (Routing)

### 4.1. Transparent Proxy

```
POST /ai-market/v2/invoke
Content-Type: application/json
X-Payment-Channel: ch_abc123...
X-AIMarket-Route-Ok: true

{
  "product_id": "prod-xxx",
  "capability_id": "translate.multi@v2",
  "source_hub": "https://hub2.example.com",
  "input": {"text": "hello", "locales": ["ru", "en"]}
}
```

The routing hub:
1. Looks up `source_hub` in its index
2. Verifies the provider hub is reachable
3. Adds `X-AIMarket-Routing-Fee: {bps}` and `X-AIMarket-Routing-Hub: {url}` headers
4. Forwards the request to the provider hub
5. Provider hub returns 200 or 402
6. If 402, routing hub forwards `X-Payment-Required` to client
7. If 200, routing hub passes through result + receipt

**Routing flow:**

```
Client → Routing Hub → Provider Hub
   ← 402 (if unpaid)
   → X-Payment: {tx_hash}
   → Provider Hub executes
   ← 200 {result, receipt}
   ← 200 {result, receipt} (pass-through)
```

**Pay-on-Verified (optional `verify` block).** A buyer MAY opt into verified
settlement by adding a `verify` block to the invoke body. The block is
additive — hubs that predate it ignore unknown keys, so new clients stay
compatible with old hubs and the wire format remains `v2`:

```json
{
  "product_id": "prod-xxx",
  "capability_id": "translate.multi@v2",
  "input": {"text": "hello", "locales": ["ru", "en"]},
  "verify": {
    "requested": true,
    "intent": "translate 'hello' into Russian and English",
    "mode": "auto",
    "wait": false,
    "wait_timeout_s": 300
  }
}
```

- `requested` (boolean, required) — opt into verified settlement.
- `intent` (string) — the buyer task description the verifier judges the
  delivered output against.
- `mode` (string, default `"auto"`) — verifier route: `"auto"` (price-tiered)
  | `"fast"` | `"thinking"` | `"council"` | `"agent"`.
- `wait` (boolean, default `false`) — hold the HTTP response until the verdict
  (bounded); default is asynchronous resolution.
- `wait_timeout_s` (integer, default 300) — only with `wait: true`; if the
  verdict is not ready in time the hub answers with a `status: "pending"`
  envelope, NOT an error.

The verify score threshold that governs money movement is operator-set; it is
not buyer-settable. The buyer-named `mode` is likewise clamped to the
price-justified route ceiling (a capability priced below the operator's council
floor is verified on the `fast` route regardless of the requested mode).

Verified settlement is LOCAL-only: the escrow hold and the verdict both live on
the hub that received the invoke. On a federated invoke (`source_hub` = a peer
URL) the block is not honoured — the hub answers with a skipped envelope
(`status: "skipped"`, `reason: "federated_unsupported"`) and charges the
routing fee normally, so the buyer gets an explicit signal instead of a silent
unescrowed charge.

When requested, the provider output is returned immediately but the channel
debit is held in escrow until the verifier delivers a verdict. Pass → the hold
is captured (debit recorded). Fail → the hold is released (refund) and the
buyer keeps a signed rejection receipt. The verdict state travels in a
`verification` envelope — present in the invoke response body, as an UNSIGNED
`verification` field of the receipt (the envelope carries its own Ed25519
signature once resolved), and at the lookup endpoint:

```json
"verification": {
  "requested": true,
  "status": "pending",
  "performed": false,
  "verified": null,
  "verify_score": null,
  "threshold": 0.7,
  "trace_id": null,
  "verifier": "metis.verify@v1",
  "mode": "fast",
  "settled": false,
  "reason": null,
  "timestamp": "2026-07-14T12:00:00Z",
  "signature": {"algorithm": "ed25519", "value": "..."}
}
```

- `status` — `"pending"` | `"settled"` | `"refunded"` | `"skipped"`.
- `performed` — true once a verifier envelope was obtained.
- `verified` / `verify_score` — verdict and score; `null` while
  pending/skipped.
- `settled` — whether the channel debit (capture) was recorded.
- `reason` — machine-readable skip/policy reason (e.g. `"below_price_floor"`,
  `"verify_failed"`), or `null`.

A pending verdict is polled by receipt nonce (`rcpt_…`):

```
GET /ai-market/v2/verification/{nonce}
```

`200 {"success": true, "verification": {…}, "rejection_receipt": {…}?,
"receipt": {…}?, "protocol_version": "v2"}`; unknown nonce → `404
{"success": false, "error": "verification_not_found"}`.

Note the deliberate asymmetry with safety blocks: a safety 403 withholds the
output, while a failed verification keeps the output with the buyer (it was
already delivered) and returns the money — the response stays HTTP 200 with
`verification.status: "refunded"` plus the rejection receipt. Verification is
quality escrow, not censorship.

### 4.2. Routing Commission

The routing hub declares its fee in the `.well-known` response (`federation.routing_fee_bps`). The client sees `routed_price_usd = price * (1 + routing_fee_bps / 10000)` in search results.

Commission settlement happens out-of-band between hubs (on-chain, monthly settlement). The protocol does not prescribe the settlement mechanism — only declares the fee schedule.

### 4.3. IoT / Physical-Oracle Profile

Devices are capabilities: a sensor read or an actuation maps onto the existing
manifest/invoke/receipt surface without new wire primitives. This profile
pins the conventions a device gateway MUST/SHOULD follow so physical data is
sellable, attributable, and verifiable. Reference implementation: the GAIA
gateway (`gaia/`).

**Device identity chain.** Every reading MUST carry a device attestation —
an Ed25519 signature by a per-device key (secure element / TEE on real
hardware; the protocol's `tee_attestation` slot is the natural carrier) over
a canonical binding identity, ordering, freshness, and content:

```
device:{device_id}|model:{model}|seq:{n}|ts:{iso}|values_sha256:{hex}
```

The gateway that sells the reading countersigns at two further links: the
request-bound provider response signature (`X-Provider-Signature`, §7) and
the signed invoke receipt. Buyer-side verification therefore chains
device → gateway → hub. Device public keys are pinned in a fleet registry
capability (e.g. `gaia.fleet.status@v1`) or the manifest; an attestation that
verifies only against a self-carried key proves consistency, not identity.

**Verifiable settlement.** Physical readings SHOULD be sold under verified
settlement (§4.1). The verifier slot is an interface, not an engine: any
service answering the `/v1/verify` envelope (`answer`, `status`, `verified`,
`verify_score`, `trace_id`, …) can gate escrow — an LLM auditor (Metis), a
statistical plausibility service (GAIA: physics bounds, robust z-scores,
rate-of-change, co-located-sibling agreement, dead-sensor detection, register
monotonicity), or an N-of-M composition. The verifier SHOULD NOT be operated
by the party selling the data; a seller-hosted verifier demonstrates the
interface, not a trust topology.

**Micro-billing.** Channel ledgers bill in whole cents (ceiling); sub-cent
readings MUST therefore be sold either as bundles (one invoke returns N
readings — e.g. `gaia.window@v1`) or through a prepaid-quota capability that
returns a session token. Bundles double as the way to clear a hub's verified-
settlement price floor. Per-event streaming (server-push with per-message
micro-debit against an open channel) is deliberately NOT specified in v2:
the invoke surface is request/response, and a conforming gateway emulates
subscription by bundle polling. A future `subscribe` primitive would add
an SSE/WebSocket form whose events debit a channel-backed quota — additive,
and out of scope here.

**W3C WoT interop.** A gateway SHOULD publish a Thing Description (TD 1.1)
per device whose property `forms` point at the AIMarket invoke endpoint,
carrying `aimarket:capability_id` and `aimarket:price_per_call_usd` extension
terms; conversely a TD imports to manifest `tools[]` mechanically (each
property → `<thing>.<property>.read@v1`, each action → `<thing>.<action>@v1`).
One JSON-LD document, two consumer worlds.

**x402 interop note.** This protocol's payment surface — HTTP `402` with
USDC settlement on Base — is wire-adjacent to x402. A hub MAY additionally
answer unpaid invokes with x402-formatted payment-required metadata; the
channel model (§6) then plays the role of x402's facilitated settlement with
escrow semantics on top. No change to either wire format is required for a
gateway to serve both kinds of payer.

---

## 5. Reputation

### 5.1. Trust Score Calculation

Each hub computes a trust score for every peer:

```
trust_score = w1 * age_factor + w2 * bond_factor + w3 * success_rate + w4 * volume_factor

where:
  age_factor        = min(hub_age_days / 365, 1.0)
  bond_factor       = min(log10(bond_usd) / 4, 1.0)  # 0 at $1, 1 at $10k
  success_rate      = successful_invocations / total_invocations (30d window)
  volume_factor     = min(log10(volume_usd_30d) / 5, 1.0)

Default weights: w1=0.2, w2=0.3, w3=0.35, w4=0.15
```

### 5.2. Reputation Events

```
POST /ai-market/v2/reputation/events
Content-Type: application/json

{
  "events": [
    {
      "type": "invocation_success",
      "provider_hub": "https://hub2.example.com",
      "capability_id": "translate.multi@v2",
      "timestamp": "2026-05-21T12:00:00Z",
      "price_usd": 0.40,
      "latency_ms": 8100,
      "consumer_hub": "https://hub.example.com",
      "signature": "..."
    }
  ]
}
```

Reputation events are Ed25519-signed by the reporting hub. Multiple reports from different consumers create a Sybil-resistant reputation graph.

### 5.3. Bond Requirement

To appear in the default seed list of the reference implementation, a hub MUST post a bond in USDT/USDC on a supported chain. The bond proves economic stake and can be slashed for malicious behavior (future governance).

Minimum bond: $100 USDT (testnet), $1,000 USDT (mainnet).

---

## 6. Payment Channels

Payment channels let a depositor pre-fund USDT/USDC on a supported chain, run
N off-chain capability invocations with off-chain receipts, and settle once
on-chain. The reference EVM contract is `AIMarketEscrow.sol`; the Solana
counterpart is `aimarket_escrow`.

### 6.1. Channel lifecycle

| Step | Caller | Endpoint / call | Effect |
|------|--------|------------------|--------|
| open | depositor | `POST /ai-market/v2/channel/open` → `openChannel(channelId, token, depositAmount)` | Transfers tokens to escrow, sets 24h expiry. |
| debit | hub (signed by depositor) | `debitChannel(channelId, amount, receiptId, deadline, sig)` | Increments `usedAmount`, marks `receiptId` used, binds hub to channel on first call. |
| settle | depositor OR bound hub | `settleChannel(channelId)` | Pays `usedAmount` to bound hub, refunds remainder to depositor. |
| refund | depositor only (and only before any debit) | `refundChannel(channelId, reason)` | Full refund (e.g. safety gate blocked). |
| expire | anyone after expiry | `expireChannel(channelId)` | Same economics as settle — permissionless cleanup. |

### 6.2. DebitAuthorization (EIP-712)

The hub must present an EIP-712 typed-data signature from the depositor for
every debit. The signature is verified on-chain by `ECDSA.recover` against
`depositor`. Implementations MUST sign the canonical typehash literal below —
any divergence (extra space, reordered fields, wrong field name) produces a
different keccak256 hash, recovers the wrong address, and the contract
reverts with `InvalidSignature()`.

**Canonical typehash literal:**

```solidity
bytes32 private constant DEBIT_TYPEHASH = keccak256(
  "DebitAuthorization(bytes32 channelId,address hub,address token,uint256 amount,bytes32 receiptId,uint256 nonce,uint256 deadline)"
);
```

**Domain separator:**

```solidity
keccak256(abi.encode(
  keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
  keccak256(bytes("AIMarketEscrow")),
  keccak256(bytes("1")),
  chainId,
  address(escrow)
));
```

**Field semantics:**

| Field | Type | Meaning |
|-------|------|---------|
| `channelId` | `bytes32` | Channel identifier returned by `openChannel`. |
| `hub` | `address` | Hub allowed to consume this signature; bound to the channel on first debit (replay protection across hubs). |
| `token` | `address` | ERC-20 token escrowed in the channel (USDT/USDC). |
| `amount` | `uint256` | Token amount in **base units** (USDT/USDC have 6 decimals). |
| `receiptId` | `bytes32` | Off-chain receipt identifier; the contract stores it in `usedReceipts[receiptId]` to prevent double-spend. |
| `nonce` | `uint256` | Current `channels[channelId].nonce`; the contract increments after a successful debit. |
| `deadline` | `uint256` | Unix timestamp after which the contract rejects the authorization. |

**EIP-712 chain-fork recomputation.** The contract caches the domain
separator at deployment time and recomputes it if `block.chainid` changes
(e.g. after a fork), so signatures cannot be replayed cross-fork. Implementors
MUST use the current `chainid` when signing.

**Solana parity.** The Solana program enforces the same payload shape via
Ed25519 sysvar verification: `channel_id || hub || token_mint || amount ||
receipt_id || nonce || deadline` is hashed and signed by the depositor's key.
The on-chain CPI signer always uses `[b"vault", channel_id, vault_bump]` —
NEVER `b"channel"` — so the accounting PDA cannot be confused with the token
authority.

**Reference SDKs.** Dart (`aimarket-sdks/dart/lib/src/signer.dart`),
TypeScript (`aimarket-sdks/typescript/src/signer.ts`), and Rust
(`aimarket-sdks/rust/src/signer.rs`) all expose
`signDebitAuthorization(...)`. SDK stubs digest with SHA-256; production
deployments MUST swap in keccak256 + secp256k1 ECDSA.

### 6.3. Cross-Hub Channels

Payment channels opened on one hub are NOT automatically valid on another hub. For cross-hub invocations:

1. Client opens a channel on the routing hub
2. Routing hub opens its own channel on the provider hub (pre-funded)
3. Client pays routing hub; routing hub pays provider hub
4. Settlement happens atomically on each respective hub

This avoids cross-hub trust requirements for payment.

### 6.4. Federated Receipts

A federated invocation produces two receipts:
1. **Client receipt** — from routing hub, includes routing fee
2. **Provider receipt** — from provider hub, for the actual execution

Both are Ed25519-signed and independently verifiable.

---

## 7. Security Model

### 7.1. Threat Model

Provider responses SHOULD bind the signature to the exact request. The canonical UTF-8 JSON object
contains `capability_id`, `product_id`, `input_sha256` (SHA-256 of canonical input JSON), and
`result`; both JSON serializations use sorted keys, no insignificant whitespace, and unescaped
Unicode. This prevents replaying a valid signed result against a different input. Hubs MAY accept
the legacy result-only signature during migration but SHOULD warn and phase it out.

| Threat | Mitigation |
|--------|------------|
| Malicious manifest from fake hub | Ed25519 signature; trust score threshold |
| Man-in-the-middle on routed invoke | HTTPS + manifest signature verification |
| Sybil reputation | Bond requirement + stake age weighting |
| Spam capabilities | Schema validation + trust score gating |
| Free-riding hub (no capabilities, only routes) | Routing fee makes this a viable business model (not a threat) |
| Routing hub steals payment | Client pays provider directly via 402; routing hub only facilitates discovery |

### 7.2. Liability

The protocol is a directory and routing standard, NOT a party to transactions. The receipt is signed by the provider hub, not the routing hub. EULA for hub operators MUST state: "This hub is a directory and routing service, not a party to capability invocations."

---

### 7.3. Canonical signing — what bytes are actually signed

> **This section is normative and was previously absent.** Until it was written, the byte
> layout of every signature in this protocol existed only in the reference implementation's
> source and in a generator script's docstrings. Three implementations were written against
> it and two of them got it wrong in ways that mattered — see the note at the end. A
> signature scheme that is not written down is not a standard; it is a re-implementation
> hazard.

#### 7.3.1. Common rules

All signatures in this protocol are **Ed25519** (RFC 8032) over the **UTF-8 encoding** of a
canonical string, with the result **base64-encoded** (standard alphabet, with padding).

A canonical string is a concatenation of `name:value` pairs joined by the ASCII pipe
character `|`. Implementations MUST emit the fields in the order given below, MUST NOT
insert whitespace, and MUST NOT reorder, add or omit pairs.

Where a value is a digest of a JSON subdocument, that digest is
`sha256(json.dumps(value, sort_keys=true, ensure_ascii=false))`, lowercase hexadecimal, with
Python's **default** separators — `", "` between members and `": "` after a key. This is not
the compact form: the manifest digests in §7.3.2 use the default separators, while the
receipt v2 field digest in §7.3.4 uses compact `(",", ":")`. The two differ, deliberately
and inconveniently, and an implementation that applies one everywhere will produce digests
that verify in one place and fail in the other.
`ensure_ascii=false` means non-ASCII characters are emitted as themselves, not as `\uXXXX`
escapes — an implementation that escapes them will produce a different digest and every
signature will fail to verify.

The signature object carried alongside the document is:

```json
{ "algorithm": "ed25519", "public_key": "<base64>", "value": "<base64>" }
```

`public_key` MAY be omitted where the verifier already holds a pinned key for the signer
(§2.2); `algorithm` MUST be `"ed25519"`.

#### 7.3.2. Manifest canonical (five fields)

```
capabilities_count:{capabilities_count}|generated_at:{generated_at}|protocol_version:{protocol_version}|tools_hash:{sha256(tools)}|by_hub_hash:{sha256(by_hub)}
```

- `tools_hash` digests the `tools` array; `by_hub_hash` digests the `by_hub` object.
- An **absent** `by_hub` MUST hash as the empty object `{}`, so a hub serving no peers
  agrees with one that serves an empty map without inventing a field.
- Defaults when a key is absent: `capabilities_count` → `0`, `generated_at` → `""`,
  `protocol_version` → `"v1"`.

Both digests are load-bearing and MUST NOT be omitted. Without `tools_hash` a relay can
rewrite every price in the catalogue under a still-valid signature; without `by_hub_hash` it
can rewrite per-peer `trust_score` and routing metadata the same way.

#### 7.3.3. Receipt canonical v1 (seven fields)

```
nonce:{nonce}|product_id:{product_id}|capability_id:{capability_id}|price_usd:{price_usd}|timestamp:{timestamp}|success:{0|1}|latency_ms:{latency_ms}
```

- `success` is serialized as the integer `1` or `0`, never as `true`/`false`.
- `latency_ms` defaults to `0` when absent.
- `nonce` and `timestamp` are what make a receipt non-replayable; both MUST be present.

`success` and `latency_ms` MUST be inside the signature. An implementation that signs only
the first five fields will accept a receipt whose `success` was flipped from false to true.

#### 7.3.4. Receipt canonical v2 (rejection-bearing receipts)

A receipt that carries a rejection MUST use v2. v1 signs essentially nothing about a
rejection: on a refusal `price_usd`, `success` and `latency_ms` are all constant, so the
reasoning the buyer's refund is argued from sits outside the signature.

```
{v1 canonical}|v:2|fields:{fields_digest}
```

where `fields_digest` is a SHA-256, lowercase hex, over exactly these keys —

```
type, channel_id, category, plugin, reason, verify_score, delivery_reasons, trace_id, refunded
```

— serialized as a JSON object with `sort_keys=true`, `ensure_ascii=false` and **compact
separators** `(",", ":")`. See §7.3.4.1 on ordering. **A key that is absent MUST be bound as JSON `null`, not omitted**,
so that deleting a field changes the digest rather than passing unnoticed.

Verifiers MUST determine the signed version from the receipt's own signature block, and the
required version from the receipt's own content — not from a request parameter.

Where the two disagree — a receipt carrying v2 fields but signed at v1 — a verifier MAY
still accept the signature for the fields it covers, because a peer that predates v2 emits
exactly this and rejecting it outright would partition the federation. What a verifier MUST
NOT do is treat the uncovered fields as authenticated: on such a receipt, `reason`,
`verify_score`, `refunded`, `channel_id`, `trace_id` and `delivery_reasons` are present and
**unsigned**, and any decision resting on them is resting on unauthenticated data.

An implementation MUST therefore expose which v2 fields a given signature leaves uncovered,
rather than returning a bare accept/reject. The reference implementation does this as
`unsigned_receipt_fields()`, and a dispute reads it before arguing from a rejection's stated
reason.

An implementation that is not required to interoperate with pre-v2 peers SHOULD refuse such
receipts outright.

#### 7.3.4.1. Field order in the digest

The nine keys above are listed in the order they appear in the reference implementation's
tuple, which is documentary only. The digest is computed over a JSON object serialized with
`sort_keys=true`, so the **sorted** order is what is actually hashed:

```
category, channel_id, delivery_reasons, plugin, reason, refunded, trace_id, type, verify_score
```

An implementation that preserves the listed order instead of sorting will produce a
different digest and every v2 signature will fail.

#### 7.3.5. Federation announce canonical (three fields)

```
hub_url:{hub_url}|well_known_url:{well_known_url}|capabilities_count:{capabilities_count}
```

`capabilities_count` defaults to `0`. Note this canonical binds no timestamp and no nonce: an
announcement is therefore replayable by design, which is acceptable only because an
announcement confers nothing (§2.4). Implementations MUST NOT extend this canonical's
authority to any admission decision.

#### 7.3.6. Test vectors are normative

`test-vectors/` in the protocol repository carries a signed example of each object above,
generated by `test-vectors/generate.py` from a fixed key. An implementation that disagrees
with a vector is non-conformant, whatever its own tests say.

> **Why this section exists.** Every formula above was previously discoverable only by
> reading the reference implementation. In practice: `oracle_core` omitted `by_hub_hash`, and
> as a result no oracle could federate at all until it was found; the published vectors
> signed a three-field manifest and a five-field receipt until 2026-07-29, teaching an
> insecure shape to anyone implementing from them. Both were caught by comparing
> implementations against each other, which is exactly the work a written specification is
> supposed to make unnecessary.

---

### 7.4. URL safety

Every mechanism in this specification causes a hub to fetch a URL supplied by another party:
a seed, a peer's `manifest_url`, a `peers` entry, an announcement (§2.4), and the crawler
identification of §2.5. Each is an instruction from a stranger about where to send a request
from inside the hub's own network.

Before fetching any URL not configured by its operator, a hub MUST:

1. **Resolve the host and inspect the address.** Refuse loopback, private (RFC 1918),
   link-local, carrier-grade NAT, multicast and unspecified ranges, in both IPv4 and IPv6,
   including IPv4-mapped and IPv4-compatible IPv6 forms. A name that resolves into any of
   these is refused however it is spelled.
2. **Close the check-to-use window.** Re-check at connection time, or pin the connection to
   the address that was checked. A DNS answer that passes the check and a DNS answer that is
   used are otherwise allowed to be different answers, which is the whole of DNS rebinding.
3. **Refuse to follow redirects automatically.** Each hop is a new URL and needs its own
   check. A hub MAY re-fetch a redirect target explicitly after re-running this section.
4. **Bound the response.** Enforce a maximum body size and a total time limit, and stop
   reading at the limit rather than after it.
5. **Reject control characters** in the URL before any of the above.

A hub MUST apply this section to a URL received in an announcement or in an
`X-AIMarket-Crawler` field before storing it as a peer, not merely before fetching it —
storage is what makes it a future fetch target.

These requirements are not defence in depth; each closes a distinct hole, and an
implementation that omits any one of them has an SSRF vector reachable by an
unauthenticated HTTP request.

---

## 8. API Reference

| Method | Path | Description | Version |
|--------|------|-------------|---------|
| GET | `/.well-known/ai-market.json` | Root discovery manifest | v1+v2 |
| GET | `/ai-market/v2/manifest` | Federated catalog | v2 |
| GET | `/ai-market/v2/search` | Federated NL search | v2 |
| POST | `/ai-market/v2/invoke` | Federated invocation | v2 |
| GET | `/ai-market/v2/verification/{nonce}` | Pay-on-Verified verdict lookup by receipt nonce | v2 |
| POST | `/ai-market/v2/federation/announce` | Peer announcement | v2 |
| GET | `/ai-market/v2/federation/peers` | List known peers | v2 |
| POST | `/ai-market/v2/federation/crawl` | Trigger manual crawl | v2 |
| GET | `/ai-market/v2/reputation/{hub_url}` | Trust score for a hub | v2 |
| POST | `/ai-market/v2/reputation/events` | Submit reputation events | v2 |
| GET | `/ai-market/v2/stats/live` | Live invocation stream | v2 |

### 8.1. HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request |
| 402 | Payment required |
| 404 | Not found |
| 502 | Provider hub unreachable |

---

## 9. Reference Implementation

The reference implementation lives at [aimarket-hub](https://github.com/alexar76/aimarket-hub/tree/main/). It is Apache-2.0 licensed and includes:

- **crawler** — Daemon that reads `.well-known` from seed list + discovered URLs
- **indexer** — SQLite/Postgres storage for manifests, schemas, prices, reputation
- **search API** — Federated search with intent matching and trust ranking
- **routing proxy** — Transparent invoke forwarding with opt-in fee
- **schema validator** — Rejects invalid manifests
- **trust scorer** — Aggregates reputation events
- **CLI** — `aimarket search`, `aimarket invoke`, `aimarket crawl`
- **Docker image** — Single-command deployment

---

## 10. References

- [Ecosystem architecture map](ecosystem.md) — Mermaid topology (Factory · Hub · Mesh · clients · chain)
- [Protocol v1](https://github.com/alexar76/aicom/blob/main/docs/ai-market-protocol-v1.md) — Single-marketplace baseline
- [JSON Schema Core](https://json-schema.org/draft/2020-12/json-schema-core.html)
- [Ed25519](https://datatracker.ietf.org/doc/html/rfc8032)
- [HTTP 402](https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.2)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Coinbase x402](https://docs.cdp.coinbase.com/x402/)

---

## Appendix A. Migration from v1 to v2

1. Add `hub_version: "2.0.0"` to `.well-known/ai-market.json`
2. Add `federation` and `peers` blocks to `.well-known`
3. Implement crawl loop (can start as no-op)
4. Register in at least one other hub's seed list
5. Optional: deploy routing proxy for incoming federated invocations

## Appendix B. Test Vectors

See [test-vectors/](test-vectors/) for reference Ed25519 signatures and manifest examples for implementor verification.
