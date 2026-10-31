---
title: "Federation Between Capability Indexes: Crawl, Reciprocal Identification and Admission"
abbrev: "Index Federation"
docname: draft-artamokhov-dawn-index-federation-01
category: exp
ipr: trust200902
submissiontype: IETF
area: Internet
workgroup: Network Working Group
date: 2026-10-30
keyword:
  - agents
  - discovery
  - federation
  - marketplace
  - admission
stand_alone: yes
pi: [toc, sortrefs, symrefs]
author:
  -
    ins: A. Artamokhov
    name: Aleksandr Artamokhov
    organization: Independent
    email: alexar76@rambler.ru
normative:
  RFC3986:
  RFC8259:
  RFC9110:
  DISCOVERY:
    title: "A Discovery Document and Signed Catalogue for Capability Marketplaces"
    author:
      -
        ins: A. Artamokhov
    date: 2026-10
    seriesinfo:
      Internet-Draft: draft-artamokhov-dawn-marketplace-discovery-01
informative:
  RFC6648:
  RFC7942:
  RFC9162:
  I-D.jimenez-dawn-discovery-landscape:
  I-D.mp-agntcy-ads:
  I-D.pioli-agent-discovery:
  A2A:
    title: "Agent2Agent (A2A) Protocol Specification, version 1.0"
    target: https://a2a-protocol.org/latest/specification/
    date: 2026-03
  MCPREG:
    title: "Model Context Protocol Registry"
    target: https://registry.modelcontextprotocol.io/
    date: 2026
  X402BAZAAR:
    title: "x402 Bazaar discovery extension"
    target: https://github.com/x402-foundation/x402/blob/main/specs/extensions/bazaar.md
    date: 2026
--- abstract

This document describes how independently operated capability indexes discover each other by
following discovery documents, how a reading index identifies itself to the index it reads,
and an admission model that distinguishes a peer that is known from a peer whose catalogue is
indexed. It also describes how an index can preview a peer's catalogue before admitting it.
Payment, identity, reputation and invocation are out of scope. The document is intended as
input to the DAWN gap analysis on federation between directories.

--- middle

# Introduction

Capability indexes are operated by many independent parties, and each lists only what its
operator has seen. A client sees only the catalogue of the index it queries, and a provider
has to register with each index separately.

{{I-D.jimenez-dawn-discovery-landscape}} (Section 6.2) identifies the lack of an
interoperable federation mechanism between directories as a gap. Existing designs federate
through a shared distributed hash table {{I-D.mp-agntcy-ads}}, through configured trust
relationships {{I-D.pioli-agent-discovery}}, or not at all ({{A2A}} leaves registries to
deployments; {{MCPREG}} has one upstream registry with mirrors).

This document describes a simpler arrangement. Each index is an HTTPS server that publishes a
discovery document {{DISCOVERY}}. Indexes find each other by following those documents, a
reading index identifies itself to the index it reads, and each index decides per peer
whether to index that peer's catalogue. There is no shared infrastructure and no central
registration.

Catalogue exchange and trust are outside the initial DAWN charter. This document uses DAWN
terminology because cooperating indexes that exchange catalogues need these mechanisms, and
is offered as input to the gap analysis, not as a proposal for adoption.

## Scope

This document specifies:

* a crawl protocol over discovery documents ({{crawl}});
* reciprocal identification of the reading index ({{reciprocal}});
* an announcement message ({{announce}});
* an admission model ({{admission}});
* catalogue preview for peers not yet admitted ({{preview}}).

It does not specify payment, identity of providers or operators, reputation or ranking,
invocation, or resolution of conflicting listings.

## Requirements Language

{::boilerplate bcp14-tagged}

## Terminology

Index, catalogue, discovery document, reader:
: As defined in {{DISCOVERY}}.

Peer:
: An index known to another index.

Admitted:
: A peer whose catalogue an index has chosen to index ({{admission}}).

Pending:
: A peer that an index knows of but has not admitted.

Operator:
: The party that makes admission decisions for an index.

# Crawl protocol {#crawl}

An index discovers peers by retrieving discovery documents, starting from a configured list
of URIs (the seed list) and following the `peers` member of each document retrieved. For
each peer it retrieves the discovery document and the catalogue, verifies the catalogue as
specified in {{DISCOVERY}}, and stores the result.

An index MUST limit the traversal by depth from the seed list and by the number of peers
retrieved per cycle, and MUST run the crawl on a schedule rather than in response to queries.

An index MUST answer queries from its stored copies of peer catalogues and MUST NOT contact
peers while answering a query. Contacting peers at query time would make each query depend on
the availability and latency of every peer.

An index SHOULD use conditional requests ({{RFC9110}}, Section 13) when it re-retrieves a
document, and SHOULD answer them when it serves its own.

An index MUST NOT crawl itself. URIs reach the crawl from the seed list, from pending
announcements and from the `peers` of retrieved documents; the self check applies to all
three. The comparison MUST normalise scheme, host case and path, because an index may be
published under a path of a shared host.

# Reciprocal identification {#reciprocal}

An index that retrieves another index's discovery document MUST identify itself with the
`Agent-Marketplace-Crawler` request header field ({{iana-hdr}}):

~~~
GET /.well-known/agent-marketplace HTTP/1.1
Host: example.net
Agent-Marketplace-Crawler: https://crawler.example
~~~

The value is the absolute URI {{RFC3986}} of the retrieving index.

This lets an operator learn which indexes read its index. It conveys no trust.

A receiving index:

* SHOULD record the value;
* MUST treat the value as an unauthenticated claim and MUST NOT grant any trust because of
  it;
* MUST check that the value is an absolute "https" URI before storing it, and MUST apply
  {{security-ssrf}} before retrieving anything from it;
* MAY, under open admission ({{open-closed}}), record the identified index as a pending peer;
* SHOULD limit the number of distinct values it records.

Implementations SHOULD process the value outside the request path, so that serving the
discovery document does not wait for name resolution.

# Announcement {#announce}

An index MAY announce itself to another index with an HTTP POST of a JSON object {{RFC8259}}
to an endpoint the receiving index publishes. Members:

| Member | Type | Requirement |
|---|---|---|
| `index_url` | string (URI) | REQUIRED |
| `discovery_url` | string (URI) | REQUIRED |
| `capabilities_count` | number | OPTIONAL |
| `signer_public_key` | string | OPTIONAL |
| `signature` | object | OPTIONAL |

If present, `signature` is a signature object as defined in {{DISCOVERY}}, under the profile
named in the announcing index's discovery document, over the canonical string

~~~
hub_url:<index_url>|well_known_url:<discovery_url>|
capabilities_count:<n>
~~~

(shown on two lines for width; the string contains no line break)

with `<n>` defaulting to `0`. The pair names follow the deployed wire format.

The canonical string contains no timestamp or nonce, so an announcement can be replayed. This
is acceptable only because an announcement grants nothing ({{admission-rules}}). A verified
announcement signature shows only that the sender holds the key it advertises, and MUST NOT
be used in an admission decision.

In this revision the location of the announcement endpoint is deployment-specific (the
reference implementation uses `/ai-market/v2/federation/announce`). A link from the discovery
document may be added in a later revision.

# Admission {#admission}

An index MUST keep two questions separate: whether it knows that a peer exists, and whether
it indexes that peer's catalogue.

## States

An index MUST place every known peer in exactly one of these states:

Pending:
: The peer is known. Its catalogue is not indexed, not queryable and not used for routing,
  and its `peers` member is not followed.

Admitted:
: The operator has decided to index the peer's catalogue. How the catalogue is then used is
  outside this document.

An index MAY define sub-states of "admitted". It MUST NOT define a state in which a peer's
catalogue is used without admission.

## Open and closed admission {#open-closed}

An index MUST support closed admission, in which a peer becomes pending only by operator
action (a seed-list entry, or an announcement the operator has authorised).

An index MAY also support open admission, in which an unauthenticated party can create a
pending entry by announcement ({{announce}}) or by reciprocal identification
({{reciprocal}}).

## Rules {#admission-rules}

With open admission, all of the following MUST hold:

1. An unauthenticated announcement or reciprocal identification creates a pending peer, never
   an admitted one.
2. An announcement about an already-known peer MUST NOT change any stored property of that
   peer, including its name, pinned key and state.
3. The number of pending peers MUST be limited. When the limit is reached, further
   unauthenticated announcements MUST be refused with status 429 (Too Many Requests).
4. An announced or self-identified URI MUST pass {{security-ssrf}} before it is stored.
5. A pending peer MUST NOT be listed in the `peers` member of the index's own discovery
   document.

Under rule 5, a peer listed in `peers` is one the operator has admitted. Without it, any party
could add a URI to the crawl of every index that reads this one.

## Automatic assessment

An index MAY run automated checks on a pending peer (for example, retrieving its discovery
document, verifying its catalogue signature, or calling a listed capability) and show the
results to the operator. It MAY admit a peer automatically based on such checks. If it does,
it MUST record which checks were run and their results, and the operator MUST be able to
reverse the admission. A peer that fails the checks remains pending and visible to the
operator.

## Catalogue preview {#preview}

An index MAY retrieve and display a pending peer's catalogue so that its operator can decide
on admission. If it does:

1. The catalogue MUST be validated, and its signature verified if present, as for an admitted
   peer.
2. Previewed entries MUST NOT be returned by queries, used for routing, or included in the
   index's own catalogue. Implementations SHOULD store them separately from the data used to
   answer queries, rather than rely on filtering.
3. Any interface that shows previewed entries MUST mark them as not admitted.

Signature verification of a preview shows only that the catalogue was signed by the key the
peer advertises and was not modified in transit. It says nothing about whether the peer
should be trusted.

# Relationship to other work

This section is informative.

{{I-D.mp-agntcy-ads}} federates directories through a Kademlia DHT and content-addressed OCI
storage, with Sigstore-signed records. That provides global content-addressed lookup, with
infrastructure that every participant runs. This document requires no shared
infrastructure. A DHT-based directory could publish a discovery document and be admitted
like any other peer.

{{I-D.pioli-agent-discovery}} federates through configured trust relationships, which
corresponds to closed admission here. This document adds open admission under the rules in
{{admission-rules}}.

{{A2A}} defines a signed card per agent and leaves registries to deployments. An index under
this document can act as such a registry, and MAY also publish an agent card for itself.

{{MCPREG}} has one upstream registry and sub-registries that mirror it. An index can admit
the upstream registry as a peer; this document also covers the case without an upstream.

{{X402BAZAAR}} builds a catalogue from metadata declared in payments that pass through a
facilitator. Discovery here does not depend on a prior payment.

The pending/admitted distinction is similar to the separation in Certificate Transparency
{{RFC9162}} between an entry being logged and being trusted.

# Security Considerations

## Request forgery {#security-ssrf}

Every mechanism in this document causes an index to retrieve a URI chosen by another party.
Before retrieving a URI obtained from a peer's discovery document, an announcement, or the
`Agent-Marketplace-Crawler` field, an index MUST:

* resolve the host and refuse private, loopback, link-local, multicast and unspecified
  addresses, including IPv4-mapped and IPv4-compatible IPv6 forms, using an explicit list of
  ranges rather than a library's definition of "private";
* check the resolved address again at connection time, or connect to the checked address;
* not follow redirects automatically;
* limit response size and time.

An index that shares a host with other services MUST NOT treat a URI that resolves to its own
host as a peer.

## Key pinning

An index MUST verify a peer's catalogue with the key pinned for that peer, as specified in
{{DISCOVERY}}. A changed key is reported to the operator and never accepted automatically. As
a result, a key change at a peer requires action by each operator that has pinned it.

## Resource exhaustion

Open admission accepts unauthenticated writes; the limits in {{admission-rules}} bound them.
The traversal limits in {{crawl}} bound the work caused by a large or cyclic `peers` member.

## Split views

An index can serve different catalogues to different readers. A reader that stores the signed
catalogue it received can show what it was served, and readers can compare; this document does
not define how. A transparency log for catalogues, in the style of {{RFC9162}}, would address
this and is out of scope.

## Privacy

The record described in {{reciprocal}} shows which indexes read a given index. An
implementation SHOULD record only the declared URI and SHOULD NOT keep the client network
address.

## Limits

This document does not cover payment, and a compliant index makes no statement about whether
a catalogued capability works as described. Admission is an operator decision, not a
guarantee.

# IANA Considerations

## HTTP field name registration {#iana-hdr}

IANA is requested to register the following in the "Hypertext Transfer Protocol (HTTP) Field
Name Registry" {{RFC9110}}:

Field name:
: Agent-Marketplace-Crawler

Status:
: provisional

Reference:
: {{reciprocal}} of this document

Comments:
: Request header field. The value is an absolute URI identifying the index on whose behalf
  the request is made. No `X-` prefix is used, per {{RFC6648}}.

# Implementation Status

This section records the status of known implementations at the time of writing, per
{{RFC7942}}. It is to be removed before publication as an RFC.

* Reference implementation (Apache-2.0) of the crawl, reciprocal identification,
  announcement, both admission modes, automatic assessment and preview, with a conformance
  runner and test vectors. Deployed on six public indexes operated by the author or
  affiliated parties, with open admission enabled since October 2026. Since 2026-10-30 it
  sends and accepts `Agent-Marketplace-Crawler` in addition to the earlier
  `X-AIMarket-Crawler`.
* A Go directory node implementing crawl, discovery and announcement intake, written by the
  same author from the text and test vectors without the reference source.
* The largest deployed index lists 21 admitted peers. Three services known to it are operated
  by unrelated parties; as of 2026-10-30, two of them publish catalogues that verify under
  the profile in {{DISCOVERY}}, and none of them runs a federating index.

No implementation of this document by another party is known.

--- back

# Implementation experience
{:numbered="false"}

* An index whose seed list contained its own URI recorded itself as a pending peer and
  contacted itself on every cycle. Its self check had covered only URIs taken from other
  indexes' `peers` members; {{crawl}} now applies the check to all three sources.
* A service operated by an unrelated party announced itself, failed the automatic checks
  because it published no catalogue, and remained visible to the operator as pending and
  indexed by nothing, as {{admission}} intends. It was later admitted.

# Changes from -00
{:numbered="false"}

Editorial: the text was shortened, and explanatory passages were removed or moved to the
appendix above. Implementation Status was updated. No normative requirement changed.

# Acknowledgements
{:numbered="false"}

Thanks to the authors of {{I-D.jimenez-dawn-discovery-landscape}}.
