/* ===== NABD AI — DELIVERY ROADMAP DATA =====
   Single source of truth for the implementation plan.

   Only leaf-level `base` and `buffer` hours are recorded here. Every other
   figure in the document (component totals, layer totals, working days, Gantt
   bar geometry, the 576-hour envelope) is derived from these numbers at render
   time so the published plan cannot drift out of arithmetic agreement.

   `s8: true` marks a sub-task whose acceptance criteria are constrained by
   Section 8 (Hierarchical Coarse-to-Fine Decision Synthesis). Section 8 adds
   no hours: it tightens what "done" means for work already scheduled.

   `runtime: false` marks a layer that is delivered but not deployed as part of
   the running system. Layers 1-4 contribute the 11 runtime components packaged
   by sub-task 5.2.1; layer 5 is the testing and integration effort itself.
*/

const ROADMAP = {
    hoursPerDay: 8,
    hoursPerWeek: 48,
    weeks: 12,

    layers: [
        {
            id: '1',
            accent: 'ai',
            runtime: true,
            title: 'AI and Knowledge Components',
            ganttLabel: '1. AI & Knowledge (AI & RAG)',
            components: [
                {
                    id: '1.1',
                    name: 'Model-Agnostic Gateway',
                    tagline: 'Provider-independent model interface and telemetry',
                    tasks: [
                        {
                            id: '1.1.1',
                            name: 'LiteLLM Multi-Provider Adapter Setup',
                            desc: 'Configure unified adapters for seamless switching between Gemini, Llama 3, and Jais.',
                            stack: ['LiteLLM', 'Python'],
                            base: 6, buffer: 4,
                            deliverable: 'LLM Adapter Core'
                        },
                        {
                            id: '1.1.2',
                            name: 'FastAPI Unified REST Endpoints',
                            desc: 'Standardize request/response schemas with secure key and header management.',
                            stack: ['FastAPI', 'Pydantic'],
                            base: 6, buffer: 4,
                            deliverable: 'Gateway Endpoints'
                        },
                        {
                            id: '1.1.3',
                            name: 'Timeouts &amp; Smart Retry Policies',
                            desc: 'Implement circuit breakers and bounded exponential retries upon provider outage.',
                            stack: ['Tenacity', 'Asyncio'],
                            base: 4, buffer: 4,
                            deliverable: 'Resilience Handler'
                        },
                        {
                            id: '1.1.4',
                            name: 'Token &amp; Cost Telemetry Tracker',
                            desc: 'Calculate token usage, latency metrics, and exact model deployment provenance.',
                            stack: ['Loguru', 'JSON Schema'],
                            base: 8, buffer: 4,
                            deliverable: 'Telemetry Module'
                        }
                    ]
                },
                {
                    id: '1.2',
                    name: 'Controlled RAG Engine',
                    tagline: 'Authorized knowledge retrieval &amp; frozen evidence manifest',
                    tasks: [
                        {
                            id: '1.2.1',
                            name: 'PDF Parsing &amp; Chunking Pipeline',
                            desc: 'Extract bylaws with exact page numbers, headers, and section structure intact.',
                            stack: ['PyMuPDF', 'LangChain'],
                            base: 10, buffer: 4,
                            deliverable: 'Ingestion Pipeline'
                        },
                        {
                            id: '1.2.2',
                            name: 'ChromaDB Vector Store &amp; Source Filter',
                            desc: 'Store embeddings in ChromaDB and strictly block unauthorized external queries.',
                            stack: ['ChromaDB', 'Embeddings'],
                            base: 10, buffer: 4,
                            deliverable: 'Vector DB &amp; Filter'
                        },
                        {
                            id: '1.2.3',
                            name: 'Exact Citation Span Resolution',
                            desc: 'Map every retrieved passage to its exact page and line offset in original source.',
                            stack: ['Python Regex', 'Span Mapper'],
                            base: 6, buffer: 4,
                            deliverable: 'Citation Span Engine'
                        },
                        {
                            id: '1.2.4',
                            name: 'Frozen Evidence Manifest Generator',
                            desc: 'Seal retrieved evidence segments with a SHA-256 hash per case.',
                            stack: ['hashlib (SHA-256)'],
                            base: 10, buffer: 4,
                            deliverable: 'Frozen Manifest Maker'
                        }
                    ]
                },
                {
                    id: '1.3',
                    name: 'Multi-Stage Refinement Pipeline',
                    tagline: 'Bounded generate-verify-refine workflow',
                    tasks: [
                        {
                            id: '1.3.1',
                            name: 'Grounded Drafter LLM Stage',
                            desc: 'Generate initial draft strictly using frozen case evidence without internet access. Emits the locked coarse decision block before any prose.',
                            stack: ['Instructor', 'LiteLLM'],
                            base: 10, buffer: 6,
                            deliverable: 'Drafter Engine',
                            s8: true
                        },
                        {
                            id: '1.3.2',
                            name: 'Atomic Claim Verifier Module',
                            desc: 'Decompose draft into claims and verify each claim word-for-word against citations. Evaluated against real Stage 1 output, never idealized drafts.',
                            stack: ['Pydantic v2', 'Claim Extractor'],
                            base: 16, buffer: 6,
                            deliverable: 'Claim Verifier Module',
                            s8: true
                        },
                        {
                            id: '1.3.3',
                            name: 'One-Pass Refiner Stage',
                            desc: 'Revise draft based on verifier feedback (enforcing strict single-pass, no loops). Confined to fine detail; the coarse block is read-only input.',
                            stack: ['Python Asyncio'],
                            base: 16, buffer: 6,
                            deliverable: 'One-Pass Refiner',
                            s8: true
                        },
                        {
                            id: '1.3.4',
                            name: 'Deterministic Output Validation',
                            desc: 'Perform final schema and integrity check before forwarding to governance.',
                            stack: ['JSON Schema'],
                            base: 10, buffer: 6,
                            deliverable: 'Refinement Pipeline Suite'
                        }
                    ]
                }
            ]
        },

        {
            id: '2',
            accent: 'gov',
            runtime: true,
            title: 'Governance and Guardrails Components',
            ganttLabel: '2. Governance &amp; Guardrails',
            components: [
                {
                    id: '2.1',
                    name: 'Deterministic Rule Engine',
                    tagline: 'Policy-as-code enforcement outside the LLM',
                    tasks: [
                        {
                            id: '2.1.1',
                            name: 'Pydantic Custom Validators Pack',
                            desc: 'Enforce strict data presence, format integrity, and field boundaries.',
                            stack: ['Pydantic v2'],
                            base: 10, buffer: 6,
                            deliverable: 'Pydantic Rule Pack'
                        },
                        {
                            id: '2.1.2',
                            name: 'Deterministic Arithmetic Checker',
                            desc: 'Verify calculations and financial figures with exact code outside model inference.',
                            stack: ['Python Decimal'],
                            base: 6, buffer: 2,
                            deliverable: 'Math Checker'
                        },
                        {
                            id: '2.1.3',
                            name: 'A5 Prohibited Boundary Guard',
                            desc: 'Hard-block self-approval, operational write-backs, and unauthorized access.',
                            stack: ['Policy Engine'],
                            base: 10, buffer: 4,
                            deliverable: 'A5 Boundary Shield'
                        },
                        {
                            id: '2.1.4',
                            name: 'Rule Override Controller',
                            desc: 'Ensure programmatic policy rules immediately override any probabilistic LLM output.',
                            stack: ['Rule Hierarchy Logic'],
                            base: 6, buffer: 4,
                            deliverable: 'Override Controller'
                        }
                    ]
                },
                {
                    id: '2.2',
                    name: 'Risk and Uncertainty Scorer',
                    tagline: 'Factor-level risk profiling without granting authority',
                    tasks: [
                        {
                            id: '2.2.1',
                            name: 'Multidimensional Factor Matrix Schema',
                            desc: 'Classify inherent risk into (Low, Moderate, High, Critical, Unknown). Bands are the coarse unit; sub-scores may only move inside a band.',
                            stack: ['Python Enums'],
                            base: 6, buffer: 0,
                            deliverable: 'Risk Matrix Schema',
                            s8: true
                        },
                        {
                            id: '2.2.2',
                            name: 'Uncertainty Profiler &amp; Gap Detector',
                            desc: 'Detect ambiguous queries and missing evidence as an independent metric.',
                            stack: ['Uncertainty Logic'],
                            base: 6, buffer: 4,
                            deliverable: 'Uncertainty Scorer'
                        },
                        {
                            id: '2.2.3',
                            name: 'Dominant Factor Scoring Algorithm',
                            desc: 'Prevent critical risks from being averaged away by lower-tier factors. Runs first, in code, and fixes the band the model inherits.',
                            stack: ['Dominant Algorithm'],
                            base: 6, buffer: 0,
                            deliverable: 'Dominant Factor Core',
                            s8: true
                        },
                        {
                            id: '2.2.4',
                            name: 'Reviewer Requirement Profiler',
                            desc: 'Automatically determine required human reviewer seniority and review depth.',
                            stack: ['Role Router'],
                            base: 10, buffer: 4,
                            deliverable: 'Reviewer Requirement Card'
                        }
                    ]
                },
                {
                    id: '2.3',
                    name: 'Stop &amp; Escalation Conditions / Kill Switch',
                    tagline: 'Fail-closed safety brakes',
                    tasks: [
                        {
                            id: '2.3.1',
                            name: 'Fail-Closed FSM State Routing',
                            desc: 'Implement transitions: READY_FOR_REVIEW, MORE_EVIDENCE, BLOCKED.',
                            stack: ['Transitions FSM'],
                            base: 5, buffer: 0,
                            deliverable: 'State Machine Core'
                        },
                        {
                            id: '2.3.2',
                            name: 'Contradiction Stop Trigger',
                            desc: 'Halt execution immediately when regulatory conflicts or unverified claims arise. Also fires when a downstream stage attempts to alter a locked coarse decision.',
                            stack: ['Conflict Detector'],
                            base: 5, buffer: 4,
                            deliverable: 'Conflict Stop Gate',
                            s8: true
                        },
                        {
                            id: '2.3.3',
                            name: 'Administrative Emergency Kill Switch',
                            desc: 'Server-side emergency stop to freeze pipeline during active security anomalies.',
                            stack: ['Redis / Memory Flag'],
                            base: 5, buffer: 0,
                            deliverable: 'Admin Kill Switch'
                        },
                        {
                            id: '2.3.4',
                            name: 'Safe Recovery &amp; Resumption Handler',
                            desc: 'Log exact root causes and require explicit authorized sign-off before resume.',
                            stack: ['Audit Logger'],
                            base: 5, buffer: 4,
                            deliverable: 'Safe Recovery Handler'
                        }
                    ]
                }
            ]
        },

        {
            id: '3',
            accent: 'ux',
            runtime: true,
            title: 'User and Decision Components',
            ganttLabel: '3. User &amp; Decision (UI &amp; HITL)',
            components: [
                {
                    id: '3.1',
                    name: 'Internal Copilot UI',
                    tagline: 'Evidence-first read-only case workspace',
                    tasks: [
                        {
                            id: '3.1.1',
                            name: 'Interactive Intake Chat Interface',
                            desc: 'Lightweight UI for employees to submit cases and follow processing steps.',
                            stack: ['React / Vite', 'TailwindCSS'],
                            base: 10, buffer: 6,
                            deliverable: 'Copilot Chat Screen'
                        },
                        {
                            id: '3.1.2',
                            name: 'Evidence &amp; Citation Preview Pane',
                            desc: 'Render cited passages with interactive links directly to document pages (Read-only).',
                            stack: ['Lucide Icons', 'PDF Viewer'],
                            base: 10, buffer: 6,
                            deliverable: 'Evidence Viewer Pane'
                        },
                        {
                            id: '3.1.3',
                            name: 'REST API Client Integration Layer',
                            desc: 'Seamlessly communicate with FastAPI backend and handle loading/error states.',
                            stack: ['Axios / Fetch'],
                            base: 6, buffer: 0,
                            deliverable: 'API Client Module'
                        },
                        {
                            id: '3.1.4',
                            name: 'Responsive Design &amp; Typography Tuning',
                            desc: 'Optimize component rendering, clean styling, and bilingual typography.',
                            stack: ['Inter Font', 'CSS Grid'],
                            base: 10, buffer: 4,
                            deliverable: 'Responsive UI Shell'
                        }
                    ]
                },
                {
                    id: '3.2',
                    name: 'Decision Readiness Packet Generator',
                    tagline: 'Canonical sealed review artifact',
                    tasks: [
                        {
                            id: '3.2.1',
                            name: 'Decision Packet Jinja2 Templates',
                            desc: 'Design structured review packet combining draft, evidence table, and risk profile.',
                            stack: ['Jinja2', 'HTML/CSS'],
                            base: 6, buffer: 0,
                            deliverable: 'Packet Template'
                        },
                        {
                            id: '3.2.2',
                            name: 'Canonical JSON Serializer Engine',
                            desc: 'Convert decision parameters into versioned machine-readable JSON schema, with the coarse block serialized and hashed separately from fine detail.',
                            stack: ['Pydantic Serializers'],
                            base: 6, buffer: 6,
                            deliverable: 'Packet JSON Schema',
                            s8: true
                        },
                        {
                            id: '3.2.3',
                            name: 'Cryptographic Packet Sealer Module',
                            desc: 'Generate SHA-256 seal for the complete review packet prior to human dispatch.',
                            stack: ['hashlib (SHA-256)'],
                            base: 6, buffer: 0,
                            deliverable: 'Packet Sealer Module'
                        },
                        {
                            id: '3.2.4',
                            name: 'Official PDF Report Exporter',
                            desc: 'Export verified decision packets into print-ready archival PDF documents.',
                            stack: ['WeasyPrint / Headless'],
                            base: 10, buffer: 6,
                            deliverable: 'PDF Export Feature'
                        }
                    ]
                },
                {
                    id: '3.3',
                    name: 'Human-in-the-Loop (HITL) Gate',
                    tagline: 'Authorized human disposition console',
                    tasks: [
                        {
                            id: '3.3.1',
                            name: 'Manager Disposition Screen',
                            desc: 'Provide 4 action buttons: [Approve, Reject, Request Modification, Escalate].',
                            stack: ['React Dashboard'],
                            base: 10, buffer: 4,
                            deliverable: 'Manager Console'
                        },
                        {
                            id: '3.3.2',
                            name: 'JWT Authority &amp; RBAC Middleware',
                            desc: 'Verify reviewer identity, role authority, and scope validity before recording action.',
                            stack: ['OAuth2 / JWT'],
                            base: 6, buffer: 0,
                            deliverable: 'Auth Middleware'
                        },
                        {
                            id: '3.3.3',
                            name: 'Separation of Duties (SoD) Validator',
                            desc: 'Block self-approval where the requester cannot approve their own submitted case.',
                            stack: ['SoD Validator'],
                            base: 6, buffer: 4,
                            deliverable: 'Conflict Prevention Rule'
                        },
                        {
                            id: '3.3.4',
                            name: 'Human Rationale &amp; Signature Binder',
                            desc: 'Require human rationale and cryptographically bind signature to packet hash.',
                            stack: ['Signature Binder'],
                            base: 10, buffer: 4,
                            deliverable: 'Disposition Service'
                        }
                    ]
                }
            ]
        },

        {
            id: '4',
            accent: 'audit',
            runtime: true,
            title: 'Audit and Observability Components',
            ganttLabel: '4. Audit &amp; Observability',
            components: [
                {
                    id: '4.1',
                    name: 'Tamper-Evident Audit Trail',
                    tagline: 'Cryptographically verified event ledger',
                    tasks: [
                        {
                            id: '4.1.1',
                            name: 'Append-Only Event Store Schema',
                            desc: 'Design database tables with strict immutable append-only constraints (No Updates).',
                            stack: ['PostgreSQL / SQLite'],
                            base: 6, buffer: 0,
                            deliverable: 'Append-Only Schema'
                        },
                        {
                            id: '4.1.2',
                            name: 'Cryptographic Hash Chaining Engine',
                            desc: 'Link each new event to previous event hash to construct a verifiable Merkle chain.',
                            stack: ['SHA-256 Merkle Chain'],
                            base: 10, buffer: 6,
                            deliverable: 'Cryptographic Chainer'
                        },
                        {
                            id: '4.1.3',
                            name: 'Event Telemetry &amp; Actor Stamp',
                            desc: 'Log exact timestamp (ms), user identity, model versions, and transition outcomes.',
                            stack: ['Loguru / Structlog'],
                            base: 6, buffer: 0,
                            deliverable: 'Audit Event Dispatcher'
                        },
                        {
                            id: '4.1.4',
                            name: 'Tamper-Detection Verification Utility',
                            desc: 'Provide inspector CLI/tool to scan and detect any retro-active history manipulation.',
                            stack: ['Integrity Verifier'],
                            base: 10, buffer: 6,
                            deliverable: 'Tamper Audit Tool'
                        }
                    ]
                },
                {
                    id: '4.2',
                    name: 'Claim Ledger &amp; Lineage Tracker',
                    tagline: 'End-to-end atomic claim-to-evidence provenance',
                    tasks: [
                        {
                            id: '4.2.1',
                            name: 'Relational Claim Lineage Schema',
                            desc: 'Map dependencies: Source Bylaw &rarr; Evidence Span &rarr; Atomic Claim &rarr; Decision.',
                            stack: ['SQLAlchemy / SQLModel'],
                            base: 6, buffer: 0,
                            deliverable: 'Lineage Relational DB'
                        },
                        {
                            id: '4.2.2',
                            name: 'Automated Claim Ingestion Service',
                            desc: 'Record all verified claims generated during refinement pipeline runs automatically.',
                            stack: ['Claim Ingestion API'],
                            base: 10, buffer: 4,
                            deliverable: 'Claim Ledger Service'
                        },
                        {
                            id: '4.2.3',
                            name: 'Explainability UI Citation Popovers',
                            desc: 'Enable reviewers to click any sentence to view exact source document and span.',
                            stack: ['React Modal / Popover'],
                            base: 10, buffer: 4,
                            deliverable: 'Explainability View'
                        },
                        {
                            id: '4.2.4',
                            name: 'Deterministic Decision Replay Suite',
                            desc: 'Verify that any historical decision can be re-evaluated with 100% fidelity.',
                            stack: ['Replay Test Suite'],
                            base: 6, buffer: 4,
                            deliverable: 'Deterministic Replay Pass'
                        }
                    ]
                }
            ]
        },

        {
            id: '5',
            accent: 'tevv',
            runtime: false,
            title: 'Integration and TEVV (Testing &amp; Validation)',
            ganttLabel: '5. Integration &amp; TEVV',
            components: [
                {
                    id: '5.1',
                    name: 'Red Teaming &amp; Security Testing',
                    tagline: 'Adversarial hardening &amp; prompt injection defense',
                    tasks: [
                        {
                            id: '5.1.1',
                            name: 'Prompt Injection &amp; Jailbreak Testing',
                            desc: 'Execute adversarial attack vectors attempting to bypass governance and bylaws.',
                            stack: ['Pytest', 'OWASP LLM01'],
                            base: 6, buffer: 2,
                            deliverable: 'Injection Test Suite'
                        },
                        {
                            id: '5.1.2',
                            name: 'Tenant &amp; Boundary Isolation Tests',
                            desc: 'Verify absolute data isolation between departments and tenants.',
                            stack: ['Security Assertions'],
                            base: 6, buffer: 4,
                            deliverable: 'Isolation Verification'
                        },
                        {
                            id: '5.1.3',
                            name: 'Service Failure &amp; Fail-Closed Tests',
                            desc: 'Simulate provider outages and network cuts to prove fail-closed security.',
                            stack: ['Chaos Simulators'],
                            base: 6, buffer: 2,
                            deliverable: 'Resilience Test Pass'
                        },
                        {
                            id: '5.1.4',
                            name: 'Security &amp; Residual Risk Audit Report',
                            desc: 'Document tested vulnerability classes, mitigations, and final assurance metrics.',
                            stack: ['NIST AI 600-1 Template'],
                            base: 10, buffer: 4,
                            deliverable: 'Security Audit Report'
                        }
                    ]
                },
                {
                    id: '5.2',
                    name: 'End-to-End Integration &amp; Executive Demo',
                    tagline: 'Complete prototype validation',
                    tasks: [
                        {
                            id: '5.2.1',
                            name: 'Unified 11-Component Runtime Build',
                            desc: 'Package all layers into a clean containerized development environment.',
                            stack: ['Docker / Compose'],
                            base: 5, buffer: 2,
                            deliverable: 'Integrated PoC Build'
                        },
                        {
                            id: '5.2.2',
                            name: 'Pilot Scenario Validation Suite',
                            desc: 'Run 20 representative real-world governance cases through end-to-end flow, replayed from captured Stage 1 drafts including their failure modes.',
                            stack: ['Synthetic Pilot Data'],
                            base: 5, buffer: 4,
                            deliverable: 'Pilot Case Validation',
                            s8: true
                        },
                        {
                            id: '5.2.3',
                            name: 'Latency &amp; Token Cost Optimization',
                            desc: 'Tune async pipelines to achieve fast response times and low token footprints, exploiting the small constrained coarse call.',
                            stack: ['Async Tuning'],
                            base: 5, buffer: 2,
                            deliverable: 'Optimized Runtime',
                            s8: true
                        },
                        {
                            id: '5.2.4',
                            name: 'Executive Live Showcase Preparation',
                            desc: 'Structure the live demonstration script proving zero-hallucination and human oversight.',
                            stack: ['Live Demo Deck &amp; Scripts'],
                            base: 5, buffer: 4,
                            deliverable: 'Executive Live Demo'
                        }
                    ]
                }
            ]
        }
    ]
};
