---
title: "A Discovery Document and Signed Catalogue for Capability Marketplaces"
abbrev: "Marketplace Discovery"
docname: draft-artamokhov-dawn-marketplace-discovery-04
category: std
ipr: trust200902
submissiontype: IETF
area: Internet
workgroup: Network Working Group
date: 2026-11-04
keyword:
  - agents
  - discovery
  - marketplace
  - well-known
  - signed catalogue
stand_alone: yes
pi: [toc, sortrefs, symrefs]
author:
  -
    ins: A. Artamokhov
    name: Aleksandr Artamokhov
    organization: Independent
    email: alexar76@rambler.ru
normative:
  RFC3339:
  RFC3986:
  RFC4648:
  RFC6234:
  RFC8032:
  RFC8259:
  RFC8615:
  RFC9110:
  RFC9364:
informative:
  RFC7942:
  RFC8785:
  RFC9727:
  I-D.jimenez-dawn-discovery-landscape:
  I-D.farrel-dawn-terminology:
  I-D.mozleywilliams-dawn-dnsaid:
  I-D.raskar-agentic-web-federated-resolution:
  DAWN-CHARTER:
    title: "Discovery of Agents With Names (dawn), charter-ietf-dawn-01"
    target: https://datatracker.ietf.org/doc/charter-ietf-dawn/
    author:
      -
        org: IETF
    date: 2026-10
  DAWN-SCOPE:
    title: "About the DAWN charter"
    target: https://mailarchive.ietf.org/arch/msg/dawn/EFmwgnuukscABvacJiulowm2uss/
    author:
      -
        ins: E. Vyncke
        name: Eric Vyncke
    date: 2026-11-02
    seriesinfo:
      "message to the": dawn@ietf.org mailing list
  MDI:
    title: "Minimum Public Discovery Information: Requirements and Common Semantics"
    author:
      -
        ins: Y. Cui
      -
        ins: K. Yao
    date: 2026-11
    seriesinfo:
      Internet-Draft: draft-cui-dawn-mdi-model-02
  FEDERATION:
    title: "Federation Between Capability Indexes: Crawl, Reciprocal Identification and Admission"
    author:
      -
        ins: A. Artamokhov
    date: 2026-11
    seriesinfo:
      Internet-Draft: draft-artamokhov-dawn-index-federation-02
  A2A:
    title: "Agent2Agent (A2A) Protocol Specification, version 1.0"
    target: https://a2a-protocol.org/latest/specification/
    date: 2026-03
  MCPREG:
    title: "Model Context Protocol Registry"
    target: https://registry.modelcontextprotocol.io/
    date: 2026
  X402:
    title: "x402 Payment Protocol Specification, version 2"
    target: https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md
    date: 2025-12
  VECTORS:
    title: "AIMarket Protocol v2 test vectors and conformance runner"
    target: https://github.com/alexar76/aimarket-protocol/tree/main/test-vectors
    date: 2026
--- abstract

This document defines a JSON discovery document, served at a well-known URI, that tells a
client where a capability index publishes its catalogue and which protocol versions the index
serves, and identifies the key that signs the catalogue. It also states the requirements for
that signed catalogue and defines one signature profile; these are work adjacent to the DAWN
charter. Discovery between indexes, catalogue exchange, trust, and search or selection among
catalogued capabilities are out of scope.

--- middle

# Introduction

Capability indexes (catalogues of invocable services offered by many providers) are now
operated by many independent parties, alongside protocols for machine payment {{X402}},
agent-to-agent interaction {{A2A}} and tool registries {{MCPREG}}. A client that wants to use
an index needs a few public facts about it: a name, the protocol versions in use, where the
catalogue is, and which key signs the catalogue.

{{I-D.jimenez-dawn-discovery-landscape}} describes the current mechanisms for publishing such
facts. Each defines its own well-known resource and schema, and signed catalogues rarely
specify the exact bytes that are signed. This document defines one discovery document and
requires any signature profile used with it to specify the signed bytes. {{mdi}} maps the
discovery document onto the information model in {{MDI}}.

Catalogue exchange between indexes and peer admission are described separately in
{{FEDERATION}}.

## Scope

This document specifies:

* a discovery document served at a well-known URI ({{discovery}});
* requirements for the catalogue referenced from it ({{catalogue}}), including requirements
  for any signature profile, and one profile ({{profile}});
* key pinning by readers ({{keys}});
* checks of catalogue freshness by readers ({{freshness}}).

It does not specify how indexes find each other, how catalogues are exchanged, searched or
ranked, how capabilities are invoked or paid for, how providers are identified, or reputation.

## Relation to the DAWN charter {#dawn}

The DAWN working group charter {{DAWN-CHARTER}} limits discovery to obtaining the minimum
public discovery information for an AI resource, which may be "a service such as a catalog
that will further the discovery process". It excludes open-ended search, semantic
matchmaking, ranking, and selection of a resource by capability or user intent, and, in the
initial phase, catalogs of capabilities and the indexing and searching of AI resources across
the wider Internet. {{I-D.farrel-dawn-terminology}} defines discovery in the same way.

The responsible Area Director has explained the intended reading of the charter
{{DAWN-SCOPE}}: discovery in DAWN means learning how to connect to a resource, and the
properties it covers are those needed to select a means of communication, such as a
protocol, in the way the "alpn" parameter of an SVCB record does.

In those terms:

* within the charter: the location of the catalogue (`catalogue_url`), the protocol versions
  the index serves (`protocol_versions`), from which a reader selects the protocol it uses,
  and the DNS record that leads to the discovery document ({{dns}}). The `name` member is
  only a display label;
* adjacent work: the other members of the discovery document. `capabilities_count`
  describes what the index offers, `peers` serves the indexing of other indexes
  ({{FEDERATION}}), and `signer_public_key`, `signature_profile` and `generated_at` serve
  the catalogue. The catalogue itself ({{catalogue}}), its signature profile ({{profile}}),
  key pinning ({{keys}}) and the freshness checks ({{freshness}}) are adjacent work too.
  They are in this document because a reader needs them to authenticate the catalogue that
  the discovery document points to. How a catalogue is searched, and how a capability in it
  is selected, is not specified here.

## Requirements Language

{::boilerplate bcp14-tagged}

## Terminology

Index:
: A server that catalogues capabilities and answers queries about them.

Capability:
: A named, invocable unit of work offered by a provider and catalogued by an index.

Catalogue:
: The signed document, referenced from the discovery document, that lists an index's
  capabilities.

Discovery document:
: The JSON document defined in {{discovery}}.

Reader:
: Any party that retrieves the discovery document or the catalogue.

Signature profile:
: A named set of rules that defines the signature algorithm, the signed bytes and the
  verification procedure for a catalogue.

# Discovery document {#discovery}

An index MUST serve a discovery document at the well-known URI
`/.well-known/agent-marketplace` ({{RFC8615}}, {{iana-wk}}) using the "https" scheme. It
MUST answer both GET and HEAD requests for it, and SHOULD support conditional requests
({{RFC9110}}, Section 13).

The document is a JSON object {{RFC8259}} with media type `application/json`. The following
members are defined:

| Member | Type | Requirement |
|---|---|---|
| `name` | string | REQUIRED |
| `protocol_versions` | array of string | REQUIRED |
| `catalogue_url` | string (URI) | REQUIRED |
| `signer_public_key` | string | REQUIRED when the catalogue is signed |
| `signature_profile` | string | REQUIRED when the catalogue is signed |
| `capabilities_count` | number | RECOMMENDED |
| `generated_at` | string (date-time) | RECOMMENDED |
| `peers` | array of string (URI) | OPTIONAL |

`name`:
: A human-readable label chosen by the operator. Names are not unique, and a reader MUST NOT
  use a name as an identifier.

`protocol_versions`:
: The versions of the catalogue and query interfaces that the index serves, as opaque
  strings. A reader that recognises none of them MUST NOT use the index.

`catalogue_url`:
: An absolute "https" URI {{RFC3986}} of the catalogue ({{catalogue}}). It MAY be on a
  different host from the discovery document.

`signer_public_key`, `signature_profile`:
: The public key that signs the catalogue, encoded as the profile specifies, and the name of
  that profile ({{profile}}). Readers handle the key as described in {{keys}}.

`capabilities_count`, `generated_at`:
: The number of catalogue entries when the document was generated, and the generation time
  ({{RFC3339}}). They are informative; a reader MUST NOT treat a mismatch with the catalogue as an error.

`peers`:
: Discovery-document URIs of other indexes that the operator publishes. This document gives
  them no further meaning; {{FEDERATION}} restricts what a federating index lists here.

A reader MUST ignore members it does not recognise and MUST NOT reject a document because it
contains them. A member defined by this document MUST
NOT change type or meaning in a later revision; a different meaning requires a new member.

## Example

~~~
{
  "name": "Example Capability Hub",
  "protocol_versions": ["v1", "v2"],
  "catalogue_url": "https://hub.example/catalogue",
  "signer_public_key": "11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo=",
  "signature_profile": "ed25519-pipe-2",
  "capabilities_count": 47,
  "generated_at": "2026-10-30T09:00:00Z",
  "peers": [
    "https://other.example/.well-known/agent-marketplace"
  ]
}
~~~

## Relation to api-catalog

{{RFC9727}} defines `/.well-known/api-catalog`, in which a host lists its own APIs. The
discovery document describes an index that lists capabilities of other hosts and identifies
the key that signs that list. An index MAY publish both.

## Locating the document through DNS {#dns}

{{I-D.mozleywilliams-dawn-dnsaid}} defines an organizational index record at
`_index._agents.<domain>` that points to a catalog, agent registry or database, and leaves
the content served there out of its scope. An index operator can publish that record for its
own domain with the well-known suffix of the discovery document:

~~~
_index._agents.hub.example. 3600 IN SVCB 1 hub.example. (
    alpn=h2 well-known=agent-marketplace )
~~~

The parameter names follow {{I-D.mozleywilliams-dawn-dnsaid}}. A reader that finds this
record retrieves `https://hub.example/.well-known/agent-marketplace` and continues as in
{{discovery}}. {{integrity}} describes how the reader protects the record and the document.

# The catalogue {#catalogue}

The resource at `catalogue_url` is a JSON object. Its full schema depends on the protocol
version; this section lists the minimum that every version has to contain.

## Minimum content

`protocol_version`:
: A string listed in the discovery document's `protocol_versions`.

`generated_at`:
: The generation time ({{RFC3339}}).

`capabilities`:
: An array of objects, each with at least `name` (string), `description` (string) and
  `input_schema` (object).

`signature`:
: A signature object ({{signature-object}}), when the discovery document names a signature
  profile.

## Requirements for signature profiles {#profile-requirements}

A signature profile MUST specify:

1. the signature algorithm and the encoding of keys and signature values;
2. the exact byte string that is signed and how it is derived from the catalogue;
3. for each member that is digested rather than copied into that byte string, its
   serialisation: handling of absent members, member order, whitespace, and non-ASCII
   characters;
4. the verification procedure, including inputs that MUST be rejected before the signature is
   evaluated.

Item 3 is required because differences there produce signatures that verify in one
implementation and not in another.

## Signature object {#signature-object}

The `signature` member of a catalogue is a JSON object:

~~~
{
  "algorithm": "<profile-defined>",
  "public_key": "<encoded public key, OPTIONAL>",
  "value": "<encoded signature>"
}
~~~

`public_key` MAY be omitted when the reader already holds a pinned key ({{keys}}). Profiles
MAY add members (for example, a second signature with another algorithm), and readers MUST
ignore members they do not recognise. A catalogue whose `signature` is not an object MUST be
treated as unsigned.

# Key pinning {#keys}

A reader MUST verify a catalogue with the key it has pinned for the index. A key carried in
the catalogue, or in the discovery document fetched in the same operation, does not by itself
authenticate the catalogue.

On first contact the reader SHOULD pin the key that the discovery document advertises and
record the time. After that, the reader:

* MUST NOT accept a different key automatically;
* SHOULD record any rejected key, with the time and the document that carried it;
* MAY accept a new key through an explicit operator decision.

As a consequence, a key change at the index requires action at each reader. See
{{security-rotation}}.

A pinned key shows that the current publisher holds the key that was first seen. It does not
identify the publisher. A reader's user interface MUST NOT present a verified signature as
evidence of the operator's identity.

# Catalogue freshness {#freshness}

The catalogue's `generated_at` is covered by the signature ({{canonical}}). A reader uses it
as follows:

* A reader that has verified a catalogue from an index SHOULD record its `generated_at`, and
  SHOULD reject a catalogue retrieved later from that index and verified under the same
  pinned key if its `generated_at` is earlier. Otherwise anyone who stored an older,
  validly signed catalogue can serve it again, for example to restore an entry or a price
  that the index has since withdrawn.
* A reader MAY treat a catalogue as stale when its `generated_at` is older than a maximum age
  that the reader chooses, and SHOULD NOT rely on a stale catalogue until a newer one
  verifies.
* A reader SHOULD reject a catalogue whose `generated_at` is ahead of its own clock by more
  than a tolerance that the reader chooses.

The first check compares two values written by the index and does not depend on the
reader's clock; the other two do. If the clock of an index moves backwards, the first check
rejects its catalogues until its clock passes the recorded value. A reader MAY reset the
recorded value by an operator decision, as for a key change ({{keys}}).

# The ed25519-pipe-2 signature profile {#profile}

This profile is identified by the `signature_profile` value `ed25519-pipe-2`. It is the
profile used by the implementations listed in {{implementation-status}}.

## Algorithm and encodings

The signature is Ed25519 {{RFC8032}} over the UTF-8 encoding of the canonical string defined
in {{canonical}}. Keys and signature values are base64-encoded with the standard alphabet and
padding ({{RFC4648}}, Section 4). The `algorithm` member of the signature object is `ed25519`.

## Canonical string {#canonical}

The canonical string is the concatenation of the following five `name:value` pairs, in this
order, separated by the character "|" (U+007C), with no whitespace:

~~~
capabilities_count:<n>|generated_at:<t>|protocol_version:<v>|
tools_hash:<h1>|by_hub_hash:<h2>
~~~

(shown on two lines for width; the string contains no line break)

where:

* `<n>` is the decimal value of `capabilities_count`, or `0` if absent;
* `<t>` is the value of `generated_at`, or the empty string if absent;
* `<v>` is the value of `protocol_version`, or `v1` if absent;
* `<h1>` is the digest ({{digest}}) of the `capabilities` array (the pair name `tools_hash`
  follows the deployed wire format, in which the array is named `tools`);
* `<h2>` is the digest of the `by_hub` object (per-peer metadata in the deployed format). If
  absent, the empty object `{}` MUST be digested.

Both digests MUST be included. Without `tools_hash`, an intermediary could change catalogue
entries, including prices, without invalidating the signature; without `by_hub_hash`, it could
change per-peer metadata.

## Digest rule {#digest}

The digest of a JSON value is the lowercase hexadecimal SHA-256 {{RFC6234}} of the UTF-8
encoding of its serialisation with these rules:

1. object members in ascending order of member name, compared by Unicode code point;
2. member separator `, ` (comma, space) and name separator `: ` (colon, space);
3. non-ASCII characters emitted as themselves, not as `\uXXXX` escapes;
4. integers without a fractional part; other numbers in the shortest decimal form that
   round-trips to the same IEEE 754 double;
5. no leading or trailing whitespace.

Rule 2 differs from {{RFC8785}}, which emits no whitespace. Changing it would change every
existing signature; an RFC 8785 based variant would be defined as a separate profile name.

## Verification {#verify}

{{RFC8032}} allows more than one verification equation. With the permissive variant used by
several common libraries, a signature made with a small-order public key can verify for any
message. A verifier implementing this profile MUST reject a signature, before evaluating the
verification equation, if:

1. the public key, or the point R in the first 32 octets of the signature, has order dividing
   8 (with the top bit of the last octet cleared, the encodings `00..00`, `01 00..00`,
   `26e8958f..fc05`, `c7176a70..037a`, `ecff..ff7f`, and the non-canonical `edff..ff7f` and
   `eeff..ff7f`); or
2. the scalar S in the last 32 octets, read as a little-endian integer, is not less than the
   group order L = 2^252 + 27742317777372353535851937790883648493.

Keys and signatures generated as specified in {{RFC8032}} pass these checks except with
negligible probability.

## Test vectors

Signed example catalogues and negative vectors (tampered members, wrong signer, version
downgrade, small-order key), with a runner, are published at {{VECTORS}}.

# Security Considerations

## Integrity of discovery information {#integrity}

The DAWN charter {{DAWN-CHARTER}} requires integrity for all discovery information
exchanged between DAWN parties. The discovery document is protected by HTTPS: a reader
retrieves it only with the "https" scheme ({{discovery}}) and verifies the server
certificate as described in {{RFC9110, Section 4.3.4}}. The document itself is not signed,
so a copy relayed by another party, for example a URI in another index's `peers`, carries no
integrity of its own; a reader retrieves the document from its own URI before using it.

A reader that finds the discovery document through DNS ({{dns}}) SHOULD validate the SVCB
record with DNSSEC {{RFC9364}}. HTTPS authenticates the host that the record names, not the
domain that the reader queried, so a forged record can lead a reader to another index whose
certificate is valid. Without DNSSEC validation, a reader SHOULD use the discovery document
only if its host is the queried domain, a name under it, or a host that the reader already
associates with that domain.

## Signatures and transport

The catalogue may be served from a different host, a content distribution network or a
cache, and a reader that stores a catalogue needs to verify it again later without the
original connection. HTTPS does not cover either case; the catalogue signature does.

## Scope of a signature

A valid signature shows that the holder of the pinned key produced the catalogue and that it
has not been modified. It does not show that the listed capabilities exist, behave as
described, or cost what is stated. A reader's user interface MUST NOT suggest otherwise.

In the terms of {{I-D.raskar-agentic-web-federated-resolution}}, the signature gives the
provenance of the catalogue and is not authority evidence: it does not show that a provider
authorised its entry. This document defines no authority evidence for individual entries.

## Privacy {#privacy}

A catalogue is published as a whole, so anyone can list every entry in it. Exact lookup of a
subject the client already knows, as in {{I-D.raskar-agentic-web-federated-resolution}},
does not have this property. An index SHOULD list only capabilities that their providers
offer to the public, and SHOULD NOT list an entry that identifies a natural person, such as
a personal account or a personal agent, unless that person asked to be listed. Federating
indexes keep copies of the catalogues they read ({{FEDERATION}}), so a published entry can
stay with them for some time after the index withdraws it.

## URIs from other parties

`catalogue_url` and `peers` contain URIs chosen by another party. Before retrieving them, a
reader MUST apply the request-forgery safeguards of {{FEDERATION}}: refuse private, loopback,
link-local, multicast and unspecified addresses (including IPv4-mapped forms), check the
resolved address at connection time, not follow redirects automatically, and limit response
size and time.

## Key rotation {#security-rotation}

Because readers do not accept a new key automatically ({{keys}}), rotating a key interrupts
readers until their operators act. An index SHOULD announce a rotation in advance and SHOULD
sign with the old and new keys in parallel for a period, using additional members of the
signature object. A rotation announcement mechanism may be defined in a later revision.

# IANA Considerations

## Well-Known URI registration {#iana-wk}

IANA is requested to register the following in the "Well-Known URIs" registry {{RFC8615}}:

URI suffix:
: agent-marketplace

Change controller:
: IETF

Specification document:
: This document, {{discovery}}

Status:
: permanent

Related information:
: JSON document describing a capability index: name, protocol versions, catalogue location
  and catalogue signing key.

## Signature profile names

This document defines one profile name, `ed25519-pipe-2`. No registry is requested for a
single value; if more profiles are defined, a registry with the Specification Required policy
would be appropriate.

# Implementation Status {#implementation-status}

This section records the status of known implementations at the time of writing, per
{{RFC7942}}. It is to be removed before publication as an RFC.

* Reference implementation (Apache-2.0), deployed on six public indexes operated by the
  author or affiliated parties. Since 2026-10-30 they serve this document at
  `/.well-known/agent-marketplace` in addition to the earlier path
  `/.well-known/ai-market.json`, which uses the member names in {{wire-mapping}}.
* Three further implementations by the same author, written from the text and test vectors
  without the reference source: a Go directory node, a Rust catalogue verifier, and a
  JavaScript verifier. Writing them found four ambiguities in the text, which were corrected.
* Two services operated by parties unrelated to the author publish catalogues that verify
  under `ed25519-pipe-2` (checked on 2026-10-30 with the conformance runner in {{VECTORS}}).
  Which software they run is not known.
* The reference implementation applies the three checks in {{freshness}}. For the first it
  keeps, for each index and pinned key, the latest `generated_at` it has verified; the
  defaults for the second and the third are seven days and one hour. All three run on the
  six indexes since 2026-11-04.

No implementation by another party is known to have been written from this document.

--- back

# Mapping to the deployed wire format {#wire-mapping}
{:numbered="false"}

| This document | Earlier deployed name |
|---|---|
| `/.well-known/agent-marketplace` | `/.well-known/ai-market.json` |
| `catalogue_url` | `manifest_url` |
| `capabilities` | `tools` |
| `signature_profile` | not present; always `ed25519-pipe-2` |
| `peers` (array of URI) | `peers` (array of objects with `url`) |

The canonical string, digest rule and verification rule are the same, so a signature valid
under one is valid under the other.

# Relation to the MDI model {#mdi}
{:numbered="false"}

{{MDI}} describes the minimum public discovery information (MDI) for one entity and lists
what a binding has to specify (its Section 9). This appendix records how the discovery
document carries MDI. It is not a complete binding.

A discovery document is one MDI instance, and its entity is the index.

| MDI element | Discovery document |
|---|---|
| Name | the URI of the discovery document, implicit in the carrier |
| Display Name | `name` |
| Entity Type | not carried; the well-known suffix implies an index |
| Endpoint, continuing discovery | `catalogue_url`, with the versions in `protocol_versions` |
| Freshness | `generated_at`, the generation time only |
| Stable Identifier | not carried |
| Authentication Hint | not carried; neither document requires authentication |
| Trust Reference | `signer_public_key` and `signature_profile` |
| Extensions | `capabilities_count`, `peers` |

Names:
: The naming scope of the Name is the "https" origin of the document. `name` is not unique
  ({{discovery}}), so it is a Display Name.

Endpoints:
: The purpose of `catalogue_url` follows from the member name. `protocol_versions` lists
  versions of the catalogue interface; the protocol itself is implied by the well-known
  suffix, and the catalogue states the version it uses in `protocol_version`. Most deployed
  documents also carry `mcp_endpoint`, an Endpoint for interaction over MCP, which this
  document does not define.

Peers:
: `peers` points to other entities, so it is not an Endpoint of this instance. Traversal
  depth and loop handling are specified in {{FEDERATION}}.

Integrity and origin:
: TLS authenticates the discovery document to its origin. The catalogue is authenticated by
  its signature under the key pinned at first contact ({{keys}}), also when another host
  serves it. The signature authenticates the index, not the providers whose capabilities the
  catalogue relays.

Change and replay:
: The catalogue's `generated_at` changes at every generation, whether or not the entries
  changed. A reader can tell whether they changed by comparing the digest of `capabilities`
  ({{digest}}) with that of the last verified catalogue. Because `generated_at` is in the signed string, a
  reader can also detect a catalogue older than one it has already verified ({{freshness}}).

Neither document carries a validity window or a refresh hint; MDI's Freshness has members for
both. A reader applies a maximum age of its own choosing ({{freshness}}).

# Implementation experience
{:numbered="false"}

These failures in deployed implementations led to requirements in this document:

* An implementation that omitted `by_hub_hash` produced catalogues no other implementation
  could verify ({{canonical}}).
* An earlier published vector set signed a canonical string without the digests ({{canonical}}).
* Three verifiers failed on a signature encoded as a bare string ({{signature-object}}).
* A widely used Ed25519 library accepted a signature under a small-order key for an arbitrary
  message ({{verify}}).

# Changes from -03
{:numbered="false"}

Added {{freshness}}: a reader SHOULD reject a catalogue older than the last one it verified
from the same index, MAY apply a maximum age, and SHOULD reject a catalogue dated ahead of its
clock. Added {{privacy}}: a catalogue can be listed in full, so an index SHOULD NOT list
entries that identify a person without that person's request. The Security Considerations
now state the scope of a signature also in the terms of
{{I-D.raskar-agentic-web-federated-resolution}}. Implementation Status records which freshness
checks the reference implementation applies. The reference to {{FEDERATION}} now names -02.

{{dawn}} now follows the responsible Area Director's reading of the charter {{DAWN-SCOPE}}:
only the catalogue location, the protocol versions and the DNS record are within it, and
the other members of the discovery document are marked as adjacent work. The Abstract says
the same. Added {{integrity}} on the integrity of the discovery document and of the DNS
record, which the charter requires.

# Changes from -02
{:numbered="false"}

Added {{dawn}}, which relates the parts of this document to the DAWN charter and marks the
catalogue, its signature profile and key pinning as adjacent work, and {{dns}}, an example of
a DNS-AID index record that leads to the discovery document. The Abstract and the Scope now
also exclude search. No requirement changed.

# Changes from -01
{:numbered="false"}

Added {{mdi}}, a mapping of the discovery document onto {{MDI}}, and a pointer to it in the
Introduction. No requirement changed.

# Changes from -00
{:numbered="false"}

Editorial: the text was shortened, and explanatory passages were removed or moved to the
Implementation experience appendix. Implementation Status was updated. One wording correction: the requirement to
ignore unrecognised members applies to readers; -00 said "index".

# Acknowledgements
{:numbered="false"}

Thanks to the authors of {{I-D.jimenez-dawn-discovery-landscape}}, and to Chenguang Du and
Siyu Deng for the discussion of minimum discovery information on the DAWN list.
