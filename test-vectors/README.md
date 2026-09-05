# Test Vectors

Reference vectors for implementers verifying Ed25519 signatures against this protocol.

**These vectors are normative.** An implementation that disagrees with them is
non-conformant, whatever its own tests say. The byte layout each one exercises is specified
in [`../spec.md` §7.3](../spec.md).

> **Corrected 2026-08-28.** An earlier version of this file published a three-field manifest
> canonical (`capabilities_count|generated_at|protocol_version`) and referenced a file named
> `well-known-signed.json` that does not exist. The three-field string does not verify
> against `manifest-signed.json` — checked, it raises `InvalidSignature` — so anyone
> implementing from it could not have succeeded, and anyone who worked around the failure by
> dropping the content digests would have built a verifier a relay can walk through: without
> `tools_hash` every price in the catalogue is outside the signature, and without
> `by_hub_hash` so is every peer's `trust_score`. Every canonical below has been verified
> against the file it describes.

## Test keypair

**Do not use in production.** Fixed so vectors are reproducible.

```
Private key (hex): 9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60
Public key  (hex): d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
Public key  (b64): 11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=
```

## The vectors

| File | What it is | Signed |
|---|---|---|
| `well-known.json` | A valid `/.well-known/ai-market.json` discovery document | no — discovery documents are not signed; the manifest they point to is |
| `manifest-signed.json` | Capability manifest, five-field canonical (§7.3.2) | yes |
| `receipt-signed.json` | Invocation receipt, seven-field v1 canonical (§7.3.3) — carries no v2 field, so it is unambiguous | yes |
| `receipt-v2-signed.json` | Rejection receipt, v2 canonical with the `fields:` digest (§7.3.4) | yes |
| `federation-announce-signed.json` | Peer announcement, three-field canonical (§7.3.5) | yes |
| `provenance-receipt-signed.json` | Provenance receipt (W3C VC-compatible envelope) | yes |
| `debit-authorization.json` | EIP-712 `DebitAuthorization` (§6.2) | EIP-712, not Ed25519 |
| `payer-proof.json` | Payer proof of deposit | — |

## Canonical strings, verified

Each string below was recomputed from the file it belongs to and checked against that file's
signature with the public key above.

**Manifest** (`manifest-signed.json`):

```
capabilities_count:5|generated_at:2026-08-28T09:00:50Z|protocol_version:v1|tools_hash:7fbf86cde4c3a1d265ce4d893a5626584b2a34cedbf3630c4f2a8d6d9a468fcb|by_hub_hash:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a
```

`by_hub_hash` here is the digest of the empty object `{}` — this manifest serves no peers,
and an absent `by_hub` MUST hash as `{}` rather than being skipped.

**Receipt v1** (`receipt-signed.json`):

```
nonce:rcpt_test001|product_id:prod-001|capability_id:translate.multi@v2|price_usd:0.4|timestamp:2026-08-28T09:00:50Z|success:1|latency_ms:8100
```

Note `success:1` — the boolean is serialized as an integer, never as `true`.

**Receipt v2** (`receipt-v2-signed.json`) — a rejection, where v1 would sign nothing about the refusal:

```
nonce:rcpt_test002|product_id:prod-001|capability_id:translate.multi@v2|price_usd:0.0|timestamp:2026-08-28T09:00:50Z|success:0|latency_ms:0|v:2|fields:62e8135ac924809d58b3b8d8e8e0ff9b3bdaaabca378881003524c36408a61aa
```

The `fields:` digest uses **compact** separators, unlike the manifest digests above. That
inconsistency is real and specified in §7.3.1; applying one form everywhere breaks the other.

**Federation announce** (`federation-announce-signed.json`):

```
hub_url:https://test-hub.example.com|well_known_url:https://test-hub.example.com/.well-known/ai-market.json|capabilities_count:5
```

## Verify them yourself

Or run `python3 ../conformance/run.py`, which checks these plus the negative vectors.
The canonicals above are from one generation of the vectors; the runner recomputes them
from whatever the files currently say, so it is the source of truth if the two disagree.

```python
import base64, hashlib, json, pathlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

V = pathlib.Path(__file__).parent
vk = Ed25519PublicKey.from_public_bytes(
    base64.b64decode("11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=")
)

def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()

def check(name, canonical, signature_b64):
    vk.verify(base64.b64decode(signature_b64), canonical.encode())
    print(f"✓ {name}")

m = json.loads((V / "manifest-signed.json").read_text())
check("manifest", (
    f"capabilities_count:{m.get('capabilities_count', 0)}"
    f"|generated_at:{m.get('generated_at', '')}"
    f"|protocol_version:{m.get('protocol_version', 'v1')}"
    f"|tools_hash:{digest(m.get('tools', []))}"
    f"|by_hub_hash:{digest(m.get('by_hub', {}))}"
), m["signature"]["value"])

r = json.loads((V / "receipt-signed.json").read_text())
check("receipt v1", (
    f"nonce:{r.get('nonce', '')}"
    f"|product_id:{r.get('product_id', '')}"
    f"|capability_id:{r.get('capability_id', '')}"
    f"|price_usd:{r.get('price_usd', 0)}"
    f"|timestamp:{r.get('timestamp', '')}"
    f"|success:{1 if r.get('success') else 0}"
    f"|latency_ms:{r.get('latency_ms', 0)}"
), r["signature"]["value"])

a = json.loads((V / "federation-announce-signed.json").read_text())
check("federation announce", (
    f"hub_url:{a['hub_url']}"
    f"|well_known_url:{a['well_known_url']}"
    f"|capabilities_count:{a.get('capabilities_count', 0)}"
), a["signature"]["value"])

print("✓ all canonicals in this README match their vectors")
```

## Two things that will bite you

1. **`ensure_ascii=False`.** The digests are over JSON that emits non-ASCII characters as
   themselves. A serializer that escapes them to `\uXXXX` — which is Python's default and
   many libraries' only behaviour — produces a different digest and every signature fails.
2. **Field order is fixed.** The canonical is a concatenation, not a set. Reordering pairs,
   inserting whitespace, or omitting a pair whose value happens to be empty all change the
   signed bytes.

## Regenerating

```bash
python3 generate.py
```

Regeneration rewrites every signed vector from the fixed key above. If a canonical formula
changes, `../spec.md` §7.3 and this file MUST change in the same commit — a vector that
disagrees with the specification is worse than no vector, because it is believed.
