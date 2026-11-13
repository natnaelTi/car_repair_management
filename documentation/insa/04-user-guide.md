# User Manual

## Document Control

| Attribute | Value |
| --- | --- |
| Document ID | CRM-UG-001 |
| Product / organization | AAP Fleet Management System / Addis Ababa Police Commission |
| Publisher | Selfmade Cloud Solutions |
| Version / issue date | 1.0 / 13 November 2026 |
| Source baseline | `5974cf7addfef5d5cfc8fde325fc964343557a2f` |
| Planned hosting | On-premise on the Commission's server |
| Technical contact | Natnael Tilaye / natnaeltilaye30@gmail.com |
| Status | Review draft; confirm labels, language and permissions during Commission UAT |

## 1. Audience and Safe Use

This guide is for fleet officers, workshop staff, technicians, inspectors, stores and finance staff, authorized approvers and integration administrators. Your account may not have access to all listed actions. Frappe Desk provides advanced document forms alongside the Workshop interface. The administrator must confirm the approved role/access matrix before production use; visible controls alone do not establish authorization.

Use only the Commission-approved server address and your own account. Do not share passwords, integration keys, vehicle traces or exported personnel/financial information through public channels. Do not approve a transaction simply to bypass an error or edit a device mapping merely to make a dashboard populate. Sensor data supports operational decisions; it is not proof of vehicle safety, exact fuel delivery or financial settlement.

## 2. Sign In and Navigation

1. Obtain the approved address and account from the Commission administrator. The workshop address ends with `/workshop`; the actual production hostname will be issued separately.
2. Open it in an approved browser. If prompted, sign in through the normal Frappe login screen. Unauthenticated protected routes redirect to login.
3. Check that the correct organization/site is selected before entering operational data.
4. Use the sidebar to open Dashboard, Repair Orders, Vehicles, Customers, Employees, Tasks, Inspections, Issues, Expenses, Fuel, Parts, Invoices, Reports or Settings.
5. When finished, use the account menu to sign out, especially on a shared workstation. Lock the workstation when leaving it unattended.

Use the normal password-recovery process if configured, or contact the administrator. Do not put a password in a support message. Language/theme options depend on deployment configuration; the shipped locale files do not mean every field or error is fully translated. A permission error must be reviewed by an administrator, not worked around using another person's login.

### 2.1 Common Conventions

| Control / state | Meaning |
| --- | --- |
| List filters and search | Narrow visible records; clear filters if an expected record is absent |
| Clickable record row | Opens details; confirm record identity before an action |
| New / Save | Creates or saves a record; success should be followed by the saved record/name |
| Draft / Submit | A saved draft is not necessarily a submitted operational transaction |
| Open in Desk | Opens the full native Frappe document for permitted advanced work |
| Empty list | May mean no matching data, permissions, a filter or a failed request; not proof of deletion |
| Status badge | Workflow state; inspect details/timestamps instead of relying on color alone |
| Error / loading | Wait for completion; capture the action and non-sensitive error text before retrying |

## 3. Daily Fleet Review

Open Dashboard to review work-order counts/status distribution, recent work and fleet summaries. Follow up overdue or blocked items using the relevant list. Dashboard totals are summaries; finance and safety decisions require the underlying documents and approved procedures.

Open **Vehicles** and search for the registration/record. Verify make/model/identity before editing. Open details to review Overview, Specs, Financials, Sensor Data, Service History, Inspection History, Work Orders, Service Reminders, Issues, Fuel and Attachments, as available in the deployment language.

### 3.1 Create or Update a Vehicle

1. Select **Vehicles > New Vehicle**.
2. Enter the plate/identity and required make/model/specification fields. Select the correct Company and vehicle type/status.
3. Enter acquisition/insurance information only from approved records. Asset creation depends on the accounting configuration.
4. Set fuel tank capacity in liters where available; this is needed to calculate percentage from a volume-only sensor.
5. Save and reopen the record. Confirm no duplicate vehicle was created.
6. Use the approved assignment screen or Desk fields to associate custodian/driver. Remove an old assignment with its historical status rather than deleting evidence.

An employee must be linked correctly for responsibility-based issue workflows. Changing a license plate does not change the hardware device identity. Replacement analysis and aging scores are advisory; they are not an automatic disposal authorization.

## 4. Report and Resolve Issues

1. Open **Issues > New Issue**.
2. Select the correct Vehicle, enter a clear subject, description, severity, category and source.
3. Save. Note the issue reference and state.
4. A driver-reported issue may require the vehicle custodian's review before work-order conversion. The custodian reviews evidence and approves/rejects using the available action.
5. An authorized workshop user selects **Create Work Order**, confirms Company/Customer and completes the work-order details.
6. For duplicates or closure, use the corresponding action and an accurate reason. Do not remove unresolved safety findings to clear a list.

Fault and recall lists are accessible under Issues. Record manufacturer notices and follow-up evidence according to the Commission's process. If an action appears available to an unauthorized account, stop and report it: known legacy authorization concerns must be resolved before production acceptance.

## 5. Repair Orders and Workshop Execution

### 5.1 Intake

1. Open **Repair Orders > New Repair Order**.
2. Select Order For (Company or Customer), the correct party and Vehicle.
3. Enter problem summary/details, priority and any agreed delivery/SLA information.
4. Select a Service Template if appropriate, then review the actual operations, parts and checklist rather than assuming defaults are correct.
5. Save a draft. Review billable/free-of-charge flags and required fields.
6. Submit when approved for scheduling; status becomes **Scheduled**.

Submission is distinct from **Start Work**. Starting scheduled work creates linked Project/Tasks as needed and moves execution forward. If the workshop interface does not expose a permitted advanced action, use Open in Desk or ask the supervisor; do not edit database values.

### 5.2 Operations, Parts and Costs

- Review and assign operation tasks to authorized technicians. Update operation progress to reflect actual work.
- Log time in the configured task/timesheet process. Submitted/cancelled time documents affect recorded labor cost.
- Create a Material Request for planned parts where appropriate. Stores process approved inventory documents; a request is not proof of physical issuance.
- Use Awaiting Parts/On Hold and explanatory notes when work cannot proceed.
- Generate a quotation and follow the approved ERPNext quotation/sales order/invoice process for commercial work.
- Verify linked document identifiers and costs. Do not create a second commercial document merely because the first page is slow to respond.

### 5.3 Quality, Handover and Closure

1. Complete operations and QC-linked tasks, then review the handover checklist and required inspections.
2. Attempt Ready for Handover only after the actual work and checks are complete. An incomplete QC task can block this transition.
3. Record handover/delivery according to the supervisor's procedure and preserve supporting attachments.
4. Finance verifies the relevant invoice/payment evidence before administrative closure.

**Important limitation:** the current close guard checks a linked invoice's status (Paid or Submitted) only when that link exists. A Closed label alone is not proof of full payment. The Commission's approved closure policy and any required hardening must be followed.

## 6. Inspections

Open **Inspections** to review history and results. Authorized users maintain form templates, schedule records and item failures through the relevant pages or Desk.

1. Select the correct vehicle and approved form/type.
2. Record inspector, date and item results accurately. Attach evidence through the approved attachment workflow.
3. Save/submit according to the form's available workflow.
4. Review failures, severity and required follow-up. Create/associate an issue or work order where the operating process requires it.
5. Confirm any required handover checklist result is associated with the correct inspection.

A stored schedule does not guarantee an email or other external reminder has been delivered. Supervisors must verify reminders and monitor overdue inspections using the configured reports.

## 7. Fuel and Expense Management

### 7.1 Refueling and Quotas

1. Open **Fuel** and review existing records/quotas for the vehicle and month.
2. Choose **New Refueling**; enter vehicle, date, liters, odometer, cost per liter, station and notes from the approved evidence.
3. Save once and record the reference. Check whether it is Approved or Pending Dept Head Approval.
4. An authorized department head reviews an over-quota request. The workflow may then require depot manager approval.
5. Confirm approved consumption and remaining quota against the actual record; use the rejection action with a reason when appropriate.

Do not click Approve repeatedly. The evaluated approval endpoint has role-verification and repeated-posting risks documented for remediation. Until those are resolved and accepted, reconcile approvals using the Commission's controlled process and do not treat the software state as the sole authorization evidence.

Measured sensor fuel level is **not** a refueling transaction, approved quota consumption or a fuel purchase invoice. A change in tank level can reflect calibration, vehicle movement, consumption, communication delay or refueling; investigate before concluding loss or fraud.

### 7.2 Expenses, Parts and Invoices

Use **Expenses > New Expense** to select vehicle/date/category, amount, vendor and notes, and attach the authorized receipt where supported. Verify saved totals and payment status. Use Parts for inventory visibility and authorized ERPNext stock processes for actual movements. Invoices shows relevant sales and purchase records; open the underlying ERPNext document for posting/payment actions that require native finance controls.

## 8. Hardware Integration Administration

Only a System Manager or Telemetry Integration Manager should configure provider access. Vehicle connection actions also require read/write access to that Vehicle. Provider keys are not normal user passwords and must not be included in screenshots or tickets.

### 8.1 Test an Unsaved API

1. Open **Settings > Integrations > Mock Hardware APIs**.
2. Enter a recognizable configuration name, approved endpoint URL, GET/POST method and key-header name. Use HTTPS for production.
3. Enter the provider key through the protected field. For POST providers, enter the optional request JSON. Set Response Root only if the device objects are nested under a known dictionary path.
4. Select **Test** before saving.
5. Review **Parsed** for IMEI, GPS, engine, speed, timestamps, volume and percentage. Switch to **RAW** to compare the original response and diagnose missing fields.
6. Review HTTP/parser errors. Testing does not save a configuration or ingest telemetry; repeat after correcting the draft settings.

The provider account may expose more than one vehicle in RAW/Find Devices. Only approved integration administrators may view that response. Even redacted output can contain sensitive fleet information; do not distribute it publicly.

### 8.2 Save, List and Activate

1. Save the tested configuration. It should appear in the saved-configuration table below the form.
2. Confirm its name, enabled state and polling settings. Use Edit for later changes; an empty key on an existing configuration preserves the stored key through the configuration API.
3. Select **Activate** on the intended enabled default API. Only one site-wide default can be active.
4. Confirm the active marker moves to the selected row. Enabled and Active are different: several configurations may be enabled, but only one is the default.

If the table is empty after a reported save, clear filters/reload once and ask support to check permissions, assets, migration and the list API response. Do not create repeated duplicate configurations. Do not delete a configuration linked to operational vehicles without an impact review.

### 8.3 Link a Vehicle and Test GPS/Fuel

1. Open **Vehicles > the intended Vehicle > Overview > Hardware Connection**.
2. Choose Active API to follow the site's selected default, or choose an explicit enabled API for that vehicle.
3. Select **Find Devices** and verify the physical device's IMEI against the installation record. Provider names/plates are only display labels.
4. Select/enter the IMEI, enable hardware tracking and **save the connection**.
5. Select **Test GPS & Fuel**. Confirm the returned IMEI and selected provider, valid GPS, measurement time and expected fuel channels. This test is read-only.
6. Select **Sync Now** to ingest the matching vehicle's data. Review the refreshed Overview and Sensor Data/Fuel context.
7. Compare measurement time with last request time and expected device behavior. A stationary/off vehicle may correctly have an unchanged tracker timestamp.

IMEI is unique per Vehicle. If already assigned elsewhere, investigate installation records rather than renaming the device to evade the check. For a replacement device, obtain approval, disable the old connection, update the correct mapping, retest and preserve the change record.

In Desk, use the Vehicle's **Hardware API Configuration**, **Telematics IMEI** and **Hardware Tracking Enabled** fields. Save before using **Hardware > Test GPS & Fuel** or **Sync Hardware**. A disabled mapping cannot ingest telemetry.

### 8.4 Set Automatic Update Intervals

1. Edit the saved provider configuration and enable **Automatic Polling**.
2. Set whole seconds for **Engine Running**, **Engine Idle** and **Engine Off**, then save.
3. Defaults are 10, 60 and 120 seconds. Accepted range is 1-86400 seconds; use only intervals approved for provider rate limits and system capacity.
4. On the Vehicle hardware panel, inspect polling status, engine condition, last/next request and errors. Automatic polling works without the browser open, provided managed workers/scheduler are running.
5. Keep a visible vehicle page open to see stored dashboard updates; it refreshes approximately every five seconds without making its own provider calls.

Running means engine on with movement. Idle means engine on without movement, or explicit idle status. Off means explicit engine off. Unknown/error uses the shortest configured interval. Changes are discovered on the next contact; an off-state 120-second schedule cannot discover a new engine-on state instantly without an intervening push.

Automatic Polling is separate from **Ingest On Run**, which controls manual configuration Run ingestion. Disabling polling/vehicle hardware prevents further scheduled requests after any in-flight work; do not use it as emergency vehicle control. Request intervals are targets, not guaranteed delivery or GPS freshness.

### 8.5 Interpret Fuel Correctly

| Reading | Interpretation |
| --- | --- |
| fuel_1_ltr_value / fuel_2_ltr_value | Explicit liters; combined volume preferred when present |
| fuel_can_level_value | Legacy milliliters when explicit liter values are absent |
| fuel_can_level_percent | Direct percentage when supplied |
| Missing percentage with valid volume | Configure verified tank capacity in liters to derive percentage |
| fuel_1 / fuel_2 | Raw channels without assumed units |
| Blank/null channel | Not a measured zero |

Calibrate against the actual sensor/provider specification. Implausible values require integration review, not manual alteration of historical evidence. Tank percentages are not guaranteed to reflect usable fuel under every vehicle condition.

## 9. Reports, Records and Exports

Open **Reports** to find overview metrics and the report library. Select the report, set dates/vehicle/other filters and run. Verify the filter period and underlying data before exporting or making decisions. Save a frequently used report configuration through Saved Reports. Authorized users can create Scheduled Reports; verify recipients, frequency, mail configuration and delivery evidence.

Do not email GPS/personnel/finance reports to unauthorized recipients. Attachment visibility must match the intended access classification. Audit/version information is useful where enabled, but not every API action creates an immutable audit event. Report suspicious changes through the security process.

## 10. Troubleshooting and Support

| Symptom | Operator action | Administrator follow-up |
| --- | --- | --- |
| Login fails | Check approved address/account; use recovery/support | Account status, identity policy, session and ingress |
| Missing record / permission error | Check filters and correct site; do not switch accounts to bypass | User/record permissions and API behavior |
| Blank workshop / asset 404 | Reload once; note time/browser | Same image on frontend/backend, mounts and hashed assets |
| DocType missing / 400 / 500 | Record page/action/error reference; avoid repeated mutations | Per-site migrate, schema audit and service/error logs |
| Provider test times out / non-JSON | Verify draft method/root; do not expose key | Provider DNS/TLS/availability, egress and response format |
| IMEI not found | Verify physical IMEI and provider account scope | Mapping, selected API and enabled state |
| Successful request, old GPS | Check tracker vs server/request timestamp | Device power/uplink/provider freshness; not necessarily app failure |
| Fuel percentage missing | Check whether volume/capacity exists | Unit contract, capacity and calibration |
| Automatic updates stopped | Note last/next request, condition and error | Long worker, Redis lease, scheduler, queue lag and provider |
| Incorrect/repeated financial state | Stop repeated approval and notify finance | Integrity investigation, reconciliation and required fixes |

Support request: product/site identifier, page/record reference through an approved secure channel, local time/timezone, action taken, expected/actual result and redacted error. Never send passwords, API keys, full provider RAW responses or sensitive attachments to an unapproved channel. Technical contact is Natnael Tilaye (natnaeltilaye30@gmail.com); production incident routing and support hours must be confirmed by the Commission.

## 11. Training Acceptance

Each role should demonstrate its permitted daily tasks on fictional test data and demonstrate that prohibited actions fail. Integration training must cover unsaved Test, saved list/Activate, IMEI mapping, read-only test vs Sync, fuel units and timestamp freshness. Record trainee/reviewer, result, date and outstanding issues in the controlled UAT record. User-guide approval/signature/date: TO BE CONFIRMED.
