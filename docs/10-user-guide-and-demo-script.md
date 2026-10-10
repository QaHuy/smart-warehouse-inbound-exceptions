# User Guide and 5-minute recruiter walkthrough

## Honest positioning

Use this disclosure at the beginning of every demonstration:

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated. No production warehouse data or physical equipment is connected.

The case study demonstrates business-analysis reasoning, traceability, state and exception controls, API/data thinking, acceptance testing, and product communication. It does not claim warehouse employment experience or production WMS/WCS delivery.

## Start locally

From `portfolio/smart-warehouse-inbound-exceptions/prototype` run:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. The application is static and local-only; no install, login, backend, or network API is required. Refresh or choose **Reset demo** to clear the in-memory synthetic state.

## Controls

- **Inbound:** validate a receipt, then explicitly assign an eligible location.
- **Tasks:** select a task, dispatch it, apply a simulated WCS event, retry, or cancel.
- **Exceptions:** inspect failure counts, retry counts, and escalation status.
- **Inventory & audit:** verify exactly-once inventory movement and chronological evidence.
- **Guided scenarios:** reset and run a complete Happy path, Offline escalation, or Duplicate event story.

## 5-minute recruiter walkthrough

### 0:00–0:35 — Frame the problem

“This is a personal BA portfolio case study for warehouse inbound and exception management. I modelled how a WMS can validate receipt data, choose a compatible location, coordinate a simulated WCS task, and protect inventory integrity when events fail or repeat.”

Point to the disclosure. Explain that the business challenge is not simply moving a pallet: it is keeping receipt, task, event, exception, and inventory truth consistent.

### 0:35–1:25 — Explain discovery and requirements

Open `docs/01-case-study-brief.md`, `docs/02-stakeholders-and-interview-guide.md`, and the As-Is / To-Be diagrams if time permits.

“I separated confirmed project constraints from proposed warehouse assumptions. The interview guide asks operators, supervisors, managers, integration engineers, and maintenance roles for observable evidence. The SRS then traces four business needs into ten functional requirements, ten business rules, twelve stories, and fourteen UAT cases.”

### 1:25–2:30 — Happy path

Choose **Run happy path**.

Expected visible evidence:

- The synthetic receipt is accepted.
- A01 is selected using compatibility, capacity, zone priority, and location-code tie-break rules.
- The task moves through `CREATED → VALIDATED → DISPATCHED → IN_PROGRESS → COMPLETED`.
- One inventory movement is committed only after the valid completion event.
- The audit trail links command, event, state, and inventory evidence.

Interview line: “The inventory write is deliberately completion-gated. This reduces the business risk of stock appearing at a destination before automation confirms the move.”

### 2:30–3:30 — Offline escalation

Choose **Run offline escalation**.

Expected visible evidence:

- Initial offline dispatch is a failure, not a retry.
- Two retries are counted.
- Failure 3 escalates the exception.
- No third retry command is created.

Interview line: “I made retry semantics explicit because ambiguous attempt counting causes operational confusion. This baseline allows two retries after the initial failure, then requires human review.”

### 3:30–4:15 — Duplicate event

Choose **Run duplicate event**.

Expected visible evidence:

- The same completion `event_id` is replayed.
- The duplicate returns a successful no-op result.
- Task state and inventory are not mutated again.
- Exactly one inventory movement remains.

Interview line: “Idempotency is both a technical and business control: duplicate delivery must not duplicate stock movement.”

### 4:15–5:00 — Close with traceability and limitations

Open the RTM and UAT pack.

“All fourteen synthetic UAT cases are executable and passed locally, including negative paths and metric reconciliation. I also retained a defect/change log so new scope is separated from defects. For a real client, my next step would be on-site observation and SME interviews to validate putaway priorities, ownership, retry limits, safety constraints, and integration contracts.”

## Scenario quick reference

| Scenario | What it proves | Screenshot |
|---|---|---|
| Happy path | Deterministic assignment, valid state flow, completion-gated inventory, auditability | `assets/02-happy-path-inventory.png` |
| Offline escalation | Initial failure semantics, two-retry limit, third-failure escalation | `assets/03-offline-escalation.png` |
| Duplicate event | Idempotent event handling and exactly-once inventory consequence | `assets/04-duplicate-event.png` |

## Likely interview questions

**Why did you choose an in-memory simulator?**  
To demonstrate the rules and evidence safely without pretending to integrate with real equipment. It keeps the portfolio reproducible and makes the limitations obvious.

**How would you validate this with a customer?**  
Observe inbound work on site, interview the five proposed personas, capture real exception examples, validate the As-Is / To-Be flow, confirm data and integration contracts, then update requirements and UAT with named decision owners.

**What is the most important control?**  
Completion-gated, idempotent inventory mutation. State and audit controls support it, but the business consequence to protect is false or duplicate stock movement.

**What would you build next?**  
Only after discovery: persistence and authentication, explicit operator ownership/SLA, API contract tests, observability, concurrency controls, and integration testing in a safe device test environment.
