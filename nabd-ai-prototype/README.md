# NABD AI Decision Review

**Governed intelligence. Human authority.**

An isolated, synthetic-only prototype that answers one bounded internal policy or standard
operating procedure question, cites exactly where each claim comes from, applies
deterministic rules that outrank the model, and prepares a sealed **Decision Readiness
Packet** for an authorised human reviewer.

It supports and prepares a decision. It does not make one, and it cannot act on one.

| | |
|---|---|
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Routes | `HUMAN_REVIEW_REQUIRED` or `CANNOT_PROCEED` — there is no auto-approve route |
| Model calls | Two maximum per case: one bounded draft, one independent verifier |
| Default model mode | `mock` — deterministic, in process, no credentials, no network |
| Built | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` |

---

## What it does

A synthetic requester asks one bounded question about a frozen synthetic policy corpus. The
system then, in a fixed order that code owns rather than a model:

1. checks an exact synthetic authorization fixture, then the requester's server-derived
   session, before anything else happens;
2. normalises the request and rejects anything that seeks an action rather than evidence;
3. decides which sources are eligible — active, in scope, permitted, hash-matched and not
   quarantined — **before** any retrieval and **before** any model call;
4. retrieves exactly located passages, each labelled untrusted content;
5. calls a model twice and only twice: once to draft candidate claims, once to verify each
   claim independently against the admitted passages;
6. re-slices every quoted span from the stored excerpt itself, so the verifier's word is
   never taken for it;
7. applies fifteen deterministic rules whose failure always outranks model confidence;
8. assembles a canonical JSON packet, validates eleven semantic invariants, seals it with
   SHA-256, and records a confirmed pre-issuance audit event before the packet may be seen;
9. waits for a separate authorised reviewer, who must be someone other than the requester
   and must write a substantive rationale;
10. records a test-only disposition, confirms a distinct later closure audit event, and
    seals the record. Nothing downstream is triggered, because there is nothing downstream
    to trigger.

Any control failure at any step produces a reason-coded `CANNOT_PROCEED` stop rather than a
degraded answer.

---

## Quick start

Requires Docker and Docker Compose.

```bash
cp .env.example .env
make up
make migrate
make seed
make test
make tevv
make audit-verify CASE_ID=<case-id>
make evidence-bundle
make down
```

The API is at `http://localhost:8000` (OpenAPI at `/api/docs`), the web application at
`http://localhost:5173`. Sign in by selecting one of three synthetic demo profiles; there
is no password, because there is no real identity system.

Run `make help` for every target.

### Running natively instead of in Docker

The repository's own development loop uses a native Python interpreter and a local
PostgreSQL 16 instance. Add `LOCAL=1` to the Python targets:

```bash
make install
createdb nabd_prototype && createdb nabd_prototype_test
psql -f scripts/sql/bootstrap_roles.sql
LOCAL=1 make migrate seed
make test-api tevv
```

`make test-api` always runs against a database whose name contains `test`, and refuses to
run otherwise. The suite truncates tables between tests, so this guard is deliberate.

---

## Demo profiles

| Profile | Can | Cannot |
|---|---|---|
| `requester.analyst@demo.nabd.local` | Create and view its own cases, packets, evidence, audit and lineage | Review or dispose of any case, including its own; modify sources or configuration |
| `reviewer.manager@demo.nabd.local` | View the review queue, packets, evidence, audit and lineage; submit a test-only disposition | Request a case; modify rules, sources, the gate or configuration |
| `admin.platform@demo.nabd.local` | Inspect non-secret configuration, verify audit chains, run TEVV, toggle the kill switch | Grant authorization; submit or review a case; modify source content; read case content |

The browser selects a profile by identifier only. Role, scope, authority and
separation-of-duties facts are derived server-side from a short-lived signed session and
the seeded fixture; the client never submits them.

Expired, revoked, unknown and cross-scope identities exist as fixtures for denial tests and
cannot obtain a session.

---

## Try the two headline paths

**A packet that reaches human review.** As the requester, ask:

> What evidence must accompany an internal policy exception request in the Corporate
> Services Unit, and who is required to review a Tier 2 request?

You get `HUMAN_REVIEW_REQUIRED`, a claim ledger where every material claim is supported by
an exact page-and-offset citation, and a sealed packet. Switch to the reviewer profile to
record a test-only disposition.

**A stop that fails closed.** As the requester, ask:

> Within how many business days must a reviewer complete an exception review where the
> exception file affects access to restricted records?

Two active, in-scope sources answer that differently, so the declared conflict fires and the
case stops with `CANNOT_PROCEED: EVIDENCE_INSUFFICIENT_OR_CONFLICTED` **before** any model
call. The system escalates rather than choosing between two authorities.

---

## Repository layout

```text
nabd-ai-prototype/
├── README.md                      This file
├── SECURITY_BOUNDARIES.md         Prohibited-connection inventory and enforcement
├── PROTOTYPE_STATUS.md            Component versions and the four status dimensions
├── docker-compose.yml             db, api, web
├── Makefile                       Every documented command
├── docs/                          Architecture, API, rules, governance, threats, TEVV
├── references/roadmap/            The nine supplied roadmap images and their checksums
├── data/
│   ├── synthetic_policy_collection_v1/   Frozen corpus, manifest, conflicts, revocations, TEVV plan
│   └── fixtures/                  Authorization, use-case contract, identities, model configurations
├── contracts/
│   ├── openapi.json               The live API contract
│   └── jsonschema/                27 closed schemas for every privileged boundary object
├── apps/
│   ├── api/                       FastAPI service, Alembic migrations, tests
│   └── web/                       React SPA
├── tests/e2e/                     Playwright end-to-end tests
├── scripts/                       Seeding, manifest, schemas, audit verify, TEVV, evidence bundle
└── artifacts/templates/           The nine assurance templates for independent parties
```

---

## Boundaries, stated plainly

This prototype does **not**: use real, personal, customer, confidential, institutional,
clinical, legal, financial or production data; connect to an identity provider, document
repository, email service, messaging platform, ticketing system, webhook, payment service,
operational database, browser or search engine; accept document uploads or dynamic
ingestion; run autonomous agent loops; let a model call a tool, select a route, waive a rule
or change a permission; fall back to another provider or model; or approve, execute,
transmit or activate anything.

In default mock mode the whole stack runs with no outbound internet access and no
credentials. See `SECURITY_BOUNDARIES.md` for the enforced inventory and
`docs/threat-model.md` for the threat analysis and residual risks.

### What "done" does and does not mean here

Every automated check in this repository produces **candidate developer-verification
evidence** (gate G-A). That is the first of six ordered assurance gates. Independent code
review, independent security testing, independent TEVV, deployment validation and
human-owner acceptance are separate gates, each requiring a person who did not do the
preceding work. Blank templates for all of them are in `artifacts/templates/`.

A developer, a model, an evaluator, an administrator or an evidence record cannot accept its
own status claim. That is why all four status dimensions above read `NOT_EVIDENCED` and
`NOT_GRANTED`, and why nothing in this repository describes itself as production ready,
compliant, secure without qualification or free of hallucinations.

---

## Documentation

| Document | Contents |
|---|---|
| `docs/architecture.md` | Trust boundaries, control and data plane, where each invariant lives in code |
| `docs/api-contract.md` | Every endpoint, role, shape and failure code |
| `docs/rule-catalog.md` | The 15 deterministic rules, precedence, and the 20-state workflow |
| `docs/source-governance.md` | The frozen corpus, eligibility, retrieval, conflicts and revocations |
| `docs/model-configuration-card.md` | Both pinned configurations, the call budget, and live mode |
| `docs/threat-model.md` | Threats, containing controls, proving tests, residual risk |
| `docs/tevv-plan.md` | The 31 frozen scenarios, acceptance targets, and coverage gaps |
| `docs/evidence-register.md` | How evidence artifacts are inventoried and accepted |

---

## Licence and provenance

The synthetic corpus, identities and organisational names in this repository are invented
for the prototype and describe no real institution. The nine roadmap images in
`references/roadmap/` are the supplied planning context; where they conflict with the build
specification, the specification governs, and the mapping is recorded in
`docs/architecture.md`.
