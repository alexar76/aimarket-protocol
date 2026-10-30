---
title: "Federation Between Capability Indexes: Crawl, Reciprocal Identification and Admission"
abbrev: "Index Federation"
docname: draft-artamokhov-dawn-index-federation-00
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
      Internet-Draft: draft-artamokhov-dawn-marketplace-discovery-00
informative:
  RFC6648:
  RFC7942:
  RFC9162:
  I-D.jimenez-dawn-discovery-landscape:
  I-D.kay-dawn-use-cases:
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

Independently operated indexes of invocable capabilities do not interoperate: an agent that
queries one index cannot see what another lists, and a provider must enrol with every index
separately. This document specifies how such indexes find one another by following discovery
documents, how an index identifies itself to the indexes it reads so that discovery is not
one-directional, and an admission model that separates knowing a peer exists from indexing
its catalogue, so that an open federation does not become an open injection point. It also
specifies how an index may preview a peer's catalogue before admitting it. Payment, identity,
reputation and invocation are out of scope. The document is offered as input to the gap
analysis on federation between directories.

--- middle

# Introduction

A survey of two widely used public indexes of paid capabilities, conducted while preparing
this document, found no overlap between their listings, with total counts differing by nearly
a factor of two. Discovery is partitioned: whichever index an agent asks, it sees a fraction of
what exists, and a provider wanting to be found must enrol with each operator, which
reintroduces the gatekeeping machine-to-machine commerce was expected to remove.

{{I-D.jimenez-dawn-discovery-landscape}} reviews the directory and registry designs now in
use and names the lack of an interoperable federation standard between directories as an open
gap. The designs it surveys either federate through a shared distributed hash table and
content-addressed storage {{I-D.mp-agntcy-ads}}, through explicitly configured trust
relationships {{I-D.pioli-agent-discovery}}, or not at all: {{A2A}} specifies a per-agent
card and leaves registries to deployments, and {{MCPREG}} defines an upstream registry with
sub-registries that mirror it.

This document specifies a different and deliberately minimal arrangement: each index remains a
plain HTTPS server publishing a discovery document {{DISCOVERY}}; indexes find one another by
following those documents; an index that reads another says so; and an index decides for
itself, per peer, whether to index what the peer publishes. There is no shared infrastructure
to join and no central party to enrol with.

The authors are aware that catalogue exchange between indexes and trust between them are
outside the initial scope of the DAWN working group. This document is nevertheless written in
that group's vocabulary and against its use cases {{I-D.kay-dawn-use-cases}}, because the
mechanisms here are what the group's phase-one discovery leads to the moment two cooperating
indexes want to show each other's listings, and because the admission model in {{admission}}
is, in the authors' experience, the part most often got wrong.

## Scope and non-goals

This document specifies:

* a crawl protocol by which an index discovers peers through their discovery documents
  ({{crawl}});
* reciprocal identification, by which a reading index identifies itself to the index it
  reads ({{reciprocal}});
* an announcement message by which an index may make itself known to another
  ({{announce}});
* an admission model that separates visibility from trust ({{admission}});
* catalogue preview of a not-yet-admitted peer ({{preview}}).

This document does not specify: the payment mechanism used to purchase a capability; the
identity system naming a provider or an operator; any reputation or ranking algorithm; the
invocation protocol; or how two indexes resolve conflicting listings of the same capability.
An index MAY use any mechanism for these.

## Requirements Language

{::boilerplate bcp14-tagged}

## Terminology

Index, catalogue, discovery document, reader:
: As defined in {{DISCOVERY}}.

Peer:
: An index known to another index.

Admitted:
: A peer whose catalogue an index has chosen to index. See {{admission}}.

Pending:
: A peer an index knows to exist but has not admitted.

Operator:
: The party responsible for an index's admission decisions.

# Crawl protocol {#crawl}

An index discovers peers by retrieving discovery documents, starting from a locally configured
set of URIs (the seed list) and continuing through the `peers` member of each document
retrieved. For each peer the index retrieves the discovery document, then the catalogue it
references, verifies the catalogue as {{DISCOVERY}} requires, and stores what it chooses to
store.

An index MUST bound this traversal by depth from the seed list and by total number of peers
retrieved per cycle, and MUST repeat the cycle on a timer rather than on demand. The authors'
implementation uses a breadth-first traversal of depth three and a cycle of one hour; the
numbers are deployment choices and the bounds are not.

An index MUST serve queries from its own stored copy of a peer's catalogue and MUST NOT
retrieve a peer's documents while answering a query. A design in which a query fans out to
peers makes every index's availability the minimum of all its peers' availability, and makes
query latency a channel a hostile peer controls.

An index SHOULD send conditional requests ({{RFC9110}}, Section 13) when re-retrieving a
document it already holds, and an index serving discovery documents SHOULD answer them, so
that a federation of N indexes polling each other hourly transfers N^2 small responses rather
than N^2 catalogues.

An index MUST NOT crawl itself. Three paths lead a URI into the traversal — the seed list,
pending announcements and the `peers` of retrieved documents — and the authors' implementation
originally checked only the last, with the result that an index seeded with its own URI
registered itself as its own pending peer and dialled itself every cycle. Comparison MUST
normalise scheme, host case and path, since an index may be published under a path of a
shared host.

# Reciprocal identification {#reciprocal}

An index retrieving another index's discovery document MUST identify the index on whose
behalf it acts, using the `Agent-Marketplace-Crawler` request header field ({{iana-hdr}}):

~~~
GET /.well-known/agent-marketplace HTTP/1.1
Host: example.net
Agent-Marketplace-Crawler: https://crawler.example
~~~

The field value is the absolute URI {{RFC3986}} of the retrieving index's host, from which
its own discovery document can be derived.

Without this, discovery is one-directional: an index may read, catalogue and route buyers to a
peer that never learns it exists. The operator of a widely read index can be part of another
party's network with no means of finding out. Reciprocal identification makes the relationship
symmetric at the level of *awareness*, without making it symmetric at the level of *trust*.

A receiving index:

* SHOULD record the value, so its operator can enumerate the indexes that read it;
* MUST treat the value as an unauthenticated claim, and MUST NOT derive any trust from it;
* MUST validate the value as an absolute URI under the "https" scheme before storing it, and
  MUST apply the safeguards in {{security-ssrf}} before retrieving anything from it;
* MAY, under open admission ({{open-closed}}), record the identified index as a pending
  peer;
* SHOULD bound the number of distinct values it records.

Implementations SHOULD perform this processing outside the request path. The discovery
document is retrieved on a timer by every peer in the network, and an index that performs
name resolution while answering it has made its most requested resource as slow as its
slowest resolution.

# Announcement {#announce}

An index MAY make itself known to another index by sending an announcement: an HTTP POST to
an endpoint the receiving index publishes, carrying a JSON object {{RFC8259}} with the
following members:

| Member | Type | Requirement |
|---|---|---|
| `index_url` | string (URI) | REQUIRED |
| `discovery_url` | string (URI) | REQUIRED |
| `capabilities_count` | number | OPTIONAL |
| `signer_public_key` | string | OPTIONAL |
| `signature` | object | OPTIONAL |

Where present, `signature` is a signature object as defined in {{DISCOVERY}} over the
canonical string

~~~
hub_url:<index_url>|well_known_url:<discovery_url>|
capabilities_count:<n>
~~~

(shown on two lines for width; the string contains no line break)

under the same profile the announcing index names in its discovery document, with `<n>`
defaulting to `0`.

This canonical string binds no timestamp and no nonce. An announcement is therefore replayable
by design, and that is acceptable only because an announcement confers nothing
({{admission-rules}}). An implementation MUST NOT extend the authority of this signature to
any admission decision, and a verified announcement signature proves only that the announcer
holds the key it advertises.

The location of the announcement endpoint is a deployment matter in this revision; the
authors' implementation uses the path `/ai-market/v2/federation/announce`. A link from the
discovery document is the obvious improvement and is deferred to a -01.

# Admission {#admission}

An index MUST distinguish two questions that are frequently conflated:

1. Does this index know that a peer exists?
2. Does this index index that peer's catalogue?

Conflating them yields either a network nobody can join, or a network anyone can poison.

## States

An index MUST classify every peer it knows into exactly one of:

Pending:
: Known to exist. Nothing the peer publishes has any effect on this index: its catalogue is
  not indexed, not queryable and not routable, and its `peers` are not followed.

Admitted:
: The operator has chosen to index this peer's catalogue. What the index then does with the
  catalogue — ranking, routing, display — is governed by mechanisms outside this document.

An index MAY define further states that refine "admitted" (for example, admitted but
currently unreachable). It MUST NOT define a state in which a peer's catalogue has any effect
without operator admission.

## Open and closed admission {#open-closed}

An index MUST support **closed admission**, in which a peer becomes pending only through
operator action: a seed-list entry, or an announcement the operator has authorised out of
band.

An index MAY support **open admission**, in which an unauthenticated party can cause a
pending record to exist, either by announcement ({{announce}}) or by identifying itself
under {{reciprocal}}.

The two produce materially different networks. Under closed admission the federation grows
only as fast as operators talk to each other; under open admission any index can become
visible to any other with one request, and the admission rules below are what keep "visible"
from meaning "trusted".

## Rules {#admission-rules}

Where open admission is supported, all of the following MUST hold:

1. An unauthenticated announcement or reciprocal identification results in a pending peer,
   never an admitted one.
2. An announcement concerning an already-known peer MUST NOT modify any stored property of
   that peer — not its name, not its pinned key, not its state. A third party's claim about a
   peer an index already knows is evidence of nothing.
3. An index MUST bound the number of pending peers it accepts and MUST refuse further
   unauthenticated announcements once that bound is reached, with the 429 (Too Many Requests)
   status.
4. An announced or self-identified URI MUST pass the safeguards of {{security-ssrf}} before
   it is stored.
5. A pending peer MUST NOT appear in the `peers` member of the index's own discovery
   document.

Rule 5 is not a matter of taste. An index that republishes unverified peers lets any party
inject a URI into the network's traversal graph under a reputable index's name, at no cost
and with no accountability. The `peers` member of a discovery document is, under this
document, a statement by the operator that each listed peer has been admitted.

Open admission changes who may knock. It MUST NOT change who is trusted.

## Automatic assessment

An index MAY run automated checks against a pending peer — retrieving its discovery document,
verifying its catalogue signature, probing a listed capability — and MAY present the results
to its operator. It MAY also admit a peer automatically on the strength of such checks, but
where it does, the checks and their outcome MUST be recorded so that the admission is
attributable to a stated rule rather than to nothing, and the operator MUST be able to
reverse it. The authors' implementation records, for every pending peer, which checks it
failed, and shows them beside the peer; a stranger that announces itself and fails every check
stays visible as "pending, indexed by nothing" rather than disappearing, so that the operator
can see who knocked.

## Catalogue preview {#preview}

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
advertises and was not altered in transit. It establishes nothing about that key belonging to
a party worth trusting, and an interface that presents it as though it does is misleading its
operator at precisely the moment a security decision is being made.

# Relationship to other work

This section is informative.

{{I-D.mp-agntcy-ads}} federates directories through a Kademlia distributed hash table and
content-addressed OCI storage, with Sigstore-signed records. That gives global
content-addressed lookup at the cost of shared infrastructure every participant runs. The
arrangement here has no shared infrastructure: an index is an HTTPS server with a JSON
document, and two indexes federate by each deciding to read the other. The designs are not
exclusive; a DHT-backed directory could publish a discovery document and be admitted like
any other peer.

{{I-D.pioli-agent-discovery}} federates through explicitly configured trust relationships,
which corresponds to closed admission here. This document adds open admission with the rules
of {{admission-rules}}, so that a network can be joined without prior arrangement and still
not be poisoned.

{{A2A}} publishes a signed card per agent and leaves registries to deployments. A capability
index under this document is, from an A2A deployment's point of view, one such registry, and
an index MAY additionally publish an agent card for itself; the authors' implementation plans
to.

{{MCPREG}} defines one upstream registry mirrored by sub-registries. That is federation with
a root. Nothing here prevents an index from treating the upstream registry as an admitted
peer; what this document adds is the case where no party is upstream of another.

{{X402BAZAAR}} catalogues payable endpoints by having each endpoint declare metadata that a
payment facilitator records when a payment passes through it. Discovery there is a
side-effect of payment; here it is prior to and independent of payment, which is the
property a provider needs in order to be found before anyone has paid it.

Certificate Transparency {{RFC9162}} is not a directory design, but its separation of
"logged" from "trusted" is the same separation {{admission}} makes between "pending" and
"admitted", and for the same reason.

# Security Considerations

## Server-side request forgery {#security-ssrf}

Every mechanism in this document causes an index to retrieve a URI supplied by another party.
An index MUST therefore, before retrieving any URI obtained from a peer's discovery document,
an announcement, or the `Agent-Marketplace-Crawler` field:

* resolve the host and refuse addresses in private, loopback, link-local, multicast and
  unspecified ranges, including IPv4-mapped and IPv4-compatible IPv6 forms, naming the
  ranges explicitly rather than relying on a library's notion of "private", which differs
  between libraries;
* re-check the resolved address at connection time, or pin the connection to the checked
  address, to defeat rebinding between check and use;
* refuse to follow redirects automatically, since each hop requires its own check;
* bound response size and time.

An index that runs on a host shared with other services MUST additionally refuse to treat a
URI that resolves to its own host as a peer, since a peer on the same host can reach services
bound to loopback that the index's own checks would otherwise admit.

## Trust on first use and key change

An index MUST verify a peer's catalogue against the key it has pinned for that peer, as
{{DISCOVERY}} requires. A changed key is a visible failure, recorded for the operator, and
never accepted automatically. The federation therefore has no key-rotation protocol in this
revision; an index that rotates its key is, to every peer, a new index until each peer's
operator acts.

## Resource exhaustion

Open admission is an unauthenticated write. The bounds required in {{admission-rules}} are
the mitigation, and an implementation that omits them has published a way to fill its
storage. The traversal bounds in {{crawl}} are the corresponding mitigation on the reading
side: a peer that publishes a very large `peers` member, or a cycle of peers, must not be able
to make an index crawl without end.

## Split views

Nothing in this document prevents an index from serving different catalogues to different
readers. A reader that stores what it retrieved and verifies the signature can prove what it
was served, and two readers can compare; the document does not specify how. A transparency
mechanism in the style of {{RFC9162}} for catalogues would close this and is outside the
present scope.

## Privacy of reciprocal identification

The record described in {{reciprocal}} reveals which indexes read a given index. An
implementation SHOULD record only the self-declared URI and SHOULD NOT retain the client
network address, which is not needed for the purpose and creates a disclosure liability. An
index that does not wish to be enumerable as a reader has no option under this document other
than not reading; the authors consider that the right trade.

## What this document does not secure

This document specifies no payment, and a compliant index makes no claim about whether a
catalogued capability performs as described. Admission expresses an operator's judgement,
not a guarantee, and an index that routes buyers to an admitted peer's capability is
responsible to its buyers under whatever terms it sets, not under this document.

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

This section records the state of implementation at the time of writing, per {{RFC7942}},
and is to be removed before publication as an RFC.

The authors operate a reference implementation of the crawl protocol, reciprocal
identification, announcement, both admission modes, automatic assessment and catalogue
preview, distributed under Apache-2.0 together with a conformance runner and signed test
vectors. It is deployed on six public indexes operated by or affiliated with the authors, and
has run with open admission and reciprocal identification enabled since October 2026. The
current deployment uses the authors' pre-standard names (`/.well-known/ai-market.json`,
`X-AIMarket-Crawler`); an implementation submitting this document plans to accept both names
during a transition.

The largest of those indexes lists twenty-one admitted peers. Two are operated by parties with
no relation to the authors: one is a payment gateway that publishes a catalogue of paid
endpoints and was admitted after automatic assessment; the other announced itself, publishes
no catalogue, and remained visible as pending and indexed by nothing for three weeks before
the operator admitted it, which is the behaviour {{admission}} intends. Neither runs the
reference implementation.

A directory node in Go, implementing the crawl, discovery and announcement intake described
here, was written from the specification text and the vectors without reading the reference
source. It is by the specification's editor and therefore does not demonstrate
interoperability between parties with no common operator. **No independent implementation of
this document exists.** The authors consider that the material open question for this work.

The following requirements exist because their absence caused a concrete failure in the
authors' deployment, in the order the failures occurred: the self-crawl rule in {{crawl}}; the
bound on pending peers in {{admission-rules}}; the structural separation of previewed entries
in {{preview}}; the same-host rule in {{security-ssrf}}; and the requirement in the
automatic-assessment section that a stranger failing every check remain visible rather than
disappear.

--- back

# Acknowledgements
{:numbered="false"}

This document describes mechanisms arrived at by implementation rather than by design. The
authors thank the authors of {{I-D.jimenez-dawn-discovery-landscape}} for naming the gap this
document addresses, and the operators of the two unrelated indexes in the authors' federation
for joining a network with one operator and no promise.
