# User Stories and Acceptance Criteria — Draft — Personal synthetic portfolio

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

## Status and usage boundary

These twelve stories specify WHAT a user needs and WHY it matters in the local simulator. Business rules, state transitions, interfaces, and data meaning remain in `docs/04-srs-fsd-lite.md`; implementation details belong to later contracts and code. Personas are archetypes, not interviewed individuals. Priority is a proposal, estimates are unavailable, and no story is represented as sprint-ready for an actual delivery team.

## Story convention

- **Priority status** stays `PROPOSED in ordered backlog; Product Owner confirmation required`.
- **Estimate status** stays `Not estimated; delivery team confirmation required`.
- **INVEST check** is a draft assessment, not a readiness sign-off.
- Each acceptance criterion is independently testable and uses synthetic input only.

## US-01 — Validation

**Story:** As an inbound operator, I want immediate validation of barcode, SKU, and quantity so that invalid receipt data cannot enter putaway.

- **Persona:** Inbound operator.
- **Capability:** Submit one pallet receipt and receive field-specific validation results.
- **Business value:** Stops invalid data before location, task, or simulated device work begins.
- **Linked BN:** `BN-01`.
- **Linked FR:** `FR-01`, `FR-02`.
- **Linked BR:** `BR-01`, `BR-02`.
- **Linked NFR:** `NFR-01`, `NFR-03`, `NFR-04`, `NFR-05`.
- **Assumptions:** `AS-01` one SKU/lot per pallet and `AS-02` positive integer quantity remain unvalidated outside the simulation.
- **Dependencies:** Synthetic SKU master and documented simulator barcode format; no prior story.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent at the receipt boundary; Negotiable presentation; Valuable prevention; Estimable after interface refinement; Small one-validation slice; Testable through explicit valid and invalid partitions.

### AC-US-01-01 — Positive AC: valid receipt fields

- **Given** a new synthetic pallet ID, a barcode matching the simulator format, a known active SKU, one lot, and integer quantity 10
- **When** the operator submits the inbound receipt
- **Then** the WMS creates one pallet record and returns field validation success without creating a movement task yet.

### AC-US-01-02 — Negative/boundary AC: invalid fields

- **Given** a receipt whose barcode is blank/malformed, whose SKU is unknown/inactive, or whose quantity is blank, non-numeric, fractional, zero, or negative
- **When** the operator submits the inbound receipt
- **Then** the WMS returns the applicable `INVALID_BARCODE`, `UNKNOWN_OR_INACTIVE_SKU`, or `INVALID_QUANTITY` result and creates neither a pallet nor a movement task.

## US-02 — Unique identity

**Story:** As an inbound operator, I want duplicate pallet identities rejected so that one physical concept cannot be represented by conflicting synthetic records.

- **Persona:** Inbound operator.
- **Capability:** Create a new pallet only when its pallet ID is unused.
- **Business value:** Preserves an unambiguous identity for later task, event, and inventory correlation.
- **Linked BN:** `BN-01`.
- **Linked FR:** `FR-03`.
- **Linked BR:** `BR-03`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-05`.
- **Assumptions:** Pallet ID is the simulator uniqueness key; relabelling and nested handling units are outside scope.
- **Dependencies:** `US-01` validation succeeds.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent uniqueness slice after validation; Negotiable feedback wording; Valuable identity integrity; Estimable with persistence contract; Small one-key rule; Testable by first and repeated submissions.

### AC-US-02-01 — Positive AC: unused pallet ID

- **Given** a valid receipt whose pallet ID does not exist
- **When** the operator submits the receipt
- **Then** the WMS creates exactly one pallet under that ID.

### AC-US-02-02 — Negative/boundary AC: repeated pallet ID

- **Given** an existing pallet and a second valid-looking receipt with the same pallet ID but different SKU, lot, or quantity
- **When** the operator submits the second receipt
- **Then** the WMS returns `DUPLICATE_PALLET`, creates no second pallet, and leaves the original record unchanged.

## US-03 — Location selection

**Story:** As an inbound operator, I want one explainable compatible destination so that putaway continues only when capacity is available.

- **Persona:** Inbound operator.
- **Capability:** Request destination selection for a valid unique pallet.
- **Business value:** Avoids assigning an incompatible or full location and provides a visible capacity outcome.
- **Linked BN:** `BN-01`, `BN-03`.
- **Linked FR:** `FR-04`.
- **Linked BR:** `BR-04`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`.
- **Assumptions:** `AS-03` integer pallet capacity and `DEC-01` compatibility then zone-priority/location-code ordering apply only to the simulator.
- **Dependencies:** `US-01`, `US-02`, and a synthetic location master.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent decision slice; Negotiable compatibility representation; Valuable safe destination; Estimable after master-data contract; Small deterministic selector; Testable with ordered and no-candidate fixtures.

### AC-US-03-01 — Positive AC: deterministic eligible choice

- **Given** shuffled locations containing incompatible, full, and multiple compatible below-capacity candidates
- **When** the operator requests putaway selection
- **Then** the WMS chooses the compatible below-capacity candidate with the lowest zone priority and then lowest location code, independent of input order.

### AC-US-03-02 — Negative/boundary AC: no available location

- **Given** every compatible location has used pallet count equal to integer capacity, or all below-capacity locations are incompatible
- **When** the operator requests putaway selection
- **Then** the WMS returns `NO_AVAILABLE_LOCATION`, selects no destination, creates no movement task, and creates one visible capacity exception.

## US-04 — Movement task and state

**Story:** As a warehouse supervisor, I want a correlated movement task with controlled states so that planned movement is traceable before dispatch.

- **Persona:** Warehouse supervisor.
- **Capability:** View one movement task connecting pallet, destination, identity, and current state.
- **Business value:** Creates the traceable unit through which dispatch, events, exceptions, and inventory can be reconciled.
- **Linked BN:** `BN-02`.
- **Linked FR:** `FR-05`.
- **Linked BR:** `BR-05`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`.
- **Assumptions:** The SRS transition table is the complete state authority for the simulator.
- **Dependencies:** `US-03` returns an eligible destination.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent task-lifecycle slice; Negotiable display; Valuable movement trace; Estimable from state contract; Small creation/transition scope; Testable by allowed and disallowed transitions.

### AC-US-04-01 — Positive AC: task creation and validation

- **Given** a valid unique pallet and selected eligible location
- **When** the WMS creates the planned movement and validates its required links
- **Then** exactly one movement task exists with task ID, pallet ID, destination, correlation ID, and the documented `CREATED -> VALIDATED` state history.

### AC-US-04-02 — Negative/boundary AC: undocumented transition

- **Given** a task in `CREATED` and a request to move directly to `COMPLETED`
- **When** the transition is evaluated
- **Then** the WMS returns `INVALID_TRANSITION`, retains `CREATED`, creates no command, and creates no inventory movement.

## US-05 — WCS dispatch

**Story:** As an integration engineer, I want eligible movement tasks dispatched with correlation evidence so that a simulated WCS command can be traced to its WMS origin.

- **Persona:** Integration engineer.
- **Capability:** Dispatch one validated task to the WCS simulator and inspect correlation evidence.
- **Business value:** Separates an internal plan from a traceable externalized command and exposes dispatch failure.
- **Linked BN:** `BN-02`, `BN-03`.
- **Linked FR:** `FR-06`.
- **Linked BR:** `BR-05`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05`.
- **Assumptions:** Device availability is synthetic and command execution does not imply physical movement.
- **Dependencies:** `US-04` task is `VALIDATED`; a simulated device is selected.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent dispatch outcome; Negotiable command shape; Valuable traceability; Estimable after API contract; Small one-command slice; Testable through eligible and offline paths.

### AC-US-05-01 — Positive AC: eligible correlated dispatch

- **Given** a `VALIDATED` task and an available simulated device
- **When** dispatch is requested
- **Then** the WMS records one command with task/correlation identity before moving the task to `DISPATCHED` and returns the command identity.

### AC-US-05-02 — Negative/boundary AC: simulated device offline

- **Given** a `VALIDATED` task whose required simulated device is offline
- **When** dispatch is requested
- **Then** the offline dispatch attempt returns `DEVICE_OFFLINE`, moves the task from `VALIDATED` to `FAILED`, records failure count 1, keeps retry count 0, creates an active exception, and creates no false command execution; this is the first failure but not a retry.

## US-06 — Event processing

**Story:** As an integration engineer, I want correlated WCS events validated against the task lifecycle so that only documented evidence changes task state.

- **Persona:** Integration engineer.
- **Capability:** Submit a unique simulated event and receive an applied or rejected outcome.
- **Business value:** Protects movement truth from malformed, unknown, or out-of-sequence device messages.
- **Linked BN:** `BN-02`, `BN-03`.
- **Linked FR:** `FR-07`.
- **Linked BR:** `BR-05`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05`.
- **Assumptions:** Simulator timestamps use UTC ISO 8601; event ordering and precision beyond the documented state checks require later contract review.
- **Dependencies:** `US-05` provides a dispatched correlated task and command.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent event-application slice; Negotiable payload; Valuable state integrity; Estimable after event contract; Small known event set; Testable with valid and invalid correlations/transitions.

### AC-US-06-01 — Positive AC: valid event sequence

- **Given** a correlated task in `DISPATCHED` and unique well-formed accepted, in-progress, and completion events with UTC ISO 8601 timestamps
- **When** the WMS processes the events in the documented order
- **Then** each event is recorded and the task follows only the allowed `DISPATCHED -> IN_PROGRESS -> COMPLETED` states.

### AC-US-06-02 — Negative/boundary AC: unknown or invalid event

- **Given** a unique event with an unknown task ID, malformed required field, or transition not allowed from the current state
- **When** the WMS processes the event
- **Then** it returns `UNKNOWN_TASK` or `INVALID_TRANSITION`, records diagnostic audit evidence, and changes neither task state nor inventory.

## US-07 — Idempotency

**Story:** As an integration engineer, I want duplicate events recognized by identity so that at-least-once delivery cannot repeat a business mutation.

- **Persona:** Integration engineer.
- **Capability:** Replay a previously processed `event_id` and receive an explicit duplicate outcome.
- **Business value:** Prevents repeated delivery from corrupting state or moving inventory twice.
- **Linked BN:** `BN-02`, `BN-04`.
- **Linked FR:** `FR-07`.
- **Linked BR:** `BR-07`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`.
- **Assumptions:** `event_id` is globally unique within the synthetic store and retained for the full demo session.
- **Dependencies:** `US-06` event intake and stable event identity.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent replay-safety slice; Negotiable response shape; Valuable integrity protection; Estimable from identity contract; Small one-event rule; Testable by before/after mutation counts.

### AC-US-07-01 — Positive AC: first unique event

- **Given** a well-formed event whose `event_id` has not been processed and whose transition is valid
- **When** the WMS receives the event
- **Then** it returns success with `duplicate: false`, records the event once, and applies the permitted state or inventory effect once.

### AC-US-07-02 — Negative/boundary AC: duplicate event_id replay

- **Given** a duplicate `event_id` matching an event already processed successfully and snapshots of current task state and inventory-movement count
- **When** the WMS receives the duplicate event
- **Then** it returns a success response with duplicate indication, records no second event effect, and makes no second state or inventory mutation.

## US-08 — Inventory commit

**Story:** As a warehouse supervisor, I want inventory committed only after verified task completion so that planned or failed movement is not presented as stored stock.

- **Persona:** Warehouse supervisor.
- **Capability:** Observe one inventory movement tied to the valid completion evidence.
- **Business value:** Keeps synthetic inventory aligned with the verified movement outcome and protects against early or repeated commitment.
- **Linked BN:** `BN-04`.
- **Linked FR:** `FR-07`, `FR-10`.
- **Linked BR:** `BR-06`, `BR-07`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05`.
- **Assumptions:** `TASK_COMPLETED` is the simulator completion authority under `DEC-02`; physical proof requires operational validation elsewhere.
- **Dependencies:** `US-06` valid event sequence and `US-07` idempotency.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent inventory-gate slice; Negotiable view; Valuable stock integrity; Estimable from event/data contract; Small one-commit outcome; Testable by exact movement counts before/after completion.

### AC-US-08-01 — Positive AC: one verified inventory movement

- **Given** a dispatched task with no inventory movement and a unique valid `TASK_COMPLETED` event from an allowed state
- **When** the WMS processes the event
- **Then** task state becomes `COMPLETED` and exactly one inventory movement links the pallet, task, destination, event, and completion time.

### AC-US-08-02 — Negative/boundary AC: no early or invalid commit

- **Given** a task in `CREATED`, `VALIDATED`, `DISPATCHED`, `IN_PROGRESS`, `FAILED`, or `TIMED_OUT`, or an unknown/malformed/invalid-transition completion event
- **When** the current inventory is inspected after that non-valid-completion condition
- **Then** there is no inventory movement before valid completion and the task's planned destination is not presented as committed inventory.

## US-09 — Exception queue

**Story:** As a warehouse supervisor, I want active exceptions collected with reason and ownership context so that recovery work is visible and controlled.

- **Persona:** Warehouse supervisor.
- **Capability:** Review validation, capacity, device, jam, timeout, and recovery failures in one queue.
- **Business value:** Makes failed work and the next control action visible instead of leaving it hidden in task status.
- **Linked BN:** `BN-03`.
- **Linked FR:** `FR-08`.
- **Linked BR:** `BR-04`, `BR-05`, `BR-09`.
- **Linked NFR:** `NFR-02`, `NFR-03`, `NFR-04`, `NFR-05`.
- **Assumptions:** Queue priority and final role ownership are proposals pending accountable review.
- **Dependencies:** Failure outcomes from `US-01`, `US-03`, `US-05`, `US-06`, and stable task identity from `US-04`.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent visibility slice; Negotiable grouping/filtering; Valuable controlled recovery; Estimable after exception contract; Small queue/read model; Testable through active and resolved filtering.

### AC-US-09-01 — Positive AC: active exception visibility

- **Given** a synthetic validation, no-location, device-offline, jam, timeout, or recovery failure with its related pallet/task when available
- **When** the supervisor opens the active exception queue
- **Then** one traceable entry shows exception identity, type, status, reason, related entity, attempt count, timestamp, and available documented next actions.

### AC-US-09-02 — Negative/boundary AC: non-active or unsupported item

- **Given** a resolved, cancelled, or escalated exception and an arbitrary unsupported message that created no exception
- **When** the supervisor filters for active exceptions
- **Then** neither item appears as active, while the historical exception remains available in audit evidence.

## US-10 — Retry, escalation, and cancellation

**Story:** As a warehouse supervisor, I want bounded retry, explicit escalation, and state-safe cancellation so that recovery cannot continue indefinitely or bypass lifecycle controls.

- **Persona:** Warehouse supervisor.
- **Capability:** Retry eligible work twice, escalate the third failure, or cancel from an eligible non-terminal state.
- **Business value:** Gives exception recovery a visible limit and prevents unsupported lifecycle actions.
- **Linked BN:** `BN-03`.
- **Linked FR:** `FR-09`.
- **Linked BR:** `BR-05`, `BR-08`, `BR-09`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-03`, `NFR-04`.
- **Assumptions:** Two retries and third-failure escalation follow `DEC-03`; failure evidence counts the initial failed attempt plus failed retries, while retry count excludes the initial attempt; cancellation origins follow `PROP-01` and need supervisor/integration/safety confirmation before operational reuse.
- **Dependencies:** `US-04` state model, `US-05` initial offline failure semantics, and `US-09` exception identity/visibility.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent recovery-control slice; Negotiable UI and role workflow; Valuable bounded recovery; Estimable after command semantics; Small fixed transitions; Testable by counters and state matrix.

### AC-US-10-01 — Positive AC: first and second retry

- **Given** a task has an active exception and is in eligible `FAILED` or `TIMED_OUT` state with fewer than two prior retries
- **When** the supervisor requests each retry in sequence
- **Then** retry attempts one and two are allowed, each creates one correlated redispatch/audit entry, and the retry count becomes 1 then 2.

### AC-US-10-02 — Negative/boundary AC: third failure escalation

- **Given** an initial attempt and retry attempts one and two have each ended in failure
- **When** the third failure is recorded
- **Then** the third failure escalates the exception, no third retry command is allowed, and the task remains in the observed `FAILED` or `TIMED_OUT` state.

### AC-US-10-03 — Positive and negative/boundary AC: cancellation state gate

- **Given** cancellation is requested separately from each documented non-terminal state (`CREATED`, `VALIDATED`, `DISPATCHED`, `IN_PROGRESS`, `FAILED`, `TIMED_OUT`) and from each terminal state (`COMPLETED`, `CANCELLED`)
- **When** the WMS evaluates each request
- **Then** cancellation is allowed only from documented non-terminal states and moves those tasks to `CANCELLED`; terminal requests return `CANCELLATION_NOT_ALLOWED` with no state or inventory change.

### AC-US-10-04 — Negative/boundary AC: end-to-end offline retry escalation

- **Given** the initial offline dispatch has left the task in `FAILED` with failure count 1, retry count 0, and an active exception, and the device remains offline during retry attempt one and retry attempt two
- **When** the supervisor requests those two retries in sequence
- **Then** retry attempt one follows `FAILED -> DISPATCHED -> FAILED`, increments failure evidence to 2 and retry count to 1, and preserves an active actionable exception; retry attempt two follows `FAILED -> DISPATCHED -> FAILED`, increments failure evidence to 3 and retry count to 2; the initial failure plus two failed retries makes that outcome the third failure overall, escalates the exception, and creates no third retry command.

## US-11 — Audit trail

**Story:** As a portfolio reviewer, I want chronological evidence for commands, events, decisions, and mutations so that I can reconstruct a synthetic movement without inferring hidden behavior.

- **Persona:** Portfolio reviewer acting through the warehouse supervisor/integration-engineer evidence view.
- **Capability:** Read a correlated, chronological audit trail for a pallet and movement task.
- **Business value:** Makes state, recovery, duplicate handling, and inventory outcomes explainable and reviewable.
- **Linked BN:** `BN-02`, `BN-04`.
- **Linked FR:** `FR-10`.
- **Linked BR:** `BR-05`, `BR-06`, `BR-07`.
- **Linked NFR:** `NFR-02`, `NFR-03`, `NFR-04`, `NFR-05`.
- **Assumptions:** Audit retention/access policy is outside the local simulator; only synthetic session evidence is shown.
- **Dependencies:** `US-04..US-10` supply stable actions, states, and identities.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent evidence view; Negotiable presentation; Valuable diagnosis/trace; Estimable from audit contract; Small read-only slice; Testable by action-to-entry reconciliation and mutation guards.

### AC-US-11-01 — Positive AC: reconstruct movement history

- **Given** a synthetic task has been created, dispatched, processed through events, and either completed or recovered from an exception
- **When** the reviewer opens its audit trail
- **Then** chronological entries show correlation/entity IDs, action, prior/new state where applicable, actor/component, and UTC timestamp for every accepted command, event, retry, cancellation, escalation, and inventory mutation.

### AC-US-11-02 — Negative/boundary AC: read-only evidence and missing fields

- **Given** an audit fixture with a missing mandatory field and a user reading a valid audit trail
- **When** automated audit reconciliation runs and the user filters/sorts the view
- **Then** reconciliation fails the incomplete fixture, while reading, filtering, or sorting creates no task, exception, or inventory mutation.

## US-12 — Metrics

**Story:** As a warehouse manager persona, I want four clearly defined synthetic metrics so that I can interpret flow outcomes without mixing undispatched tasks into the cohort.

- **Persona:** Warehouse manager persona.
- **Capability:** View Completion Rate, Exception Rate, First Pass Success Rate, and Average Simulated Cycle Time with formulas and cohort explanation.
- **Business value:** Provides a reconciled summary for the demo while keeping denominator and simulation limits visible.
- **Linked BN:** `BN-02`, `BN-03`, `BN-04`.
- **Linked FR:** `FR-10`.
- **Linked BR:** `BR-10`.
- **Linked NFR:** `NFR-01`, `NFR-02`, `NFR-03`, `NFR-04`, `NFR-05`.
- **Assumptions:** Only tasks that reached `DISPATCHED` enter the cohort; empty rate denominators display `N/A` under `PROP-02` pending manager confirmation.
- **Dependencies:** `US-04..US-11` provide trusted state, retry, exception, completion, timestamp, and audit data.
- **Priority status:** PROPOSED in ordered backlog; Product Owner confirmation required.
- **Estimate status:** Not estimated; delivery team confirmation required.
- **INVEST check:** Independent reporting slice after data integrity; Negotiable presentation; Valuable transparent interpretation; Estimable from formulas/read model; Small four-metric scope; Testable with fixed histories and empty cohort.

### AC-US-12-01 — Positive AC: formula reconciliation

- **Given** a fixed synthetic history containing dispatched completed, dispatched failed/timed-out, completed-with-retry, completed-without-retry, and undispatched tasks with known timestamps
- **When** metrics are calculated
- **Then** Completion Rate equals completed/dispatched, Exception Rate equals dispatched tasks ever failed-or-timed-out/dispatched, First Pass Success Rate equals completed with zero retries/dispatched, Average Simulated Cycle Time equals the average `completed_at - dispatched_at` for completed tasks in the dispatched cohort, and undispatched tasks affect none of the four outputs.

### AC-US-12-02 — Negative/boundary AC: empty dispatched cohort

- **Given** a synthetic store with zero tasks that reached `DISPATCHED`
- **When** metrics are calculated
- **Then** the three rates and Average Simulated Cycle Time display `N/A`, expose dispatched cohort count 0, and never return an infinite or misleading success value.

## Coverage and readiness review

- Exactly twelve stories are defined in dependency/risk order, with 26 unique acceptance criteria.
- Every story links to at least one valid business need, functional requirement, business rule, and non-functional requirement.
- Every business rule `BR-01..BR-10` is exercised by at least one story; high-risk idempotency, inventory, retry, escalation, and cancellation boundaries have explicit Given/When/Then checks.
- Priority and estimate ownership remain with an accountable Product Owner and delivery team. Persona, policy, threshold, cancellation, and metric-display fit require human review before use beyond the local simulation.
- Later tasks may refine technical payload or display design but must not weaken these observable outcomes without recording a proposed requirement change and its traceability impact.
