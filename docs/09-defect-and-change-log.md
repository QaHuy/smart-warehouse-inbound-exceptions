# Defect and Change Log — Portfolio handover

## Handover summary

- Open defects at handover: **0**.
- Closed implementation findings: **1**.
- Deferred change requests: **2**.
- Implemented change requests after handover: **1**.
- Open assumption gaps: **1**.
- No production deployment, real WCS connection, or customer data was used.

## Classification rules

| Classification | Use when | Example response |
|---|---|---|
| Defect | Implemented behavior contradicts an approved requirement or acceptance criterion. | Reproduce, assess impact, fix, run regression, retain evidence. |
| Change request | Requested behavior is new or intentionally outside the approved baseline. | Assess value, scope, risk, dependencies, and approval before changing the baseline. |
| Assumption gap | The solution depends on an unvalidated operational fact or stakeholder decision. | Do not guess; plan discovery, record owner, and revisit linked artefacts. |

## Log

| ID | Classification | Finding / request | Impact | Decision and evidence | Status |
|---|---|---|---|---|---|
| `DEF-001` | Defect | Recruiter demo UI and handover evidence did not yet exist when the UI acceptance tests were introduced. | The domain logic was testable, but a recruiter could not execute or inspect the workflow visually. | Implemented local static UI, wired all public domain actions, added accessibility and privacy gates, and retained four screenshots. `tests/test_prototype.py` now passes. | Closed |
| `CR-001` | Change request | Connect the portfolio to a real WCS, PLC, conveyor, lift, or robot. | Would introduce credentials, networking, device safety, vendor contracts, and operational risk beyond a portfolio demonstration. | Deferred. Keep simulated integration disclosure. A future initiative would require architecture, security, safety, and vendor review. | Deferred |
| `CR-002` | Change request | Add outbound picking, replenishment, wave planning, and labor optimization. | Expands the domain well beyond the inbound exception-management product goal and weakens the current interview narrative. | Deferred to a separately scoped roadmap; do not add to this MVP baseline. | Deferred |
| `CR-003` | Change request | Publish a recruiter pack: static GitHub Pages case study and demo, PDF and Word case study, one-page summary, rendered BPMN images, and a simplified To-Be overview. | Makes the work reviewable without local setup; adds a public surface that must stay synthetic. | Approved by the portfolio author on 2026-10-10. `PC-03` revised; requirement documents stay Draft, with only stale UAT-pending notes corrected (SRS v0.2, no requirement change); full automated suite and privacy checks re-run. | Implemented |
| `AG-001` | Assumption gap | Proposed actors, putaway priorities, retry limit, and cancellation rights have not been validated by a warehouse SME or customer. | Real operating constraints could change workflow, ownership, exceptions, or acceptance criteria. | Keep all requirements labelled as portfolio decisions/proposals. Before real delivery, run the interview guide and obtain decision-owner sign-off. | Open for real-world adoption |

## Change-control path

1. Record the trigger, requested outcome, and decision owner.
2. Classify it as Defect, Change request, or Assumption gap.
3. Trace affected `BN`, `FR`, `BR`, `US`, interfaces, data objects, and UAT cases.
4. Assess safety, privacy, integration, and regression impact.
5. Update the approved baseline only after decision-owner review.
6. Re-run affected automated tests and the full UAT pack before handover.
