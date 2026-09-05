# Governance

How this specification changes, who decides, and what a reader is entitled to rely on.

## Status, stated plainly

AIMarket Protocol is currently maintained by a **single editor**. Calling that a
"working group" would be a lie a reader could check in thirty seconds of commit history,
and a specification that misrepresents its own governance has no business asking anyone to
depend on it.

What that means in practice: decisions are fast, and the bus factor is one. §6 describes
the conditions under which that stops being true, and it is a commitment rather than an
aspiration.

## Roles

| Role | Who | What they may do |
|---|---|---|
| **Editor** | The maintainer of this repository | Merge changes, cut releases, decide when discussion has converged |
| **Contributor** | Anyone who opens an issue or PR | Propose anything, including changes the editor dislikes |
| **Implementer** | Anyone running a hub, SDK or client that speaks this protocol | Everything a contributor may do, plus the standing right described below |

**The implementer's standing right.** An implementer who reports that a normative
requirement is unimplementable, ambiguous or contradicted by another section is entitled
to a written answer in the issue — either a fix, or an explanation of why the text is
correct. "Works in the reference implementation" is not an answer to that report; the
reference implementation is one data point, and where it and the specification disagree,
at least one of them is wrong.

## How the specification changes

1. **Propose** — open an issue describing the problem before the solution. Text that
   arrives as a finished PR without a stated problem gets asked for the problem first.
2. **Discuss** — normative changes stay open for comment for **14 days** unless every
   known implementer has already responded. Editorial fixes (typos, clarifications that
   change no behaviour) merge immediately.
3. **Implement** — see the rule below.
4. **Merge and version** — the editor merges, updates the version per § Versioning and records the
   change in the release notes.

### No normative change without an implementation

A change to a MUST, MUST NOT, SHOULD or wire format is not merged until at least one
implementation has run it. A specification written ahead of its implementations
accumulates requirements that are impossible, expensive or meaningless, and every one of
them is discovered by the first person who tries to build against it — by which point the
text is already published.

This rule is the reason for `test-vectors/`. A wire-format change that cannot produce a
test vector is not specified precisely enough to merge.

## What "normative" means here

Only text using RFC 2119 keywords — MUST, MUST NOT, REQUIRED, SHALL, SHOULD, MAY — is
normative. Examples, rationale, and anything in a note or appendix marked non-normative
are explanatory. Where an example contradicts normative text, the normative text wins and
the example is a bug worth reporting.

## Versioning — two numbers, two meanings

They are separate on purpose, and conflating them has already caused confusion:

| Number | Where | What it tracks |
|---|---|---|
| **Protocol version** — currently `2.0.0-draft` | `spec.md` header, `protocol_versions` in `.well-known` | The wire contract. A peer speaks `v1`, `v2`, or both. |
| **Repository version** — currently `0.1.0` | `VERSION` | This repository's releases: schemas, vectors, editorial revisions. |

The repository can release many times without the protocol version moving. The protocol
version moves only when the wire contract does.

`0.x` on the repository means **breaking changes are expected** until the 1.0 freeze
described in `ROADMAP.md`. Implementers should pin an exact version and read release
notes before upgrading.

### Compatibility rules once the protocol reaches 1.0

- A new **optional** field, endpoint or header is a MINOR change. Peers that ignore it
  must keep working, and any peer that breaks on an unknown field is non-conformant.
- Removing or changing the meaning of anything normative is a MAJOR change and requires a
  new `protocol_versions` entry, so a peer can negotiate rather than guess.
- Security fixes may break compatibility in a PATCH release. This exception is deliberate
  and narrow: a wire format with a hole in it is not a compatibility promise worth keeping.

## Conformance

Until the conformance suite in `ROADMAP.md` v1.0 exists, no implementation — including the
reference hub — may be described as "certified" or "conformant" by this project. It may be
described as *interoperating with* a named peer, which is a claim anyone can check.

Passing `test-vectors/` is necessary and not sufficient: the vectors cover signature and
serialization, not behaviour.

## Disagreement

If the editor rejects a proposal and the proposer believes the rejection is wrong, the
disagreement is recorded in the issue and the issue stays open with a `disputed` label
rather than being closed. An open record of what the maintainer decided against is more
useful to a future implementer than a clean issue tracker.

Because the project is permissively licensed (Apache-2.0 OR MIT), the ultimate remedy is
always available: fork the
spec, implement it, and let the network choose. That is a feature.

## When this document changes

This project moves to shared governance under a neutral body — a W3C Community Group, an
IETF working group, or a foundation — **when three implementations exist that are not
operated by the maintainer**. Not "when it seems appropriate": three, counted, and at
least two of them not derived from the reference implementation.

The reason is honest self-interest. A protocol whose editor also runs the largest hub has
an incentive problem that no amount of good intent resolves, and the moment other people
have skin in it, the governance should stop being one person's.

Until then, this file describes what actually happens, and it gets updated when that
changes rather than when it would look better.
