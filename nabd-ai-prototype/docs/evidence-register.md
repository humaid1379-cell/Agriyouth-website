# Evidence register

**Document version:** 1.0.0
**Environment:** `ISOLATED_PROTOTYPE_V1`

This document explains how evidence artifacts are produced, inventoried, hashed and
accepted for this prototype. It is a description of the process. It is not itself evidence,
and it accepts nothing.

---

## 1. What counts as evidence

An evidence artifact is a retained, hashed record of something that was actually executed
or reviewed, tied to exact component versions and to the environment it ran in. A summary,
a screenshot without a hash, a passing CI badge or an assistant's report is not evidence.

Every artifact carries: the component and version it concerns, the status dimension it
speaks to, its type, its path, its SHA-256, the environment, the period, the **narrow**
claim it supports, its limitations, who prepared it, who evaluated it, who accepted it, the
decision, an expiry, and a revocation path.

The narrow claim matters more than the artifact. "The frozen TEVV suite executed 31 of 31
scenarios with 31 passes against corpus manifest `6dfcef80…` on this date" is a narrow
claim. "The system works" is not a claim anyone can accept.

---

## 2. Artifact types produced by this repository

| Type | Produced by | Speaks to | Retained at |
|---|---|---|---|
| Corpus manifest | `scripts/build_corpus_manifest.py` | Built | `data/synthetic_policy_collection_v1/manifest.json` |
| JSON Schema contracts | `scripts/export_json_schemas.py` | Built | `contracts/jsonschema/` |
| OpenAPI contract | Application export | Built, Integration | `contracts/openapi.json` |
| Backend test report | `make test-api` | Built | Terminal output and coverage under `artifacts/coverage/` |
| Frontend test report | `make test-web` | Built | Terminal output |
| End-to-end report | `make test-e2e` | Integration | `artifacts/e2e/` |
| TEVV raw report | `make tevv` | Integration | `artifacts/tevv/tevv_report_<timestamp>.json` |
| Audit chain verification | `make audit-verify` | Integration | Terminal output, or JSON with `--json` |
| Evidence bundle | `make evidence-bundle` | Built, Integration | `artifacts/evidence_bundle_<timestamp>/` |

Each of these is **candidate developer-verification evidence** (gate G-A) when the
implementation team runs it. None of them advances a status dimension on its own.

---

## 3. The evidence bundle

`scripts/export_evidence_bundle.py` assembles a timestamped directory containing:

* `MANIFEST.json` — the inventory: bundle id, generation time, environment, git commit,
  component versions, corpus manifest hash, the rule catalog, every artifact with its path,
  SHA-256 and size, the four status dimensions at their defaults, an acceptance state of
  `NOT_ACCEPTED`, and the three-function separation rule;
* `SHA256SUMS` — checksums in the standard format, verifiable with `sha256sum -c`;
* `README.md` — what the bundle is, and explicitly what it is not;
* `files/` — a copy of every inventoried artifact, so a reviewer can verify hashes against
  content without needing the original working tree.

The manifest carries its own `manifest_sha256`, computed over the canonical serialization
of the manifest with that field omitted, using the same `nabd-canonical-json-v1` profile as
the packet seal.

To verify a bundle:

```bash
cd artifacts/evidence_bundle_<timestamp>
sha256sum -c SHA256SUMS
```

---

## 4. The register itself

The register template is `artifacts/templates/evidence_register.csv`, and the
machine-readable inventory template is
`artifacts/templates/release_evidence_index.json`. Both are blank templates for completion
by the parties named in each row. They are deliberately not pre-filled: an evidence record
that arrives already asserting its own acceptance is not evidence of anything.

`EvidenceRecord` in `apps/api/app/schemas/packet.py` is the typed form of a register row.
It enforces the three-function separation in code: if a record names a preparer, an
evaluator and an acceptor, all three must be distinct identities. `StatusRecord` in
`apps/api/app/schemas/governance.py` enforces the same principle for status claims — a
record cannot accept its own.

---

## 5. Acceptance

The only human-owner acceptance outcomes are `ACCEPT_BUILT_EVIDENCE`,
`ACCEPT_INTEGRATION_EVIDENCE`, `ACCEPT_WITH_CONDITIONS`, `REJECT_EVIDENCE`,
`REQUEST_RETEST` and `STOP_AND_REVISE`. An acceptance record defaults Operational to
`NOT_EVIDENCED` and Authorization to `NOT_GRANTED`, and never contains "approve action",
"activate system", "go live" or "production-ready".

Acceptance is the sixth of six ordered gates:

1. **G-A** Developer verification — the implementation team may execute, but cannot accept
   its own evidence.
2. **G-B** Independent code review — the reviewer did not author the reviewed changes.
3. **G-C** Independent security testing — the tester is separate from the primary
   developer, with no real data or credentials.
4. **G-D** TEVV — the executor and evaluator are independent of the sole code author where
   feasible.
5. **G-E** Deployment validation — a separate validator, or a clean environment.
6. **G-F** Human-owner evidence acceptance — the owner accepts the evidence presented but
   cannot replace missing tests or certify their own work.

A failed stage blocks movement until correction and targeted regression. Failed evidence is
retained visibly and is never overwritten. Any unresolved `S0_CRITICAL` or `S1_HIGH` defect
blocks acceptance of the affected release.

---

## 6. Current state

No independent review, security test, TEVV, deployment validation or owner acceptance has
been performed for this build. Every register row is therefore `NOT_ACCEPTED`, and the four
status dimensions stand at their defaults.

---

| Dimension | Value |
|---|---|
| Built | `NOT_EVIDENCED` |
| Integration | `NOT_EVIDENCED` |
| Operational | `NOT_EVIDENCED` |
| Authorization | `NOT_GRANTED` |
