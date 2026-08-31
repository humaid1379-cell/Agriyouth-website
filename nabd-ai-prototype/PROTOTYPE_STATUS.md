# Prototype status

**Document version:** 1.0.0
**Environment:** `ISOLATED_PROTOTYPE_V1`
**Data boundary:** `SYNTHETIC_ONLY`
**Business scope:** `BUSINESS_UNIT_V1`

This document records exact component versions and four **independent** status dimensions.
It makes no operational or authorization claim. A generic `ready` or `production-ready`
status is never rendered anywhere in this repository, by design.

---

## 1. Status dimensions

The four dimensions are separate and are never merged into one value.

| Dimension | Value | What it would take to change |
|---|---|---|
| **Built** | `NOT_EVIDENCED` | Independent code review (gate G-B) accepting the developer-verification evidence pack |
| **Integration** | `NOT_EVIDENCED` | Independent TEVV (gate G-D) and deployment validation (gate G-E) accepted by an evaluator who did not author the code |
| **Operational** | `NOT_EVIDENCED` | Not applicable to this prototype. It runs in an isolated synthetic environment and is not operated |
| **Authorization** | `NOT_GRANTED` | A human owner, separate from the preparer and the evaluator, accepting a narrow status claim (gate G-F) |

Automated checks in this repository produce **candidate** developer-verification evidence
(gate G-A). A developer cannot accept their own evidence, so no dimension advances on the
strength of a passing test run, a green CI job or a build summary.

---

## 2. Component versions

| Component | Version |
|---|---|
| Workflow | `workflow-v1.0.0` |
| Schema | `nabd-schema-v1` |
| Canonical JSON profile | `nabd-canonical-json-v1` |
| Rule catalog | `rule-catalog-v1.0.0` |
| Corpus | `synthetic_policy_collection_v1` |
| Retrieval | `retrieval-lexical-v1.0.0` |
| Draft prompt | `prompt-draft-v1.0.0` |
| Verifier prompt | `prompt-verify-v1.0.0` |
| Packet schema | `decision-readiness-packet-v1` |
| Audit chain | `audit-chain-sha256-v1` |
| Use-case contract | `UC-POLICY-SOP-EVIDENCE-V1` |
| Injection pattern set | `injection-patterns-v1.0.0` |
| Packet notices | `packet-notices-v1.0.0` |
| TEVV plan | `tevv-plan-v1.0.0` |
| Authorization fixture | `SYNTHETIC_DEMO_AUTHORIZATION` (test fixture, `NOT_GRANTED`) |
| Corpus manifest SHA-256 | `6dfcef807e120ef197a321290d297cfe007029c5104b57c7984d13141c98b944` |

Model configurations, both pinned and both in mock mode:

| Configuration | Task role | Revision | Prompt | Tools | Fallback |
|---|---|---|---|---|---|
| `MC-MOCK-DRAFTER-V1` | `DRAFTER` | `deterministic-mock-1.0.0` | `prompt-draft-v1.0.0` | Disabled | Disabled |
| `MC-MOCK-VERIFIER-V1` | `VERIFIER` | `deterministic-mock-1.0.0` | `prompt-verify-v1.0.0` | Disabled | Disabled |

Live-model evaluation is `NOT_RUN`. The optional live adapter exists and is guarded, but no
live endpoint was configured or exercised in this build.

---

## 3. Runtime stack as built

| Layer | Choice | Note |
|---|---|---|
| API | Python 3.12, FastAPI 0.115.6, Pydantic 2.10.4, SQLAlchemy 2.0.36, Alembic 1.14.0 | Closed schemas, explicit service layers |
| Database | PostgreSQL 16 | SQLite permitted only in isolated unit tests |
| Retrieval | PostgreSQL full-text search over a stored generated `tsvector` | `pgvector` optional and disabled by default |
| Seed parsing | PyMuPDF 1.25.1, seeding only | Renders a derived read-only PDF facsimile and cross-checks page counts |
| UI | React 19, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Zod | Bilingual English and Arabic, accessible |
| Packaging | Docker Compose: `db`, `api`, `web` | Pinned tags, health checks, non-root, read-only corpus mount |

### Recorded stack substitutions

1. **Corpus authoring format.** Sources are authored as normalised UTF-8 text with explicit
   `<<<PAGE n>>>` markers and `## ` section headings rather than committed as binary PDFs,
   so that character offsets are exactly reproducible and diff-reviewable. PyMuPDF is still
   used during seeding, to render a derived read-only PDF facsimile of each source and to
   cross-check its page count against the parsed structure. There is no runtime upload or
   ingestion path either way.
2. **Fixture location.** Control-plane fixtures live in `data/fixtures/`, alongside the
   corpus in `data/synthetic_policy_collection_v1/`.
3. **Packet seal ordering.** A packet carries its pre-issuance audit event id inside its own
   sealed preimage, so the event id is generated before sealing and the event is written
   afterwards binding the resulting hash. The hash sealed at pre-issuance is retained
   separately in `decision_packets.issued_sha256`, because attaching a disposition reseals
   the packet and changes its current hash. Display and disposition bind the issued hash.

---

## 4. Verification performed in this build

All figures are exact numerators over denominators. They are candidate developer-verification
evidence, produced by the implementation team, and they are not an acceptance of anything.

| Check | Command | Result |
|---|---|---|
| Corpus manifest currency | `make manifest-check` | Current at `6dfcef80…c98b944` |
| JSON Schema currency | `make schemas-check` | 27/27 schemas current |
| Python lint and format | `ruff check`, `ruff format --check` | 0 findings across 72 files |
| Python static types | `mypy app` (strict) | 0 errors across 55 source files |
| Frontend lint | `eslint .` | 0 findings |
| Frontend static types | `tsc --noEmit` | 0 errors |
| Backend tests | `make test-api` | **276/276 passed** — 148 unit, 101 integration, 27 security |
| Frontend tests | `make test-web` | **16/16 passed** |
| End-to-end tests | `make test-e2e` | **30/30 passed** — 15 scenarios in each of the `ltr` and `rtl` projects |
| Frozen TEVV suite | `make tevv` | **31/31 passed** — 0 failed, 0 blocked, 0 not run |
| Audit chain verification | `make audit-verify` | **287/287 chains verified** |
| Deployment validation | `make deployment-validate` | **11/12 passed** — 0 failed, 1 not run |
| Evidence bundle | `make evidence-bundle` | 72 artifacts with a manifest and SHA-256 checksums |

Not run in this build, with reasons:

* **Live-model evaluation** — the default mode is the deterministic mock. No live endpoint
  was configured or exercised, so live-mode behaviour is `NOT_RUN`.
* **Docker Compose image build** — Docker is unavailable in the build environment, so
  deployment-validation check 1 is `NOT_RUN`. The API package installs from the same
  `apps/api/pyproject.toml` dependency set the image installs, and the web bundle builds
  with the same `npm run build` the image runs, but neither image was assembled.
* **Image rollback** — only one build exists in this environment, so there is no previous
  pinned image to roll back to. The schema rollback and re-upgrade were exercised.
* **Manual browser accessibility smoke test** — automated checks cover bilingual direction,
  keyboard reachability, focus visibility and colour-independent status. A human pass with
  assistive technology has not been performed.

---

## 5. Bounded V1 scope

| Binding boundary | Value |
|---|---|
| Environment | `ISOLATED_PROTOTYPE_V1` local workbench |
| Data | `SYNTHETIC_ONLY`, versioned frozen source corpus |
| Business scope | `BUSINESS_UNIT_V1` only |
| Question | One bounded internal policy or SOP evidence question |
| AI calls | Two maximum: one bounded draft, one independent verifier |
| Model configuration | Exactly one pinned configuration per task role per run |
| Outputs | Decision Readiness Packet and controlled test records |
| Routes | `HUMAN_REVIEW_REQUIRED` or `CANNOT_PROCEED` |
| Dispositions | `RETURN_FOR_CLARIFICATION`, `ACCEPT_AS_TEST_EVIDENCE`, `REJECT_AS_TEST_EVIDENCE` |

The prototype does not use real, personal, customer, confidential, institutional, clinical,
legal, financial or production data, and it connects to no identity provider, document
repository, email service, messaging platform, ticketing system, webhook, payment service,
operational database, browser or search engine.

---

## 6. Assurance gates

The sequence is strict. A failed stage blocks movement until correction and targeted
regression, and failed evidence is retained visibly rather than overwritten.

| Gate | Activity | State |
|---|---|---|
| G-A | Developer verification | Performed in this build; **not self-acceptable** |
| G-B | Independent code review | `NOT_STARTED` — template at `artifacts/templates/independent_code_review.md` |
| G-C | Independent security testing | `NOT_STARTED` — template at `artifacts/templates/security_test_report.md` |
| G-D | Independent TEVV | `NOT_STARTED` — template at `artifacts/templates/tevv_report.md` |
| G-E | Deployment validation | `NOT_STARTED` — template at `artifacts/templates/deployment_validation_checklist.md` |
| G-F | Human-owner evidence acceptance | `NOT_STARTED` — template at `artifacts/templates/human_owner_acceptance_record.md` |

The three-function separation is mandatory. The technical owner prepares code and developer
evidence; an independent evaluator reviews code, security, TEVV and deployment results; a
human owner or delegate accepts or rejects a narrow evidence or status claim. One identity
must not perform all three functions for the same component, version, status dimension and
evidence set.

---

## 7. Known limitations

Recorded in full at `artifacts/templates/known_limitations.md`. In summary: this is a
synthetic-only prototype; live-model evaluation is `NOT_RUN`; benign-case threshold coverage
is incomplete against the Section 16.2 target because the frozen plan implements 2 benign
scenarios where the target requires at least 60; and no independent review, security test,
TEVV, deployment validation or owner acceptance has been performed.

---

| Dimension | Value |
|---|---|
| Built | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` |
