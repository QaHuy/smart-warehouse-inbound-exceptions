# WMS–WCS Sequence — Happy Path and Controlled Exceptions

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

## Scope and reading guide

Read from top to bottom. Solid arrows are requests or simulated commands; dashed arrows are returned outcomes or simulated events. The sequence deliberately shows the happy path and four explicit exception groups: no compatible capacity, device offline with bounded retry, timeout recovery, and duplicate completion idempotency.

```mermaid
sequenceDiagram
    actor UI as Operator UI
    participant WMS as WMS Demo
    participant INTAKE as WMS Event Intake
    participant DB as SQLite contract database
    participant WCS as WCS Simulator
    participant DEV as Device Simulators

    UI->>WMS: Submit synthetic inbound receipt
    WMS->>WMS: Validate barcode, SKU, quantity, duplicate pallet ID
    WMS->>DB: Read compatible locations ordered by zone priority and code
    alt Full or no compatible location
        WMS->>DB: Record capacity exception
        WMS-->>UI: NO_AVAILABLE_LOCATION; no task or dispatch
    else Compatible location available
        WMS->>DB: Create task and record CREATED to VALIDATED
        alt Device offline
            WMS->>DB: Record VALIDATED to FAILED; failure count 1, retry count 0
            WMS-->>UI: DEVICE_OFFLINE with active actionable exception
            UI->>WMS: Retry 1
            WMS->>DB: Record FAILED to DISPATCHED and retry count 1
            WMS->>WCS: Redispatch correlated simulated command
            WCS-->>INTAKE: TASK_FAILED with task/correlation and unique event_id
            INTAKE->>INTAKE: Start independent intake instance; validate context and transition
            INTAKE-->>WMS: Route unique valid failure to active task workflow
            WMS->>DB: Retry 1 path FAILED to DISPATCHED to FAILED; failure evidence 2
            UI->>WMS: Retry 2
            WMS->>DB: Record FAILED to DISPATCHED and retry count 2
            WMS->>WCS: Redispatch correlated simulated command
            WCS-->>INTAKE: TASK_FAILED with task/correlation and unique event_id
            INTAKE->>INTAKE: Start independent intake instance; validate context and transition
            INTAKE-->>WMS: Route unique valid failure to active task workflow
            WMS->>DB: Record DISPATCHED to FAILED; failure evidence 3
            WMS-->>UI: Escalate on failure 3; no third retry command after third failure
        else Device online
            WMS->>DB: Persist correlated command before state change
            WMS->>WCS: Dispatch simulated WCS command
            WMS->>DB: Record VALIDATED to DISPATCHED
            WCS->>DEV: Execute simulated conveyor, lift, and robot steps
            DEV-->>WCS: Simulated progress evidence
            WCS-->>INTAKE: TASK_STARTED with unique event_id
            INTAKE->>INTAKE: Validate payload, task/correlation identity, event_id, and current-state transition
            INTAKE-->>WMS: Route unique valid event to active task workflow
            WMS->>DB: Record DISPATCHED to IN_PROGRESS
            alt Timeout
                WCS-->>INTAKE: TASK_TIMEOUT with unique event_id
                INTAKE->>INTAKE: Validate context and allowed transition
                INTAKE-->>WMS: Route unique valid timeout to active task workflow
                WMS->>DB: Record TIMED_OUT and active exception
                UI->>WMS: Retry from TIMED_OUT when retry count is below 2
                WMS->>WCS: Redispatch correlated command
                WMS->>DB: Record TIMED_OUT to DISPATCHED
            else Completion received
                WCS-->>INTAKE: TASK_COMPLETED with unique event_id
                INTAKE->>INTAKE: Start independent intake instance; validate required context
                INTAKE->>INTAKE: Confirm unique event is valid for current state
                INTAKE-->>WMS: Route unique valid completion to active task workflow
                WMS->>DB: Record COMPLETED
                WMS->>DB: Commit inventory exactly once
                WMS-->>UI: Pallet stored with audit evidence
            end
        end
    end
    opt Replay after original inbound process ended
        WCS-->>INTAKE: Replay prior TASK_COMPLETED with same event_id
        INTAKE->>INTAKE: Message start creates a new independent intake instance
        INTAKE->>INTAKE: Validate required context and look up task state/event identity
        alt Duplicate completion event
            INTAKE-->>WCS: success with duplicate: true
            INTAKE->>DB: No second state or inventory mutation
            Note over INTAKE,WMS: Terminal task stays terminal; no parent-process reactivation
        else Late unique, invalid, unknown, or out-of-sequence event
            INTAKE->>DB: Record diagnostic audit only; preserve state and inventory
            INTAKE-->>WCS: Invalid event response; no mutation
        end
    end
```

## Business walkthrough

- A full or incompatible location stops before task creation and dispatch.
- Because no movement task exists on a receipt-validation or no-location error, that pre-task branch cannot perform task cancellation.
- An initially offline device produces `VALIDATED -> FAILED`, failure count 1, retry count 0, and an active exception. The first attempt is a failure, not a retry.
- Retry 1 and Retry 2 each redispatch from `FAILED`. If the device remains offline, the task returns to `FAILED`; the third failure overall escalates and creates no third retry command.
- A timeout records `TIMED_OUT` and may re-enter `DISPATCHED` only through an eligible bounded retry.
- Every WCS event starts a logically separate `WMS Event Intake` instance. It validates required payload, task/correlation identity, event identity, current task state, and allowed transition before routing any unique valid event to the active workflow.
- An invalid, unknown, or out-of-sequence event records diagnostic audit evidence, preserves state/inventory, responds, and ends only that intake instance. A later event starts another instance.
- A unique valid `TASK_COMPLETED` can complete the task and commit inventory once. Replaying its `event_id` after the original inbound process ended starts a new intake instance and returns duplicate success without reactivating the terminal task or creating a second mutation.

## Linked requirements and rules

- Input and location: `FR-01..FR-04`, `BR-01..BR-04`, `US-01..US-03`.
- Dispatch and event lifecycle: `FR-05..FR-07`, `BR-05`, `US-04..US-06`.
- Idempotency and inventory: `BR-06`, `BR-07`, `US-07`, `US-08`.
- Exceptions, retry, escalation, and cancellation boundary: `FR-08`, `FR-09`, `BR-08`, `BR-09`, `US-09`, `US-10`.
- Auditability and local simulation: `NFR-01`, `NFR-02`, `NFR-04`, `NFR-05`.

## Assumptions and gaps

- The diagram uses a single simulated device boundary; later contracts may distinguish conveyor, lift, and robot payloads.
- Retry dispatch is shown immediately after the supervisor action. Exact acknowledgement timing and event-order controls are not yet designed.
- Task cancellation is guarded by task existence and the exact allowed origins in the state model; receipt/no-location exceptions have no task to cancel.
- Timeout recovery is shown as an eligible rejoin. A later implementation must also enforce the shared two-retry limit across failure types.

## Human review boundary

The retry and cancellation workflow is a proposed simulator policy. Warehouse supervision, integration, maintenance, and safety reviewers must confirm recovery ownership, acknowledgement timing, physical-motion constraints, and escalation evidence before operational reuse.
