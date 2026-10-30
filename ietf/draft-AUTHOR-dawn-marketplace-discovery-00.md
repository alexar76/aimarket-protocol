---
title: "A Discovery Document and Signed Catalogue for Capability Marketplaces"
abbrev: "Marketplace Discovery"
docname: draft-AUTHOR-dawn-marketplace-discovery-00
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
    ins: A. AUTHOR
    name: AUTHOR NAME
    organization: Independent
    email: AUTHOR@EXAMPLE.COM
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
        ins: A. AUTHOR
    date: 2026-10
    seriesinfo:
      Internet-Draft: draft-AUTHOR-dawn-index-federation-00
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

Autonomous software agents obtain capabilities from services catalogued by independently
operated indexes. For an agent, or another index, to use such a catalogue it must first learn a
small set of public properties of the index: what it is called, which protocol versions it
speaks, where its catalogue is, and which key signs that catalogue. This document specifies a
JSON discovery document served at a well-known URI that carries exactly those properties, and
the requirements a signed catalogue referenced from it has to meet so that a reader can verify
it without trusting the transport or the operator. It specifies nothing about how indexes find
one another, exchange catalogues, or decide whom to trust; those are the subject of a
companion document.

--- middle

# Introduction

Machine-readable catalogues of invocable capabilities have appeared alongside protocols for
machine payment {{X402}}, agent-to-agent interaction {{A2A}} and tool registries {{MCPREG}}.
Each catalogue is operated by one party. Before a client can use one, it needs to know a few
things about the operator's index that are public by nature: a name, the protocol versions in
use, the location of the catalogue, and the public key under which the catalogue is signed.

{{I-D.jimenez-dawn-discovery-landscape}} surveys the mechanisms through which such properties
are published today and finds them fragmented: each system defines its own well-known resource,
its own schema and, where a signature is present, its own unstated canonicalisation. This
document specifies the smallest discovery document the authors found sufficient in operation,
and it specifies the one thing most signed-catalogue systems leave implicit: the exact byte
string under a catalogue signature.

The document is written for discussion in the DAWN working group. Its subject matter — the
public properties of an AI resource that a client needs before interacting with it, and the
integrity of that information — is within that group's charter. Catalogue exchange between
indexes, admission of peers and trust are outside this document; they are specified in
{{FEDERATION}}, which is offered as input to the gap analysis in
{{I-D.jimenez-dawn-discovery-landscape}} rather than as chartered work.

## Scope and non-goals {#scope}

This document specifies:

* a discovery document served at a well-known URI ({{discovery}});
* the requirements a signed catalogue referenced from that document has to meet
  ({{catalogue}}), including the obligation on any signature profile to state its signed
  byte string, and one such profile ({{profile}});
* how a reader pins and verifies the signing key ({{keys}}).

This document does not specify: how an index learns that other indexes exist; how catalogues
are exchanged, merged or ranked; how a capability is invoked or paid for; the identity system
naming a provider; or any reputation mechanism. The discovery document is compatible with all
of them and depends on none.

## Requirements Language

{::boilerplate bcp14-tagged}

## Terminology

Index:
: A server that catalogues capabilities and answers queries about them. The authors'
  implementation calls it a hub.

Capability:
: A named, invocable unit of work offered by a provider and catalogued by an index.

Catalogue:
: The signed document, referenced from the discovery document, that lists an index's
  capabilities. The authors' implementation calls it a manifest.

Discovery document:
: The JSON document defined in {{discovery}}.

Reader:
: Any party retrieving the discovery document or the catalogue: an agent, a client library,
  or another index.

Signature profile:
: A named rule set stating which algorithm signs a catalogue, over which byte string, and how
  a reader verifies it.

# Discovery document {#discovery}

An index MUST serve a discovery document at the well-known URI
`/.well-known/agent-marketplace` ({{RFC8615}}, {{iana-wk}}) under the "https" scheme. It MUST
answer both GET and HEAD requests for it, and SHOULD honour conditional requests
({{RFC9110}}, Section 13) so that readers polling on a timer transfer nothing when nothing
changed.

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

`name` is a human-readable label chosen by the operator. It carries no identity: two indexes
MAY have the same name, and a reader MUST NOT key any decision on it.

`protocol_versions` lists the versions of the catalogue and query interfaces the index
serves, as opaque strings. A reader that recognises none of them MUST treat the index as
unusable and MUST NOT guess.

`catalogue_url` is an absolute URI {{RFC3986}} under the "https" scheme from which the
catalogue ({{catalogue}}) is retrieved. It MAY be on a different host from the discovery
document.

`signer_public_key` is the public key under which the catalogue is signed, encoded as the
signature profile requires. `signature_profile` names that profile ({{profile}}). A reader
MUST treat the pair as a claim to be pinned, not as proof of anything ({{keys}}).

`capabilities_count` is the number of entries in the catalogue at the time the discovery
document was generated, and `generated_at` is that time in {{RFC3339}} format. Both exist so
that a reader can decide whether retrieving the catalogue is worthwhile; neither is
authoritative, and a reader MUST NOT treat a mismatch with the catalogue as an error on its
own.

`peers`, when present, lists the discovery-document URIs of other indexes the operator has
chosen to publish. This document assigns the member no semantics beyond "the operator chose
to publish these"; {{FEDERATION}} constrains what an index that exchanges catalogues MAY put
here.

An index MUST ignore members it does not recognise, and MUST NOT fail to parse a document
because it carries an unknown member. Extension by addition is the intended evolution path.
A member defined by this document MUST NOT change its type or meaning in a later version;
a changed meaning is a new member.

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

## Relationship to the api-catalog well-known resource

{{RFC9727}} defines `/.well-known/api-catalog` for a host to list its APIs. The two resources
answer different questions. An api-catalog lists what a host offers; the document specified
here identifies a party that catalogues what *other* hosts offer, under a key, with a version
list a reader negotiates against. An index MAY additionally publish an api-catalog, and a
future revision of this document may define a link relation between the two.

# The signed catalogue {#catalogue}

The resource at `catalogue_url` is a JSON object listing the index's capabilities. Its full
schema belongs to the protocol version in use and is out of scope here; this section
specifies only what any version has to satisfy for the discovery document to be useful.

## Minimum content

The catalogue MUST contain:

`protocol_version`:
: string, one of the values the discovery document lists in `protocol_versions`;

`generated_at`:
: the generation time in {{RFC3339}} format;

`capabilities`:
: an array of objects, each with at least a `name` (string), a `description` (string) and
  an `input_schema` (object). Other members, such as a price or a measured success rate, are
  defined by the protocol version in use.

`signature`:
: an object as defined by the signature profile ({{signature-object}}), when the discovery
  document names a profile.

## Requirements on any signature profile {#profile-requirements}

A signature profile MUST state, in text that an implementer can follow without reading any
implementation:

1. the signature algorithm and the encoding of public keys and signature values;
2. the exact byte string that is signed, derived from the catalogue by a rule that two
   independent implementations will apply identically;
3. for every member that is digested rather than copied into that byte string, the
   serialisation under the digest, including the handling of absent members, member order,
   whitespace and non-ASCII characters;
4. the verification rule, including which malformed keys or signature values a verifier
   MUST reject before evaluating the signature.

Item 3 is where signed-document systems fail in practice. Two implementations that disagree
on whether a missing member hashes as an empty object or is omitted, or on whether a
non-ASCII character is emitted raw or escaped, produce documents that verify against
themselves and fail against each other, and the failure is silent until the two meet in
production. A profile that leaves any of these to the implementation has not specified a
signature; it has specified a hazard.

## The signature object {#signature-object}

Whatever the profile, the `signature` member of a catalogue is a JSON object, never a bare
string:

~~~
{
  "algorithm": "<profile-defined>",
  "public_key": "<encoded public key, OPTIONAL>",
  "value": "<encoded signature>"
}
~~~

`public_key` MAY be omitted where the reader already holds a pinned key for the index
({{keys}}). A reader MUST NOT fail on additional members: a profile that adds, for example,
a post-quantum signature next to the primary one does so by adding members.

A reader that encounters a bare string where the object is expected MUST reject the
catalogue as unsigned. The authors added this rule after three separate implementations
crashed on exactly that input.

# Key pinning and verification {#keys}

A reader MUST verify a catalogue against the key it has pinned for the index, never against
a key carried inside the catalogue or in the discovery document retrieved in the same
operation. A document signed by an attacker's key verifies perfectly against that same key.

On first contact a reader has nothing to compare against. It SHOULD pin the key the discovery
document advertises (trust on first use), record when it did so, and thereafter:

* MUST NOT accept a different key automatically;
* SHOULD record a rejected key together with the time and the document that carried it, so
  an operator can distinguish a rotation from a takeover;
* MAY accept a new key through an out-of-band operator decision.

A key rotation is therefore an operator decision on the reading side, by design. The cost is
that an index which rotates its key loses every reader until each reader's operator acts; the
alternative is that a party able to alter the discovery document in transit, or to compromise
the host serving it, silently replaces the key and every subsequent catalogue.

Pinning establishes continuity, not identity. A pinned key proves that the party publishing
today holds the same key as the party a reader first met. It proves nothing about who that
party is, and an interface MUST NOT present a verified signature as evidence of the
operator's identity or good faith.

# The ed25519-pipe-2 signature profile {#profile}

This section defines the profile the authors deploy, identified by the `signature_profile`
value `ed25519-pipe-2`. It is specified here because the discovery document is useless
without at least one profile a reader can implement, and because every rule in it exists
because its absence caused a concrete failure.

## Algorithm and encodings

The signature is Ed25519 {{RFC8032}} over the UTF-8 encoding of the canonical string defined
in {{canonical}}. Public keys and signature values are base64-encoded with the standard
alphabet and padding ({{RFC4648}}, Section 4). The `algorithm` member of the signature object
is the string `ed25519`.

## Canonical string {#canonical}

The canonical string is the concatenation of the following five `name:value` pairs, in this
order, joined by the ASCII vertical bar (U+007C), with no whitespace anywhere:

~~~
capabilities_count:<n>|generated_at:<t>|protocol_version:<v>|
tools_hash:<h1>|by_hub_hash:<h2>
~~~

(shown on two lines for width; the string contains no line break)

where:

* `<n>` is the decimal value of `capabilities_count`, or `0` when the member is absent;
* `<t>` is the string value of `generated_at`, or the empty string when absent;
* `<v>` is the string value of `protocol_version`, or `v1` when absent;
* `<h1>` is the digest ({{digest}}) of the `capabilities` array (named `tools` in the
  authors' current wire format, which is why the pair is called `tools_hash`);
* `<h2>` is the digest of the `by_hub` object, which carries per-peer metadata in the
  authors' format. When the member is absent it MUST be digested as the empty object `{}`,
  so that an index serving no peer metadata agrees with one that serves an empty map.

Both digests are load-bearing. Without the first, an intermediary can rewrite every price in
the catalogue under a still-valid signature; without the second it can rewrite per-peer
metadata the same way. An implementation of this profile MUST compute both and MUST NOT sign
a canonical string with fewer pairs. The authors' published vectors did exactly that for two
months in 2026 and taught the insecure shape to anyone implementing from them.

## Digest rule {#digest}

The digest of a JSON value is the lowercase hexadecimal SHA-256 {{RFC6234}} of the UTF-8
encoding of the value's serialisation under the following rules:

1. object members are emitted in ascending order of member name, compared by Unicode code
   point;
2. the member separator is the two characters `, ` (comma, space) and the name/value
   separator is `: ` (colon, space);
3. non-ASCII characters are emitted as themselves, not as `\uXXXX` escapes;
4. integers are emitted without a fractional part; non-integral numbers are emitted in the
   shortest decimal form that round-trips to the same IEEE 754 double;
5. there is no leading or trailing whitespace.

Rule 2 is the point at which this profile differs from JSON Canonicalization Scheme
{{RFC8785}}, which emits no whitespace. The authors' deployment and every published vector
use the separators above; moving this profile to {{RFC8785}} would change every signature and
is a decision for a working group, not for a -00. A later profile name, not a revision of
this one, is the right vehicle for that change.

## Verification rule {#verify}

{{RFC8032}} permits more than one verification rule, and widely used libraries pick the
permissive one. Under that rule the public key encoding the identity point, together with a
signature whose first 32 octets encode the base point and whose scalar is 1, verifies for
every message, and anybody can produce it since no private key exists for that public key.

A verifier implementing this profile MUST therefore reject a signature before evaluating the
group equation when either of the following holds:

1. the public key, or the point R in the first 32 octets of the signature, encodes a point of
   order dividing 8 (after clearing the top bit of the final octet: the encodings
   `00..00`, `01 00..00`, `26e8958f..fc05`, `c7176a70..037a`, `ecff..ff7f`, and the
   non-canonical `edff..ff7f` and `eeff..ff7f`);
2. the scalar S in the last 32 octets, read little-endian, is not strictly less than the
   group order L = 2^252 + 27742317777372353535851937790883648493.

The rule costs honest signers nothing: a key and nonce derived per {{RFC8032}} are of small
order with negligible probability. It matters wherever the key was chosen by someone other
than the verifier, which in a federation is always.

## Test vectors

Signed example catalogues, together with negative vectors that a conforming verifier MUST
reject (tampered members, wrong signer, version downgrade, small-order key) and a runner that
exercises them offline, are published at {{VECTORS}}. A -01 of this document will carry a
minimal vector set inline so that the document is self-contained.

# Security Considerations

## Transport is not enough

The discovery document is served over HTTPS and could, in principle, be trusted on that basis
alone. It is not, for two reasons. First, the catalogue may be served from a different host
({{discovery}}), by a content distribution network, or from a cache, and the chain of custody
is not the reader's to audit. Second, a reader that stores a catalogue and serves queries
from the stored copy, which {{FEDERATION}} requires, needs to be able to re-verify it later
without the connection that delivered it. A signature over a specified byte string gives a
reader both.

## What a verified signature proves

A verified signature proves that the catalogue was produced by the holder of the pinned key
and was not altered since. It proves nothing about whether the listed capabilities exist,
perform as described, or cost what the catalogue says. An index makes no such claim by
publishing a signed catalogue, and a reader's interface MUST NOT imply that it does.

## Retrieval of operator-supplied URIs

`catalogue_url` and every entry of `peers` are URIs supplied by another party. A reader MUST,
before retrieving any of them, apply the server-side request forgery safeguards specified in
{{FEDERATION}}: refuse private, loopback, link-local, multicast and unspecified address
ranges including IPv4-mapped forms, re-check the resolved address at connection time, refuse
automatic redirects, and bound response size and time.

## Key rotation

{{keys}} makes rotation an operator decision on every reader, which is a denial-of-service
exposure for the index that rotates. An index SHOULD therefore plan rotation as an announced
event and SHOULD serve the old and new keys side by side for a period, using the extension
path in {{signature-object}}, so that readers can pin the successor before the predecessor
stops signing. The mechanism for that announcement is a candidate for a future revision.

# IANA Considerations

## Well-Known URI registration {#iana-wk}

IANA is requested to register the following in the "Well-Known URIs" registry established by
{{RFC8615}}:

URI suffix:
: agent-marketplace

Change controller:
: IETF

Specification document:
: This document, {{discovery}}

Status:
: permanent

Related information:
: The resource is a JSON object identifying a capability index: its name, protocol versions,
  catalogue location and catalogue signing key.

## Signature profile names

This document defines one profile name, `ed25519-pipe-2` ({{profile}}). Should a second
profile be defined, a registry with a Specification Required policy would be the appropriate
home; one is not requested for a single value.

# Implementation Status

This section records the state of implementation at the time of writing, per {{RFC7942}},
and is to be removed before publication as an RFC.

The authors operate a reference implementation of the discovery document and the
`ed25519-pipe-2` profile, distributed under Apache-2.0, deployed on six public indexes they
operate or are affiliated with. The discovery document is currently served at
`/.well-known/ai-market.json` with the member names of the authors' pre-standard wire format
(`manifest_url` for `catalogue_url`, `tools` for `capabilities`); an implementation
submitting this document plans to serve both names during a transition.

Three further implementations of the profile exist, written from the specification text and
the vectors without reading the reference source: a Go directory node, a Rust verifier for
catalogues and announcements, and a JavaScript verifier for receipts. All three are by the
specification's editor, so they demonstrate that the text is implementable and found four
places where it was not (each now fixed), but they do not demonstrate interoperability between
parties with no common operator.

Two indexes admitted to the authors' federation are operated by parties unrelated to the
authors. Neither runs the reference implementation; one publishes no catalogue. **No
independent implementation of this document exists.** The authors consider that the material
open question for this work and would rather state it than have a reviewer find it.

--- back

# Mapping to the authors' current wire format
{:numbered="false"}

For readers of the authors' deployed protocol, the correspondence is:

| This document | Deployed format |
|---|---|
| `/.well-known/agent-marketplace` | `/.well-known/ai-market.json` |
| `catalogue_url` | `manifest_url` |
| `capabilities` | `tools` |
| `signature_profile` | implied; always `ed25519-pipe-2` |
| `peers` (array of URI) | `peers` (array of object with `url`) |

The canonical string, digest rule and verification rule are identical, so a signature valid
under one is valid under the other.

# Acknowledgements
{:numbered="false"}

Every normative rule in {{profile}} exists because its absence caused a concrete failure in a
deployed system: a missing digest that let one implementation federate nothing, a vector set
that signed too little, a bare-string signature that crashed three verifiers, and a
permissive Ed25519 library that accepted a forgeable key. The authors thank the authors of
{{I-D.jimenez-dawn-discovery-landscape}} for a survey that made the shape of the gap visible.
