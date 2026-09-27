#!/usr/bin/env python3
"""Generate reference test vectors for AIMarket Protocol v2.

Uses a deterministic test keypair. DO NOT USE THESE KEYS IN PRODUCTION.
"""

import base64
import json
import time

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Deterministic test keypair (ed25519 test vector seed from RFC 8032)
SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
priv = Ed25519PrivateKey.from_private_bytes(SEED)
pub = priv.public_key()
PUBLIC_KEY_BYTES = pub.public_bytes_raw()
PUBLIC_KEY_HEX = PUBLIC_KEY_BYTES.hex()
PUBLIC_KEY_B64 = base64.b64encode(PUBLIC_KEY_BYTES).decode()

print(f"Public key (hex):  {PUBLIC_KEY_HEX}")
print(f"Public key (b64):  {PUBLIC_KEY_B64}")


def sign_bytes(data: bytes) -> bytes:
    return priv.sign(data)


def sign_canonical(canonical: str) -> str:
    sig = sign_bytes(canonical.encode())
    return base64.b64encode(sig).decode()


def sign_manifest(manifest: dict) -> dict:
    """FIVE fields, byte-identical to ``aimarket_hub.signing.Signer.manifest_canonical``.

    The two content digests are the security of this signature. Without them — as this
    signed until 2026-07-29 — a relay could rewrite every price in `tools[]` and every
    per-peer `trust_score` in `by_hub` and the signature would still verify. `oracle_core`
    was missing the `by_hub_hash` field for the same reason, which is why no oracle could
    federate at all until it was fixed; the vectors were the third implementation and the
    only one nobody had compared against the hub.

    An absent `by_hub` hashes as `{}`, which is exactly what the hub computes for the missing
    key, so a manifest that serves no peers agrees without inventing a field.
    """
    import hashlib

    tools_hash = hashlib.sha256(
        json.dumps(manifest.get("tools", []), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    by_hub_hash = hashlib.sha256(
        json.dumps(manifest.get("by_hub", {}), sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    canonical = (
        f"capabilities_count:{manifest['capabilities_count']}"
        f"|generated_at:{manifest['generated_at']}"
        f"|protocol_version:{manifest['protocol_version']}"
        f"|tools_hash:{tools_hash}"
        f"|by_hub_hash:{by_hub_hash}"
    )
    sig_b64 = sign_canonical(canonical)
    manifest["signature"] = {
        "algorithm": "ed25519",
        "public_key": PUBLIC_KEY_B64,
        "value": sig_b64,
    }
    print(f"\nManifest canonical string: {canonical}")
    print(f"Manifest signature: {sig_b64}")
    return manifest


def sign_receipt(receipt: dict) -> dict:
    """v1 interop canonical — SEVEN fields, byte-identical to
    ``aimarket_hub.signing.Signer.receipt_canonical(receipt, 1)``.

    This signed only the first five until 2026-07-29, which left `success` and `latency_ms`
    OUTSIDE the signature. Anyone implementing a client from these vectors — which is what
    they are for — would have accepted a receipt whose `success` was flipped from false to
    true without the signature breaking. The live hub has signed seven fields all along, so
    production was never affected; the reference material was teaching the insecure shape,
    and no test compared the two.
    """
    canonical = (
        f"nonce:{receipt['nonce']}"
        f"|product_id:{receipt['product_id']}"
        f"|capability_id:{receipt['capability_id']}"
        f"|price_usd:{receipt['price_usd']}"
        f"|timestamp:{receipt['timestamp']}"
        f"|success:{1 if receipt.get('success') else 0}"
        f"|latency_ms:{receipt.get('latency_ms', 0)}"
    )
    sig_b64 = sign_canonical(canonical)
    receipt["signature"] = {
        "algorithm": "ed25519",
        "value": sig_b64,
    }
    print(f"\nReceipt canonical string: {canonical}")
    print(f"Receipt signature: {sig_b64}")
    return receipt


def sign_federation_announce(msg: dict) -> dict:
    canonical = (
        f"hub_url:{msg['hub_url']}"
        f"|well_known_url:{msg['well_known_url']}"
        f"|capabilities_count:{msg.get('capabilities_count', 0)}"
    )
    sig_b64 = sign_canonical(canonical)
    msg["signature"] = {
        "algorithm": "ed25519",
        "value": sig_b64,
    }
    print(f"\nAnnounce canonical string: {canonical}")
    print(f"Announce signature: {sig_b64}")
    return msg


# ── Well-Known ────────────────────────────────────────────────
well_known = {
    "name": "Test AI Hub",
    "protocol_versions": ["v1", "v2"],
    "hub_version": "2.0.0",
    "mcp_endpoint": "https://test-hub.example.com/ai-market/mcp",
    "manifest_url": "https://test-hub.example.com/ai-market/manifest",
    "products_count": 3,
    "capabilities_count": 5,
    "federated_capabilities_count": 12,
    "supported_chains": ["base"],
    "supported_tokens": ["USDT"],
    "signer_public_key": PUBLIC_KEY_B64,
    "federation": {
        "crawl_interval_s": 3600,
        "routing_fee_bps": 100,
        "min_trust_score": 0.3,
        "seed_list": [],
    },
    "peers": [],
}

with open("well-known.json", "w") as f:
    json.dump(well_known, f, indent=2)

# ── Manifest ──────────────────────────────────────────────────
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
manifest = {
    "protocol_version": "v1",
    "generated_at": now,
    "base_url": "https://test-hub.example.com",
    "products_count": 3,
    "capabilities_count": 5,
    "tools": [
        {
            "name": "prod-001.translate.multi@v2",
            "description": "Translate text to multiple locales",
            "input_schema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "locales": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "translations": {
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    }
                },
            },
            "price_per_call_usd": 0.40,
            "p50_latency_ms": 8100,
            "success_rate_30d": 0.97,
            "product_id": "prod-001",
            "capability_id": "translate.multi@v2",
        }
    ],
}
manifest = sign_manifest(manifest)

with open("manifest-signed.json", "w") as f:
    json.dump(manifest, f, indent=2)

# ── Receipt ───────────────────────────────────────────────────
# A CLEAN v1 receipt. `channel_id` was removed on 2026-08-28: it is one of the fields only
# the v2 canonical binds, so carrying it here made the reference positive vector the exact
# ambiguous document §7.3.4 has to reason about — signed at v1, carrying v2 evidence. An
# interop example must be unambiguous; the v2 case is a vector of its own, below.
receipt = {
    "nonce": "rcpt_test001",
    "product_id": "prod-001",
    "capability_id": "translate.multi@v2",
    "price_usd": 0.40,
    "latency_ms": 8100,
    "success": True,
    "timestamp": now,
}
receipt = sign_receipt(receipt)

with open("receipt-signed.json", "w") as f:
    json.dump(receipt, f, indent=2)

# ── Federation Announce ───────────────────────────────────────
announce = {
    "hub_url": "https://test-hub.example.com",
    "well_known_url": "https://test-hub.example.com/.well-known/ai-market.json",
    "capabilities_count": 5,
    "hub_name": "Test AI Hub",
    "signer_public_key": PUBLIC_KEY_B64,
}
announce = sign_federation_announce(announce)

with open("federation-announce-signed.json", "w") as f:
    json.dump(announce, f, indent=2)

# ── DebitAuthorization (EIP-712) ──────────────────────────────
# Mirrors contracts/evm/AIMarketEscrow.sol DEBIT_TYPEHASH. The SDK stubs use
# SHA-256 in place of keccak256; the canonical string and field order here
# match the production contract, so swapping in keccak256 + secp256k1 ECDSA
# in production keeps the same wire format.
DEBIT_TYPEHASH = (
    "DebitAuthorization(bytes32 channelId,address hub,address token,"
    "uint256 amount,bytes32 receiptId,uint256 nonce,uint256 deadline)"
)
debit_auth = {
    "typehash": DEBIT_TYPEHASH,
    "domain": {
        "name": "AIMarketEscrow",
        "version": "1",
        "chainId": 8453,  # Base mainnet
        "verifyingContract": "0x0000000000000000000000000000000000000000",
    },
    "message": {
        "channelId": (
            "0x0000000000000000000000000000000000000000000000000000000000000001"
        ),
        "hub": "0x000000000000000000000000000000000000bEEF",
        "token": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
        "amount": "5000000",  # 5.00 USDC (6 decimals)
        "receiptId": (
            "0x0000000000000000000000000000000000000000000000000000000000001234"
        ),
        "nonce": "0",
        "deadline": "2000000000",
    },
    "signature_format": "eip712:<hex>",
    "notes": (
        "SDK stubs (Dart / TS / Rust) digest with SHA-256 over the canonical "
        "string `0x1901|domain:<sha256>|DebitAuthorization:<sha256(sorted fields)>`. "
        "Production: replace with keccak256 + secp256k1 ECDSA; `ECDSA.recover` "
        "on-chain MUST return the depositor address or `debitChannel` reverts "
        "with `InvalidSignature()`."
    ),
}

with open("debit-authorization.json", "w") as f:
    json.dump(debit_auth, f, indent=2)

print("\n✅ All test vectors generated.")
print(f"Files written to: test-vectors/")


# ── Receipt v2 (rejection-bearing) ────────────────────────────
# The v1 canonical signs essentially nothing about a refusal: price, success and latency are
# all constant on a rejection, so the reasoning a refund is argued from sat outside the
# signature. v2 binds it. Byte-identical to
# `aimarket_hub.signing.Signer.receipt_canonical(receipt, 2)`.
_RECEIPT_V2_FIELDS = (
    "type", "channel_id", "category", "plugin", "reason", "verify_score",
    "delivery_reasons", "trace_id", "refunded",
)


def _fields_digest(obj: dict, names: tuple) -> str:
    import hashlib
    import json as _json

    payload = {name: obj.get(name) for name in names}
    return hashlib.sha256(
        _json.dumps(payload, sort_keys=True, ensure_ascii=False,
                    separators=(",", ":"), default=str).encode()
    ).hexdigest()


def sign_receipt_v2(receipt: dict) -> dict:
    base = (
        f"nonce:{receipt['nonce']}"
        f"|product_id:{receipt['product_id']}"
        f"|capability_id:{receipt['capability_id']}"
        f"|price_usd:{receipt['price_usd']}"
        f"|timestamp:{receipt['timestamp']}"
        f"|success:{1 if receipt.get('success') else 0}"
        f"|latency_ms:{receipt.get('latency_ms', 0)}"
    )
    canonical = f"{base}|v:2|fields:{_fields_digest(receipt, _RECEIPT_V2_FIELDS)}"
    sig_b64 = sign_canonical(canonical)
    receipt["signature"] = {"algorithm": "ed25519", "value": sig_b64, "version": 2}
    print(f"\nReceipt v2 canonical string: {canonical}")
    print(f"Receipt v2 signature: {sig_b64}")
    return receipt


receipt_v2 = sign_receipt_v2({
    "nonce": "rcpt_test002",
    "product_id": "prod-001",
    "capability_id": "translate.multi@v2",
    "price_usd": 0.0,
    "latency_ms": 0,
    "success": False,
    "timestamp": now,
    "type": "rejection",
    "channel_id": "ch_test001",
    "reason": "verification_below_threshold",
    "verify_score": 0.41,
    "refunded": True,
    "trace_id": "tr_test002",
    "delivery_reasons": ["claim_unsupported"],
})

with open("receipt-v2-signed.json", "w") as f:
    json.dump(receipt_v2, f, indent=2)
print("Wrote receipt-v2-signed.json")
