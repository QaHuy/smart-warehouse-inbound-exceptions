# CV project entry — copy and adapt

Plain text, no tables or icons, so applicant tracking systems (ATS) can parse it. Keep the word "synthetic" or "self-directed": it is honest and interviewers will ask.

## Full version (Projects section)

**Smart Warehouse Inbound & Exception Management** — Business Analyst (self-directed case study, synthetic data)
Live demo and case study: qahuy.github.io/smart-warehouse-inbound-exceptions

- Framed an inbound putaway problem into 4 business needs and a fixed scope; mapped 5 stakeholder personas with a RACI and a structured interview guide.
- Modelled As-Is and To-Be processes in BPMN 2.0 and ran a gap analysis linking each process gap to a requirement.
- Wrote an SRS/FSD with 10 functional requirements, 10 business rules, 5 NFRs, and a 13-code error catalogue.
- Built a 12-story backlog ordered by dependency and risk, with 26 Given/When/Then acceptance criteria covering positive and negative paths.
- Specified a 9-table data model, data dictionary, SQL integrity checks, and an OpenAPI 3.1 contract.
- Validated the design with a clickable prototype and 14 automated UAT cases (14/14 passed), traced end to end in an RTM with 0 orphaned requirements.

## Short version (2 lines)

**Smart Warehouse Inbound & Exception Management** (self-directed BA case study, synthetic data) — BPMN As-Is/To-Be, SRS with 10 FRs and 10 business rules, 12 user stories with Given/When/Then criteria, RTM, and 14/14 passing UAT on a clickable prototype. qahuy.github.io/smart-warehouse-inbound-exceptions

## Keywords this project supports

Requirements elicitation, stakeholder analysis, RACI, BPMN 2.0, process mapping, gap analysis, SRS, FSD, business rules, user stories, INVEST, acceptance criteria, Given/When/Then, product backlog, requirements traceability matrix (RTM), UAT, test cases, OpenAPI, REST API, SQL, data dictionary, ERD, change control, Agile.

## Interview talking points

- **Most important control:** inventory changes only once, and only after a verified completion event; duplicate events cannot move stock twice.
- **Why no numeric prioritisation:** no effort or value data existed, so a WSJF or RICE score would be false precision; the order follows dependency and risk instead.
- **What you would do first on a real project:** observe inbound work, interview the five personas, collect real exception examples, then revise requirements and UAT with named decision owners.
