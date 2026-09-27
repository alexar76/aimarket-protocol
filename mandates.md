# AIMarket Mandates and Subcontracting

Extension to [AIMarket Protocol v2](spec.md). Status: implemented in `aimarket-hub`
(reference), version 1 of both documents. The key words MUST, MUST NOT, SHOULD and MAY are
used as in RFC 2119.

This extension defines two things that the core protocol leaves to the caller:

- **A mandate** (`AMD/1`): an owner's signed statement that *this* agent key may spend *this
  much*, on *these* capabilities, at *these* hubs, until *then*. The hub verifies it and
  enforces the limits itself. The agent never holds the owner's API key.
- **Subcontracting** (`SUB/1`): a provider that, while serving a call, buys from another
  provider. The hub links the two calls into one job tree. The buyer MAY give the job a
  pass-through allowance for such purchases, and the hub enforces that allowance as well.

Both are defined on the hub's existing rails. Neither moves money that the core protocol
would not have moved; they constrain and attribute it.

## 1. Why these are one extension

A mandate answers "who authorised this spend, and up to how much". Subcontracting asks the
same question one hop further down: agent A pays provider B, and B pays C *on A's behalf*.
Without a mandate, the only answer a hub can give is "whoever holds the API key". Without job
linkage, the answer ends at B. Together they give every paid call in a chain an authoriser, a
limit and a place in a tree.

## 2. Terminology

- **Owner**: the principal whose money is spent. Identified by an Ed25519 `did:key`.
- **Agent**: the key a mandate is issued to (`credentialSubject.id`).
- **Chain**: a leaf mandate and its ancestors up to the root, linked by `parent` digests. The
  root's issuer is the owner.
- **Funding account**: the hub credit account (Protocol §6, credits rail) linked to the root
  issuer. It is what a mandated call is paid from.
- **Job**: the tree of invocations started by one root invoke that asked for subcontracting,
  or that a provider extended by calling back with the job token.
- **Allowance**: the part of a job's budget that providers may spend on subcontractors,
  paid from the root buyer's funding.
- **µUSD**: integer micro-dollars (1 µUSD = 10⁻⁶ USD). All money in signed documents is an
  integer in µUSD. The hub's credits ledger counts millicents (10 µUSD); conversions are exact
  in that direction.

## 3. The mandate document (AMD/1)

### 3.1 Shape

A mandate is a W3C Verifiable Credential 2.0 secured with a `DataIntegrityProof` using the
`eddsa-jcs-2022` cryptosuite — the same suite, canonicalization (RFC 8785) and `did:key`
rules as AWR/2 (`awr/SPEC.md` §4–§6). An implementation that verifies AWR/2 proofs verifies
mandate proofs with no new cryptography.

```json
{
  "@context": ["https://www.w3.org/ns/credentials/v2"],
  "type": ["VerifiableCredential", "AIMarketMandate"],
  "id": "urn:uuid:5f0c1c1e-3a4f-4c1b-9d58-2b7f0b1f9a10",
  "issuer": "did:key:z6Mk…owner",
  "validFrom": "2026-09-26T00:00:00Z",
  "validUntil": "2026-10-26T00:00:00Z",
  "credentialSubject": {
    "id": "did:key:z6Mk…agent",
    "aimarketMandate": {
      "version": 1,
      "audience": ["https://modelmarket.dev"],
      "scope": ["gaia.*", "atlas.nearest.read@v1"],
      "limits": {
        "perCall": 20000,
        "perDay": 1000000,
        "total": 10000000,
        "perProductPerDay": 400000
      },
      "subcontract": { "perCallAllowance": 5000, "maxDepth": 2 },
      "parent": "sha256-…"
    }
  },
  "proof": { "type": "DataIntegrityProof", "cryptosuite": "eddsa-jcs-2022", "…": "…" }
}
```

### 3.2 Field rules

A verifier MUST reject a mandate that breaks any of these rules. A hub answers
`403 mandate_invalid`, or `400 mandate_malformed` when the body is not a JSON object or has
no canonical form, and `413 mandate_malformed` when it is larger than the hub accepts.

| Field | Rule |
|---|---|
| `@context` | Exactly `["https://www.w3.org/ns/credentials/v2"]`. |
| `type` | Exactly `["VerifiableCredential", "AIMarketMandate"]`. |
| `id` | A `urn:uuid:` URI. It names ONE mandate per issuer: a hub MUST refuse to register a second document from the same issuer with the same `id` (§3.3). |
| `issuer` | An Ed25519 `did:key`. |
| `validFrom`, `validUntil` | RFC 3339 UTC with a `Z` suffix and whole seconds. `validFrom` < `validUntil`, and the span is at most 366 days. |
| `credentialSubject.id` | An Ed25519 `did:key`, different from `issuer`. |
| `aimarketMandate.version` | `1`. |
| `audience` | 1–8 hub base URLs (`scheme://host[:port][/path]`, no trailing slash) — the public URL the hub publishes, path included for a hub mounted under one. A hub MUST refuse a mandate that does not name its own configured public URL. |
| `scope` | 1–64 capability patterns: an exact capability id, a prefix ending in `.*`, or `*` alone. |
| `limits.perCall`, `limits.perDay` | Required, integers ≥ 1. |
| `limits.total` | Optional integer ≥ 1. Absent: the chain's other limits still apply. |
| `limits.perProductPerDay` | Optional integer ≥ 1, applied per `product_id`. |
| `subcontract` | Optional. Absent means calls made under this mandate may not open a subcontracting allowance (§6.2). `perCallAllowance` ≥ 1 and `maxDepth` 1–3, both integers. |
| `parent` | Optional SRI digest (`sha256-<base64>`) of the parent mandate (§3.4). |
| numbers | Every number in the document MUST be an integer, as in AWR/2, within the I-JSON range ±(2^53 − 1). |
| `proof` | Exactly the keys `@context`, `type`, `cryptosuite`, `created`, `verificationMethod`, `proofPurpose` and `proofValue`, with `proof.@context` equal to the document's `@context` (§3.3). |
| size | The canonical form MUST NOT exceed 16 KiB. |

A "day" is a **UTC calendar day**. A rolling 24-hour window cannot be enforced with one
atomic statement per counter, and the counters are what make the limits race-free (§5.3). The
consequence is stated rather than hidden: an agent can spend up to `perDay` either side of
midnight. `total` bounds everything absolutely.

### 3.3 Identity: the digest

A mandate is named by `sha256-<base64>` over its RFC 8785 canonical form **including the
proof** — the AWR/2 `digestSRI` of the secured document. The digest is what the invoke
header carries, what a child's `parent` commits to, and what revocation names.

Because the name covers bytes the signature does not, every such byte has to be pinned, or
it is a free parameter of the name. `eddsa-jcs-2022` hashes the proof configuration with the
DOCUMENT's `@context` in place of whatever the proof carries, so `proof.@context` is
unsigned; left free, the agent a mandate constrains could register copy after copy of it,
each a new digest with fresh counters and none touched by revoking the original. Hence the
exact key set and the `@context` equality in §3.2, and — as a second wall should any
encoding freedom remain — one registered document per `(issuer, id)`.

### 3.4 Delegation chains

A mandate with `parent` is a re-delegation: its issuer passes part of its own authority to a
third key. For each link, child → parent, a verifier MUST check that:

1. `child.issuer == parent.credentialSubject.id`;
2. the child's validity window lies inside the parent's;
3. every child `audience` entry is in the parent's `audience`;
4. every child `scope` pattern is covered by some parent pattern — `*` covers everything,
   `x.*` covers anything starting with `x.`, and an exact id covers only itself;
5. every child limit is ≤ the parent's same limit, and a limit the parent sets is also set
   by the child;
6. if the child has `subcontract`, the parent has it too, with a
   `perCallAllowance` and `maxDepth` at least as large.

A chain is at most **4** mandates long (root plus three re-delegations).

Spend is recorded against **every** mandate in the chain, so the sum of what all of a
parent's children spend can never exceed the parent's own limits.

### 3.5 Registration

`POST /ai-market/v2/mandates` with the mandate JSON as the body. The hub verifies the proof,
the field rules and — when `parent` is set — the whole chain against mandates it already
holds. It returns `{"digest", "status": "active", "root", "depth"}`.

A hub MUST refuse to register a chain whose root issuer is not linked to a funding account
(§4): a mandate nobody can pay from is storage the hub would give away. Registration is
idempotent by digest.

`GET /ai-market/v2/mandates/{digest}` returns its validity, revocation and chain: `status`
is that of the chain as a whole — `active`, `revoked` (it or an ancestor), `expired`,
`pending` (not yet valid) or `invalid` — with `status_reason` when it is not active, and
`chain` lists the digests root → leaf. Usage figures (spent today, spent in total,
remaining) are returned only to the root's funding account (`X-API-Key`) or with a valid
request proof (§5.1, method `GET`, empty body) from any key in the chain — any issuer or
subject, so an owner can watch an agent it re-delegated to.

## 4. Linking an owner to a funding account

`POST /ai-market/v2/mandates/owners`, authenticated with the account's `X-API-Key`:

```json
{
  "did": "did:key:z6Mk…owner",
  "require_mandate": true,
  "proof": { "t": 1790000000, "n": "b64url-nonce", "s": "b64url-signature" }
}
```

`s` is the owner key's Ed25519 signature over the UTF-8 bytes of

```
aimarket-owner-link/1
<hub base URL>
<account_id>
<did>
<t>
<n>
```

The API key proves the account; the signature proves the key. One DID links to at most one
account on a hub. An account MAY link several DIDs (key rotation).

That is enough for the FIRST owner only. Once an account has an owner, every later change —
linking another DID, unlinking one, changing `require_mandate` — MUST also carry
`"authorization": {"by", "t", "n", "s"}`, where `by` is an already-linked owner and `s` signs

```
aimarket-owner-change/1
<hub base URL>
<account_id>
<link | unlink | policy>
<the DID being changed>
<require_mandate: 0 | 1 — the value after the change; 0 for an unlink>
<t>
<n>
```

Without this, the API key alone would be enough to link an attacker's DID (and so issue an
unlimited mandate) or to unlink the row that carries `require_mandate`. The API key is
exactly what leaks. A hub MAY let its operator's admin credential stand in for the
authorization, as the recovery path for an owner who has lost every key.

With `require_mandate: true`, the account's API key alone no longer pays for invokes — the
hub answers `402 mandate_required` — so a leaked key cannot bypass the limits.
`POST /ai-market/v2/mandates/owners/unlink` with `{"did", "authorization"}` (and the API key)
unlinks; an owner may authorize its own removal.

## 5. Presenting a mandate at invoke

### 5.1 Headers

```
X-AIMarket-Mandate:       sha256-<digest of the leaf mandate>
X-AIMarket-Mandate-Proof: t=<unix seconds>;n=<nonce>;s=<b64url signature>
```

`s` is the leaf agent key's Ed25519 signature over the UTF-8 bytes of

```
aimarket-mandate-request/1
<hub base URL>
<HTTP method> <request path, relative to the base URL>
<leaf digest>
<t>
<n>
<lowercase hex SHA-256 of the raw request body>
```

The request path is the part after the base URL: for a hub published at
`https://example.net/hub`, a POST to `https://example.net/hub/ai-market/v2/invoke` signs
`POST /ai-market/v2/invoke`. It is percent-decoded and carries no query string.

The hub MUST reject the proof when `t` is more than 300 seconds from its clock, and MUST
accept each `(agent, n)` pair at most once. `n` is 16–64 base64url characters. Binding the
hub origin stops a proof being replayed at another hub. Binding the body stops it being
attached to a different request.

### 5.2 Admission

On a mandated invoke the hub:

1. resolves the chain by digest and verifies every link (§3.4), expiry and revocation;
2. verifies the request proof against the leaf subject key;
3. requires `capability_id` to match the leaf scope, and the hub's origin to be in the
   leaf audience;
4. uses the root issuer's linked account as the funding account — unless the request also
   carries `X-API-Key`, in which case that key must resolve to the **same** account;
5. refuses any other rail on the same request (`X-Payment-Channel`, x402): a mandate is
   enforced on the credits ledger, and a request that pays elsewhere would escape it.

### 5.3 Enforcement

When the hub reserves money for the call (the auth leg of auth/capture, Protocol §6), it
first reserves the same amount against every limit of every mandate in the chain. Amounts are
compared as the ledger will actually hold them (the credits ledger counts millicents, so a
price is rounded to 10 µUSD before it meets a limit). `perCall` applies to everything ONE call
reserves — a federated call's price and its routing fee together — and a subcontracting
allowance is bounded by `subcontract.perCallAllowance` instead of `perCall`, while still
counting against `perDay`, `total` and `perProductPerDay`. The product a per-product limit
counts is the product the hub executes, resolved from its catalogue, never the `product_id`
string the caller sent. Each
counter is moved by a single conditional statement (`spent + amount <= limit`), so no number
of concurrent requests can push one past its limit. A refusal releases whatever the request
had already reserved, and the call answers `402 mandate_limit` naming the limit.

The reservation follows the money: captured when the credit hold is captured, released when
it is released. The routing fee on a federated invoke is money the agent spends, so it is
reserved against the mandate as well.

### 5.4 What the provider learns

A mandated call forwards two hub-verified facts to the provider:

```
X-AIMarket-Agent:     did:key:… (leaf subject)
X-AIMarket-Principal: did:key:… (root issuer)
```

Nothing else about the mandate is forwarded. This is the "know your agent" part of the
extension: a seller sees who is behind a call, as vouched for by the hub, without learning
the owner's account or limits.

They are sent only to a provider the hub executes itself. A call the hub routes to a peer
hub carries neither: the peer did not verify the mandate, and a header it would pass on
unverified is not a fact.

A mandated call that delivers carries a `mandate` block in its answer: the leaf `digest`,
the `agent` and `principal` DIDs, and the leaf's `depth` in its chain.

### 5.5 Revocation

`POST /ai-market/v2/mandates/revoke`:

```json
{ "digest": "sha256-…", "by": "did:key:…", "t": 1790000000, "n": "…", "s": "…" }
```

`by` MUST be the issuer of the mandate or of any of its ancestors. `s` signs

```
aimarket-mandate-revoke/1
<hub base URL>
<digest>
<t>
<n>
```

Alternatively the root's funding account may revoke with its `X-API-Key` and
`{"digest"}` alone. That is the owner's kill switch when they no longer hold a key.
Revoking a mandate revokes everything below it. Holds already taken are settled normally.

## 6. Subcontracting (SUB/1)

### 6.1 Job context

When a hub executes a local provider, it sends:

```
X-AIMarket-Job: <token>
X-AIMarket-Hub: <hub base URL — where to present the token>
```

The token is `base64url(JCS(claims)) "." base64url(signature)`. The signature is Ed25519, by
the hub's signing key (the `signer_public_key` in its `/.well-known/ai-market.json`), over
the UTF-8 bytes `aimarket-job-token/1` + LF followed by `JCS(claims)`. The prefix keeps a
job token from ever verifying as anything else the same key signs.

```json
{
  "v": 1, "iss": "https://modelmarket.dev", "job": "job_…", "node": "node_…",
  "depth": 0, "maxDepth": 2, "exp": 1790000060,
  "path": ["summarize@v1"]
}
```

`job` and `node` are the hub's own names for the job and for this call within it. A root
without an allowance has the hub's maximum depth (§6.5): every hop pays for itself, so the
depth bounds only the tree's size. With an allowance it is the buyer's `max_depth`.

A provider that buys from another provider while serving the call SHOULD send the same
header back to the hub on that purchase. The hub then:

- verifies the signature (its own key) and `exp`, and refuses (`403 job_invalid`) when the
  call the token names has already returned: a provider holding a token past its call
  cannot graft purchases onto a tree whose bill of materials and receipt are already out.
  A purchase that spends money is additionally bound to the grant, which the hub closes the
  moment the root call returns (§6.2);
- refuses if the child's depth would exceed `maxDepth`, or the child `capability_id` is
  already on `path` (a cycle);
- refuses when the job already holds 64 nodes (the root included), or `node` already has 16
  children. A child refused after it joined — its capability outside the mandate's scope,
  say — gives both slots back and is recorded as `refused`;
- records the child under `node`, and sends the provider it executes for the child a token
  of its own (`depth + 1`, the child appended to `path`), so the tree can grow further.

The token carries no money. Presenting one only attaches the call to a tree, so a provider
that pays for its subcontractors itself (fixed-price subcontracting) needs nothing else.

### 6.2 Pass-through allowance (cost-plus subcontracting)

A root buyer MAY let the providers of a job spend part of the buyer's own funding on
subcontractors:

```json
{ "product_id": "…", "capability_id": "…", "input": {},
  "subcontract": { "allowance_usd": 0.005, "max_depth": 2 } }
```

The hub then:

1. reserves the call's price **and** the allowance from the buyer's funding account, and —
   for a mandated call — against the mandate chain. The mandate's `subcontract` block MUST
   be present and bounds both numbers;
2. sends the provider, next to the job token,
   `X-AIMarket-Job-Grant: <random 256-bit secret>`;
3. treats a child invoke that presents both the grant and a job token of the same job as
   paid **from the allowance**. The child's price is moved out of the allowance reservation
   into a hold of its own with one conditional statement, so children can never spend more
   than the allowance, however many run at once. A child that fails hands its amount back to
   the allowance, not to the buyer's balance, so a retry can still be paid;
4. closes the grant when the root call returns, releases what is left of the allowance, and
   answers the root buyer with the bill of materials (§6.4).

A child funded by the grant must still fall inside the root chain's scope and audience. Its
cost is already inside the mandate reservation made in step 1, so it is not reserved against
the mandate a second time. The child is paid from the root buyer's account, but the caller is
a provider: every balance figure the child's responses carry is what is left of the allowance,
never the buyer's balance.

An allowance the root call failed to settle (a crash, a release that kept failing) is settled
by the hub once its grant has been expired for five minutes: a sweep runs when the hub
starts and then on a timer (every two minutes by default).

The allowance is available only when the root call is paid on the credits rail and executes
on this hub. A root paid on chain or routed to a peer answers `400 subcontract_unsupported`:
the hub can only pass through money it meters.

### 6.3 Who carries which risk

- A subcontractor that fails is not paid. Its amount returns to the allowance.
- A subcontractor that delivers is paid, even if the provider that hired it then fails. That
  is the cost-plus rule: materials consumed are paid for. The buyer's exposure is bounded by
  the allowance they chose, and the bill of materials shows which provider failed.
- In fixed-price subcontracting (no grant) the provider pays its subcontractors from its own
  rail and carries that risk alone. The job tree still records every hop.

### 6.4 Bill of materials

The root response carries

```json
"subcontracting": {
  "job_id": "job_…",
  "allowance_usd": 0.005,
  "spent_usd": 0.002,
  "released_usd": 0.003,
  "nodes": [
    { "node": "node_…", "parent": "node_…", "depth": 1,
      "product_id": "…", "capability_id": "…",
      "price_usd": 0.001, "funded_by": "allowance", "status": "captured",
      "receipt_id": "urn:uuid:…", "receipt_digest": "sha256-…" }
  ]
}
```

An allowance-funded node's `price_usd` is what that call took from the allowance — for a child
the hub routed to a peer, its price and the routing fee together — so those nodes add up to
`spent_usd`.

`status` is `running`, `captured`, `failed` or `refused`. `spent_usd` and `released_usd` are
what the ledger settled; they are `null` while the settlement is still pending (a release
that failed, which the sweep retries). The block is present on the root's answer whether the
root delivered or not: a root whose own provider failed after its subcontractors delivered
still pays for them (§6.3), and the bill is what explains the charge.

The root's AWR/2 work receipt lists each delivered child's work receipt in `parents`
(AWR/2 §3.2): `id` is the child receipt's own `id` and `digestSRI` its digest, so a verifier
holding the bundle can resolve every edge. Each child's receipt does the same for ITS
children, so the tree is committed to hop by hop, not only reported.

A child's own answer carries a `job` block: `job_id`, `node`, `parent`, `depth` and
`funded_by`.
`GET /ai-market/v2/jobs/{job_id}` returns the same tree later. The job id is an unguessable
capability: anyone holding it may read the tree, and it is given only to the root buyer and
the providers of the job.

### 6.5 Limits a hub enforces regardless of the buyer

| Limit | Value |
|---|---|
| depth | ≤ 3 |
| nodes per job | ≤ 64, the root included (a counter moved by one conditional statement, so concurrent joins cannot exceed it) |
| direct children per node | ≤ 16 (likewise) |
| token lifetime | the provider timeout plus 30 s |
| allowance per root call | `AIMARKET_SUBCONTRACT_MAX_ALLOWANCE_USD`, default 1.00 |

## 7. Errors

| Status | `error` | Meaning |
|---|---|---|
| 400 | `mandate_malformed` | The header, proof or document is not well formed. |
| 413 | `mandate_malformed` | The mandate document is larger than the hub accepts. |
| 400 | `mandate_rail_unsupported` | A mandate arrived together with a channel or x402 payment. |
| 400 | `subcontract_unsupported` | An allowance was asked on a rail or route that cannot carry it. |
| 401 | `mandate_proof_invalid` | Bad signature, stale `t`, or a reused nonce. |
| 402 | `mandate_required` | The account requires a mandate and none was presented. |
| 402 | `mandate_unfunded` | The root issuer has no linked funding account on this hub. |
| 402 | `mandate_limit` | A limit would be exceeded; `limit` and `mandate` name which. |
| 403 | `mandate_invalid` | Unknown, expired, revoked, broken chain, wrong audience. |
| 403 | `mandate_scope` | The capability is outside the leaf's scope. |
| 403 | `job_invalid` | Bad or expired job token, unknown or finished node, or a grant sent together with another payment. |
| 403 | `job_limit` | Depth, cycle, fan-out or node limit. |
| 402 | `allowance_exhausted` | The grant is closed, or cannot cover the child's price. |
| 403 | `owner_authorization_required` | The account already has an owner, and the change is not signed by one. |
| 404 | `mandate_unknown` | No mandate with that digest is registered here. |
| 404 | `job_unknown` | No job with that id. |
| 409 | `owner_linked_elsewhere` | The DID is already linked to another account on this hub. |
| 503 | `mandates_unavailable` | The hub cannot verify mandates, or its credits rail is off. |

## 8. Security considerations

- **A mandate is not a bearer token.** Without the agent's private key the digest is
  worthless. With it, the damage is bounded by the chain's limits, scope, audience and
  expiry, and the owner can revoke.
- **A grant is a bearer token**, deliberately: it is handed to a provider so that the
  provider can spend. It is scoped to one job and one allowance, dies with the root call and
  is never forwarded to peers. A provider that leaks it loses at most the rest of that
  allowance for at most the provider timeout.
- **The hub is trusted** to enforce limits it is shown. A mandate constrains what *this hub*
  will serve. It does not stop an agent spending from a wallet it holds elsewhere. On-chain
  spending limits (smart-account session keys) are the control for that, and they compose
  with this one: the mandate names the owner and the policy, and the chain enforces custody.
- **Races.** Every limit and every allowance is moved by one conditional statement, never a
  read-then-write. That is the same invariant the credits ledger already holds for balances.
- **Privacy.** Providers learn the agent and principal DIDs, never the funding account.
  Usage figures are readable only by the chain's keys and the funding account.

## 9. Test vectors

`test-vectors/mandate-signed.json` holds a root mandate and a re-delegation signed with
fixed seeds, their digests, a request proof over a fixed body, an owner link, an owner-change
authorization and a revocation. Every implementation MUST reproduce the digests and every
signature. `test-vectors/generate_mandates.py` regenerates the file byte for byte.
