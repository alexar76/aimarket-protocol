#!/usr/bin/env python3
"""Generate the receipt binding vector (spec §7.3.9). Deterministic: re-running it rewrites
receipt-binding-signed.json byte for byte. Uses the RFC 8032 test seed of generate.py;
DO NOT USE THIS KEY IN PRODUCTION."""

import base64
import hashlib
import json
import pathlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HERE = pathlib.Path(__file__).resolve().parent
SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
priv = Ed25519PrivateKey.from_private_bytes(SEED)
PUBLIC_KEY_B64 = base64.b64encode(priv.public_key().public_bytes_raw()).decode()

BINDING_FIELDS = (
    "v", "hub", "receipt_nonce", "receipt_signer", "input_sha256",
    "output_member", "output_sha256", "client_nonce", "timestamp",
)


def sha256_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def binding_canonical(binding: dict) -> str:
    return "receipt_binding:1|" + sha256_json({k: binding.get(k) for k in BINDING_FIELDS})


receipt = json.loads((HERE / "receipt-signed.json").read_text())
request_input = {"text": "Grüß Gott", "target": "en"}
response = {
    "success": True,
    "result": {"translation": "Good day", "detected": "de"},
    "receipt": receipt,
}
binding = {
    "v": 1,
    "hub": "https://test-hub.example.com",
    "receipt_nonce": receipt["nonce"],
    "receipt_signer": PUBLIC_KEY_B64,
    "input_sha256": sha256_json(request_input),
    "output_member": "result",
    "output_sha256": sha256_json(response["result"]),
    "client_nonce": "agent-task-0042",
    "timestamp": "2026-10-30T12:00:00Z",
}
canonical = binding_canonical(binding)
binding["signature"] = {
    "algorithm": "ed25519",
    "public_key": PUBLIC_KEY_B64,
    "value": base64.b64encode(priv.sign(canonical.encode())).decode(),
}
response["receipt_binding"] = binding

vector = {
    "description": "Receipt binding (spec §7.3.9): the request input, the answer's output member "
                   "and the client nonce, signed by the hub that answered.",
    "request": {"headers": {"X-Client-Nonce": "agent-task-0042"}, "input": request_input},
    "response": response,
    "canonical": canonical,
    "public_key": PUBLIC_KEY_B64,
}
(HERE / "receipt-binding-signed.json").write_text(json.dumps(vector, indent=2, ensure_ascii=False) + "\n")
print("canonical:", canonical)
print("Wrote receipt-binding-signed.json")
