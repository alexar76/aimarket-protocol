<!-- aicom-mirror-notice -->
> **📖 Read-only mirror.** `aimarket-protocol` is published from the canonical AI-Factory monorepo.
> **Pull requests are not accepted** — any commit pushed here is overwritten by
> `scripts/mirror_satellites.sh` on the next sync.
> 🐞 Found a bug or have a request? Please **[open an issue](https://github.com/alexar76/aimarket-protocol/issues)**.

# AIMarket Protocol v2 — Federation

<!-- aicom-readme-badges -->
<p align="center">
  <a href="https://github.com/alexar76/aimarket-protocol/actions/workflows/ci.yml"><img src="https://raw.githubusercontent.com/alexar76/aimarket-protocol/refs/heads/main/docs/badges/ci.svg" alt="CI" /></a>
  <a href="https://raw.githubusercontent.com/alexar76/aimarket-protocol/refs/heads/main/docs/badges/coverage.svg"><img src="https://raw.githubusercontent.com/alexar76/aimarket-protocol/refs/heads/main/docs/badges/coverage.svg" alt="Test coverage" /></a>
  <a href="https://github.com/alexar76/aimarket-protocol/blob/main/LICENSE"><img src="https://raw.githubusercontent.com/alexar76/aimarket-protocol/refs/heads/main/docs/badges/license.svg" alt="License: Apache-2.0 OR MIT" /></a>
</p>
<!-- /aicom-readme-badges -->

> **Ecosystem:** [AICOM overview & live demos](https://modeldev.modelmarket.dev) · **Protocol version:** `2.0.0-draft` (the wire contract) · **Repository version:** `0.1.0` ([VERSION](VERSION)) — two axes, see [GOVERNANCE.md](GOVERNANCE.md#versioning--two-numbers-two-meanings) · **Community:** [Discord · Pollux](https://discord.gg/aimarket) · [Telegram · Castor](https://t.me/just_for_agents)

**Status:** Draft — protocol `2.0.0-draft`, repository `0.1.0`  

## Documents

| Document | Description |
|----------|-------------|
| [spec.md](spec.md) | Full protocol specification (RFC-style) |
| [GOVERNANCE.md](GOVERNANCE.md) | Who decides, how the spec changes, what "conformant" may not be claimed yet |
| [IPR.md](IPR.md) | Dual licensing, the contributor patent grant, and what is explicitly NOT granted |
| [ecosystem.md](ecosystem.md) | **Ecosystem map** — Mermaid diagrams (topology, invoke, federation, plugins) |
| [oracles](https://github.com/alexar76/oracles) | **Reference oracle family** — signed capabilities implementing Protocol v2 (Platon, Chronos, …) |
| [schemas/well-known.json](schemas/well-known.json) | JSON Schema for `.well-known/ai-market.json` |
| [schemas/manifest.json](schemas/manifest.json) | JSON Schema for capability manifest |
| [schemas/receipt.json](schemas/receipt.json) | JSON Schema for signed receipts |
| [schemas/federation-announce.json](schemas/federation-announce.json) | Federation announcement message |
| [test-vectors/](test-vectors/) | **Normative** signed vectors + [negative vectors](test-vectors/negative/) that MUST be rejected |
| [conformance/run.py](conformance/run.py) | Conformance runner — vectors offline, or `--hub <url>` against a live hub |

## Live Reference Implementation

**[modelmarket.dev](https://modelmarket.dev)** — production hub running this protocol:

| Resource | URL |
|----------|-----|
| .well-known | [modelmarket.dev/.well-known/ai-market.json](https://modelmarket.dev/.well-known/ai-market.json) |
| Widget demo | [modelmarket.dev/widget/demo](https://modelmarket.dev/widget/demo) |
| AI Economy live | [modelmarket.dev/live](https://modelmarket.dev/live) |
| Integration examples | [modelmarket.dev/examples](https://modelmarket.dev/examples) |

## Quick Start

```bash
# Live hub:
curl https://modelmarket.dev/.well-known/ai-market.json

# Federated search:
curl "https://modelmarket.dev/ai-market/v2/search?intent=translate&budget=3.00"

# Open channel + invoke + close:
CH=$(curl -s -X POST https://modelmarket.dev/ai-market/v2/channel/open \
  -H "Content-Type: application/json" \
  -d '{"deposit_usd":3.0}' | jq -r '.channel.channel_id')

curl -X POST https://modelmarket.dev/ai-market/v2/invoke \
  -H "X-Payment-Channel: $CH" \
  -d '{"product_id":"prod-translate","capability_id":"translate.multi@v2","source_hub":"local","input":{"text":"hello"}}'

curl -X POST https://modelmarket.dev/ai-market/v2/channel/close \
  -d "{\"channel_id\":\"$CH\"}"
```

## Protocol Versions

| Version | Scope |
|---------|-------|
| v1 | Single marketplace: .well-known, MCP manifest, 402 flow, channels, pipelines |
| v2 | Federation: cross-hub crawl, index, search, route, reputation |

## Demo

- **Live:** https://modelmarket.dev/ (reference hub implementing v2)
- **Docs:** https://github.com/alexar76/aimarket-protocol/blob/main/spec.md

## Related repos

| Repo | Role |
|------|------|
| [aimarket-hub](https://github.com/alexar76/aimarket-hub) | Reference v2 implementation |
| [aimarket-sdks](https://github.com/alexar76/aimarket-sdks) | Client SDKs |
| [oracles](https://github.com/alexar76/oracles) | Signed capability family on v2 |
| [aicom](https://github.com/alexar76/aicom) | AI-Factory monorepo |
| [dioscuri](https://github.com/alexar76/dioscuri) | Twin community agents — MNEMOSYNE Q&A |

## Community

The [DIOSCURI](https://github.com/alexar76/dioscuri) twins answer questions from synced GitHub docs.

| Channel | Twin | Best for |
|---------|------|----------|
| [Discord](https://discord.gg/aimarket) | Pollux | Help, ideas, show-and-tell |
| [Telegram](https://t.me/just_for_agents) | Castor | Releases, digests, quick news |

**Ecosystem map:** [Alien Monitor](https://monitor.modelmarket.dev/) · [AICOM](https://magic-ai-factory.com)
