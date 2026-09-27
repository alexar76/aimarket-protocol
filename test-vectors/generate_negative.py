#!/usr/bin/env python3
"""Derive negative vectors from the positive ones.

Every file in `negative/` MUST fail verification. They are derived here rather than
hand-written so they cannot drift from the positive vectors they mutate: regenerate the
positives and these follow.

Each negative carries a `_expect` block naming what a conformant verifier must reject and
why. That block is metadata about the vector, not part of any signed payload.
"""
from __future__ import annotations

import base64
import copy
import json
import pathlib

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:  # pragma: no cover
    raise SystemExit("pip install cryptography>=44")

V = pathlib.Path(__file__).parent
OUT = V / "negative"
OUT.mkdir(exist_ok=True)

# A key that is NOT the test key — used for the wrong-signer case.
OTHER_KEY = Ed25519PrivateKey.from_private_bytes(bytes.fromhex("11" * 32))
OTHER_PUB_B64 = base64.b64encode(
    OTHER_KEY.public_key().public_bytes_raw()
).decode()


def load(name: str) -> dict:
    return json.loads((V / name).read_text(encoding="utf-8"))


def write(name: str, doc: dict, must: str, why: str, section: str) -> None:
    doc["_expect"] = {"result": "reject", "reason": must, "why": why, "spec": section}
    (OUT / name).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote negative/{name}  — {must}")


def main() -> None:
    print("negative vectors:")

    # ---- manifest: content tampered under a still-present signature ----------
    m = load("manifest-signed.json")
    tampered = copy.deepcopy(m)
    if tampered.get("tools"):
        first = tampered["tools"][0]
        for price_key in ("price_per_call_usd", "price_usd", "price"):
            if price_key in first:
                first[price_key] = 0.0001
                break
        else:
            first["price_per_call_usd"] = 0.0001
    write(
        "manifest-tampered-price.json", tampered,
        "signature-invalid",
        "A price inside tools[] was rewritten. tools_hash is inside the canonical, so the "
        "signature must no longer verify. A verifier that accepts this is one a relay can "
        "walk through, rewriting every price in the catalogue.",
        "§7.3.2",
    )

    tampered_peers = copy.deepcopy(m)
    tampered_peers["by_hub"] = {"https://evil.example": {"trust_score": 0.99}}
    write(
        "manifest-tampered-by-hub.json", tampered_peers,
        "signature-invalid",
        "by_hub was replaced to inflate a peer's trust_score. by_hub_hash is inside the "
        "canonical, so this must fail. This is the exact hole that existed before "
        "2026-07-29.",
        "§7.3.2",
    )

    # ---- manifest: signed with the superseded three-field canonical ----------
    legacy = copy.deepcopy(m)
    legacy_canonical = (
        f"capabilities_count:{legacy.get('capabilities_count', 0)}"
        f"|generated_at:{legacy.get('generated_at', '')}"
        f"|protocol_version:{legacy.get('protocol_version', 'v1')}"
    )
    legacy["signature"] = {
        "algorithm": "ed25519",
        "public_key": legacy.get("signature", {}).get("public_key", ""),
        "value": base64.b64encode(
            Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(
                    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
                )
            ).sign(legacy_canonical.encode())
        ).decode(),
    }
    write(
        "manifest-legacy-3field-canonical.json", legacy,
        "signature-invalid",
        "Signed correctly, by the right key — over the SUPERSEDED three-field canonical. A "
        "verifier that still accepts the old shape leaves tools[] and by_hub outside the "
        "signature entirely. Published documentation taught this shape until 2026-08-28, so "
        "third-party implementations of it plausibly exist.",
        "§7.3.2",
    )

    # ---- receipt: outcome flipped -------------------------------------------
    r = load("receipt-signed.json")
    flipped = copy.deepcopy(r)
    flipped["success"] = not bool(r.get("success"))
    write(
        "receipt-flipped-success.json", flipped,
        "signature-invalid",
        "success was flipped. It is inside the seven-field canonical, so this must fail. "
        "Under the five-field canonical published before 2026-07-29 it would have passed, "
        "which means a failed invocation could be presented as a successful one.",
        "§7.3.3",
    )

    latency = copy.deepcopy(r)
    latency["latency_ms"] = 1
    write(
        "receipt-tampered-latency.json", latency,
        "signature-invalid",
        "latency_ms rewritten to fake an SLA. Inside the canonical since the seven-field "
        "shape; must fail.",
        "§7.3.3",
    )

    # ---- receipt: correct content, wrong signer ------------------------------
    wrong_key = copy.deepcopy(r)
    canonical = (
        f"nonce:{r.get('nonce', '')}"
        f"|product_id:{r.get('product_id', '')}"
        f"|capability_id:{r.get('capability_id', '')}"
        f"|price_usd:{r.get('price_usd', 0)}"
        f"|timestamp:{r.get('timestamp', '')}"
        f"|success:{1 if r.get('success') else 0}"
        f"|latency_ms:{r.get('latency_ms', 0)}"
    )
    wrong_key["signature"] = {
        "algorithm": "ed25519",
        "public_key": OTHER_PUB_B64,
        "value": base64.b64encode(OTHER_KEY.sign(canonical.encode())).decode(),
    }
    write(
        "receipt-wrong-signer.json", wrong_key,
        "key-not-pinned",
        "Internally consistent: the canonical is right and the signature verifies against "
        "the key the document itself advertises. It is signed by the WRONG KEY. A verifier "
        "that trusts the embedded public_key instead of the key it pinned for this peer "
        "accepts anything anyone signs.",
        "§2.2, §7.3.1",
    )

    # ---- receipt: stale / replayed ------------------------------------------
    stale = copy.deepcopy(r)
    stale["timestamp"] = "2020-01-01T00:00:00Z"
    write(
        "receipt-stale-timestamp.json", stale,
        "signature-invalid",
        "timestamp rewritten to an old date. It is inside the canonical, so tampering fails "
        "on the signature. Note what this vector does NOT test: a correctly signed receipt "
        "REPLAYED unchanged is signature-valid by construction, and can only be caught by "
        "nonce state the verifier keeps. See negative/README.md.",
        "§7.3.3",
    )

    # ---- receipt: v2 evidence under a v1 signature (downgrade) --------------
    try:
        v2 = load("receipt-v2-signed.json")
    except FileNotFoundError:
        v2 = None
    if v2 is not None:
        downgraded = copy.deepcopy(v2)
        base = (
            f"nonce:{v2['nonce']}|product_id:{v2['product_id']}"
            f"|capability_id:{v2['capability_id']}|price_usd:{v2['price_usd']}"
            f"|timestamp:{v2['timestamp']}|success:{1 if v2.get('success') else 0}"
            f"|latency_ms:{v2.get('latency_ms', 0)}"
        )
        downgraded["signature"] = {
            "algorithm": "ed25519",
            "value": base64.b64encode(
                Ed25519PrivateKey.from_private_bytes(
                    bytes.fromhex(
                        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
                    )
                ).sign(base.encode())
            ).decode(),
        }
        write(
            "receipt-v2-downgraded-to-v1.json", downgraded,
            "version-under-covers-content",
            "A rejection receipt — reason, verify_score, refunded, channel_id all present — "
            "signed at v1 by the right key. The v1 signature is valid over the fields it "
            "covers, and every field the refund is actually argued from sits outside it. A "
            "verifier MAY accept the signature for back-compat with pre-v2 peers, but MUST "
            "NOT treat the v2 fields as authenticated, and MUST be able to say which ones "
            "are not. Accepting this as a fully verified rejection is the failure.",
            "§7.3.4",
        )

    # ---- announce: url rewritten --------------------------------------------
    a = load("federation-announce-signed.json")
    hijack = copy.deepcopy(a)
    hijack["hub_url"] = "https://attacker.example"
    write(
        "announce-tampered-hub-url.json", hijack,
        "signature-invalid",
        "hub_url rewritten to redirect an announcement at an attacker's host. Inside the "
        "canonical; must fail.",
        "§7.3.5",
    )

    print(f"\n{len(list(OUT.glob('*.json')))} negative vectors in {OUT}")


if __name__ == "__main__":
    main()
