# Assumptions and Decisions

## Governance note

This log preserves why the synthetic case uses each rule. It does not record decisions made by a real warehouse, client, or stakeholder. “Approved” means locked by the approved portfolio plan for this case study only.

### Classification

| Class | Meaning | Authority/status rule |
|---|---|---|
| Approved plan constraint | Scope or disclosure fixed by the portfolio plan/specification | May be implemented as written; not real-world authorization |
| Approved plan decision | Design choice fixed for consistency across the portfolio | Portfolio author owns implementation; role-based validation remains proposed |
| Case-study assumption | Simplification accepted temporarily without operational evidence | Must remain labelled and have a validation/revisit trigger |
| Proposal | Suggested governance, control, or future choice | Must not be described as decided until an authorized owner confirms it |
| Evidence | Traceable source that supports or challenges a statement | Current evidence is limited to the portfolio plan/specification and local tests |

No interview output, site observation, operational baseline, device test, or measured benefit exists at Task 1.

## Approved plan constraints

| Ref | Constraint | Source and status | Consequence |
|---|---|---|---|
| PC-01 | The project is a personal WMS/WCS case study using synthetic data; WCS behavior and device events are simulated. | Approved portfolio plan/specification | Every artifact and demo must retain this boundary. |
| PC-02 | MVP is inbound and putaway only. | Approved portfolio plan/specification | Outbound, cycle count, multi-warehouse, advanced FEFO, production optimization, enterprise authentication, and real integrations remain excluded. |
| PC-03 | No publication or public URL is authorized. | Approved portfolio plan/specification | Keep delivery local until separate approval is given. |

## Case-study assumption log

All proposed validation owners below are role archetypes. Status “Locked assumption” means required for the portfolio implementation, not validated in a real operation.

| Ref | Assumption | Why used / rationale | Proposed validation owner | Status | Validation method and evidence needed | Revisit trigger | Affected artifacts and consequence if false |
|---|---|---|---|---|---|---|---|
| AS-01 | One pallet contains one SKU and one lot. | Keeps receipt, inventory, and traceability unambiguous in the MVP. | Warehouse supervisor with inbound operator input | Locked assumption; unvalidated | Walk through recent mixed-content pallets and inspect a redacted receipt/pallet composition policy. | Evidence of mixed SKU, split lot, nested handling unit, or relabelling. | Requirements, process, ERD, API, UI, tests, and UAT; model pallet lines and allocation if false. |
| AS-02 | Quantity is a positive integer. | Supports a simple count-based receipt and rejects zero, negative, and fractional input. | Warehouse supervisor with integration engineer input | Locked assumption; unvalidated | Review authorized unit-of-measure rules and redacted recent quantity payloads. | Catch-weight, decimal unit, unknown quantity, or adjustment workflow appears. | Validation rule, schema type, API, UI, test data, and UAT; introduce unit-of-measure semantics if false. |
| AS-03 | Location capacity is an integer number of pallets. | Makes the synthetic compatibility and full-location check deterministic. | Warehouse manager with warehouse supervisor input | Locked assumption; unvalidated | Review authorized capacity policy and reconstruct recent placement decisions. | Capacity depends on volume, weight, dimensions, stacking, hazard class, or shared slots. | Location model, selection logic, exception rules, UI, tests, and UAT; replace pallet-count capacity if false. |

## Approved plan decision log

The decision owner is `Portfolio author` because these choices belong only to the case study. Proposed operational validators are listed separately and have not approved anything.

### DEC-01 — Deterministic putaway selection

- **Decision:** Select the first compatible available location ordered by zone priority, then location code.
- **Status/effective date:** Approved plan decision for the portfolio; effective 2026-09-08.
- **Owner:** Portfolio author. Proposed validator: warehouse supervisor.
- **Evidence:** Approved portfolio plan/specification only; no warehouse selection history has been collected.
- **Rationale:** A deterministic rule is explainable, repeatable, and testable without pretending to implement production optimization.
- **Criteria used:** compatibility, available capacity, stable ordering, local testability, and audit explanation.
- **Alternatives recorded:** dynamic travel-time, congestion, FEFO, or equipment-aware optimization were excluded from the MVP rather than evaluated as production options.
- **Consequences:** Later requirements, diagrams, data, simulator, UI explanation, and UAT must use the same ordering. The result is a demonstration choice, not an optimal route claim.
- **Revisit trigger:** Operational evidence shows additional mandatory constraints or zone priority/location code cannot safely break ties.

### DEC-02 — Inventory commitment gate

- **Decision:** Inventory moves only on a valid `TASK_COMPLETED` event.
- **Status/effective date:** Approved plan decision for the portfolio; effective 2026-09-08.
- **Owner:** Portfolio author. Proposed validators: warehouse supervisor and integration engineer.
- **Evidence:** Approved portfolio plan/specification only; no physical completion signal has been verified.
- **Rationale:** Separates planned movement from verified completion and creates one explicit audit point.
- **Criteria used:** inventory integrity, traceability, idempotency, and recovery safety.
- **Alternatives recorded:** committing at task creation, dispatch, or in-progress state is excluded because those states do not represent verified completion in this model.
- **Consequences:** Duplicate or invalid completion events must not create another inventory movement. State/event contract, schema, domain tests, SQL controls, and UAT must prove this behavior.
- **Revisit trigger:** A real authoritative completion event differs, requires dual confirmation, or permits partial placement.

### DEC-03 — Retry and escalation limit

- **Decision:** Retry limit is two; the third failure requires escalation.
- **Status/effective date:** Approved plan decision for the portfolio; effective 2026-09-08.
- **Owner:** Portfolio author. Proposed validators: warehouse supervisor and maintenance technician.
- **Evidence:** Approved portfolio plan/specification only; no safety procedure or incident history has been collected.
- **Rationale:** Creates a bounded, visible recovery path and prevents unlimited automated retry in the simulation.
- **Criteria used:** controllability, auditability, demonstrable exception flow, and conservative recovery.
- **Alternatives recorded:** unlimited retry and immediate escalation were not selected for the case-study flow; neither has been operationally evaluated.
- **Consequences:** The counter, failure event, exception queue, escalation state, UI, audit, and UAT must agree on two retries and escalation on failure three.
- **Revisit trigger:** Approved safety or operations evidence requires a different limit, condition-specific limits, or no automatic retry.

### DEC-04 — Simulator timestamp standard

- **Decision:** Simulator timestamps use UTC ISO 8601.
- **Status/effective date:** Approved plan decision for the portfolio; effective 2026-09-08.
- **Owner:** Portfolio author. Proposed validator: integration engineer.
- **Evidence:** Approved portfolio plan/specification only; no cross-system timestamp sample has been collected.
- **Rationale:** A single explicit standard makes synthetic event ordering and local audit comparison consistent.
- **Criteria used:** interoperability, unambiguous timezone, sortable representation, and testability.
- **Alternatives recorded:** local-time strings and timestamps without offsets were excluded as ambiguous; precision and clock-skew policy remain open for real validation.
- **Consequences:** API examples, seed data, simulator events, audit displays, and tests must use UTC ISO 8601 while user-facing localization remains a later design concern.
- **Revisit trigger:** Contract evidence requires another precision/format, monotonic sequence, source clock, or timezone display rule.

## Proposal register

| Ref | Proposal | Proposed owner to confirm | Status | Evidence needed / consequence |
|---|---|---|---|---|
| PR-01 | Warehouse supervisor governs retry, cancel, and escalation procedure in the simulation. | Authorized sponsor or PM | Proposed; unconfirmed | Governance record and recent decision example; revise RACI if another role owns the action. |
| PR-02 | Warehouse manager governs capacity policy and synthetic metric interpretation. | Authorized sponsor or PM | Proposed; unconfirmed | Policy/KPI ownership evidence; split accountability if the decisions belong to different roles. |
| PR-03 | Integration engineer governs command/event semantics and idempotency contract. | Authorized sponsor or architecture owner | Proposed; unconfirmed | Interface governance and approval process; revise contract review path if ownership differs. |
| PR-04 | Maintenance technician supplies recovery evidence but does not commit inventory. | Warehouse supervisor and authorized safety owner | Proposed; unconfirmed | Recovery procedure and system access boundary; revise workflow if maintenance has another formal responsibility. |

## Decision and assumption relationships

- The pallet-content, quantity, and capacity statements are assumptions because their fit depends on warehouse operating evidence.
- The location selector, inventory gate, retry limit, and timestamp format are decisions because the approved portfolio plan locks them for cross-artifact consistency.
- The proposed RACI and validation owners are proposals, not decisions or evidence.
- A passing local test proves only that artifacts implement the case-study contract; it cannot validate a warehouse policy or confer authority.

## Artifact update checklist

When an assumption or decision changes, review all applicable artifacts:

- case brief and stakeholder/interview guide;
- detailed requirements, business rules, Product Goal, backlog, and acceptance criteria;
- BPMN, context, sequence, and state diagrams;
- data schema/dictionary, API contract, synthetic seed, and SQL controls;
- simulator domain logic, UI states, audit trail, and metric definitions;
- automated tests, traceability matrix, UAT cases/results, user guide, and demo script.

Record the change as a proposal first, identify the role-based decision owner, preserve the prior rationale, and update linked tests only after the portfolio decision is approved.

## Validation queue and revisit triggers

There are no overdue real-world validations because no engagement, owner, or deadline has been authorized. The following items are intentionally **pending before real-world reuse**:

| Priority | Item | Required evidence | Human checkpoint |
|---:|---|---|---|
| 1 | Authoritative physical-completion signal and exactly-once inventory rule | Event/inventory timeline, duplicate behavior, system-of-record decision | Warehouse operations and integration owners approve |
| 2 | Retry limit and escalation safety | Recovery procedure, incident examples, safety constraints | Supervisor, maintenance, and safety owner approve |
| 3 | Location compatibility/capacity and selection order | Location policy and recent placement decisions | Warehouse policy owner approves |
| 4 | Pallet composition and quantity semantics | Receipt policy and redacted examples | Inbound and inventory owners approve |
| 5 | Timestamp semantics | Interface contract, clock/precision requirements | Integration owner approves |

## Open decisions for later tasks

Task 2 may specify detailed requirement wording and acceptance criteria inside the reserved ID contract, but must not alter the locked statements silently. Precision for compatible location, valid completion, correlation, cancellation eligibility, metric fields, and error catalogue must be made explicit and traceable. Any choice beyond the approved plan remains a proposal until reviewed by the Portfolio author, and any claim of operational suitability remains unavailable without authorized real-world evidence.

