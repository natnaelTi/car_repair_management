# Software Requirements Documentation

## Document Control

| Attribute | Value |
| --- | --- |
| Document ID | CRM-PRD-001 |
| Product | AAP Fleet Management System (`car_repair_management`) |
| Version / issue date | 1.0 / 13 November 2026 |
| Prepared for | Addis Ababa Police Commission; INSA software production assessment application |
| Publisher | Selfmade Cloud Solutions |
| Source baseline | `5974cf7addfef5d5cfc8fde325fc964343557a2f` |
| Status | Technical review draft; approval and deployment evidence pending |
| Approvers | Commission product owner and authorized signatory: TO BE CONFIRMED |

## 1. Purpose

Define the business, functional, interface, data and operational requirements for the Commission's fleet and workshop management system. Requirements are traceable to implementation areas and acceptance checks. This document describes the evaluated application and identifies requirements that still need production validation; it does not claim all security or nonfunctional requirements have been met.

The planned deployment is on-premise on the Commission's server, with more than 700 vehicles and more than 500 users. Registered user count is not simultaneous user count. Technical contact: Natnael Tilaye (natnaeltilaye30@gmail.com). These project facts were supplied by the Commission representative; hardware sizing and peak load remain to be validated.

**Status vocabulary:** Implemented = identifiable source implementation, not full acceptance; Partial = implementation exists with a specified limitation; Required = production requirement whose evidence or implementation is outstanding; Out of scope = not represented as a delivered feature.

## 2. Business Context

The Commission needs a single record of vehicles, responsibility assignments, reported defects, maintenance work, fuel allocation, operating costs and hardware observations. Workshop staff need work-order progress and parts visibility. Fleet supervisors need vehicle condition, service reminders, inspection history and exception reporting. Finance personnel need traceability from a repair to its commercial and expense records.

The hardware integration uses a device's IMEI as its stable vehicle association. Provider APIs can be previewed before saving, selected as the site's active configuration, and used for mapped-vehicle synchronization. The system also accepts authenticated device pushes. A successful request is distinct from a new tracker measurement.

### 2.1 Objectives and Measures

| Objective | Proposed measure | Acceptance owner |
| --- | --- | --- |
| Trace repair decisions and execution | Sample an issue through work order, task, parts and handover records | Workshop supervisor |
| Improve fleet visibility | Review vehicle overview, inspection history, open issues and latest sensor timestamps | Fleet manager |
| Control fuel processes | Reconcile approved refueling with quota and financial evidence | Fuel/finance owner |
| Validate hardware ingestion | Match a fictional/test IMEI to exactly one vehicle; confirm GPS and fuel conversion | Integration owner |
| Repeat deployment reliably | Clean Docker installation and upgrade pass schema audit and workflow tests | Infrastructure owner |
| Protect Commission information | Negative authorization, network, secrets and restore evidence accepted | Security owner |

Numeric targets and fleet scale must be approved before formal acceptance. No service-level or performance commitment is inferred from these objectives.

## 3. Scope

### 3.1 Included

- Vue workshop frontend at `/workshop` and Frappe Desk for full document administration.
- Fleet master records, driver/custodian associations, meter readings and vehicle histories.
- Repair orders, operations, service templates, checklists, quality controls and linked ERPNext documents.
- Issues, faults, recalls, inspection templates, inspection records and schedules.
- Fuel quotas, refueling records, approval-state handling, expenses, parts and invoice visibility.
- Reports, saved report configurations, scheduled report execution, application settings and installation health audit.
- Hardware configuration, raw/parsed preview, active API selection, IMEI mapping, manual tests/sync, automatic polling and telemetry history.
- Docker image and service override design supplied in the repository.

### 3.2 Exclusions and Boundaries

- Hardware manufacture, firmware, SIM/network service, sensor calibration and vehicle ECU interpretation are provider responsibilities.
- Device-side primary/fallback POST destination selection is not controlled by this application. A single ingest API may be exposed through operator-managed redundant ingress, but that is not application-level automatic failover.
- Automatic health-ranked provider switching, offline browser operation, automated driving/remote engine control and guaranteed real-time tracking are not delivered claims.
- Customer self-service portal, bespoke government identity/payment integrations, unrelated bench apps and a complete ERP implementation are not assumed included.
- Certification decisions, legal interpretation, formal security testing and final hosting approval are outside the documentation preparation scope.

## 4. Stakeholders and Actors

| Actor | Operational responsibility | Access expectation |
| --- | --- | --- |
| Commission sponsor/product owner | Approves scope, priorities and acceptance | Governance; not necessarily a system administrator |
| Fleet manager | Fleet records, assignments, maintenance oversight | Approved vehicle and history access |
| Service advisor/workshop supervisor | Intake, planning, work progression, handover | Repair and customer/vehicle context |
| Technician/inspector | Assigned work, inspections, findings | Minimum records needed for assigned work |
| Stores officer | Parts and material movements | Inventory permissions |
| Fuel approvers | Department/depot approval decisions | Independently enforced approval authority required |
| Finance officer | Expenses, invoices and reconciliation | ERPNext finance permissions |
| Telemetry Integration User | Device/API ingestion service account | Telemetry create/read/list only at custom API role layer |
| Telemetry Integration Manager | Provider configuration and device mapping | Integration administration plus relevant Vehicle permissions |
| System Manager | User, schema and system administration | Privileged and audited access |
| Infrastructure/security operators | Hosting, backup, deployment, assurance | Controlled shell and infrastructure access |

These are business personas. Not all persona labels are provisioned Frappe roles. Actual per-DocType roles are enumerated in the TDD. Legacy custom API permission gaps are recorded in the Security document; this table is not evidence of complete least-privilege enforcement.

## 5. Functional Requirements

### 5.1 Fleet and Responsibility

| ID | Requirement and acceptance condition | Status / implementation |
| --- | --- | --- |
| FR-FLT-01 | Store vehicle identity, license plate, make/model, specifications, ownership and status; retrieve the same saved record | Implemented: Vehicle extensions and vehicle frontend |
| FR-FLT-02 | Track driver/custodian associations and retain removed-assignment history; reject conflicting active driver assignment according to validation | Implemented: Vehicle hooks and assignment APIs |
| FR-FLT-03 | Present service, repairs, inspections, issues, fuel, attachments and financial context on a vehicle page | Implemented: vehicle dashboard and tabs |
| FR-FLT-04 | Support meter and cost histories and fleet aging/replacement analysis; distinguish advisory analytics from approved decisions | Implemented: analysis APIs and pages |
| FR-FLT-05 | Maintain linked asset/acquisition and insurance context when required ERPNext master data is configured | Partial: setup-dependent Asset integration; validate account configuration |

### 5.2 Workshop and Quality

| ID | Requirement and acceptance condition | Status / implementation |
| --- | --- | --- |
| FR-WO-01 | Create a draft RO for a Company or Customer and a Vehicle, with problem, priority, operations and parts | Implemented: Repair Order controller and forms |
| FR-WO-02 | Validate party selection, billable/FoC exclusions and SLA inputs; submit into Scheduled status | Implemented: RO validation and submit hooks |
| FR-WO-03 | Start scheduled work, create linked Project/Tasks as needed and assign operations | Implemented: `start_work` and operation actions; submit alone does not create tasks |
| FR-WO-04 | Track work and costs from task, timesheet, purchase/sales document events | Implemented: document hooks and cost recomputation |
| FR-WO-05 | Generate quotation/material request and continue supported ERPNext commercial flows | Implemented: RO commercial actions, ERPNext workflow permissions still apply |
| FR-WO-06 | Prevent Ready for Handover when a QC-linked task is incomplete; display checklist/inspection results | Implemented: submitted-order QC guard and checklist APIs |
| FR-WO-07 | Close only according to approved financial policy | Partial: current guard accepts linked invoice status Paid or Submitted and only checks when an invoice is linked; stricter settlement policy requires review |
| FR-QLT-01 | Record issues, faults and recalls; support approval, rejection, duplicate marking and work-order conversion | Implemented: issue APIs; authorization gaps require remediation |
| FR-QLT-02 | Maintain inspection forms, schedules, inspections and item failures; retrieve results against the vehicle | Implemented: inspection DocTypes and pages; operational scheduling acceptance required |

### 5.3 Fuel, Finance and Reporting

| ID | Requirement and acceptance condition | Status / implementation |
| --- | --- | --- |
| FR-FIN-01 | Maintain monthly fuel quota and refueling records; identify over-quota requests and approval states | Implemented: fuel APIs/DocTypes |
| FR-FIN-02 | Restrict approval decisions to authorized approvers and prevent repeated consumption posting | Required: negative authorization and repeated-approval tests; current `approve_refueling` trusts a role parameter |
| FR-FIN-03 | Record vehicle expenses and view parts/stock and sales/purchase invoices | Implemented: expense, parts and invoice modules |
| FR-RPT-01 | Run report library filters and view/save report configurations | Implemented: report APIs and pages; review record visibility |
| FR-RPT-02 | Execute due report schedules and maintain job-costing snapshots | Implemented: hourly/daily scheduler hooks; delivery requires working mail/service configuration |
| FR-RPT-03 | Restrict sensitive exports and scheduled report recipients | Required: approved information-sharing policy and recipient/access tests |

### 5.4 Hardware and Telemetry

| ID | Requirement and acceptance condition | Status / implementation |
| --- | --- | --- |
| FR-HW-01 | Enter provider URL, GET/POST method, key header/key, optional JSON body and response root; test without saving or ingesting | Implemented: configuration `test` action |
| FR-HW-02 | Display raw and parsed responses and errors, excluding the submitted provider key from preview output | Implemented: fetch/parser and frontend preview; redaction has documented limits |
| FR-HW-03 | List saved configurations, update them and select one enabled active default per site | Implemented: configuration API and controller serialization |
| FR-HW-04 | Associate one IMEI with one Vehicle; prevent duplicate mapping; allow explicit API or follow Active API | Implemented: unique field, Vehicle validation and connection UI |
| FR-HW-05 | Allow authorized read-only GPS/fuel tests and manual sync for the saved enabled mapping | Implemented: `vehicle_hardware` actions |
| FR-HW-06 | Receive provider-shaped authenticated telemetry; reject unmapped or disabled vehicles and invalid payloads | Implemented: central telemetry API; record/device scope concerns remain |
| FR-HW-07 | Interpret GPS, speed, odometer, engine and fuel with explicit units; do not invent percentages without capacity | Implemented: shared parser and ingestion |
| FR-HW-08 | Configure Running/Idle/Off intervals in whole seconds, 1-86400; defaults 10/60/120 | Implemented: validation and configuration UI |
| FR-HW-09 | Poll eligible mapped vehicles, share due-provider requests, avoid unchanged poll snapshots, record errors and retry | Implemented: long-queue polling module; timing is best effort |
| FR-HW-10 | Show last/next request, engine condition, provider error and stored measurement timestamp; refresh visible dashboard data | Implemented: Vehicle hardware panel and five-second stored-data refresh |
| FR-HW-11 | Preserve newer live vehicle location/odometer against older telemetry; separate transport success from sensor freshness | Implemented guard; future timestamps and clock skew need policy/testing |
| FR-HW-12 | Recover ingress/provider outages using the approved redundancy design | Partial: device/operator retry and configurable provider selection; automatic multi-provider failover not implemented |

## 6. Data and Interface Requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| DR-01 | Use IMEI text for association, not the provider's display name or registration-like label | Duplicate/unmapped-device tests and saved mapping |
| DR-02 | Keep measurement timestamps and batch/source traceability with telemetry records | Read back a synthetic create batch and its child records |
| DR-03 | Preserve consistent units: km, km/h, meters, degrees, liters/milliliters and percentage | Parser tests and independently calibrated provider comparison |
| DR-04 | Define retention for location history, employee associations, financial documents, files, logs and backups | Commission-approved retention matrix; no universal automatic purge is asserted |
| IR-01 | Serve workshop and Desk through controlled HTTPS; use authenticated Frappe APIs | Final ingress configuration and login/API negative tests |
| IR-02 | Integrate ERPNext vehicle, employee, customer/company, project/task, inventory and finance records | Cross-document workflow tests on the clean deployment |
| IR-03 | Permit only approved external provider/map/mail destinations | Egress policy, provider agreement and map-data disclosure review |

The provider's `dt_tracker` is preferred over `dt_server`. Incoming provider timestamps do not establish a timezone contract themselves; the integration owner must agree the timezone and stale/future tolerance. TDD section 4 defines the sample contract.

## 7. Nonfunctional Requirements

These are production acceptance requirements, not measured service claims.

| ID | Requirement | Target / validation |
| --- | --- | --- |
| NFR-SEC-01 | Enforce server-side authentication, role and record-scope checks for every protected API | No unauthorized read/write in signed access matrix; Security register closure |
| NFR-SEC-02 | Protect secrets and data in transit/at rest and prevent internal-network provider requests | HTTPS and egress controls, key management, scans and penetration tests |
| NFR-REL-01 | Continue controlled operation after provider outage; record failure without losing other vehicles' data | Timeout/error/recovery and multi-vehicle tests |
| NFR-REL-02 | Meet approved availability, RPO and RTO | TO BE CONFIRMED; restore rehearsal and outage exercise |
| NFR-PERF-01 | Meet UI/API response and telemetry lag targets at agreed fleet/concurrency scale | TO BE CONFIRMED; representative load test, p95 latency, queue lag and database growth |
| NFR-OPS-01 | Reproduce install/upgrade with one approved Docker release and migration per site | Image digest, final Compose, clean install/upgrade and audit reports |
| NFR-OBS-01 | Alert on failed requests, stale sensors, queue backlog, storage and authentication anomalies | Monitoring demonstration; current app status fields alone are not alerting |
| NFR-USR-01 | Support approved browsers, mobile layouts, language and keyboard workflows | Commission UAT; locale files do not establish translation completeness/accessibility compliance |
| NFR-MNT-01 | Version source, dependencies, documents and changes with rollback procedures | Release manifest, SBOM, review and restore evidence |

Polling interval is not end-to-end freshness. Overall age includes sensor sampling, device upload, provider processing, poll interval, network/worker latency and browser refresh. An engine transition is discovered only on the next contact when no push is received.

## 8. Acceptance and Traceability

| Acceptance ID | Requirements | Procedure and expected result |
| --- | --- | --- |
| AT-01 | FR-FLT-01..05 | Create fictional vehicle, assign responsibility, update meter, inspect all tabs and verify linked asset conditions |
| AT-02 | FR-WO-01..07 | Draft, submit, start, complete operations, exercise QC failure/pass, create documents and test financial closure policy |
| AT-03 | FR-QLT-01..02 | Driver issue, custodian review, work-order conversion, inspection failure and follow-up; test unauthorized actor |
| AT-04 | FR-FIN-01..03 | Within/over-quota refueling, role denial, repeated approval and expense/invoice reconciliation |
| AT-05 | FR-RPT-01..03 | Run filtered report, save/schedule and verify delivery plus forbidden-recipient behavior |
| AT-06 | FR-HW-01..05 | Unsaved preview creates no configuration/telemetry; save lists row; switch active; map IMEI; test then sync |
| AT-07 | FR-HW-06..11, DR-01..03 | Synthetic push; wrong IMEI, disabled vehicle, invalid GPS, missing time, optional fuel, duplicate and out-of-order cases |
| AT-08 | FR-HW-08..12, NFR-REL-01 | Running/idle/off transitions, outage/recovery, worker restart, shared request, queue contention and selected-provider change |
| AT-09 | NFR-OPS-01, NFR-MNT-01 | Fresh Docker install and upgraded second site, asset HTTP checks, schema audit, database/files/key restore |
| AT-10 | NFR-SEC-01..02, IR-01..03 | Role/record negative tests, private-host request checks, TLS/secrets/image review, independent security assessment |
| AT-11 | NFR-PERF-01, NFR-OBS-01, NFR-USR-01 | Approved load/browser/language/accessibility checks and alert demonstrations |

Focused parser/polling tests do not replace these end-to-end acceptance exercises. Execution evidence and current test limitations are in `verification.md`; technical source traceability is in the TDD inventory.

## 9. Dependencies, Risks and Sign-Off

Dependencies include ERPNext v15, compatible Frappe/runtime services, correctly configured Company/accounts/warehouses, provider availability and calibration, DNS/time synchronization, managed workers/scheduler, and an approved operating network. Demo data seeded by a new install must not become Commission operational data.

Priority risks are legacy API authorization, financial approval integrity, unverified Docker build/restore, secret/network exposure, unknown operating scale, and clock/retention policy. The Security document owns the detailed register; the SDD owns infrastructure assumptions. A feature is not accepted merely because a UI control is present.

Product reviewer: TO BE CONFIRMED. QA acceptance record: TO BE CONFIRMED. Commission approval/signature/date: TO BE CONFIRMED. Any exception must identify its owner, compensating controls and expiry; it must not be silently removed from the signed dossier.
