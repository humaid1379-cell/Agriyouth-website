# Human-Owner Evidence Acceptance Record — NABD AI Decision Review

## 0. Template control block

| Field | Value |
|---|---|
| Template ID | `TPL-HUMAN-OWNER-ACCEPTANCE-RECORD-V1` |
| Template version | `1.0.0` |
| Template kind | `CONTROL_ARTIFACT` |
| Assurance gate | `G-F — Human-owner evidence acceptance` |
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Controlling specification | `docs/NABD_AI_CURSOR_FULL_PROTOTYPE_BUILD_SPEC.md`, Sections 3, 7.1, 17, 17.1, 17.2 |
| Preceding gate | `G-E — Deployment validation` |
| Following gate | None. This is the final gate in the V1 assurance order. |
| Completion state | `<PENDING>` |

> **Control artifact notice.** This template is a control artifact. It does not itself constitute evidence, and its presence in the repository does not indicate that any evidence has been examined, that any decision has been taken, or that any status dimension has changed. A decision exists only when a named human owner or delegate has completed every field below against a specific evidence index and has signed it.

### 0.1 Placeholder tokens

Every cell must carry a value before the record is considered complete. An unpopulated cell is read as `<PENDING>` and never as acceptance.

| Token | Meaning |
|---|---|
| `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` | The named owner or delegate must supply the value personally. |
| `<TO BE COMPLETED BY TECHNICAL OWNER>` | The technical owner supplies the value as an input; the owner verifies it. |
| `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` | A named independent evaluator supplies the value as an input. |
| `<PENDING>` | Not yet determined. |
| `<NOT_RUN>` | The underlying activity has not been executed. |
| `<NOT_ASSESSED>` | The item has not been examined. |
| `<NONE_RECORDED>` | Deliberately empty at completion time; must be affirmed by the completer. |
| `<NOT_APPLICABLE: reason>` | Requires a written reason. A bare `NOT_APPLICABLE` is invalid. |

---

## 1. What this record is, and what it is not

This record captures one human decision about one narrow evidence or status claim concerning an isolated synthetic prototype.

| This record does | This record does not |
|---|---|
| Accept or reject a narrow, written evidence or status claim about a named component version. | Confer institutional authority of any kind. Human authority is non-delegable (INV-01). |
| Record the conditions, limitations and residual risks the owner considered. | Replace a test that was not run, a scenario that was not executed, or coverage that was marked incomplete. |
| Set a review date, an expiry date and a documented withdrawal route. | Set the Operational dimension. `ISOLATED_PROTOTYPE_V1` has no operational use, no real data and no institutional workload. |
| Bind the decision to an exact evidence index and exact artifact digests. | Grant authorization, permit deployment outside the synthetic environment, or permit use with real data. |
| Sit downstream of five separate assurance gates. | Authorize, trigger, schedule or enable any institutional action, connector, message, write or transaction (INV-12). |

The prototype supports and prepares decisions. Authorized people retain final authority, and any institutional action happens separately under another procedure.

---

## 2. Independence declaration

### 2.1 Three-function separation (Section 17)

- The **technical owner** prepares code and developer evidence.
- The **independent evaluator or reviewer** reviews code, security, TEVV and deployment results.
- The **human owner or delegate** accepts or rejects a narrow evidence or status claim.

One identity must not perform all three functions for the same component, version, status dimension and evidence set. Invariant INV-16 prohibits self-acceptance: a developer, model, evaluator, administrator or evidence record cannot accept its own status claim. Under the gate G-F independence rule the owner considers the evidence presented but cannot replace missing tests and cannot independently attest to their own work.

### 2.2 Declaration by the human owner or delegate

| Declaration | Owner response |
|---|---|
| Owner or delegate name | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Role and the basis of the authority to record this decision | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| If a delegate, the delegating owner and the written scope of the delegation | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| I did not author the code, the developer evidence, or the tests under consideration | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| I did not perform the independent code review, security testing, TEVV or deployment validation | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| I have read the limitations record and the open defect list in full | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| I understand that this decision confers no institutional authority and permits no institutional action | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Any exception to independence, and the compensating control applied | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |

| Function | Named identity | Distinct from the other two functions |
|---|---|---|
| Technical owner | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` |
| Independent evaluator or reviewer (each gate) | `<TO BE COMPLETED BY INDEPENDENT EVALUATOR>` | `<PENDING>` |
| Human owner or delegate (this record) | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` | `<PENDING>` |

If any two rows above name the same identity for the same component, version, status dimension and evidence set, this record is invalid and the decision must be reassigned.

---

## 3. Exact scope of the claim under consideration

State one narrow claim. A claim that is broader than the attached evidence must be rejected or narrowed before a decision is recorded.

| Field | Value |
|---|---|
| The single narrow claim being considered, stated in one sentence | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Status dimension to which the claim relates | `<PENDING: built or integration only>` |
| Component or component set covered | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Exact pinned component versions covered | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Commit SHA | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Container image digests (`db`, `api`, `web`) | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Corpus version and manifest SHA-256 | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Rule catalog version | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Model configuration IDs and `MODEL_MODE` | `<TO BE COMPLETED BY TECHNICAL OWNER>` |
| Environment | `ISOLATED_PROTOTYPE_V1` |
| Data boundary | `SYNTHETIC_ONLY` |
| Business scope | `BUSINESS_UNIT_V1` |
| Period the evidence covers (UTC start and end) | `<PENDING>` |
| Decision date (UTC) | `<PENDING>` |

### 3.1 Explicitly outside this scope

The following are outside the scope of any decision recorded here. This list is not exhaustive and may be extended, but no item may be removed.

| Out of scope | Reason |
|---|---|
| Any use with real, personal, customer, confidential, institutional, clinical, legal, financial or production data | The prototype admits synthetic data only. |
| Any environment other than `ISOLATED_PROTOTYPE_V1` | Deployment does not change authority (INV-15), and evidence is bound to the environment in which it was produced. |
| Any business scope other than `BUSINESS_UNIT_V1` | The V1 boundary is single-scope. |
| Any component version other than those named in Section 3 | Evidence does not carry forward across versions. |
| Any institutional action, connector, message, write, transaction or downstream workflow | No such path exists, and none may be created under this record (INV-12). |
| Setting the Operational dimension to anything other than its default | The prototype has no operational use to evidence. |
| Granting authorization of any kind | Authorization is not within the reach of this gate. |
| Any claim of external compliance, conformity assessment or third-party attestation | No such assessment has been performed or is claimed. |

---

## 4. Evidence index presented

The owner considers only the artifacts listed here. An artifact not listed is not before the owner.

| Gate | Artifact | Path | SHA-256 | Prepared by | Independently reviewed by | Digest recomputed and matched | Indexed in `release_evidence_index.json` |
|---|---|---|---|---|---|---|---|
| `G-A` Developer verification | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<TO BE COMPLETED BY TECHNICAL OWNER>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| `G-B` Independent code review | `independent_code_review.md` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| `G-C` Independent security testing | `security_test_report.md` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| `G-D` TEVV | `tevv_report.md` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| `G-E` Deployment validation | `deployment_validation_checklist.md` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| Cross-gate | `evidence_register.csv` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| Cross-gate | `defect_register.csv` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| Cross-gate | `known_limitations.md` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |
| Cross-gate | `release_evidence_index.json` (completed instance) | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<NOT_RUN>` | `<PENDING>` |

| Field | Value |
|---|---|
| Release evidence index ID and SHA-256 | `<PENDING>` |
| Assurance order confirmed as G-A, G-B, G-C, G-D, G-E before this gate | `<NOT_ASSESSED>` |
| Any gate completed out of order, and the recorded justification | `<PENDING>` |

### 4.1 Evidence that is absent, incomplete or not run

The owner cannot replace a missing test. Anything recorded here constrains the decision and must be reflected in the conditions and the limitations.

| Item | Gate | State | Effect on the claim under consideration |
|---|---|---|---|
| Scenarios recorded `NOT_RUN` in the TEVV report | `G-D` | `<PENDING>` | `<PENDING>` |
| Acceptance targets marked `COVERAGE_INCOMPLETE` | `G-D` | `<PENDING>` | `<PENDING>` |
| Live-model evaluation | `G-D` | `NOT_RUN` | The evidence describes deterministic mock-mode behaviour only. |
| Confirmations recorded `NOT_RUN` in the deployment validation checklist | `G-E` | `<PENDING>` | `<PENDING>` |
| Security tests recorded `NOT_RUN` or `BLOCKED` | `G-C` | `<PENDING>` | `<PENDING>` |
| Checklist rows remaining `NOT_ASSESSED` in the code review | `G-B` | `<PENDING>` | `<PENDING>` |
| Any other absent evidence | `<PENDING>` | `<PENDING>` | `<PENDING>` |

---

## 5. Limitations considered

| Field | Value |
|---|---|
| Limitations record examined | `artifacts/templates/known_limitations.md` (completed instance) |
| Limitations record SHA-256 | `<PENDING>` |
| V1 exclusions understood and accepted as boundaries of the claim | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Unevaluated elements understood | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Non-production boundary understood | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Measurement and coverage limitations understood, including the prohibition on percentage-only reporting | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
| Limitations the owner considers material to this decision, in the owner's own words | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |

---

## 6. Residual risks and open defects

| Severity | Open count | Defect IDs | Blocks this decision |
|---|---|---|---|
| `S0_CRITICAL` | `<PENDING>` | `<PENDING>` | Yes. Any unresolved `S0_CRITICAL` defect blocks acceptance of the affected release. |
| `S1_HIGH` | `<PENDING>` | `<PENDING>` | Yes. Any unresolved `S1_HIGH` defect blocks acceptance of the affected release. |
| `S2_MODERATE` | `<PENDING>` | `<PENDING>` | Must be recorded as a condition or a limitation. |
| `S3_LOW` | `<PENDING>` | `<PENDING>` | Must be recorded as a limitation. |

| Residual risk ID | Description | Source gate | Existing containment | Residual exposure | Owner's position | Review date |
|---|---|---|---|---|---|---|
| `EXAMPLE-000` | ILLUSTRATIVE ROW ONLY. Remove before use. This row records no risk and no position. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

| Field | Value |
|---|---|
| Blocking defect check performed against `defect_register.csv` | `<NOT_RUN>` |
| Result of the blocking defect check | `<PENDING>` |

---

## 7. Conditions attached to the decision

Conditions are mandatory when the decision is `ACCEPT_WITH_CONDITIONS`, and permitted otherwise. Each condition must be verifiable and must name a responsible party and a date.

| Condition ID | Condition | Verification method | Responsible party | Due date | Consequence if unmet | State |
|---|---|---|---|---|---|---|
| `EXAMPLE-000` | ILLUSTRATIVE ROW ONLY. Remove before use. This row imposes no condition. | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |
| `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` | `<PENDING>` |

Condition state vocabulary: `NOT_STARTED`, `IN_PROGRESS`, `MET`, `NOT_MET`, `WITHDRAWN`. The default is `NOT_STARTED`.

---

## 8. Decision

The owner records exactly one outcome from the list below. No other outcome exists, and no outcome may be added.

| Acceptance outcome | Meaning |
|---|---|
| `ACCEPT_BUILT_EVIDENCE` | The owner accepts the narrow evidence claim relating to the Built dimension for the exact component versions in Section 3. |
| `ACCEPT_INTEGRATION_EVIDENCE` | The owner accepts the narrow evidence claim relating to the Integration dimension for the exact component versions in Section 3. |
| `ACCEPT_WITH_CONDITIONS` | The owner accepts a narrow evidence claim subject to the conditions recorded in Section 7. The conditions form part of the decision. |
| `REJECT_EVIDENCE` | The owner does not accept the narrow evidence claim. The reason must be recorded. |
| `REQUEST_RETEST` | The owner requires a further test, retest or regression before a decision can be recorded. The scope of the retest must be stated. |
| `STOP_AND_REVISE` | The owner requires work to stop and the approach to be revised before any further evidence is prepared. |

| Field | Value |
|---|---|
| Decision recorded | `<PENDING>` |
| Reasoning, in the owner's own words | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Specific evidence relied upon, by artifact ID | `<PENDING>` |
| Evidence explicitly not relied upon, and why | `<PENDING>` |
| If `ACCEPT_WITH_CONDITIONS`, the condition IDs that form part of this decision | `<NOT_APPLICABLE: reason required if selected>` |
| If `REJECT_EVIDENCE`, the reason and what would change the outcome | `<NOT_APPLICABLE: reason required if selected>` |
| If `REQUEST_RETEST`, the exact scope and the gate to which the work returns | `<NOT_APPLICABLE: reason required if selected>` |
| If `STOP_AND_REVISE`, the concern and the required revision | `<NOT_APPLICABLE: reason required if selected>` |
| Date and time of the decision (UTC) | `<PENDING>` |

---

## 9. Status dimensions after this decision

The four dimensions are independent and are recorded separately. They must never be merged, averaged or rendered as a single readiness state (INV-14). Each dimension below is recorded on its own line with its own value.

| Dimension | Permitted values (Section 7.1) | Default | Value recorded by this decision | Basis |
|---|---|---|---|---|
| **Built** | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` | `<PENDING>` |
| **Integration** | `NOT_EVIDENCED` / `PARTIALLY_EVIDENCED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` | `<PENDING>` |
| **Operational** | `NOT_EVIDENCED` / `HISTORICAL_CONFIRMED` / `EVIDENCED` | `NOT_EVIDENCED` | `NOT_EVIDENCED` | Fixed at the default. `ISOLATED_PROTOTYPE_V1` has no operational use, no real data, no institutional workload and no service monitoring. This record cannot change this dimension. |
| **Authorization** | `NOT_GRANTED` / `GRANTED_WITH_CONDITIONS` / `GRANTED` | `NOT_GRANTED` | `NOT_GRANTED` | Fixed at the default. This record confers no authorization of any kind. The `SYNTHETIC_DEMO_AUTHORIZATION` fixture is a build-controlled test fixture and is not owner acceptance, deployment authorization or institutional authority. |

Rules for completing the table above:

1. Built and Integration may change only where the corresponding acceptance outcome was recorded in Section 8 and the supporting evidence is listed in Section 4.
2. Operational remains `NOT_EVIDENCED`. There is no evidence pathway to any other value within this environment.
3. Authorization remains `NOT_GRANTED`. There is no acceptance outcome in Section 8 that grants authorization.
4. No consumer of this record may combine these four values into a single indicator, badge, score or summary state.

---

## 10. Review date, expiry and re-acceptance triggers

| Field | Value |
|---|---|
| Review date, by which this decision must be re-examined | `<PENDING>` |
| Expiry date, after which this decision is no longer current | `<PENDING>` |
| Person responsible for initiating the review | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Behaviour on expiry | The recorded values return to their defaults: Built `NOT_EVIDENCED`, Integration `NOT_EVIDENCED`, Operational `NOT_EVIDENCED`, Authorization `NOT_GRANTED`. |

A new decision is required, and the existing decision ceases to apply, when any of the following occurs.

| Trigger | Effect |
|---|---|
| Any pinned component version in Section 3 changes | This decision no longer applies to the changed version. |
| The rule catalog, prompts, schemas, packet schema, canonical JSON profile or audit chain profile changes | This decision no longer applies. |
| The corpus or its manifest SHA-256 changes | This decision no longer applies. |
| The model configuration or `MODEL_MODE` changes | This decision no longer applies. |
| A new `S0_CRITICAL` or `S1_HIGH` defect is raised against a covered component | The decision is suspended pending re-examination. |
| A condition in Section 7 is recorded as `NOT_MET` | The decision is suspended pending re-examination. |
| The environment, data boundary or business scope changes | This decision no longer applies. |
| The review date or expiry date passes | The decision lapses and the defaults apply. |

---

## 11. Revocation path

| Field | Value |
|---|---|
| Revocation status | `NOT_REVOKED` |
| Who may withdraw this decision | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Documented route by which the decision is withdrawn | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Notice required, and to whom | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Immediate effect of withdrawal | The recorded values return to their defaults: Built `NOT_EVIDENCED`, Integration `NOT_EVIDENCED`, Operational `NOT_EVIDENCED`, Authorization `NOT_GRANTED`. |
| Treatment of historical records after withdrawal | Historical records retain their dated facts and carry a withdrawal warning. They are never deleted or rewritten. |
| Where the withdrawal is recorded | `evidence_register.csv`, `release_evidence_index.json` and a new instance of this record. |
| Date of withdrawal, if any | `<NONE_RECORDED>` |
| Reason for withdrawal, if any | `<NONE_RECORDED>` |

---

## 12. Owner signature and date

Signing records the decision stated in Section 8 and nothing further. It confers no institutional authority, permits no institutional action, and does not bring any component into use outside the synthetic environment.

| Field | Value |
|---|---|
| Owner or delegate name | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Function | Human owner or delegate |
| Signature | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE>` |
| Date signed (UTC) | `<PENDING>` |
| Decision recorded | `<PENDING>` |
| Component version set to which this decision is bound | `<PENDING>` |
| Release evidence index SHA-256 to which this decision is bound | `<PENDING>` |
| Record ID for this decision | `<PENDING>` |
| Supersedes decision record ID, if any | `<NONE_RECORDED>` |

| Witness or countersignature (optional, records receipt only) | Value |
|---|---|
| Name | `<PENDING>` |
| Function | `<PENDING>` |
| Date (UTC) | `<PENDING>` |

---

## 13. Record retention

| Field | Value |
|---|---|
| Storage location for the completed immutable record | `<PENDING>` |
| Record SHA-256 | `<PENDING>` |
| Listed in `evidence_register.csv` | `<PENDING>` |
| Indexed in `release_evidence_index.json` | `<PENDING>` |
| Superseded records retained without overwriting | `<TO BE COMPLETED BY HUMAN OWNER OR DELEGATE: CONFIRMED / NOT_CONFIRMED + explanation>` |
