# Smart Warehouse Inbound and Exception Management

> Personal WMS/WCS portfolio case study using synthetic data. WCS behavior and device events are simulated.

This completed local case study addresses fragmented inbound checks and poor exception visibility. It demonstrates traceable pallet receipt and putaway with safe recovery, without changing inventory before completion is verified.

## Recruiter summary

- **Users:** inbound operator, warehouse supervisor, warehouse manager, integration engineer, and maintenance technician.
- **In scope:** barcode/SKU/quantity/duplicate validation, deterministic location selection, movement tracking, simulated device events, exception recovery, inventory audit, and synthetic metrics.
- **Out of scope:** outbound, cycle count, multi-warehouse, advanced FEFO, production optimization, enterprise authentication, and real ERP/PLC/robot/device integration.
- **Implemented evidence:** executable domain rules, static recruiter demo, data and API contracts, RTM, 14 / 14 passing UAT cases, and four screenshots.
- **Limitation:** this is a designed and simulated operating model, not evidence from a warehouse engagement, physical equipment test, or production system.

## Architecture direction

The local browser demo sends synthetic pallet data to an in-memory WMS domain model. The WMS validates receipt, chooses a compatible location by an explicit rule, creates a movement task, and dispatches to a WCS simulator. Simulated device events drive task status. Only a valid completion event may commit inventory. The exception queue and audit trail expose failures, retries, escalation, cancellation, and duplicate events.

The artefact also includes BPMN/flow/sequence/state/data diagrams, a SQLite-compatible data contract, OpenAPI specification, and a dependency-free JavaScript simulator. No physical device or production environment is connected.

## Run the demo

From `prototype/` run `python -m http.server 8765 --bind 127.0.0.1`, then open the local address `127.0.0.1:8765` in a browser.

The guided buttons reset the in-memory state and run three recruiter-ready stories:

- **Happy path:** valid inbound, deterministic location assignment, task completion, and exactly-one inventory movement.
- **Offline escalation:** initial device failure plus two failed retries; the third failure escalates with no third retry command.
- **Duplicate event:** the same completion event is replayed with no second state or inventory mutation.

## Delivery legend

| Label | Meaning in this portfolio |
|---|---|
| **Implemented** | Present and locally verifiable through source, executable tests, or retained visual evidence. |
| **Simulated** | Synthetic WCS/device behavior or demo data; never real equipment evidence. |
| **Designed only** | Proposed real-world extensions such as production persistence, authentication, observability, and physical device integration. |

## Current artifact map

| Artifact | Purpose | Current status |
|---|---|---|
| [Case study brief](docs/01-case-study-brief.md) | Problem, goal, scope, business needs, and stable ID contract | Implemented |
| [Stakeholders and interview guide](docs/02-stakeholders-and-interview-guide.md) | Proposed stakeholder model and unexecuted interview plan | Implemented; engagement is Designed only |
| [Assumptions and decisions](docs/03-assumptions-and-decisions.md) | Assumption, decision, proposal, and revisit controls | Implemented |
| [SRS and FSD lite](docs/04-srs-fsd-lite.md) | 4 needs, 10 functional requirements, 10 business rules, 5 NFRs, errors, and interfaces | Implemented |
| [Product goal and backlog](docs/05-product-goal-and-backlog.md) | Product goal and dependency-aware ordering for 12 stories | Implemented |
| [Stories and acceptance criteria](docs/06-user-stories-and-acceptance-criteria.md) | Testable positive and negative behavior | Implemented |
| [Traceability matrix](docs/07-requirements-traceability-matrix.md) | BN-to-UAT coverage with retained evidence | Implemented; 0 orphaned requirements |
| [UAT pack](docs/08-uat-pack-and-results.md) | 14 executed acceptance cases and residual limitations | Implemented; 14 / 14 PASS |
| [Defect and change log](docs/09-defect-and-change-log.md) | Defect, change, and assumption-gap classification | Implemented; 0 open functional defects |
| [User guide and demo script](docs/10-user-guide-and-demo-script.md) | Local setup and five-minute recruiter walkthrough | Implemented |
| [OpenAPI contract](api/openapi.yaml) | Simulated receipt, task, event, retry, exception, inventory, audit, and metric interfaces | Implemented and schema-tested |
| [Data contract](data/schema.sql) | SQLite-compatible relational model, seed data, metrics, and lineage | Implemented and query-tested |
| [Local prototype](prototype/index.html) | Accessible responsive UI backed by the deterministic simulator | Implemented and visually checked |
| [UAT automation](tests/uat.test.mjs) | Executable evidence for UAT-01 through UAT-14 | Implemented; 14 / 14 PASS |
| [Structure tests](tests/test_structure.py) | Foundation, disclosure, ID, link, neutral-question, and privacy checks | Implemented |

## Evidence and privacy boundary

All examples are synthetic. The project contains no client names, private links, real identifiers, credentials, production screenshots, or copied internal rules. Stakeholder authority is proposed for the simulation. No interview, site observation, warehouse baseline, measured benefit, hardware test, customer sign-off, or production validation is claimed.

Public URL: https://github.com/QaHuy/smart-warehouse-inbound-exceptions
