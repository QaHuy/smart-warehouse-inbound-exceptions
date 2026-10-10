# Case Study Brief

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

## Document status and evidence labels

Status: approved portfolio foundation for a synthetic case study; not approved for a real warehouse.

| Label | Meaning |
|---|---|
| **Source constraint** | A boundary fixed by the approved portfolio plan or design specification. |
| **Design assumption** | A simplifying statement used to make the synthetic case executable; it still needs real-world validation. |
| **Proposal** | A suggested operating model, role, control, or validation approach; it is not authorized by a real organization. |
| **Decision** | A choice locked by the approved portfolio plan for consistency across later artifacts. |
| **Evidence** | Material that could support or challenge a claim. No warehouse evidence has been collected for this case study. |

## Business problem

**Design premise, not a measured baseline:** inbound checks are fragmented and exception visibility is poor. Barcode, SKU, quantity, duplicate-pallet, location-capacity, and device-status checks may be handled at different points, making it hard to understand whether a pallet is safe to put away and who should recover a failed movement.

Potential consequences to examine in a real discovery are invalid pallets entering an automated flow, incomplete movement history, late recovery from capacity or device exceptions, and inventory being updated before physical completion. These are hypotheses for elicitation, not claims about an observed warehouse.

## Goal and intended outcome

Create a traceable pallet receipt and putaway flow with safe recovery. A user should be able to follow a synthetic pallet from validation through dispatch and simulated completion, understand any exception, and see that inventory changes exactly once only after verified completion.

The case study demonstrates analysis and design quality. It does not claim operational savings, throughput improvement, production readiness, or successful hardware integration.

## Personas

| Persona | Primary concern in the proposed flow |
|---|---|
| Inbound operator | Enter a pallet correctly and understand the next action or validation error. |
| Warehouse supervisor | Control the queue, recovery path, retry, cancellation, and escalation. |
| Warehouse manager | See safe flow, exception patterns, capacity exposure, and auditable synthetic metrics. |
| Integration engineer | Preserve command/event identity, state transitions, timestamps, and traceability. |
| Maintenance technician | Identify simulated device symptoms and record recovery evidence without changing WMS inventory directly. |

These are role archetypes for the simulation, not people who were interviewed.

## Scope

### In scope

- Validate inbound barcode, known SKU, positive integer quantity, and unique pallet identity.
- Select a compatible available putaway location using a deterministic rule.
- Create a WMS movement task and a command for a WCS simulator.
- Simulate conveyor, lift, and robot events and task transitions.
- Surface validation, capacity, offline-device, jam, and timeout exceptions.
- Support controlled retry, cancellation, and escalation paths.
- Expose synthetic inventory location, movement history, audit trail, and demo metrics.

### Out of scope

- Outbound, cycle count, and multi-warehouse operations.
- Advanced FEFO and production optimization.
- Real ERP, PLC, robot, conveyor, lift, or device integration.
- Enterprise authentication, production security architecture, and production deployment.
- Claims about a real warehouse baseline, measured benefit, or stakeholder approval.

## Business needs

- `BN-01`: Prevent invalid or duplicate pallets from entering automated putaway.
- `BN-02`: Make each WMS-to-WCS movement traceable from dispatch to completion.
- `BN-03`: Surface device and capacity exceptions for controlled recovery.
- `BN-04`: Update inventory location exactly once after verified completion.

These four needs are the only fully defined requirement-level content in this foundation task.

## Stable ID contract and ownership

| Namespace | Reserved range | Status and next owner |
|---|---|---|
| Business need | BN-01 through BN-04 | Defined above; changes require an explicit portfolio-plan review. |
| Functional requirement | `FR-01..FR-10` | Reserved for Task 2; detailed statements are intentionally absent here. |
| Business rule | `BR-01..BR-10` | Reserved for Task 2; detailed rules are intentionally absent here. |
| Non-functional requirement | `NFR-01..NFR-05` | Reserved for Task 2; detailed statements are intentionally absent here. |
| User story | `US-01..US-12` | Reserved for Task 2; stories and acceptance criteria are intentionally absent here. |
| UAT case | `UAT-01..UAT-14` | Reserved for Task 7; test steps and results are intentionally absent here. |

Each later artifact must define an ID once, reference it consistently, and preserve traceability. A reference is not a second definition. New IDs or range changes require review because diagrams, API/data contracts, tests, and UAT will consume them.

## Architecture direction

The proposed local demo separates five concerns: an operator-facing browser interface, WMS validation and movement decisions, a local data contract, a WCS simulator, and simulated conveyor/lift/robot events. The WMS owns business validation and inventory commitment. The WCS simulator represents command execution and emits device events; it does not make inventory decisions.

This direction is designed only at Task 1. Later tasks must prove consistency between requirements, diagrams, state transitions, API, data model, JavaScript behavior, and tests.

## Demonstration success criteria

These are portfolio acceptance targets, not measured warehouse KPIs:

- A synthetic happy path can be traced from receipt to one inventory movement.
- At least three synthetic exception paths can be demonstrated with a visible recovery state.
- Replaying the same simulated event does not create a second inventory movement.
- Every important requirement can ultimately trace to an acceptance criterion and an executed UAT result.
- Automated and manual privacy checks find no private, client, credential, or production material.

## Constraints, dependencies, and risks

| Type | Item | Treatment |
|---|---|---|
| Constraint | Local, synthetic, inbound-only MVP | Keep every artifact and example inside this boundary. |
| Dependency | Task 2 defines detailed requirements and stories | Do not pre-emptively define them in this brief. |
| Dependency | Later diagrams, contracts, simulator, UI, and UAT must reuse the same rules and states | Enforce through tests and traceability. |
| Risk | Readers may interpret simulation as warehouse experience | Keep disclosure and delivery legend prominent. |
| Risk | Proposed authority may be mistaken for confirmed governance | Mark decision rights as proposed until validated. |
| Risk | Deterministic simplifications may not fit a real warehouse | Record validation methods and revisit triggers in the assumption log. |

## Task 2 handoff

Task 2 receives the four business needs, persona concerns, approved scope, stable ID reservations, and locked assumptions/decisions. It must produce detailed requirements, business rules, a Product Goal, ordered backlog, and acceptance criteria without adding real-world claims. Human review is required before any simulated rule is represented as suitable for an actual operation.

