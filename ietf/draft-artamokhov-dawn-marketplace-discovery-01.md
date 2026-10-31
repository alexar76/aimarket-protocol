---
title: "A Discovery Document and Signed Catalogue for Capability Marketplaces"
abbrev: "Marketplace Discovery"
docname: draft-artamokhov-dawn-marketplace-discovery-01
category: std
ipr: trust200902
submissiontype: IETF
area: Internet
workgroup: Network Working Group
date: 2026-10-30
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
informative:
  RFC7942:
  RFC8785:
  RFC9727:
  I-D.jimenez-dawn-discovery-landscape:
  FEDERATION:
    title: "Federation Between Capability Indexes: Crawl, Reciprocal Identification and Admission"
    author:
      -
        ins: A. Artamokhov
    date: 2026-10
    seriesinfo:
      Internet-Draft: draft-artamokhov-dawn-index-federation-01
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

This document defines a JSON discovery document, served at a well-known URI, that carries the
public properties a client needs before using a capability index: its name, the protocol
versions it serves, the location of its catalogue, and the key that signs the catalogue. It
also states the requirements for that signed catalogue and defines one signature profile.
Discovery between indexes, catalogue exchange and trust are out of scope.

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
requires any signature profile used with it to specify the signed bytes.

Catalogue exchange between indexes and peer admission are described separately in
{{FEDERATION}}.

## Scope

This document specifies:

* a discovery document served at a well-known URI ({{discovery}});
* requirements for the catalogue referenced from it ({{catalogue}}), including requirements
  for any signature profile, and one profile ({{profile}});
* key pinning by readers ({{keys}}).

It does not specify how indexes find each other, how catalogues are exchanged or ranked, how
capabilities are invoked or paid for, how providers are identified, or reputation.

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

## Signatures and transport

The catalogue may be served from a different host, a content distribution network or a
cache, and a reader that stores a catalogue needs to verify it again later without the
original connection. HTTPS does not cover either case; the catalogue signature does.

## Scope of a signature

A valid signature shows that the holder of the pinned key produced the catalogue and that it
has not been modified. It does not show that the listed capabilities exist, behave as
described, or cost what is stated. A reader's user interface MUST NOT suggest otherwise.

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

# Implementation experience
{:numbered="false"}

These failures in deployed implementations led to requirements in this document:

* An implementation that omitted `by_hub_hash` produced catalogues no other implementation
  could verify ({{canonical}}).
* An earlier published vector set signed a canonical string without the digests ({{canonical}}).
* Three verifiers failed on a signature encoded as a bare string ({{signature-object}}).
* A widely used Ed25519 library accepted a signature under a small-order key for an arbitrary
  message ({{verify}}).

# Changes from -00
{:numbered="false"}

Editorial: the text was shortened, and explanatory passages were removed or moved to the
appendix above. Implementation Status was updated. One wording correction: the requirement to
ignore unrecognised members applies to readers; -00 said "index".

# Acknowledgements
{:numbered="false"}

Thanks to the authors of {{I-D.jimenez-dawn-discovery-landscape}}.
