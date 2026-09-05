# AIMarket Protocol — roadmap (0.x)

Early-stage open standard. **0.x means breaking changes are expected** until a 1.0 RFC freeze.

## v0.1.x (now)

- [x] JSON schemas for manifest, well-known, receipt, federation announce
- [x] Reference test vectors with Ed25519 examples
- [ ] Wider implementer feedback on v2 invoke + channel lifecycle

## v0.2.x (in progress)

- [x] Governance and IPR policy published ([GOVERNANCE.md](GOVERNANCE.md), [IPR.md](IPR.md))
- [x] Admission model specified — pending vs active, open vs closed (spec §2.4)
- [x] Reciprocal discovery specified — `X-AIMarket-Crawler` (spec §2.5)
- [x] Quarantined catalogue preview specified (spec §2.6)

- [x] Conformance runner ([conformance/run.py](conformance/run.py)) — offline vectors + live hub checks
- [x] Canonical signing bytes specified normatively (spec §7.3) — previously only in source
- [ ] Formal compatibility matrix (hub ↔ SDK ↔ widget)
- [x] Negative test vectors for tampering, wrong-signer and version downgrade — 9, generated from the positives ([test-vectors/negative/](test-vectors/negative/))
- [ ] Replay detection conformance — behavioural, needs live-hub checks; no static vector can catch a correctly signed receipt presented twice
- [ ] Published JSON Schema `$id` hosting on a stable CDN path

## v1.0 (future)

- [ ] RFC-style freeze, versioned error codes, migration guide from v1 wire
- [ ] Third-party conformance suite

Track work in [GitHub Issues](https://github.com/alexar76/aimarket-protocol/issues) — `good first issue` welcome.
