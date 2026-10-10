# Product Goal and Ordered Backlog — Draft — Personal synthetic portfolio

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

## Product Goal

Enable warehouse staff to receive and put away a pallet with visible status and controlled exception recovery without updating inventory before verified completion.

This goal describes the intended value of a local simulator. It is not an operating-site outcome or a measured benefit.

## Ordering method

The backlog is ordered qualitatively by:

1. **Dependency:** establish valid identity and deterministic decisions before commands, events, inventory, and reporting consume them.
2. **Operational risk:** protect inventory and event identity before adding recovery views and management outputs.
3. **User value:** first enable a safe end-to-end movement, then make exceptions, evidence, and metrics easier to act on.

No WSJF, RICE, effort, reach, monetary value, or delivery-date inputs are available. Numeric scoring would therefore create false precision. The order is a **PROPOSED portfolio sequence** derived from the plan; an accountable Product Owner must confirm final priority and the delivery team must estimate feasibility and effort in an actual project.

## Ordered backlog

| Rank | Story | Title | User outcome | Dependency rationale | Operational-risk rationale | Status |
|---:|---|---|---|---|---|---|
| 1 | `US-01` | Validation | Operator receives specific feedback and invalid receipt data cannot continue. | Establishes trusted barcode, SKU, and quantity for every later step. | Invalid input must be stopped before location or automation decisions. | PROPOSED priority; not estimated |
| 2 | `US-02` | Unique identity | Operator cannot create a second pallet under an existing identity. | Requires receipt validation; protects all later correlations. | Duplicate identity can make tasks, events, and inventory ambiguous. | PROPOSED priority; not estimated |
| 3 | `US-03` | Location selection | Operator receives one explainable compatible destination or a visible capacity exception. | Requires a valid, unique pallet and location master. | An incompatible or full destination must be caught before task creation. | PROPOSED priority; not estimated |
| 4 | `US-04` | Movement task and state | Supervisor can trace one planned movement through documented states. | Requires pallet and destination identity. | State discipline prevents silent or unsupported movement progress. | PROPOSED priority; not estimated |
| 5 | `US-05` | WCS dispatch | Integration engineer can correlate an eligible task to one simulated command. | Requires a movement task and allowed dispatch origin. | Prevents false dispatch and exposes simulated device unavailability. | PROPOSED priority; not estimated |
| 6 | `US-06` | Event processing | Integration engineer can apply valid simulated events and reject invalid sequences. | Requires a dispatched command and state model. | Event validation protects task truth before inventory consequences. | PROPOSED priority; not estimated |
| 7 | `US-07` | Idempotency | Integration engineer can replay an event safely with a clear duplicate outcome. | Requires event intake and stable event identity. | Duplicate delivery must not repeat state or inventory mutations. | PROPOSED priority; not estimated |
| 8 | `US-08` | Inventory commit | Supervisor sees one inventory movement only after verified completion. | Requires valid event processing and idempotency. | Inventory integrity is the highest-impact mutation boundary. | PROPOSED priority; not estimated |
| 9 | `US-09` | Exception queue | Supervisor can see active validation, capacity, device, jam, timeout, and recovery exceptions. | Depends on failure-producing validation, location, dispatch, and event paths. | Visible ownership prevents failure states from becoming hidden work. | PROPOSED priority; not estimated |
| 10 | `US-10` | Retry, escalation, and cancellation | Supervisor can recover or stop eligible work within bounded rules. | Requires task states and exception identity. | Unlimited retry or unsafe cancellation can obscure or worsen failure. | PROPOSED priority; not estimated |
| 11 | `US-11` | Audit trail | Reviewer can reconstruct commands, events, decisions, and mutations. | Relies on stable action/state semantics from the preceding stories. | Evidence is needed to diagnose inconsistency and support later UAT. | PROPOSED priority; not estimated |
| 12 | `US-12` | Metrics | Manager can interpret four reconciled synthetic metrics from the dispatched cohort. | Requires trustworthy task, retry, exception, audit, and timestamp data. | Metrics must follow integrity controls so they do not hide denominator or state errors. | PROPOSED priority; not estimated |

## Dependency view

`US-01 -> US-02 -> US-03 -> US-04 -> US-05 -> US-06 -> US-07 -> US-08`

The core flow then supplies failure/evidence data to `US-09 -> US-10 -> US-11 -> US-12`. This is a delivery dependency, not a claim that user feedback must wait until the end; each completed story can be reviewed with synthetic examples.

## Priority decision record

| Item | Current treatment | Why | Human checkpoint / trigger |
|---|---|---|---|
| Backlog order | PROPOSED as listed | Uses plan dependency and risk sequence without invented numbers | Product Owner confirms when stakeholder evidence, release objective, cost, or deadline exists |
| Estimates | Not estimated | No delivery-team evidence is available | Delivery team estimates after technical refinement and Definition of Ready review |
| Strategic override | None asserted | No sponsor outcome or regulatory/safety constraint has been supplied | Accountable owner records any override with rationale and affected dependency |
| Scope additions | Excluded from this backlog | Keep exactly twelve Task 2 stories and the inbound-only boundary | New need enters change review rather than silently changing a story |

## Review notes

- All twelve stories preserve the exact order required by the Task 2 brief.
- Validation and identity precede automation; event idempotency precedes inventory commitment; evidence precedes metrics.
- Story details and Given/When/Then acceptance criteria are defined in `docs/06-user-stories-and-acceptance-criteria.md`.
- Final priority, scope acceptance, and estimates remain human decisions. This document does not assert sprint readiness, delivery dates, capacity, or quantified value.
