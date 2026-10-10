# UAT Pack and Executed Results — Synthetic local simulator

## Test objective

Confirm that the portfolio prototype implements the documented business outcomes and integrity controls: invalid input is stopped early, task transitions fail closed, exceptions are visible, retry is bounded, duplicate events are idempotent, and inventory is committed exactly once after verified completion.

## Environment and execution

- Execution date: 18 September 2026.
- Environment: local browser prototype and in-memory JavaScript domain simulator.
- Data: synthetic `DEMO` / `UAT` identifiers only.
- Runner: Node built-in test runner.
- Command: `node --test tests/uat.test.mjs`.
- Automated result: **14 / 14 passed**, 0 failed, 0 skipped.
- Visual checks: default desktop viewport and responsive 390 × 844 viewport; no blocking layout or interaction issue observed.

## Acceptance results

| ID | Scenario | Requirement links | Preconditions / input | Expected outcome | Status | Actual result | Evidence |
|---|---|---|---|---|---|---|---|
| UAT-01 | Valid inbound happy path | `FR-01`, `FR-04..FR-07`, `FR-10`; `US-01`, `US-03..US-06`, `US-08`, `US-11` | Active ambient SKU, quantity 10, online simulated device | Pallet received; A01 selected; task reaches COMPLETED; one movement is committed | PASS | Task completed and inventory movement count equalled exactly 1 | `tests/uat.test.mjs` — UAT-01; `assets/02-happy-path-inventory.png` |
| UAT-02 | Malformed barcode | `FR-02`; `US-01` | Barcode contains a space | Return INVALID_BARCODE; create no pallet or task | PASS | Validation rejected input and pallet count remained 0 | `tests/uat.test.mjs` — UAT-02 |
| UAT-03 | Unknown or inactive SKU | `FR-02`; `BR-02`; `US-01` | Inactive synthetic SKU | Return UNKNOWN_OR_INACTIVE_SKU; create no task | PASS | Receipt was rejected and task count remained 0 | `tests/uat.test.mjs` — UAT-03 |
| UAT-04 | Zero quantity | `FR-02`; `BR-01`; `US-01` | Quantity 0 | Return INVALID_QUANTITY; create no pallet | PASS | Quantity boundary was enforced and pallet count remained 0 | `tests/uat.test.mjs` — UAT-04 |
| UAT-05 | Duplicate pallet identity | `FR-03`; `BR-03`; `US-02` | Submit same pallet ID twice with changed quantity | Reject second receipt and preserve original | PASS | Returned DUPLICATE_PALLET; original quantity remained 8 | `tests/uat.test.mjs` — UAT-05 |
| UAT-06 | No compatible capacity | `FR-04`, `FR-08`; `BR-04`; `US-03`, `US-09` | All compatible locations at capacity | Create NO_AVAILABLE_LOCATION exception; no movement task | PASS | Exception was visible and task count remained 0 | `tests/uat.test.mjs` — UAT-06 |
| UAT-07 | Device offline at initial dispatch | `FR-06`, `FR-08`, `FR-09`; `US-05`, `US-09`, `US-10` | Validated task; default device offline | Task fails; failure count 1; retry count 0; no command | PASS | Returned DEVICE_OFFLINE with zero retry and zero command records | `tests/uat.test.mjs` — UAT-07 |
| UAT-08 | Simulated pallet jam | `FR-07..FR-09`; `US-06`, `US-09`, `US-10` | Dispatched task; TASK_FAILED with PALLET_JAM | Task becomes FAILED and active jam exception is visible | PASS | FAILED state and PALLET_JAM exception were both recorded | `tests/uat.test.mjs` — UAT-08 |
| UAT-09 | Simulated task timeout | `FR-07..FR-09`; `US-06`, `US-09`, `US-10` | Dispatched task; TASK_TIMEOUT | Task becomes TIMED_OUT and timeout exception is visible | PASS | TIMED_OUT state and TASK_TIMEOUT exception were both recorded | `tests/uat.test.mjs` — UAT-09 |
| UAT-10 | Retry after device recovery | `FR-06`, `FR-09`; `BR-08`; `US-05`, `US-10` | Initial offline failure; device changed to online | First retry creates attempt 1 command and returns DISPATCHED | PASS | Retry succeeded with state DISPATCHED and attempt number 1 | `tests/uat.test.mjs` — UAT-10 |
| UAT-11 | Third failure escalation | `FR-08`, `FR-09`; `BR-08`, `BR-09`; `US-09`, `US-10` | Device remains offline for initial attempt and two retries | Third failure escalates; no third retry command | PASS | Exception status escalated at failure 3, retry count 2, command count 0 | `tests/uat.test.mjs` — UAT-11; `assets/03-offline-escalation.png` |
| UAT-12 | Cancellation state gate | `FR-09`; `BR-05`; `US-10` | One timed-out task and one completed task | Permit timeout cancellation; reject completion cancellation | PASS | Timeout became CANCELLED; completed task returned CANCELLATION_NOT_ALLOWED | `tests/uat.test.mjs` — UAT-12 |
| UAT-13 | Duplicate completion event | `FR-07`, `FR-10`; `BR-06`, `BR-07`; `US-07`, `US-08`, `US-11` | Replay identical completed event ID | Return duplicate success; no second state or inventory mutation | PASS | Replay was flagged duplicate; inventory movement count remained 1 | `tests/uat.test.mjs` — UAT-13; `assets/04-duplicate-event.png` |
| UAT-14 | Metric reconciliation | `FR-10`; `BR-10`; `US-12` | Fixed cohort: 4 dispatched, 2 completed, 3 failed/timeout ever, 1 first-pass, cycles 60s and 180s | Return 50%, 75%, 25%, and 120 seconds | PASS | Metrics exactly matched 0.50, 0.75, 0.25, and 120 seconds | `tests/uat.test.mjs` — UAT-14 |

## Exit decision

Portfolio quality gate: **PASS**. The current synthetic scope has executable evidence for every reserved UAT case and no open functional defect. This decision authorizes the case study to be shown as a completed personal portfolio artefact. It does not authorize a production release or claim customer acceptance.

## Residual limitations

- The WCS is a deterministic in-memory simulator, not a physical device or third-party integration.
- Persistence, authentication, concurrency, network retry, observability, and production performance are intentionally outside scope.
- No warehouse user or domain SME has validated the proposed workflow; real discovery could change rules and priorities.
