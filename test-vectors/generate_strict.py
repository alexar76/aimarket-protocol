#!/usr/bin/env python3
"""Vectors for §7.3.7 (strict Ed25519) and §7.3.8 (hybrid ML-DSA-65 signatures).

Derived from `receipt-signed.json` so they cannot drift from it. The ML-DSA keys come from fixed
seeds through FIPS 204 `key_derive`, so regeneration yields the same keys; signatures are hedged
and change on every run, which is fine — vectors pin keys and signatures, not signing randomness.

    python test-vectors/generate_strict.py      # needs cryptography and dilithium-py
"""
from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import pathlib

from dilithium_py.ml_dsa import ML_DSA_65

V = pathlib.Path(__file__).parent
OUT = V / "negative"
b64 = lambda raw: base64.b64encode(raw).decode()  # noqa: E731

_spec = importlib.util.spec_from_file_location("conformance_run", V.parent / "conformance" / "run.py")
run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run)


def pq_keypair(label: str) -> tuple[bytes, bytes]:
    return ML_DSA_65.key_derive(hashlib.sha256(label.encode()).digest())


def write(path: pathlib.Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(V)}")


def main() -> None:
    receipt = json.loads((V / "receipt-signed.json").read_text(encoding="utf-8"))
    canonical = run.receipt_canonical(receipt).encode()
    pk, sk = pq_keypair("aimarket-protocol test vector ml-dsa-65 key 1")
    other_pk, other_sk = pq_keypair("aimarket-protocol test vector ml-dsa-65 key 2 (not pinned)")
    pins = {"ed25519": run.TEST_PUBKEY_B64, "ml-dsa-65": b64(pk)}

    hybrid = copy.deepcopy(receipt)
    hybrid["signature"].update({"pq_algorithm": "ml-dsa-65", "pq_public_key": b64(pk),
                                "pq_value": b64(ML_DSA_65.sign(sk, canonical))})
    hybrid["_pins"] = pins
    write(V / "receipt-hybrid-signed.json", hybrid)

    def negative(name: str, doc: dict, reason: str, why: str, section: str, **extra) -> None:
        doc = copy.deepcopy(doc)
        doc["_pins"] = pins
        doc["_expect"] = {"result": "reject", "reason": reason, "why": why, "spec": section, **extra}
        write(OUT / name, doc)

    bad = copy.deepcopy(hybrid)
    raw = bytearray(base64.b64decode(bad["signature"]["pq_value"]))
    raw[100] ^= 0x01
    bad["signature"]["pq_value"] = b64(bytes(raw))
    negative("receipt-hybrid-pq-invalid.json", bad, "pq-signature-invalid",
             "The Ed25519 half is valid; one bit of the ML-DSA signature is flipped. A present "
             "pq_value MUST verify (§7.3.8 rule 3).", "§7.3.8")

    stripped = copy.deepcopy(hybrid)
    for key in ("pq_algorithm", "pq_public_key", "pq_value"):
        stripped["signature"].pop(key)
    negative("receipt-hybrid-pq-stripped.json", stripped, "pq-required-but-absent",
             "Every pq_* member was deleted. For a signer whose PQ signatures are required this is "
             "the downgrade an Ed25519 forger performs (§7.3.8 rule 2).", "§7.3.8", require_pq=True)

    substituted = copy.deepcopy(hybrid)
    substituted["signature"]["pq_public_key"] = b64(other_pk)
    substituted["signature"]["pq_value"] = b64(ML_DSA_65.sign(other_sk, canonical))
    negative("receipt-hybrid-pq-key-substituted.json", substituted, "pq-key-not-pinned",
             "The ML-DSA signature is valid under the key the object carries, which is not the "
             "signer's pinned PQ key (§7.3.8 rule 4).", "§7.3.8")

    small = copy.deepcopy(receipt)
    identity = bytes.fromhex("01" + "00" * 31)
    base_point = bytes.fromhex("58" + "66" * 31)
    small["signature"] = {"algorithm": "ed25519", "public_key": b64(identity),
                          "value": b64(base_point + (1).to_bytes(32, "little"))}
    negative("receipt-small-order-key.json", small, "small-order-key",
             "Signed under the identity key with R = base point, S = 1: valid for EVERY message "
             "under OpenSSL, tweetnacl and WebCrypto, and no private key exists. A verifier MUST "
             "refuse a small-order key or R (§7.3.7).", "§7.3.7")


if __name__ == "__main__":
    main()
