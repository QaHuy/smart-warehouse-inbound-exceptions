# Smart Warehouse Inbound and Exception Management SRS/FSD-lite — Draft — Personal synthetic portfolio

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

## Version history

| Version | Date | Status | Change | Author/reviewer boundary |
|---|---|---|---|---|
| 0.1 | 2026-09-08 | Draft for portfolio review | Initial requirements, rules, NFRs, interfaces, errors, and traceability | Prepared by Portfolio author; accountable roles must review before use outside this simulation |

This document is neither an operational baseline nor evidence of a warehouse deployment. The behaviors below are requirements for a local synthetic simulator.

## Purpose

Specify the observable behavior and quality controls for receiving and putting away one synthetic inbound pallet while preserving movement traceability, controlled exception recovery, and exactly-once inventory commitment.

## Audience

- Portfolio reviewers and recruiters assessing BA/PO analysis quality.
- The portfolio author implementing diagrams, contracts, simulator behavior, tests, and UAT in later tasks.
- Proposed role reviewers: inbound operator, warehouse supervisor, warehouse manager, integration engineer, and maintenance technician. These are role archetypes; no person has been interviewed or assigned authority.

## Scope

### In scope

- Inbound pallet capture and barcode, SKU, quantity, and duplicate checks.
- Deterministic compatible-location selection using integer pallet capacity.
- WMS movement tasks, simulated WCS commands/events, documented state transitions, and exceptions.
- Controlled retry, escalation, and cancellation in the simulator.
- Read-only synthetic inventory, audit, and metric views.

### Out of scope

- Outbound, cycle count, multi-warehouse, advanced FEFO, routing optimization, enterprise authentication, and physical ERP/PLC/device connectivity.
- Safety certification, live operating procedures, actual stakeholder authority, and operational performance claims.

## System context

The inbound operator provides synthetic receipt data through a local browser interface. The WMS simulator owns validation, location selection, movement-task state, exception records, inventory commitment, audit evidence, and metrics. The WCS simulator accepts commands and emits synthetic conveyor, lift, and robot events. A maintenance-technician persona supplies recovery evidence but cannot mutate inventory directly. The browser, domain logic, and local data contract form one self-contained learning environment with no external network dependency.

Responsibility boundary:

| Concern | Owner inside the simulator | Boundary |
|---|---|---|
| Receipt validity, location choice, task state, inventory, metrics | WMS simulator | WCS/device events provide evidence; they do not decide inventory policy |
| Command execution and device event emission | WCS simulator | Behavior and events are synthetic |
| Retry, cancellation, escalation | WMS simulator under proposed supervisor workflow | Role authority requires human confirmation before operational reuse |
| Device diagnosis evidence | Maintenance-technician persona | No direct inventory mutation |

## Glossary

| Term | Meaning in this portfolio |
|---|---|
| WMS | Simulator component that makes inbound, putaway, task, inventory, and exception decisions. |
| WCS | Simulator component that represents command execution and emits device events. |
| Pallet | One synthetic handling unit containing one SKU and one lot in this MVP. |
| Movement task | Traceable instruction to move a pallet to one selected location. |
| Compatible location | A location that accepts the pallet/SKU attributes represented by the synthetic compatibility key. |
| Valid `TASK_COMPLETED` | A unique, well-formed completion event correlated to the task from an allowed prior state. |
| Retry attempt | A redispatch after a failed or timed-out attempt; initial dispatch is not a retry. |
| Exception | A visible record requiring recovery, cancellation, or escalation. |
| Idempotent | Reprocessing the same `event_id` returns a duplicate outcome without a second mutation. |
| Dispatched cohort | Tasks that reached `DISPATCHED` at least once and therefore enter metric calculations. |

## Business needs

| ID | Need received from Task 1 |
|---|---|
| `BN-01` | Prevent invalid or duplicate pallets from entering automated putaway. |
| `BN-02` | Make each WMS-to-WCS movement traceable from dispatch to completion. |
| `BN-03` | Surface device and capacity exceptions for controlled recovery. |
| `BN-04` | Update inventory location exactly once after verified completion. |

## Assumptions and constraints

| Ref | Type and status | Statement | Human checkpoint and revisit trigger |
|---|---|---|---|
| `AS-01` | Locked case-study assumption; unvalidated operationally | One pallet contains one SKU and one lot. | Warehouse supervisor and inbound owner review if mixed SKU, split lot, nesting, or relabelling appears. |
| `AS-02` | Locked case-study assumption; unvalidated operationally | Quantity is a positive integer. | Warehouse supervisor and integration owner review if catch-weight, decimal units, unknown quantity, or adjustment workflow appears. |
| `AS-03` | Locked case-study assumption; unvalidated operationally | Location capacity is an integer pallet count. | Warehouse manager and warehouse supervisor review if capacity depends on dimensions, weight, stacking, hazard, or shared slots. |
| `DEC-01` | Portfolio design decision | Select the first compatible available location ordered by zone priority, then location code. | Warehouse policy owner reviews when another mandatory constraint or tie-breaker appears. |
| `DEC-02` | Portfolio design decision | Commit inventory only on a valid `TASK_COMPLETED`. | Operations and integration owners review if another authoritative completion signal, partial placement, or dual confirmation is required. |
| `DEC-03` | Portfolio design decision | Permit at most two retries; escalate on the third failure. | Supervisor, maintenance, and safety owners review if condition-specific limits or a no-retry rule is required. |
| `DEC-04` | Portfolio design decision | Use UTC ISO 8601 simulator timestamps. | Integration owner reviews if precision, source-clock, ordering, or display requirements change. |
| `PROP-01` | PROPOSED simulator policy | Cancellation is eligible only from `CREATED`, `VALIDATED`, `DISPATCHED`, `IN_PROGRESS`, `FAILED`, or `TIMED_OUT`; completion and cancellation are terminal. | Warehouse supervisor and integration owner confirm safe-stop semantics; revisit if command acknowledgement or physical motion changes eligibility. |
| `PROP-02` | PROPOSED metric policy | When the dispatched-task denominator is zero, rate values display `N/A` rather than zero. | Warehouse manager confirms interpretation; revisit if reporting policy requires another null/empty-cohort representation. |

## Functional requirements

### FR-01 — Create inbound pallet

- **Statement:** The synthetic WMS SHALL create one inbound pallet record from a provided pallet ID, barcode, SKU, lot, and quantity only after the request is structurally readable.
- **Source:** Task 2 brief; `docs/01-case-study-brief.md` scope.
- **Linked BN:** `BN-01`.
- **Verification method:** Automated domain test with one valid synthetic request and malformed-request boundaries.
- **Acceptance signal:** `AC-US-01-01` and `AC-US-01-02` return a created record or a specific validation error with no partial record.

### FR-02 — Validate barcode, SKU, and quantity

- **Statement:** The synthetic WMS SHALL validate that barcode is present and well formed for the simulator, SKU is known and active, and quantity is a positive integer before putaway continues.
- **Source:** Task 2 brief; `AS-02`; Task 1 inbound scope.
- **Linked BN:** `BN-01`.
- **Verification method:** Parameterized automated tests for valid input, blank/malformed barcode, unknown/inactive SKU, and zero, negative, fractional, or non-numeric quantity.
- **Acceptance signal:** `AC-US-01-01` permits valid data and `AC-US-01-02` rejects every listed invalid boundary without creating a movement task.

### FR-03 — Reject duplicate pallet ID

- **Statement:** The synthetic WMS SHALL reject receipt when the supplied pallet ID already exists and SHALL preserve the existing pallet without mutation.
- **Source:** Task 2 brief; `BN-01`.
- **Linked BN:** `BN-01`.
- **Verification method:** Automated test creates one pallet and repeats the same ID with changed fields.
- **Acceptance signal:** `AC-US-02-01` accepts a new ID and `AC-US-02-02` returns `DUPLICATE_PALLET` while the original record remains unchanged.

### FR-04 — Select available compatible location deterministically

- **Statement:** The synthetic WMS SHALL select the first compatible location with used pallet count below integer capacity when candidates are ordered by ascending zone priority and then ascending location code.
- **Source:** Task 2 brief; `AS-03`; `DEC-01`.
- **Linked BN:** `BN-01`, `BN-03`.
- **Verification method:** Automated test uses shuffled candidate input with compatibility, full-capacity, zone-priority, and location-code boundaries.
- **Acceptance signal:** `AC-US-03-01` always selects the expected candidate and `AC-US-03-02` creates `NO_AVAILABLE_LOCATION` when none qualifies.

### FR-05 — Create movement task

- **Statement:** The synthetic WMS SHALL create one movement task linking the validated pallet, selected destination, correlation identity, and initial `CREATED` state.
- **Source:** Task 2 brief; `BN-02`; documented state model in this SRS.
- **Linked BN:** `BN-02`.
- **Verification method:** Automated test inspects the public task result after validated pallet and location selection.
- **Acceptance signal:** `AC-US-04-01` creates one traceable task and `AC-US-04-02` prevents an undocumented state change.

### FR-06 — Dispatch simulated WCS command

- **Statement:** The synthetic WMS SHALL dispatch one correlated simulated WCS movement command only for an eligible task and, when the initial dispatch finds the simulated device offline, record the first failure, move the task from `VALIDATED` to `FAILED`, and keep an active exception without incrementing retry count.
- **Source:** Task 2 brief; `BN-02`; WMS/WCS responsibility boundary.
- **Linked BN:** `BN-02`, `BN-03`.
- **Verification method:** Automated test checks eligible dispatch, correlation, audit order, and the initial offline path with task state `FAILED`, failure count 1, retry count 0, and an active exception.
- **Acceptance signal:** `AC-US-05-01` records command and state, while `AC-US-05-02` proves the offline initial failure is recoverable and is not counted as a retry.

### FR-07 — Apply simulated WCS events

- **Statement:** The synthetic WMS SHALL apply a well-formed, correlated, unique simulated WCS event only when its transition is allowed, while treating repeated `event_id` values idempotently.
- **Source:** Task 2 brief; `DEC-02`; `DEC-04`.
- **Linked BN:** `BN-02`, `BN-04`.
- **Verification method:** Automated event-sequence tests cover accepted, in-progress, completed, failed, timed-out, invalid-transition, unknown-task, and duplicate events.
- **Acceptance signal:** `AC-US-06-01`, `AC-US-06-02`, `AC-US-07-01`, `AC-US-07-02`, `AC-US-08-01`, and `AC-US-08-02` prove valid application, rejection, idempotency, and the inventory gate.

### FR-08 — Manage exception queue

- **Statement:** The synthetic WMS SHALL create and expose one traceable exception entry for each active validation, capacity, device, jam, timeout, or recovery failure and SHALL keep its status visible until resolved, cancelled, or escalated.
- **Source:** Task 2 brief; `BN-03`.
- **Linked BN:** `BN-03`.
- **Verification method:** Automated queue tests create each supported exception type and verify identity, task/pallet correlation, status, reason, and recovery visibility.
- **Acceptance signal:** `AC-US-09-01` shows an actionable queued exception and `AC-US-09-02` prevents an unsupported or resolved item from appearing as active.

### FR-09 — Retry, cancel, and escalate

- **Statement:** The synthetic WMS SHALL permit retry attempts one and two for eligible failed or timed-out tasks, return an offline retry to `FAILED` with incremented failure evidence, escalate the exception on the third failure overall, and permit cancellation only from documented non-terminal states.
- **Source:** Task 2 brief; `DEC-03`; `PROP-01`.
- **Linked BN:** `BN-03`.
- **Verification method:** Automated state tests execute the initial offline failure, two still-offline retries, third-failure escalation, every documented cancellation origin, and terminal-state cancellation rejection.
- **Acceptance signal:** `AC-US-10-01..AC-US-10-04` prove bounded retry, the complete offline recovery/escalation chain, and cancellation eligibility.

### FR-10 — Expose inventory, audit, and metrics

- **Statement:** The synthetic WMS SHALL expose read-only synthetic inventory position, chronological audit evidence, and four metric outputs derived from the documented dispatched cohort.
- **Source:** Task 2 brief; portfolio design metric formulas; `DEC-02`; `PROP-02`.
- **Linked BN:** `BN-02`, `BN-03`, `BN-04`.
- **Verification method:** Automated reconciliation tests compare returned inventory, audit entries, and metrics against known synthetic event histories.
- **Acceptance signal:** `AC-US-11-01`, `AC-US-11-02`, `AC-US-12-01`, and `AC-US-12-02` prove traceability, read-only behavior, exact formulas, and empty-cohort handling.

## Business rules

### BR-01 — Positive integer quantity

- **Rule:** Quantity must be an integer greater than zero; zero, negative, fractional, blank, and non-numeric values are invalid.
- **Source:** Task 2 brief and `AS-02`.
- **Verification route:** `US-01` / `AC-US-01-01` and `AC-US-01-02`; parameterized domain validation test.

### BR-02 — Known active SKU

- **Rule:** SKU must exist in the synthetic SKU master and have active status at receipt time.
- **Source:** Task 2 brief.
- **Verification route:** `US-01` / `AC-US-01-01` and `AC-US-01-02`; active, inactive, and unknown-SKU tests.

### BR-03 — Unique pallet ID

- **Rule:** Pallet ID must be unique; a repeated ID is rejected without changing the first record.
- **Source:** Task 2 brief and `BN-01`.
- **Verification route:** `US-02` / `AC-US-02-01` and `AC-US-02-02`; uniqueness test at receipt seam.

### BR-04 — Compatible location below capacity

- **Rule:** A candidate location is eligible only when its compatibility key matches and its integer used pallet count is strictly below integer capacity; select by zone priority then location code.
- **Source:** Task 2 brief, `AS-03`, and `DEC-01`.
- **Verification route:** `US-03` / `AC-US-03-01` and `AC-US-03-02`; deterministic selector and full-location tests.

### BR-05 — Allowed task state transitions

- **Rule:** Only these transitions are allowed: `CREATED -> VALIDATED|CANCELLED`; `VALIDATED -> DISPATCHED|FAILED|CANCELLED`; `DISPATCHED -> IN_PROGRESS|COMPLETED|FAILED|TIMED_OUT|CANCELLED`; `IN_PROGRESS -> COMPLETED|FAILED|TIMED_OUT|CANCELLED`; `FAILED -> DISPATCHED|CANCELLED`; `TIMED_OUT -> DISPATCHED|CANCELLED`. `COMPLETED` and `CANCELLED` are terminal.
- **Source:** Task 2 brief state names and `PROP-01` for cancellation origins.
- **Verification route:** `US-04`, `US-06`, and `US-10`; transition-table tests plus negative terminal/unsupported-transition tests.

### BR-06 — Completion-gated inventory

- **Rule:** Inventory location changes only once on a valid `TASK_COMPLETED`; no earlier, unknown, malformed, duplicate, or invalid-transition event may change inventory.
- **Source:** Task 2 brief and `DEC-02`.
- **Verification route:** `US-08` / `AC-US-08-01` and `AC-US-08-02`; event-to-inventory reconciliation test.

### BR-07 — Idempotent event identity

- **Rule:** A duplicate `event_id` returns a successful duplicate indication and creates no second task-state or inventory mutation.
- **Source:** Task 2 brief and portfolio design quality gate.
- **Verification route:** `US-07` / `AC-US-07-01` and `AC-US-07-02`; replay the identical event and compare mutation counts.

### BR-08 — Maximum two retries

- **Rule:** Retry attempts one and two are allowed only after eligible `FAILED` or `TIMED_OUT` outcomes; the initial failed dispatch is failure number 1 but retry count 0, and no third retry command is dispatched.
- **Source:** Task 2 brief and `DEC-03`.
- **Verification route:** `US-10` / `AC-US-10-01`, `AC-US-10-02`, and `AC-US-10-04`; retry-counter, failure-count, state, exception, and command-count tests.

### BR-09 — Third failure escalation

- **Rule:** The third failure overall across the initial attempt and two failed retries escalates the linked exception; task state remains the observed `FAILED` or `TIMED_OUT` state, the exception stops being actionable for another retry, and no unlisted `ESCALATED` task state is introduced.
- **Source:** Task 2 brief and `DEC-03`.
- **Verification route:** `US-10` / `AC-US-10-02` and `AC-US-10-04`; three-failure sequence test verifies exception escalation and no further dispatch.

### BR-10 — Dispatched-task metric cohort

- **Rule:** Metric cohort contains tasks that reached `DISPATCHED`: Completion Rate = completed tasks / dispatched tasks; Exception Rate = dispatched tasks ever `FAILED` or `TIMED_OUT` / dispatched tasks; First Pass Success Rate = completed tasks with zero retries / dispatched tasks; Average Simulated Cycle Time = average of `completed_at - dispatched_at` for completed tasks in the dispatched cohort. An empty denominator follows `PROP-02`.
- **Source:** Task 2 brief and portfolio design metric formulas.
- **Verification route:** `US-12` / `AC-US-12-01` and `AC-US-12-02`; fixed synthetic-history reconciliation with independently calculated expected outputs.

## Non-functional requirements catalog

The following thresholds are proposals for this local simulator. Passing them shows conformance to the portfolio contract only; it does not demonstrate formal standards certification or operational service performance.

### NFR-01 — Deterministic processing

- **Statement:** Given the same synthetic master data, request sequence, and event sequence, the simulator SHALL produce the same location choice, state sequence, mutation counts, and metric values, excluding generated identifiers and timestamps.
- **Linked BN:** `BN-01`, `BN-02`, `BN-04`.
- **PROPOSED threshold:** 30 of 30 consecutive clean-state runs produce identical normalized output.
- **Test conditions:** Bundled local runtime, fixed synthetic fixture, reset before each run, no external calls, generated IDs/timestamps removed before comparison.
- **Rationale:** Repeatability makes rule behavior explainable and lets later artifacts detect cross-contract drift.
- **Source:** `DEC-01`, Task 2 brief, and portfolio design quality gate.
- **Verification method:** Automated repeat-run comparison at the public domain interface.
- **Acceptance signal:** Repeat test reports 30 matching normalized results and zero unexplained divergence.

### NFR-02 — Auditability

- **Statement:** The simulator SHALL record chronological audit evidence for every accepted command, received event, task-state mutation, retry, cancellation, escalation, and inventory mutation, including correlation ID, entity ID, action, prior/new state when applicable, actor/component, and UTC timestamp.
- **Linked BN:** `BN-02`, `BN-03`, `BN-04`.
- **PROPOSED threshold:** 100% of mutations in the fixed audit test set have one corresponding audit entry with all mandatory fields; a duplicate event adds at most one deduplication outcome and zero state or inventory mutations.
- **Test conditions:** Execute happy path, offline, jam, timeout, retry, cancellation, escalation, and duplicate-event scenarios against a clean synthetic store.
- **Rationale:** Reviewers must be able to reconstruct why state and inventory changed.
- **Source:** Task 2 brief, `DEC-02`, `DEC-04`, and `BR-07`.
- **Verification method:** Automated action-to-audit reconciliation plus chronological-order assertion.
- **Acceptance signal:** Reconciliation reports zero missing mandatory fields, zero unaudited mutations, and zero duplicate inventory mutation.

### NFR-03 — Browser accessibility

- **Statement:** The local browser interface SHALL expose semantic landmarks, one page heading, programmatic labels or accessible names for every interactive control, keyboard-operable actions, visible focus, non-color-only status text, and a live status region.
- **Linked BN:** `BN-01`, `BN-03`.
- **PROPOSED threshold:** 100% of interactive controls in the four planned views pass the automated markup checklist, and all primary actions complete by keyboard at 1280 px and 360 px viewport widths.
- **Test conditions:** Inspect inbound, task, exception, and inventory/audit views in default, validation-error, loading, success, and empty states using local browser tooling.
- **Rationale:** Operators and portfolio reviewers need understandable feedback without relying on mouse input or color alone.
- **Source:** Portfolio implementation plan Task 6 and Task 2 brief.
- **Verification method:** Static HTML assertions plus a manual keyboard and narrow-width walkthrough; no formal accessibility certification is inferred.
- **Acceptance signal:** Automated checklist has zero failures and the manual walkthrough records every primary action reachable with visible focus and readable status text.

### NFR-04 — Local operation

- **Statement:** The simulator SHALL load and complete the synthetic happy path using local bundled runtimes without requiring external services or network requests.
- **Linked BN:** `BN-01`, `BN-02`, `BN-03`, `BN-04`.
- **PROPOSED threshold:** 0 external network requests and 100% completion of one scripted local happy path from receipt through inventory view.
- **Test conditions:** Serve the static prototype on loopback, start from a clean synthetic state, disable non-loopback connectivity, and execute the documented demo sequence.
- **Rationale:** The portfolio must remain self-contained, reproducible, and within the authorization boundary.
- **Source:** Portfolio implementation plan architecture and global constraints.
- **Verification method:** Browser network inspection and scripted/manual happy-path test.
- **Acceptance signal:** No external request is observed and the local flow reaches one verified inventory movement.

### NFR-05 — Synthetic-data privacy

- **Statement:** All portfolio artifacts, fixtures, screenshots, and audit examples SHALL contain only synthetic or generalized identifiers and SHALL exclude personal data, customer material, credentials, private repository references, device addresses, and absolute user paths.
- **Linked BN:** `BN-01`, `BN-02`, `BN-03`, `BN-04`.
- **PROPOSED threshold:** 0 matches in the recursive privacy scan and 0 exceptions in manual artifact review.
- **Test conditions:** Scan all text-based project artifacts with the maintained forbidden-pattern list and manually inspect rendered screenshots before any handoff.
- **Rationale:** Demonstrating analysis must not disclose restricted material or imply access to an operating site.
- **Source:** Portfolio design privacy boundary and implementation-plan global constraints.
- **Verification method:** Automated recursive pattern scan plus manual visual review.
- **Acceptance signal:** Both checks report zero findings; any finding blocks portfolio handoff until removed and rechecked.

### Quality coverage and trade-offs

| Quality concern | NFR | Trade-off / human decision still required |
|---|---|---|
| Repeatability | `NFR-01` | Fixed ordering favors explainability over dynamic optimization. |
| Evidence reconstruction | `NFR-02` | More audit detail increases storage/noise; retention is outside this simulator. |
| Usable browser interaction | `NFR-03` | Automated checks cannot replace review by users with varied access needs. |
| Reproducible local demo | `NFR-04` | Self-contained operation excludes enterprise integration behavior. |
| Data minimization | `NFR-05` | Generalized examples limit realism by design. |

### NFR human review checkpoints

Every role below is a **PROPOSED reviewing role for this design**, not a person with confirmed organizational authority.

| NFR | Proposed reviewing role | Review checkpoint | Concrete revisit trigger |
|---|---|---|---|
| `NFR-01` | PROPOSED integration engineer and warehouse supervisor | Before locking domain/state acceptance fixtures, review deterministic ordering and normalized-output exclusions. | An authorized location rule adds dynamic travel, congestion, equipment, or non-deterministic tie-breaking. |
| `NFR-02` | PROPOSED integration engineer and warehouse supervisor | Before freezing event/audit contracts, review mandatory audit fields, mutation coverage, chronology, and deduplication evidence. | An audit consumer requires another actor, source timestamp, retention field, correlation key, or event-order rule. |
| `NFR-03` | PROPOSED access-needs reviewer, inbound operator, and warehouse supervisor | Before completing browser UAT, perform keyboard, focus, label, status-text, and narrow-width walkthroughs on every planned state. | A user cannot perceive status or complete a primary action with the tested input/navigation method or viewport. |
| `NFR-04` | PROPOSED operations reviewer and integration engineer | Before demo handoff, execute the clean local happy path with non-loopback connectivity disabled and inspect browser network activity. | Any required runtime, asset, API, telemetry, or authentication dependency initiates a non-loopback request. |
| `NFR-05` | PROPOSED privacy/security reviewer and portfolio author | Before every artifact handoff or screenshot inclusion, run recursive pattern checks and manual visual inspection. | A scan or reviewer finds personal/customer material, credential-like content, private references, device addresses, or absolute user paths. |

## Interfaces and data overview

| Interface/data object | Minimum contract for later design | Direction and responsibility | Linked requirements |
|---|---|---|---|
| Inbound pallet request | pallet ID, barcode, SKU, lot, integer quantity, correlation ID | Browser to WMS simulator; WMS validates | `FR-01`, `FR-02`, `FR-03`; `BR-01..BR-03` |
| Location master/query | location code, compatibility key, zone priority, integer capacity, used pallet count | Local data contract to WMS selector | `FR-04`; `BR-04` |
| Movement task | task ID, pallet ID, destination, state, retry count, timestamps, correlation ID | WMS-owned | `FR-05`, `FR-09`; `BR-05`, `BR-08`, `BR-09` |
| Simulated WCS command | command ID, task ID, pallet ID, destination, UTC timestamp, correlation ID | WMS to WCS simulator | `FR-06`; `NFR-02` |
| Simulated WCS event | unique `event_id`, task ID, event type, UTC timestamp, device type, correlation ID | WCS simulator to WMS | `FR-07`; `BR-05..BR-07` |
| Exception entry | exception ID, type, linked task/pallet, status, reason, attempt count, timestamps | WMS-owned queue | `FR-08`, `FR-09`; `BR-08`, `BR-09` |
| Inventory movement | movement ID, task ID, pallet ID, from/to location, committed-at timestamp, source event | WMS-owned, one per completed task | `FR-10`; `BR-06`, `BR-07` |
| Read models | task list, inventory, audit trail, exception queue, four metrics | WMS to local browser | `FR-08`, `FR-10`; `BR-10` |

Later API and data-contract tasks define field syntax and persistence constraints. This SRS defines business meaning and observable outcomes, not endpoint or table implementation.

## Error catalogue

| Code | Trigger | Observable outcome | Recovery/owner boundary | Linked requirement/rule |
|---|---|---|---|---|
| `INVALID_BARCODE` | Barcode blank or malformed for simulator format | Receipt rejected; no task | Operator corrects synthetic input | `FR-02` |
| `UNKNOWN_OR_INACTIVE_SKU` | SKU absent or inactive | Receipt rejected; no task | Operator selects known active synthetic SKU | `FR-02`, `BR-02` |
| `INVALID_QUANTITY` | Quantity fails positive-integer rule | Receipt rejected; no task | Operator corrects input | `FR-02`, `BR-01` |
| `DUPLICATE_PALLET` | Pallet ID exists | Existing record unchanged; new receipt rejected | Operator/supervisor review identity | `FR-03`, `BR-03` |
| `NO_AVAILABLE_LOCATION` | No compatible location below capacity | No dispatch; capacity exception visible | Supervisor reviews capacity/compatibility | `FR-04`, `FR-08`, `BR-04` |
| `DEVICE_OFFLINE` | Selected simulated device unavailable during initial dispatch or retry | Initial attempt moves `VALIDATED -> FAILED`, sets failure count 1 and retry count 0; each still-offline retry returns `DISPATCHED -> FAILED`, increments failure evidence, and preserves an active actionable exception until failure 3 escalates it | Maintenance persona supplies recovery evidence; supervisor persona chooses an eligible retry or cancellation | `FR-06`, `FR-08`, `FR-09`, `BR-05`, `BR-08`, `BR-09` |
| `PALLET_JAM` | Simulated jam event | Allowed failure transition and exception visible | Supervisor coordinates recovery | `FR-07..FR-09`, `BR-05` |
| `TASK_TIMEOUT` | Simulated timeout event | `TIMED_OUT` state and exception visible | Retry/cancel/escalate by documented rule | `FR-07..FR-09`, `BR-05`, `BR-08`, `BR-09` |
| `INVALID_TRANSITION` | Event/action requests an undocumented state change | Request rejected; state and inventory unchanged | Integration/supervisor reviews sequence | `FR-07`, `FR-09`, `BR-05` |
| `UNKNOWN_TASK` | Event/action cannot correlate to a task | Request rejected; no mutation; audit evidence retained | Integration persona reviews identity | `FR-07`, `NFR-02` |
| `DUPLICATE_EVENT` | `event_id` already processed | Successful duplicate indication; no second mutation | No retry required | `FR-07`, `BR-07` |
| `RETRY_LIMIT_REACHED` | Third failure overall follows the initial attempt and two failed retries | Exception escalated; task remains in observed failure state; no third retry command | Human checkpoint required | `FR-09`, `BR-08`, `BR-09` |
| `CANCELLATION_NOT_ALLOWED` | Cancellation requested from terminal or undocumented origin | Request rejected; state unchanged | Supervisor reviews current state | `FR-09`, `BR-05` |

## Traceability summary

| Business need | Functional coverage | Rule/control coverage | Story acceptance route |
|---|---|---|---|
| `BN-01` | `FR-01..FR-04` | `BR-01..BR-04`, `NFR-01`, `NFR-03..NFR-05` | `US-01..US-03` |
| `BN-02` | `FR-05..FR-07`, `FR-10` | `BR-05`, `BR-07`, `BR-10`, `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05` | `US-04..US-07`, `US-11`, `US-12` |
| `BN-03` | `FR-04`, `FR-06`, `FR-08..FR-10` | `BR-04`, `BR-05`, `BR-08..BR-10`, `NFR-02..NFR-05` | `US-03`, `US-05`, `US-09`, `US-10`, `US-12` |
| `BN-04` | `FR-07`, `FR-10` | `BR-06`, `BR-07`, `BR-10`, `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05` | `US-07`, `US-08`, `US-11`, `US-12` |

The detailed `BN -> FR -> BR -> US -> UAT -> result` matrix and executed evidence belong to Task 7. No UAT result is asserted here.

## Verification methods

| Method | What it can establish | Limitation |
|---|---|---|
| Markdown integrity test | Exact IDs, links, metadata, story order, required language, and banned claims | Does not execute simulator behavior |
| Domain automated test | Validation, deterministic selection, state, retry, idempotency, inventory, and metrics | Uses synthetic fixtures only |
| Contract/data test | Schema, uniqueness, referential integrity, event identity, and SQL controls | Does not represent an enterprise platform |
| Static/browser check | Local operation, accessibility checklist, disclosure, and visible states | Manual access-needs review remains necessary |
| UAT | End-to-end portfolio scenarios and evidence | Scheduled for Task 7; no result exists in this draft |

## Open questions

No unresolved placeholder is used. Each item below is a deliberate proposal requiring a role-based checkpoint before use outside the simulation.

| Question | Current portfolio treatment | Human checkpoint | Revisit trigger |
|---|---|---|---|
| What barcode syntax and source are authoritative? | A documented simulator format will be defined in the API/data task. | Inbound and integration owners | Authorized field contract differs. |
| Which attributes determine location compatibility? | One synthetic compatibility key. | Warehouse policy owner | Weight, dimensions, hazard, temperature, or equipment limits appear. |
| What event proves physical completion? | Unique valid `TASK_COMPLETED`. | Warehouse operations and integration owners | Dual signal, partial placement, or another system of record is required. |
| From which states is cancellation safe? | `PROP-01` state list. | Warehouse supervisor, integration, maintenance/safety owners | Physical motion or acknowledgement changes safe-stop behavior. |
| How should empty metric cohorts display? | `PROP-02`: `N/A`. | Warehouse manager | Reporting policy defines zero or another null representation. |
| What audit retention and access policy applies? | Outside local simulator scope; keep only synthetic session evidence. | Security, operations, and sponsor roles | Portfolio moves beyond local demonstration. |

## Review findings

- **Completeness:** Exact ranges `FR-01..FR-10`, `BR-01..BR-10`, and `NFR-01..NFR-05` are defined once; four Task 1 business needs have functional coverage.
- **Consistency:** Deterministic location selection, task states, completion gate, idempotency, retry/escalation, UTC timestamps, and metric formulas align with Task 1 decisions and the Task 2 brief.
- **Ambiguity controls:** Cancellation origins and empty-cohort display are explicit `PROPOSED` policies; each NFR also has its own proposed reviewing role, checkpoint, and concrete revisit trigger.
- **Verification:** Every FR and NFR includes source, linked BN, verification method, and acceptance signal; every business rule has a story/test route.
- **Evidence boundary:** No interview, site observation, hardware test, operational KPI, external connection, or stakeholder authority is claimed.
- **Review required:** Portfolio author reviews internal consistency; accountable business, technical, safety, security, and delivery roles must validate fit, thresholds, feasibility, priority, and risk before any operational reuse.
