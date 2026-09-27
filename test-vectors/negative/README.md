# Negative vectors

Every file here MUST be **rejected**. They are generated from the positive vectors by
[`../generate_negative.py`](../generate_negative.py), so they cannot drift from what they
mutate.

Run them: `python3 ../../conformance/run.py`

## What each one catches

| Vector | Rejected because | Spec |
|---|---|---|
| `manifest-tampered-price.json` | A price inside `tools[]` was rewritten; `tools_hash` is signed | §7.3.2 |
| `manifest-tampered-by-hub.json` | A peer's `trust_score` was inflated; `by_hub_hash` is signed | §7.3.2 |
| `manifest-legacy-3field-canonical.json` | Correctly signed by the right key — over the **superseded** canonical | §7.3.2 |
| `receipt-flipped-success.json` | `success` flipped false→true | §7.3.3 |
| `receipt-tampered-latency.json` | `latency_ms` rewritten to fake an SLA | §7.3.3 |
| `receipt-stale-timestamp.json` | `timestamp` rewritten | §7.3.3 |
| `receipt-wrong-signer.json` | Internally consistent, signed by a key that is **not the pinned one** | §2.2, §7.3.1 |
| `announce-tampered-hub-url.json` | `hub_url` redirected at an attacker's host | §7.3.5 |

Each file carries an `_expect` block naming the rejection and why it matters. That block is
metadata about the vector; it is not part of any signed payload.

## The two that deserve attention

**`manifest-legacy-3field-canonical.json`** is not tampered. The key is right, the signature
is valid, the maths is correct — over the canonical this project's own documentation
published until 2026-08-28. A verifier that accepts it has `tools[]` and `by_hub` outside
its signature entirely, which is the difference between a signed catalogue and a decorated
one. Third-party implementations written from that documentation plausibly exist, so this
vector is the one most likely to fail against real code.

**`receipt-wrong-signer.json`** is the trap that catches verifiers written the obvious way.
It verifies perfectly against the public key it carries. A verifier that reads
`signature.public_key` from the document and checks against that will accept it — and will
accept anything anyone signs. Trust the key you **pinned** for that peer (§2.2); the key
inside the document is a claim, not an identity.

## What is NOT covered here, and cannot be

A **replayed** receipt — a correct, untampered, correctly signed receipt presented a second
time — is signature-valid by construction. No static vector can catch it, because there is
nothing wrong with the bytes. Detecting it requires the verifier to keep state: the
`nonce`/`receiptId` set (§6.2), per-channel nonces, and deadlines. A conformance run that
passes every file here says nothing about whether an implementation has that state.

The same applies to the admission rules in §2.4–2.6: they are behavioural, and a hub is
checked against them live (`conformance/run.py --hub <url>`), not by a file on disk.
