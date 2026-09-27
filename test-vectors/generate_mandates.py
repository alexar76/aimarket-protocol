#!/usr/bin/env python3
"""Generate mandate-signed.json — the normative vectors for mandates.md §9.

Deterministic: fixed seeds, fixed ids, fixed times. Ed25519 signatures are deterministic too,
so re-running this reproduces the file byte for byte. DO NOT USE THESE KEYS IN PRODUCTION.

Needs the awr reference package (``pip install awr/reference/python`` from the monorepo root).
"""
from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from awr.didkey import SigningKey
from awr.digest import canonical_sri
from awr.jcs import canonicalize
from awr.proof import sign_document

HUB = "https://modelmarket.dev"
OWNER = SigningKey.from_seed(hashlib.sha256(b"aimarket-mandate-vector-owner").digest())
AGENT = SigningKey.from_seed(hashlib.sha256(b"aimarket-mandate-vector-agent").digest())
DELEGATE = SigningKey.from_seed(hashlib.sha256(b"aimarket-mandate-vector-delegate").digest())


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def mandate(issuer: SigningKey, subject: SigningKey, uid: str, body: dict) -> dict:
    document = {
        "@context": ["https://www.w3.org/ns/credentials/v2"],
        "type": ["VerifiableCredential", "AIMarketMandate"],
        "id": f"urn:uuid:{uid}",
        "issuer": issuer.did,
        "validFrom": "2026-09-26T00:00:00Z",
        "validUntil": "2026-12-25T00:00:00Z",
        "credentialSubject": {"id": subject.did, "aimarketMandate": body},
    }
    return sign_document(document, issuer, "2026-09-26T00:00:00Z")


root = mandate(OWNER, AGENT, "0b8f6f2e-9a41-4d8e-8f1b-6a1f3c2d4e51", {
    "version": 1,
    "audience": [HUB],
    "scope": ["gaia.*", "atlas.nearest.read@v1"],
    "limits": {"perCall": 20000, "perDay": 1000000, "total": 10000000, "perProductPerDay": 400000},
    "subcontract": {"perCallAllowance": 5000, "maxDepth": 2},
})
root_digest = canonical_sri(root)

child = mandate(AGENT, DELEGATE, "7c2d9e10-3b5a-4f6c-9d8e-1a2b3c4d5e6f", {
    "version": 1,
    "audience": [HUB],
    "scope": ["gaia.weather.read@v1"],
    "limits": {"perCall": 5000, "perDay": 100000, "total": 1000000, "perProductPerDay": 100000},
    "parent": root_digest,
})
child_digest = canonical_sri(child)

body = b'{"product_id":"gaia.gateway","capability_id":"gaia.weather.read@v1","input":{"latitude":60.17,"longitude":24.94},"source_hub":"local"}'
t, nonce = 1790000000, "vector-nonce-000000000001"
request_message = "\n".join([
    "aimarket-mandate-request/1", HUB, "POST /ai-market/v2/invoke", child_digest, str(t), nonce,
    hashlib.sha256(body).hexdigest(),
])
request_signature = b64url(DELEGATE.sign(request_message.encode()))

account = "acct_0123456789abcdef"
link_message = "\n".join(["aimarket-owner-link/1", HUB, account, OWNER.did, str(t), nonce])
link_signature = b64url(OWNER.sign(link_message.encode()))

# A second owner key linked by an existing owner (§4): the change authorization the first
# owner signs, and the owner's own revocation of the root (§5.5).
SECOND = SigningKey.from_seed(hashlib.sha256(b"aimarket-mandate-vector-second-owner").digest())
change_nonce, revoke_nonce = "vector-nonce-000000000002", "vector-nonce-000000000003"
change_message = "\n".join(["aimarket-owner-change/1", HUB, account, "link", SECOND.did, "1",
                             str(t), change_nonce])
change_signature = b64url(OWNER.sign(change_message.encode()))
revoke_message = "\n".join(["aimarket-mandate-revoke/1", HUB, root_digest, str(t), revoke_nonce])
revoke_signature = b64url(OWNER.sign(revoke_message.encode()))

vectors = {
    "description": "AIMarket mandates — normative vectors (aimarket-protocol/mandates.md §9). Test keys only.",
    "hub_origin": HUB,
    "keys": {
        "owner": {"seed_hex": OWNER.seed_hex(), "did": OWNER.did},
        "agent": {"seed_hex": AGENT.seed_hex(), "did": AGENT.did},
        "delegate": {"seed_hex": DELEGATE.seed_hex(), "did": DELEGATE.did},
        "second_owner": {"seed_hex": SECOND.seed_hex(), "did": SECOND.did},
    },
    "root": {"document": root, "canonical_sha256": hashlib.sha256(canonicalize(root)).hexdigest(),
             "digest": root_digest},
    "child": {"document": child, "digest": child_digest},
    "request_proof": {
        "method": "POST",
        "path": "/ai-market/v2/invoke",
        "body": body.decode(),
        "t": t,
        "n": nonce,
        "leaf": child_digest,
        "message": request_message,
        "signature": request_signature,
        "header": f"t={t};n={nonce};s={request_signature}",
    },
    "owner_link": {
        "account_id": account,
        "did": OWNER.did,
        "t": t,
        "n": nonce,
        "message": link_message,
        "signature": link_signature,
    },
    "owner_change": {
        "account_id": account,
        "by": OWNER.did,
        "action": "link",
        "did": SECOND.did,
        "require_mandate": 1,
        "t": t,
        "n": change_nonce,
        "message": change_message,
        "signature": change_signature,
    },
    "revoke": {
        "digest": root_digest,
        "by": OWNER.did,
        "t": t,
        "n": revoke_nonce,
        "message": revoke_message,
        "signature": revoke_signature,
    },
}

out = Path(__file__).with_name("mandate-signed.json")
out.write_text(json.dumps(vectors, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} (root {root_digest}, child {child_digest})")
