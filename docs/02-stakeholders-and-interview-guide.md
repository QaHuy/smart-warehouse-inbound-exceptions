# Proposed Stakeholders and Interview Guide

## Status and ethical boundary

This is an **unexecuted interview plan** for a synthetic portfolio case. The personas are role archetypes, not identified individuals. No interview, site observation, authority assignment, operational statement, or evidence request below has been completed or confirmed.

All decision rights are **proposed for the simulation**. In a real engagement, the sponsor or appointed governance owner would confirm authority before any decision or sign-off.

## Stakeholder register

| Persona | Interest and impact | Proposed decision authority | Information needed | Expected evidence to request | Proposed cadence |
|---|---|---|---|---|---|
| Inbound operator | High impact; performs receipt and responds to validation feedback | Recommend usability and safe-workflow changes; no proposed authority over inventory policy or device recovery | Required scan fields, error clarity, physical handoffs, common workarounds | Redacted recent receipt examples, field checklist, screen/form walkthrough, anonymized error notes | One 45-minute discovery session; one prototype walkthrough |
| Warehouse supervisor | High influence and high impact; coordinates queue and exceptions | Approve the simulated operating procedure for retry, cancel, and escalation, subject to real governance confirmation | Queue priority, recovery limits, handoff ownership, exception evidence | Redacted exception log, escalation procedure, shift handover template, recent incident timeline | One 60-minute discovery session; weekly decision review during design |
| Warehouse manager | High influence; accountable for operational risk and reporting expectations | Approve the proposed business outcome, scope, and metric interpretation for the simulation; not technical event semantics | Risk exposure, capacity visibility, decision-ready metrics, audit needs | Existing KPI definitions, capacity policy, audit sample, governance chart | One 45-minute outcome session; milestone review |
| Integration engineer | High influence; high technical impact on traceability and idempotency | Approve proposed message contract and technical state/event semantics within the simulation | IDs, ordering, retry behavior, timestamps, duplicate handling, observability | Redacted payload/schema sample, interface catalogue, event timeline, error-code list | Two 45-minute technical sessions; contract review on changes |
| Maintenance technician | Medium influence and high recovery impact | Confirm diagnostic steps and evidence needed for simulated device recovery; no proposed authority to commit inventory | Device symptoms, safe checks, ownership boundary, recovery confirmation | Redacted alarm history, maintenance checklist, device-state walkthrough, escalation record | One 45-minute discovery session; one exception-path walkthrough |

“Expected evidence” means material to request if an authorized real engagement occurs. It is not evidence held by this portfolio.

## Influence and impact view

| Segment | Personas | Engagement approach |
|---|---|---|
| High influence / high impact | Warehouse supervisor, integration engineer | Collaborate on decision wording and validate exception/event controls frequently. |
| High influence / medium impact | Warehouse manager | Align outcome, scope, risk tolerance, and metric interpretation at milestones. |
| Medium influence / high impact | Inbound operator, maintenance technician | Observe workflow and test usability/recovery assumptions with artifact walkthroughs. |

The placements are proposals based on role responsibilities in this synthetic operating model. They must not be interpreted as an assessment of real people or an organization chart.

## Proposed decision-rights and RACI

R = responsible for supplying input or performing the proposed activity; A = proposed accountable role for the simulation; C = consulted; I = informed. Each row has one proposed A to make the model testable, but no authority is confirmed for a real warehouse.

| Decision or deliverable | Inbound operator | Warehouse supervisor | Warehouse manager | Integration engineer | Maintenance technician |
|---|---:|---:|---:|---:|---:|
| Receipt fields and operator feedback | R | A | I | C | I |
| Putaway compatibility and capacity policy | C | R | A | C | I |
| Retry, cancel, and escalation procedure | C | A | I | C | R |
| Command/event contract and idempotency semantics | I | C | I | A/R | C |
| Device diagnostic and recovery evidence | I | A | I | C | R |
| Synthetic metric meaning and management view | I | R | A | C | I |

Human checkpoint: an authorized sponsor or PM must replace these proposed assignments with confirmed governance before reuse outside the portfolio.

## Engagement risks

| Risk | Why it matters | Mitigation in the interview plan |
|---|---|---|
| Authority is inferred from a job title | A role may advise without owning the decision | Ask who made the most recent comparable decision and request the governance artifact. |
| Recall bias | General answers may hide actual exceptions | Anchor questions to the most recent concrete receipt, failure, or handover. |
| Leading toward the planned solution | Participants may agree with a WMS/WCS design they did not request | Ask for current behavior and consequences before showing any proposed artifact. |
| Sensitive operational or personal data is exposed | Logs and screenshots can contain identifiers | Request redacted examples; do not record names, credentials, customer data, or device addresses. |
| One shift or role dominates | The model may omit handovers and alternate conditions | Sample different responsibilities and compare evidence before changing a rule. |
| Simulation is mistaken for validation | Portfolio decisions could appear production-approved | Keep all findings labelled pending until actual evidence and authorized sign-off exist. |

## Interview objectives and evidence types

The guide deliberately separates five learning types:

- **Observed fact:** what the participant did or saw in a recent concrete event.
- **Assumption:** what is believed but not yet supported by direct evidence.
- **Constraint:** a policy, safety, capacity, timing, or system boundary that limited action.
- **Exception:** a deviation, failure, workaround, escalation, or unresolved case.
- **Desired outcome:** how the participant judges a safer or clearer result, without asking them to design the solution.

## Suggested 45-minute session

| Time | Activity | Output |
|---:|---|---|
| 0–3 min | Introduce purpose, voluntary participation, privacy, and note-taking choice | Consent and boundaries |
| 3–8 min | Role and recent-work context | Responsibilities and vocabulary |
| 8–25 min | Walk through the most recent relevant event | Timeline, observed facts, artifacts, and handoffs |
| 25–34 min | Explore exceptions, constraints, and workarounds | Failure paths and decision rights |
| 34–40 min | Walk through one redacted artifact or neutral sketch | Gaps, interpretation, and terminology |
| 40–44 min | Desired outcomes and priorities | Outcome criteria and trade-offs |
| 44–45 min | Recap, corrections, follow-up permission | Validated notes and open evidence requests |

## Core questions by persona

Questions are phrased around recent behavior. Bracketed labels identify the evidence type being elicited, not a presumed answer.

### Inbound operator

1. **[Observed fact]** Please walk me through the most recent pallet receipt you handled, from the first scan or entry until you handed it off. What did you look at at each step?
2. **[Exception]** Thinking of the most recent receipt that could not continue, what appeared first, what did you do next, and where was the outcome recorded?
3. **[Constraint]** During that receipt, which rule, field, time pressure, or system limitation restricted what you could do?
4. **[Assumption]** Which information did you have to trust without checking directly, and what made you treat it as reliable?
5. **[Desired outcome]** Looking back at that event, what information would have let you decide the next safe action sooner, and how would you know it was sufficient?

### Warehouse supervisor

1. **[Observed fact]** Please reconstruct the most recent inbound exception you coordinated: who noticed it, who decided the next action, and what record was left?
2. **[Exception]** In the last case involving a retry or cancellation, what checks happened before the action and what caused escalation?
3. **[Constraint]** Which safety, capacity, staffing, or approval rule limited the available recovery actions in that case?
4. **[Assumption]** What did the team believe about pallet, location, or device status that was not independently verified at the time?
5. **[Desired outcome]** After reviewing that case, which status and evidence would have made the handover unambiguous?

### Warehouse manager

1. **[Observed fact]** In the most recent operational review of inbound work, which decisions were made and which underlying records were checked?
2. **[Exception]** What recent exception pattern received management attention, and what consequence made it important?
3. **[Constraint]** Which policy or risk threshold constrained the decision made in that review?
4. **[Assumption]** Which reported figure or status required interpretation because its source or definition was unclear?
5. **[Desired outcome]** For that same review, what evidence would have made the decision more confident, and what would still require escalation?

### Integration engineer

1. **[Observed fact]** Please trace the most recent movement message through the systems you support, including the identifiers and timestamps used to correlate it.
2. **[Exception]** For the most recent duplicate, delayed, or out-of-order event, how was it detected and what state changed, if any?
3. **[Constraint]** Which interface, ordering, timeout, or retention constraint shaped the recovery behavior in that event?
4. **[Assumption]** Which delivery or device behavior did the integration rely on without being able to verify it end to end?
5. **[Desired outcome]** Looking back at that trace, what minimum fields and audit evidence would have made diagnosis conclusive?

### Maintenance technician

1. **[Observed fact]** Please walk through the most recent device alarm you investigated, from notification to return-to-service or handoff.
2. **[Exception]** What symptom, check, and recorded result distinguished the most recent jam or offline case from another failure?
3. **[Constraint]** Which safety procedure, access limit, spare-part issue, or ownership boundary restricted the actions you could take?
4. **[Assumption]** Which device or pallet condition was initially assumed, and what later evidence supported or contradicted it?
5. **[Observed fact]** For the most recent recovery event, what evidence confirmed the device or flow was ready to continue?
   - **Probe:** Who, if anyone, determined whether inventory should be updated, and what criteria or record supported that determination?

## Neutral probe bank

- “What happened immediately before and after that?”
- “How did you know?”
- “Where could we see that recorded?”
- “Who made that decision in this specific case?”
- “What did the status mean at that moment?”
- “Was there a different outcome on another recent occasion?”
- “What remained unknown?”
- “Could you show a redacted example, or describe its fields if sharing is not permitted?”
- Silence prompt: pause after an answer before moving to the next question; do not complete the participant’s sentence.

Avoid asking “Would you use this feature?”, “Is this workflow good?”, or questions that combine two decisions. A general yes/no answer is not evidence of behavior.

## Artifact walkthrough prompts

Only use redacted material that the participant is authorized to share.

- Receipt form or scan screen: “Please point to the fields you checked in the recent example. Which source did each field come from?”
- Exception or alarm record: “Which entry first changed the team’s action? What remained unresolved?”
- Movement/event timeline: “Please trace one identifier across the entries. Where did the meaning or order become ambiguous?”
- Capacity view: “For the recent placement decision, which value was treated as available capacity and how was it verified?”
- Neutral prototype sketch, shown last: “Please describe what you think each status means. Which next action is unclear?”

## Assumption-to-question map

| Assumption to validate | Primary personas | Questions/evidence |
|---|---|---|
| One pallet can be represented by one SKU and one lot in the MVP | Inbound operator, warehouse supervisor | Recent mixed-content receipt walkthrough; redacted receipt fields |
| Quantity can be restricted to a positive integer | Inbound operator, integration engineer | Recent quantity entry and payload walkthrough; validation examples |
| Location capacity can be represented as an integer pallet count | Warehouse supervisor, warehouse manager | Recent capacity decision; policy or location master definition |
| Zone priority then location code is an acceptable deterministic selector | Warehouse supervisor, warehouse manager | Reconstruct the most recent placement decision and competing constraints |
| Completion event is sufficient evidence for one inventory move | Warehouse supervisor, integration engineer | Event-to-inventory timeline; duplicate or delayed completion case |
| Two retries followed by escalation is safe and workable | Warehouse supervisor, maintenance technician | Most recent retry/escalation timeline; safety and ownership procedure |
| UTC ISO 8601 timestamps support correlation | Integration engineer, maintenance technician | Cross-system alarm and movement timeline; timezone and precision evidence |

## Interviewer checklist

Before:

- Confirm learning objective, participant role, proposed duration, and who may receive the notes.
- Confirm participation is voluntary and whether notes or recording are permitted.
- Prepare neutral prompts; place solution sketches after current-state questions.
- Ask for redacted examples only; do not request credentials, personal data, customer identifiers, private links, or device network details.

During:

- State that this is research, not performance assessment or approval.
- Anchor to a recent concrete event and separate observation from interpretation.
- Record exact artifact names only when safe; otherwise record the business meaning.
- Ask who made a decision rather than inferring authority from title.
- Read back key points and invite correction.

After:

- Remove unnecessary identifiers and store only authorized notes.
- Classify each statement as observed fact, participant assumption, constraint, exception, desired outcome, or unresolved claim.
- Link evidence without copying restricted material.
- Record contradictions and missing roles; do not force consensus.
- Do not change an assumption or decision to “validated” without traceable evidence and an authorized reviewer.

## Privacy and consent note

Suggested opening: “This session supports a learning exercise about inbound and exception workflows. Participation is voluntary. Please do not share personal data, customer information, credentials, confidential screenshots, private links, device addresses, or restricted operating details. You may decline any question. With your permission, I will take notes; no recording is assumed. We will agree who may review the notes and how long they should be retained.”

The portfolio itself should contain only generalized findings or synthetic examples. Raw interview records must not be added to this repository.

## Debrief template

| Field | Entry |
|---|---|
| Session status | Planned / completed with consent / cancelled |
| Participant archetype | Role only; no personal identifier |
| Consent and note boundary | What was permitted and who may review it |
| Recent event examined | Generalized description |
| Observed facts | Actions or records directly described/shown |
| Participant assumptions | Beliefs not yet corroborated |
| Constraints | Policy, safety, capacity, time, or system limits |
| Exceptions and workarounds | Trigger, action, owner, outcome, record |
| Desired outcomes | Evidence-based outcome criteria, not requested features |
| Artifacts reviewed | Redacted/generalized name and permitted reference only |
| Contradictions | Conflicting statements or evidence |
| Open questions | Missing facts, roles, or definitions |
| Follow-up evidence | Item, proposed role owner, permission, and target review point |
| Decision impact | No change / candidate assumption update / candidate proposal / escalation for owner decision |

## Open questions before any real engagement

- Who is authorized to approve receipt validity, putaway policy, retry/cancel actions, metric definitions, and event contracts?
- Which shifts, warehouse areas, and exception types must be sampled to avoid a one-sided model?
- What evidence may be viewed, redacted, retained, or referenced?
- Which safety procedure governs device recovery and return-to-service confirmation?
- What event proves physical completion, and which system is authoritative for inventory?
- Which assumptions have an expiry or validation deadline?
