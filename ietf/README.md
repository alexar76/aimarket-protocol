# IETF Internet-Draft

`draft-aimarket-agent-marketplace-federation-00.md` — the federated discovery and admission
mechanism of this protocol, written as an Internet-Draft for submission as an **independent
submission**.

## Status

**Not submitted.** The text is complete and the placeholders below need real values first.
This directory exists so that the draft is reviewable and versioned alongside the
implementation it describes, which is the part reviewers ask about.

## Before submitting — replace these

| Placeholder | Value |
|---|---|
| `AUTHOR` in `docname` | Your surname, lowercase, no spaces — the file becomes `draft-<surname>-agent-marketplace-federation-00` |
| `A. AUTHOR` / `AUTHOR NAME` | Initials and full name |
| `AUTHOR@EXAMPLE.COM` | A working email; it is published |
| `organization: Independent` | Keep for an individual submission |

## Build it

```bash
gem install kramdown-rfc2629
kramdown-rfc draft-aimarket-agent-marketplace-federation-00.md > draft.xml
# then render locally, or upload the .xml at https://datatracker.ietf.org/submit/
```

`ipr: trust200902` in the front matter is what generates the "Status of This Memo" and
Copyright Notice. **Do not hand-write that boilerplate** — a draft missing or mangling it is
rejected outright, with no fixup by the Secretariat.

## What to expect

- **No working group adoption is required.** Anyone may submit `draft-<surname>-<subject>-00`
  themselves. Only names beginning `draft-ietf-<wg>-` need chair approval.
- **Drafts expire after 185 days.** Expiry is normal and not a rejection; you repost a `-01`.
- Submitting is not publishing. It makes the text citable, dated and public, which is the
  point at this stage.

## Two things worth knowing before spending the effort

**The space is crowded.** A survey while preparing this found roughly ten active drafts
directly adjacent to agent discovery and agent-to-agent interaction. A draft that does not
say plainly what it does *not* specify — payment, identity, reputation, invocation — will be
read as one more entrant in a race rather than as the layer between the entrants. Section 1.1
exists for that reason and should not be trimmed.

**The Implementation Status section is the strongest part and it contains an admission.**
{{RFC7942}} sections are read closely, and this one says the network is not yet
multi-operator. That is a genuine weakness and stating it is deliberate: the mechanisms are
running, the property they exist to produce has not been demonstrated between independent
parties, and a reviewer who discovers that themselves will discount everything else in the
document. Removing the sentence would be the single most damaging edit available.

## Relationship to the rest of this repository

The draft is a subset of [`../spec.md`](../spec.md) — specifically §2.1–2.6 — rewritten to
IETF conventions and stripped of everything specific to one implementation. Where the two
disagree, `spec.md` is what the reference implementation follows; the draft is what is being
proposed for wider review. They are kept deliberately separate so that a change to the
protocol does not silently become a change to a submitted document.

Notable differences, all intentional:

- The well-known suffix is `agent-marketplace`, not `ai-market`. A registry entry should not
  carry one project's brand.
- The header field is `Agent-Marketplace-Crawler`, not `X-AIMarket-Crawler`. `X-` prefixes
  are deprecated by RFC 6648, and an implementation submitting this should plan to accept
  both names during any transition.
