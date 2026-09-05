# Intellectual property policy

What you are allowed to do with this specification, what contributors grant, and one
question the project has not yet answered.

> **Not legal advice.** This file states the project's intent and the licences actually in
> force. An organisation with real exposure should have its own counsel read it.

## The specification

`spec.md`, the JSON Schemas in `schemas/`, and the vectors in `test-vectors/` are
**dual-licensed: Apache-2.0 OR MIT**, at your option.

    SPDX-License-Identifier: Apache-2.0 OR MIT

Full texts: [`LICENSE-APACHE`](LICENSE-APACHE), [`LICENSE-MIT`](LICENSE-MIT).
[`LICENSE`](LICENSE) points at both.

Take whichever suits you; you do not need both, and you never need permission to choose.

You may implement this protocol, in any language, for any purpose, commercial or not,
without asking, notifying or paying anyone. You may fork the specification, publish a
modified version, and compete with the reference implementation. No conformance mark, no
membership and no fee stands between a reader and an implementation.

Two limits worth stating so nobody has to infer them:

- **No trademark licence.** Neither licence grants trademark rights: MIT is silent on
  names, and Apache-2.0 §6 excludes them expressly. It does not grant the right
  to call a product "AIMarket" or to imply endorsement. Say your product *implements the
  AIMarket Protocol* — that is a factual claim and is always permitted.
- **No certification.** See `GOVERNANCE.md` § Conformance. Nobody may describe an
  implementation as certified by this project, because there is nothing to certify against
  yet.

## Why two licences

MIT is the licence most implementers have already cleared internally, and it is what this
specification shipped under first. It grants copyright permission and says nothing about
patents.

That silence is a known problem for a *specification*, and a bigger one than it is for
ordinary code: the entire purpose of a standard is that many independent parties implement
the same thing, and in doing so they all step into the same patent claims. A reader
evaluating that exposure should not have to guess.

Apache-2.0 answers it directly. Its §3 is an express patent licence from every contributor,
with a defensive termination clause for anyone who initiates patent litigation over the
work. Offering it alongside MIT closes the gap without withdrawing anything from anyone who
already relies on MIT.

The reference hub (`aimarket-hub`) is Apache-2.0, so implementers taking code from it have
that grant over the code as well as the specification.

## Contributions

By opening a pull request against this repository you confirm that:

1. You have the right to submit the work.
2. You license it under the same terms as the work — **Apache-2.0 OR MIT**. Unless you
   state otherwise in the pull request, a contribution intentionally submitted for
   inclusion is dual licensed as above, with no additional terms or conditions.
3. To the extent you own or control patent claims that are **necessarily infringed by
   implementing the contribution as merged**, you grant every implementer a perpetual,
   worldwide, royalty-free, non-exclusive licence to those claims for the purpose of
   implementing this specification. This mirrors Apache-2.0 §3 and applies whichever of the
   two licences a given implementer chooses, so a downstream MIT user is not left without
   the grant.

Clause 3 is a **defensive** grant: it covers what your own contribution makes unavoidable,
and nothing else. It is deliberately narrower than a blanket patent licence, and it
terminates for any party that initiates patent litigation alleging that this specification
or an implementation of it infringes a patent.

No copyright assignment is requested. Contributors keep their copyright, and
`CONTRIBUTORS.md` records who they are.

## Resolved: the patent gap in a specification licensed only under MIT

**Status: resolved 2026-08-28 by dual licensing. Recorded here rather than deleted, because
an implementer who read the earlier version deserves to see what changed and why.**

The problem was real. MIT grants copyright permission and is silent on patents. Standards
bodies close that silence deliberately — W3C with a royalty-free policy, IETF with
disclosure rules, and many projects simply by choosing a licence that carries the grant.
This specification did none of those, and said so.

Three options were on the table:

1. **Dual-license Apache-2.0 OR MIT.** ← adopted
2. Publish a standalone royalty-free non-assertion covenant.
3. Move the specification to a body with its own IPR policy.

Option 1 was taken because it is the smallest change with the largest coverage: existing
MIT users lose nothing, implementers needing a patent grant simply select Apache-2.0, and
no new bespoke legal instrument has to be written, published and trusted. Option 3 remains
the endgame described in `GOVERNANCE.md` § When this document changes and is not displaced by this — a body's IPR
policy would sit on top of these licences, not replace them.

To the maintainer's knowledge the project holds no patents and has applied for none, and no
third party has disclosed a patent claim over this specification. That is a statement of
fact today; the licence, not the statement, is what an implementer relies on.

## Disclosure

If you believe a patent — yours or anyone's — reads on this specification, open an issue
titled `IPR disclosure`. Disclosures are published, never handled privately. A standard
with a quietly known patent problem is worse than one with a publicly known one.
