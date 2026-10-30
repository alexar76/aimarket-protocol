# IETF Internet-Drafts

Two drafts, split from the single federation draft that lived here until 2026-10-30, so that
each lands in the scope of the body that owns its layer:

| File | Subject | Category | Where it is aimed |
|---|---|---|---|
| `draft-artamokhov-dawn-marketplace-discovery-00.md` | the discovery document at a well-known URI, the signed catalogue, key pinning, the `ed25519-pipe-2` signature profile (= spec §2.1, §7.3.1–7.3.2, §7.3.7) | Standards Track | inside the DAWN WG charter: public properties of an AI resource + integrity of discovery information |
| `draft-artamokhov-dawn-index-federation-00.md` | crawl, reciprocal identification, announcement, admission (pending ≠ admitted), catalogue preview (= spec §2.2–2.6) | Experimental | input to DAWN's gap analysis — `draft-jimenez-dawn-discovery-landscape` §6.2 names "no interoperable federation between directories" |

The IETF formed the **DAWN working group** (Discovery of Agents, Workloads, and Named
entities) on 2026-10-22: chairs Dapeng Liu and Frank Brockners, AD Éric Vyncke, list
`dawn@ietf.org`. Its phase-one charter covers initial discovery and integrity and excludes
catalogues, Internet-wide search, identity and trust — which is why the material is split as
above rather than submitted as one document.

## Status

Author fields filled on 2026-10-30 (A. Artamokhov, alexar76@rambler.ru — the repository's git identity). Submission
state is recorded below this line as it happens.

- **2026-10-30 (datatracker shows 2026-10-29 UTC):** both drafts uploaded through the datatracker web form,
  passed the submission checks (idnits: 1 warning each, nothing blocking), submitter set to the author.
  Status **Awaiting Submitter Authentication**: a confirmation email went to alexar76@rambler.ru for each;
  the drafts are posted when those links are followed. Status pages:
  `https://datatracker.ietf.org/submit/status/171295/` (discovery), `https://datatracker.ietf.org/submit/status/171296/`
  (federation). Trap: the post form's `replaces` field must be omitted, not sent empty.
- **2026-10-30 06:51 UTC — POSTED.** The author confirmed both emails; the datatracker lists
  https://datatracker.ietf.org/doc/draft-artamokhov-dawn-marketplace-discovery/ and
  https://datatracker.ietf.org/doc/draft-artamokhov-dawn-index-federation/ at revision 00. They expire
  on 2027-05-03 unless a -01 is posted; the next step is the note to dawn@ietf.org.
- The datatracker API (`/api/submission`) needs a datatracker account on the author's email; without one it
  answers `No such user`. The web form needs no account.

## Build

`./build.sh` renders every `draft-*.md` here to XML, text and HTML in `ietf/build/`
(git-ignored). It uses `kramdown-rfc` from the Homebrew Ruby (`/opt/homebrew/opt/ruby`,
Ruby ≥ 3.2 — the system Ruby 2.6 cannot run it) and installs `xml2rfc` into
`ietf/.venv-xml2rfc` on first run. Both drafts built on 2026-10-30 with no errors and one cosmetic
width warning on the example document.

Without the toolchain, https://author-tools.ietf.org/ accepts the `.md` directly, returns XML,
text and HTML, and runs `idnits`. Either way the XML is what goes to
https://datatracker.ietf.org/submit/.

`ipr: trust200902` in the front matter generates the "Status of This Memo" and Copyright
Notice. **Do not hand-write that boilerplate** — a draft missing or mangling it is rejected
outright.

## Timing

IETF 127 is 14–20 November 2026 (San Francisco). The Internet-Draft cut-off is the Monday two
weeks before the meeting — **2 November 2026, 23:59 UTC** — check "Important dates" on the
datatracker meeting page. Between the cut-off and the end of the meeting no drafts are
accepted; from 21 November submissions reopen. Missing the cut-off costs three weeks, nothing
more.

After submission: ten lines to `dawn@ietf.org` (subscribe at
https://mailman3.ietf.org/mailman3/lists/dawn.ietf.org/) naming both drafts and the live
instance. No presentation slot is needed; the archive of the list and the datatracker entry
are the durable record. `draft-kay-dawn-use-cases-01` §8 carries "TBD" slots for use-case
classes; "cooperating capability indexes exchanging catalogues" is the one these drafts fill.

## What to expect

- **No working group adoption is required** to submit. Anyone may submit
  `draft-<surname>-<subject>-00`. Only names beginning `draft-ietf-<wg>-` need chair approval.
- **Drafts expire after 185 days.** Expiry is normal and not a rejection; repost a `-01`.
- Submitting is not publishing. It makes the text citable, dated and public, which is the
  point at this stage.
- **The space is crowded.** Roughly a dozen individual drafts sit adjacent to agent discovery
  (AIDIP, ADP, DNS-AID, AID, ARDP, AGNTCY ADS, …). Each draft's §1.1 says plainly what it does
  *not* specify; do not trim it.
- **The Implementation Status sections contain an admission.** Both say in bold that no
  independent implementation exists. A reviewer who discovers that unaided will discount
  everything else; removing the sentence would be the single most damaging edit available.

## Relationship to the rest of this repository

Both drafts are rewritten from `../spec.md` to IETF conventions and stripped of everything
specific to one implementation. Where the two disagree, `spec.md` is what the reference
implementation follows; the drafts are what is being proposed for wider review. They are kept
deliberately separate so that a change to the protocol does not silently become a change to a
submitted document.

Intentional differences:

- Well-known suffix `agent-marketplace`, not `ai-market.json`; header field
  `Agent-Marketplace-Crawler`, not `X-AIMarket-Crawler` (RFC 6648). The reference hub serves,
  sends and accepts both spellings since 2026-10-30 (`aimarket_hub/discovery_names.py`,
  hub docs `discovery-names.md`); `conformance/run.py --hub` checks the draft path and skips,
  not fails, on a hub that serves only the legacy one.
- Member names `catalogue_url` / `capabilities` in place of `manifest_url` / `tools`; the
  canonical string keeps the pair name `tools_hash`, so signatures are byte-identical under
  both. The discovery draft's appendix carries the mapping table.
- The discovery draft names the deployed canonicalisation `ed25519-pipe-2` and says in §5.3
  that moving to RFC 8785 would be a new profile name, decided by a working group.
- The federation draft's announcement message uses `index_url` / `discovery_url`; the canonical
  string keeps `hub_url` / `well_known_url` as pair names for the same reason.
