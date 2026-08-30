# Roadmap reference images

**Status:** supplementary visual context only.

These are the nine supplied NABD AI work-breakdown and deployment roadmap images. They are
planning context. Where they conflict with the build specification, the specification
governs, and the narrowing is recorded below and in `docs/architecture.md`.

## Provenance

The bundle manifest supplied with the specification lists SHA-256 values for the original
`IMG_0229(1).jpeg` … `IMG_0237(1).jpeg` files. The copies in this directory were delivered
through an upload pipeline that re-encoded them, so their bytes — and therefore their
hashes — differ from the originals. `SHA256SUMS` in this directory records the hashes of
the files **as committed here**, not the hashes from the supplied bundle manifest. This is
stated plainly rather than silently, because an evidence register that quietly substitutes
one hash for another is worse than no hash at all.

The images were mapped to their specification filenames by content, matching each image to
the roadmap theme that Section 21 assigns to it.

| File | Content | Section 21 theme |
|---|---|---|
| `IMG_0229(1).jpeg` | 12-week technical WBS, hours roadmap, commercial proposal | 12-week WBS, hours and costs |
| `IMG_0230(1).jpeg` | Gantt roadmap and the model-agnostic gateway component | Gateway and telemetry |
| `IMG_0231(1).jpeg` | Controlled RAG engine and multi-stage refinement pipeline | RAG and refinement |
| `IMG_0232(1).jpeg` | Deterministic rule engine and risk/uncertainty scorer | Rules and risk |
| `IMG_0233(1).jpeg` | Stop, escalation and kill switch; internal copilot UI | Stop/kill switch and intake UI |
| `IMG_0234(1).jpeg` | Decision readiness packet generator and human-in-the-loop gate | Packet and HITL |
| `IMG_0235(1).jpeg` | Tamper-evident audit trail and claim lineage tracker | Audit and lineage |
| `IMG_0236(1).jpeg` | Red teaming, security testing and end-to-end validation | Security and TEVV |
| `IMG_0237(1).jpeg` | Target deployment spec and hardware requirements | Hardware and deployment |

## What was narrowed, and why

The images propose several things that V1 does not implement. Each is recorded here as a
deliberate narrowing rather than an omission.

| Roadmap proposal | V1 decision |
|---|---|
| Multi-provider adapters with dynamic switching between Gemini, Llama 3 and Jais | One pinned model configuration per task role per run. No discovery, no switching, no fallback. |
| Three-stage generate, verify and refine pipeline | Two model calls maximum: one bounded draft and one independent verifier. There is no third refiner call. |
| Manager "Approve" action in the disposition console | Test-only dispositions. There is no approval value, and no disposition reaches a connector. |
| Real-world pilot cases | Synthetic cases only, drawn from a frozen corpus. |
| "Zero-hallucination" demonstration claim | Measurable evidence and citation thresholds reported as exact numerators over denominators. No such guarantee is made or implied. |
| Hardware sizing for GPU or air-gapped hosting | Future deployment context only. V1 runs as a local Docker workbench with a deterministic mock model baseline. |
| Hourly rates, totals and payment schedule | Planning context only. No commercial figure appears in the product or in any status claim. |

## Licence

These images are the user's supplied planning material, retained here as reference
attachments for implementation context.
