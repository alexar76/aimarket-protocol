---
title: "Federated Discovery and Admission for Agent Marketplaces"
abbrev: "Agent Marketplace Federation"
docname: draft-AUTHOR-agent-marketplace-federation-00
category: exp
ipr: trust200902
area: ART
workgroup: Independent Submission
keyword:
  - agents
  - discovery
  - marketplace
  - federation
stand_alone: yes
pi: [toc, sortrefs, symrefs]
author:
  -
    ins: A. AUTHOR
    name: AUTHOR NAME
    organization: Independent
    email: AUTHOR@EXAMPLE.COM
normative:
  RFC2119:
  RFC3986:
  RFC8174:
  RFC8615:
  RFC8032:
  RFC9110:
  RFC8259:
informative:
  RFC6648:
  RFC7942:
--- abstract

Autonomous software agents increasingly obtain capabilities from third-party services
listed in machine-readable indexes. Existing indexes are operated independently and do not
interoperate: an agent that queries one index cannot see capabilities listed in another, and
a capability provider must enrol separately with every index it wishes to appear in. This
document specifies a discovery document, a crawl protocol, and an admission model that allow
independently operated marketplace indexes to discover one another and to serve a merged
view without a central registry. It defines a reciprocal identification mechanism so that an
index learns of indexes that read it, and an admission model that separates being *visible*
from being *trusted*, so that an open discovery network does not become an open injection
point.

--- middle

# Introduction

Machine-readable indexes of purchasable capabilities have appeared rapidly alongside
protocols for machine payment. Each such index is operated by a single party and catalogues
only what that party observes. In practice this has produced disjoint catalogues: a survey
of two widely used public indexes conducted while preparing this document found no overlap
between their listings, with total counts differing by nearly a factor of two.

The consequence for an agent is that discovery is partitioned. The consequence for a
provider is that visibility requires enrolling with each operator separately, which
reintroduces exactly the gatekeeping that machine-to-machine commerce is expected to remove.

This document does not specify payment, identity, or reputation. Those are addressed by
other work, and this specification is intended to compose with them rather than replace
them. It specifies only the layer at which independently operated indexes find each other
and exchange catalogues.

## Scope and non-goals

This document specifies:

* a discovery document served at a well-known URI ({{discovery}});
* a crawl protocol between indexes, including reciprocal identification ({{crawl}});
* an admission model distinguishing visibility from trust ({{admission}}).

This document does not specify: the payment mechanism used to purchase a capability; the
identity system used to name a provider; the reputation algorithm used to rank one; or the
invocation protocol used to execute one. An index MAY use any of these.

## Requirements Language

{::boilerplate bcp14-tagged}

## Terminology

Index:
: A server that catalogues capabilities and answers queries about them. Also called a hub.

Peer:
: An index known to another index.

Capability:
: A named, invocable unit of work offered by a provider and catalogued by an index.

Discovery document:
: The JSON document defined in {{discovery}}, served at a well-known URI.

Admitted:
: A peer whose catalogue an index has chosen to index. See {{admission}}.

Pending:
: A peer an index knows to exist but has not admitted.

# Discovery document {#discovery}

An index MUST serve a discovery document at the well-known URI
`/.well-known/agent-marketplace` (see {{iana-wk}}), using the "https" scheme, and MUST answer
both GET and HEAD requests for it.

The document is a JSON object {{RFC8259}}. The following members are defined:

| Member | Type | Requirement |
|---|---|---|
| `name` | string | REQUIRED |
| `protocol_versions` | array of string | REQUIRED |
| `manifest_url` | string (URI) | REQUIRED |
| `capabilities_count` | number | RECOMMENDED |
| `signer_public_key` | string | RECOMMENDED |
| `peers` | array of object | OPTIONAL |
| `federation` | object | OPTIONAL |

An index MUST ignore members it does not recognise. An index MUST NOT fail to parse a
document because it carries an unknown member; extension by addition is the intended
evolution path.

`manifest_url` identifies a document listing the index's catalogue. That document SHOULD be
signed; a signature scheme is out of scope here, but where Ed25519 {{RFC8032}} is used, the
signed byte string MUST be specified by the profile in use rather than left implicit. An
unspecified canonicalisation is the most common source of interoperability failure in
signed-document systems, and it is silent: implementations disagree only at verification
time, in production, against documents that look correct.

`peers`, when present, lists peers the index has admitted. An index MUST NOT list a pending
peer here; see {{admission-rules}}.

# Crawl protocol {#crawl}

An index discovers peers by retrieving discovery documents, starting from a
locally configured set of URIs and continuing through the `peers` member of each document
retrieved. An index MUST bound this traversal by depth and by total peers retrieved.

An index MUST serve queries from its own stored copy of a peer's catalogue and MUST NOT
retrieve a peer's document while answering a query. A design in which a query fans out to
peers makes every index's availability the minimum of all its peers' availability, and makes
query latency a channel a hostile peer controls.

## Reciprocal identification {#reciprocal}

An index retrieving another index's discovery document MUST identify the index on whose
behalf it acts, using the `Agent-Marketplace-Crawler` header field ({{iana-hdr}}):

~~~
GET /.well-known/agent-marketplace HTTP/1.1
Host: example.net
Agent-Marketplace-Crawler: https://crawler.example
~~~

The field value is the absolute URI {{RFC3986}} of the retrieving index.

Without this, discovery is one-directional: an index may read, catalogue and route buyers to
a peer that never learns it exists. The operator of a widely read index can be part of
another party's network with no means of finding out. Reciprocal identification makes the
relationship symmetric at the level of *awareness*, without making it symmetric at the level
of *trust*.

A receiving index:

* SHOULD record the value, so its operator can enumerate the indexes that read it;
* MUST treat the value as an unauthenticated claim, and MUST NOT derive any trust from it;
* MUST validate the value as an absolute URI before storing it, and MUST apply the
  safeguards in {{security-ssrf}} before retrieving it;
* SHOULD bound the number of distinct values it records.

Implementations SHOULD perform this processing outside the request path. The discovery
document is retrieved on a timer by every peer in the network, and an index that performs
name resolution while answering it has made its most requested resource as slow as its
slowest resolution.

# Admission {#admission}

An index MUST distinguish two questions that are frequently conflated:

1. Does this index know that a peer exists?
2. Does this index index that peer's catalogue?

Conflating them yields either a network nobody can join, or a network anyone can poison.

## States

An index MUST classify every peer it knows into exactly one of:

Pending:
: Known to exist. Nothing the peer publishes has any effect on this index.

Admitted:
: The operator has chosen to index this peer's catalogue.

## Open and closed admission

An index MUST support **closed admission**, in which a peer becomes pending only through
operator action.

An index MAY support **open admission**, in which an unauthenticated party can cause a
pending record to exist, either by announcement or by identifying itself under
{{reciprocal}}.

## Rules {#admission-rules}

Where open admission is supported, all of the following MUST hold:

1. An unauthenticated announcement results in a pending peer, never an admitted one.
2. An announcement concerning an already-known peer MUST NOT modify any stored property of
   that peer. A third party's claim about a peer an index already knows is evidence of
   nothing.
3. An index MUST bound the number of pending peers it accepts and MUST refuse further
   unauthenticated announcements once that bound is reached.
4. An announced URI MUST pass the safeguards of {{security-ssrf}} before it is stored.
5. A pending peer MUST NOT appear in the `peers` member of the index's own discovery
   document.

Rule 5 is not a matter of taste. An index that republishes unverified peers lets any party
inject a URI into the network's traversal graph under a reputable index's name, at no cost
and with no accountability.

Open admission changes who may knock. It MUST NOT change who is trusted.

## Catalogue preview

An index MAY retrieve and display a pending peer's catalogue so that an operator can decide
whether to admit it. Where it does:

1. The catalogue MUST be validated, and its signature verified where one is present, exactly
   as for an admitted peer.
2. Previewed entries MUST NOT be returned from queries, MUST NOT be routable, and MUST NOT
   appear in the index's own published catalogue. Implementations SHOULD achieve this
   structurally, by storing preview entries outside the store that query paths read, rather
   than by filtering. A filter can be forgotten by a query written later; a separate store
   cannot.
3. Any interface presenting previewed entries MUST mark them as not admitted.

Verification of a preview establishes only that the catalogue was signed by the key the peer
advertises and was not altered in transit. It establishes nothing about that key belonging
to a party worth trusting, and an interface that presents it as though it does is misleading
its operator at precisely the moment a security decision is being made.

# Security Considerations

## Server-side request forgery {#security-ssrf}

Every mechanism in this document causes an index to retrieve a URI supplied by another
party. An index MUST therefore, before retrieving any URI obtained from a peer, an
announcement, or the `Agent-Marketplace-Crawler` field:

* resolve the host and refuse addresses in private, loopback, link-local, multicast and
  unspecified ranges, including IPv4-mapped and IPv4-compatible IPv6 forms;
* re-check the resolved address at connection time, or pin the connection to the checked
  address, to defeat rebinding between check and use;
* refuse to follow redirects automatically, since each hop requires its own check;
* bound response size and time.

## Trust on first use

An index that pins a peer's key on first contact and thereafter refuses a changed key
converts a silent takeover into a visible failure. Implementations SHOULD do this, SHOULD
record the rejected key for the operator, and MUST NOT accept a key change automatically. A
key rotation is an operator decision.

An index MUST verify a peer's documents against the key it has pinned for that peer, not
against a key carried inside the document. A document signed by an attacker's key verifies
perfectly against that same key.

## Resource exhaustion

Open admission is an unauthenticated write. The bounds required in {{admission-rules}} are
the mitigation, and an implementation that omits them has published a way to fill its
storage.

## Privacy of reciprocal identification

The record described in {{reciprocal}} reveals which indexes read a given index. An
implementation SHOULD record only the self-declared URI and SHOULD NOT retain the client
network address, which is not needed for the purpose and creates a disclosure liability.

## What this document does not secure

This document specifies no payment, and a compliant index makes no claim about whether a
catalogued capability performs as described. Admission expresses an operator's judgement,
not a guarantee.

# IANA Considerations

## Well-Known URI registration {#iana-wk}

IANA is requested to register the following in the "Well-Known URIs" registry established by
{{RFC8615}}:

URI suffix:
: agent-marketplace

Change controller:
: IESG

Specification document:
: This document

Status:
: permanent

Related information:
: The resource is a JSON document as specified in {{discovery}}.

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

This section records the state of implementation at the time of writing, per {{RFC7942}},
and is to be removed before publication as an RFC.

The authors operate a reference implementation of the discovery document, crawl protocol,
reciprocal identification and admission model described here. It is distributed under an open
source licence together with a conformance runner and signed test vectors, including negative
vectors that MUST be rejected.

Two limits are stated deliberately, because a reviewer who discovers them unaided will
discount everything else in this document. First, **no independent implementation exists**:
every implementation the authors know of is their own, so the interoperability this
specification exists to enable has not been demonstrated between parties with no common
operator. Second, at the time of writing the admission and reciprocal-identification
mechanisms are **implemented but not yet deployed** on the authors' public instance; what is
publicly reachable today is the discovery document and crawl protocol without them.

The authors consider the first of these the material open question for this work.

--- back

# Acknowledgements
{:numbered="false"}

This document describes mechanisms arrived at by implementation rather than by design, and
several of its requirements exist because their absence caused a concrete failure first.
