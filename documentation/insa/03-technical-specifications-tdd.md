# Technical Specifications and Low-Level Design

## Document Control

| Attribute | Value |
| --- | --- |
| Document ID | CRM-TDD-001 |
| Product / customer | AAP Fleet Management System / Addis Ababa Police Commission |
| Implementation | `car_repair_management`, published by Selfmade Cloud Solutions |
| Version / issue date | 1.0 / 13 November 2026 |
| Evaluated source | `5974cf7addfef5d5cfc8fde325fc964343557a2f` |
| Deployment | Planned on-premise; more than 700 vehicles and 500 users |
| Technical contact | Natnael Tilaye / natnaeltilaye30@gmail.com |
| Status / approval | Technical review draft / Commission engineering reviewer pending |

## 1. Build and Runtime Specification

| Component | Source-declared specification | Interpretation |
| --- | --- | --- |
| Application | Package version `0.0.1`; MIT | Use source SHA plus image digest to identify a release |
| Python | `requires-python >=3.10` | Runtime depends on compatible Frappe/ERPNext base |
| Framework | Frappe v15 and ERPNext v15; `required_apps = ["erpnext"]` | ERPNext must be installed on the target site |
| Image base | `frappe/erpnext:v15.79.0` default | Tag from Dockerfile, not a verified immutable digest |
| Node | Docker PATH references `v18.18.2` | Build compatibility must be tested, not assumed across base tags |
| Frontend | Vue `^3.5.13`, Router `^4.2.2`, Pinia `^2.1.7`, Vite `^4.4.9`, TypeScript `^5.8.3` | Ranges from package.json, not installed/locked version attestations |
| Frontend libraries | Frappe UI, Tailwind, Lucide, Leaflet, date-fns, Vue I18n, Zod, Socket.IO client | Final lockfile and image SBOM establish resolved dependencies |
| Data/services | MariaDB, Redis cache/queue, nginx/web, Socket.IO and managed workers/scheduler | Actual versions inherited from deployment stack; confirm in final manifest |

Build entry: root `package.json` invokes the frontend build; frontend Vite writes to `car_repair_management/public/frontend/` with public base `/assets/car_repair_management/frontend/`. Docker installs the app, registers it in bench apps, builds frontend and runs bench asset linking. Do not add real site credentials to image layers or the build context.

## 2. Code and Installation Contracts

| Source | Responsibility |
| --- | --- |
| `hooks.py` | ERPNext dependency, document events, scheduler, fixtures and workshop routes |
| `install.py` | Canonical idempotent `setup_site`, roles, telemetry DocTypes, custom fields and workspace/master setup |
| `patches.txt` and setup patch | Apply installation convergence to older sites |
| `api/health.py` | CLI site audit of expected DocTypes, roles, fields and API imports |
| `api/*` | Workshop/fleet/report/settings/hardware method APIs |
| RO controller and `auto_status.py` | Work lifecycle, operation/task links, commercial actions and guards |
| `overrides/vehicle.py` | Vehicle mapping/assignment validation and linked asset/fuel behavior |
| `polling.py` | Conditional provider polling, leasing and per-vehicle status |
| `tasks.py` | Scheduled reports and job-costing refresh |
| `www/workshop.py` | Bootstrap/CSRF and hashed asset resolution |
| `frontend/src/router.ts`, `api/client.ts` | Workshop routes and session-aware method/resource requests |

Both `after_install` and `after_migrate` call canonical setup. New installation also attempts demo data seeding. Setup catches/logs some failures, so successful command exit alone is insufficient: run the site audit and workflow checks. Audit success establishes only its listed schema/import checks, not security or every business invariant.

## 3. API Transport and Authorization

### 3.1 Request Conventions

- Application methods use `/api/method/<dotted.python.function>`. A method result is normally inside Frappe's JSON `message` envelope.
- Generic document operations use `/api/resource/<DocType>` and named resources, with framework-defined `data` responses and permissions.
- Browser client calls include session credentials, JSON headers and `X-Frappe-CSRF-Token` when available. The host is used as the site header; ingress must validate host/site routing.
- Machine integrations use a dedicated Frappe service user's token header: `Authorization: token <api_key>:<api_secret>`, over HTTPS. Do not confuse this with the external provider's configurable header (commonly `key`).
- Use POST for all mutations even where the current whitelist permits GET. The central telemetry whitelist allows GET and POST without an action-specific GET mutation guard; enforce/repair this before production exposure.
- Do not promise fixed application HTTP error codes: Frappe version/exception types determine status and error envelopes. Handle non-2xx responses and returned `ok: false` separately; do not expose stack traces to operators.

### 3.2 Integration Permission Contract

| Operation | Explicit custom API gate | Scope limitation |
| --- | --- | --- |
| Telemetry create/read/list | Telemetry Integration User, Telemetry Integration Manager or System Manager | Create resolves enabled mapped IMEI; roles are not per-device authorization |
| Telemetry update/delete | Telemetry Integration Manager or System Manager | Batch operations bypass ordinary DocType permission checks |
| Provider configuration actions | Telemetry Integration Manager or System Manager | Configuration changes/test/run require POST except read/list |
| Vehicle hardware read | Vehicle read permission | Configuration names/statuses may be returned; not provider credentials |
| Vehicle save/discover/test/sync | Integration admin role plus Vehicle read/write | Discovery/RAW preview can include the provider account's other objects |

Provision service accounts per approved integration scope. The app does not currently bind each credential to one IMEI, and ordinary business API methods do not all provide equivalent explicit gates. See security register SEC-01 through SEC-05 before relying on role labels as enforcement.

### 3.3 Endpoint Contracts

| Endpoint suffix after `/api/method/` | Inputs / actions | Important output |
| --- | --- | --- |
| `car_repair_management.api.telemetry.telemetry` | action create/read/list/update/delete; payload, batch_id, optional vehicle/imei/date filters and pagination | Create: ok/action/batch_id/vehicle/created; other actions return batch/list details |
| `car_repair_management.api.telemetry.hardware_test_configuration` | action list/read/create/update/delete/activate/test/run; name; data object | List: records/total; read/save omits api_key; test: raw/parsed/errors/http_status |
| `car_repair_management.api.hardware.vehicle_hardware` | vehicle, action read/save/discover/test/sync; save uses imei/configuration/enabled | Saved connection or preview/sync result with ingested_count |
| `car_repair_management.api.vehicle.get_vehicle_dashboard` | vehicle_name | Vehicle, responsibility, cost/history summaries and telemetry/polling data |

The source inventory below lists all declared application API functions, signatures and whitelist restrictions. It is more comprehensive than this high-value contract table and is not a guarantee of authorization or business correctness.

## 4. Hardware Data Contract

### 4.1 Synthetic Push Example

The example is fictional; replace the IMEI only with an approved test mapping. Coordinates `(0, 0)` here are example numbers, not Commission operational locations. Provider device names never establish the Vehicle link.

```json
{
  "action": "create",
  "payload": {
    "imei": "999000000000001",
    "name": "TEST-VEHICLE-001",
    "group": null,
    "odometer": "10000",
    "engine": "on",
    "status": "Moving",
    "dt_server": "2026-11-13 09:00:05",
    "dt_tracker": "2026-11-13 09:00:00",
    "lat": "0.000000",
    "lng": "0.000000",
    "altitude": "1000",
    "angle": "90",
    "speed": "25",
    "fuel_1": "0.00",
    "fuel_2": null,
    "fuel_1_ltr_value": "20",
    "fuel_can_level_percent": null,
    "fuel_can_level_value": 20000,
    "custom_fields": null
  }
}
```

```bash
# Credentials must be supplied securely; never commit or echo real secrets.
curl --fail-with-body --request POST \
  'https://fleet.example.invalid/api/method/car_repair_management.api.telemetry.telemetry' \
  --header 'Authorization: token <API_KEY>:<API_SECRET>' \
  --header 'Content-Type: application/json' \
  --data-binary @approved-synthetic-telemetry.json
```

`example.invalid` is intentionally non-operational. The JSON file must contain the full example request object. Do not send live sensor traces to a public test service.

### 4.2 Field Interpretation

| Field | Type / validation | Storage or meaning |
| --- | --- | --- |
| imei | Required; trimmed text; mapping UI accepts numeric up to 32 digits | Matches unique `Vehicle.custom_telematics_imei` |
| name | Optional text | Source device display name, not vehicle identity |
| dt_tracker / dt_server | At least one required and parseable | Tracker time preferred; server time retained separately in previews/source metadata |
| lat / lng | Optional finite numbers, lat -90..90, lng -180..180 | Paired values create Vehicle Location |
| speed | Optional finite nonnegative number | km/h sensor and location value |
| odometer | Optional finite nonnegative number | km sensor and live Vehicle odometer subject to time guard |
| altitude / angle | Optional finite number; angle 0..360 | Meters / degrees |
| engine / status | Provider values | Engine condition classifier / tracker status sensor |
| fuel_1 / fuel_2 | Optional finite numeric raw channels | Raw values; no invented unit conversion |
| fuel_1_ltr_value / fuel_2_ltr_value | Optional finite nonnegative numbers | Explicit liters; sum takes precedence over legacy CAN volume |
| fuel_can_level_value | Optional finite nonnegative number | Milliliters under the supplied provider specification |
| fuel_can_level_percent | Optional finite number 0..100 | Direct percentage; otherwise derive from volume and configured capacity |
| group / custom_fields | Optional provider metadata | Sensor/source metadata handling; custom fields are not an arbitrary executable schema |

Numeric strings are accepted by parsing. Null/missing optional readings are not the same as measured zero. Capacity is taken from the configured Vehicle liter capacity or supported fuel-tank-capacity field. Derived percentage is clamped to 0..100. If capacity is absent, volume remains available but no percentage fuel row can be derived. Agree units per provider/device before use; raw screenshots alone are not a calibration certificate.

No timezone offset is required by the current payload parser. The deployment/integration owner must agree provider timestamp timezone, normalize clocks and establish future/stale limits. Source timestamps are not cryptographically signed by this adapter.

### 4.3 Ingestion Algorithm and Storage

1. Parse a JSON object; require IMEI and a source timestamp; run shared numeric/time validation.
2. Resolve the unique IMEI and reject missing/disabled hardware mapping. Do not create a vehicle automatically.
3. Allocate or use the batch ID; default generated IDs use the `TLM-` prefix.
4. If both coordinates exist, create Vehicle Location with timestamp, direction, speed, altitude and source/batch metadata.
5. If percent is supplied/derivable, create Vehicle Fuel Level and optional location association.
6. Create Vehicle Sensor Data rows for mapped nonempty sensor fields, and retain source traceability metadata.
7. Update live vehicle location/fuel/odometer fields, guarded against older source time. A future timestamp is not a freshness guarantee and requires policy.
8. Return created document identifiers. Framework transaction handling applies to the request; polling additionally uses savepoints and explicit commits.

Telemetry read/list/delete uses the batch metadata across telemetry DocTypes. Update deletes a batch then recreates from the submitted payload in the request transaction. Do not treat update/delete as immutable audit history or assume deleting a batch rebuilds live Vehicle snapshot fields. Reconciliation, access scope and transactional failure behavior require explicit production tests.

## 5. Provider Configuration and Fetch

| Setting | Default / range | Effect |
| --- | --- | --- |
| configuration_name | Required, unique | Document naming field |
| enabled / is_active | Enabled by default; active off initially | Disabled API cannot be active; one active default serialized by controller |
| endpoint_url / http_method | Absolute HTTP(S); GET or POST | Use HTTPS in production; HTTP is currently accepted by validation |
| api_key_header / api_key | `key` / Password | Backend request header; read API returns has_api_key instead of value |
| request_body_json | Optional valid JSON | Sent as JSON for provider POST requests |
| response_root | Optional dot path | Extract nested response before supported-object detection |
| ingest_on_run | Enabled by default | Controls manual Run ingestion, not background automatic polling |
| max_records_per_run | Default 50; controller bounds 1..500 | Truncates manual Run payloads; not a global automatic-poller limit |
| auto_poll_enabled | Default off | Enables polling eligible mapped vehicles |
| running/idle/off_poll_seconds | Defaults 10/60/120; whole 1..86400 | Per-condition request schedule |

Extraction supports a single device object, a device list, common `data/objects/items/results` containers and objects keyed by IMEI. Explicit response-root traversal uses dot-separated dictionary keys, not arbitrary JSONPath or array-index expressions.

Before fetch, the host is resolved and all returned addresses must be globally routable. Redirects are disabled. Requests use a 5-second connect timeout, a 20-second read timeout, streaming and a 2 MiB body limit. These are requests-library connect/read bounds, not a hard total wall-clock deadline against a slow streaming response. DNS resolution is separate from the actual connection and does not eliminate DNS-rebinding risk; restrict egress at the network/proxy layer.

Preview returns `ok`, optional `http_status`, `raw`, `parsed`, `fetched_count` and `errors`; DNS/transport failures may not include a status. Literal API-key text is redacted from preview output. Manual Run can store a truncated response sample and return samples; full secret-aware structured redaction is not guaranteed for every storage/return path. Provider content should never contain credentials, and access must be restricted.

## 6. Polling Low-Level Design

| Element | Implementation behavior |
| --- | --- |
| Selection | Enabled API + auto_poll_enabled; enabled Vehicle with IMEI; explicit config else active default |
| Due time | Last request completion + interval based on last fetched condition; new source/IMEI due immediately |
| Grouping | One fetch per due provider group; process only due mapped vehicles |
| Off | Engine value off/false/0/stopped, including numeric zero |
| Running | Engine on/true/1/running and speed greater than zero; unknown engine with movement also Running |
| Idle | Engine on without movement, or idle status when engine is not explicitly Off |
| Unknown / error | Shortest configured interval |
| Stable hash | SHA-256 of selected sensor fields, IMEI, tracker time, GPS/custom data; excludes status/group; server time only if tracker time absent |
| Changed snapshot | Ingest; update hash/condition/status; publish after-commit vehicle event |
| Unchanged snapshot | No new poll-ingested telemetry; advance request/next due status |
| Error | Roll back vehicle savepoint; record bounded error text; retain prior successful snapshot |
| Commit boundary | Independently per provider; isolates another provider's committed work |
| Worker lifecycle | Site Redis NX lease 180 sec; long-queue jobs timeout 120 sec; work window 45 sec; one-second ticks; self-requeue |
| Recovery | Vehicle/config after-commit wake and minute cron watchdog |

Identical push requests/manual Sync are not globally deduplicated by this hash. There is no durable device replay sequence or exactly-once idempotency key contract. Lease expiry/process termination can create overlaps; test concurrency and data reconciliation rather than assuming perfect mutual exclusion.

For 700 changing vehicles continuously sampled every 10 seconds, the planning upper scenario is approximately **6,048,000 vehicle samples/day**, before multiplying sensor rows. The provider fetch count may be much lower through grouping, but database volume is not. This is arithmetic for sizing, not a benchmark or guaranteed supported load. Confirm actual running/idle/off mix, changed-snapshot rate, retained channels, retention/aggregation and more-than-700 fleet growth. More than 500 registered users also requires an independently agreed peak concurrency and page-refresh workload.

## 7. Business Logic and Scheduled Jobs

RO validation enforces party-specific fields and billable/FoC mutual exclusion. Submit sets Scheduled and expands templates. Start Work creates Project/Tasks if needed and starts work. Task and invoice hooks can advance status; Timesheet/Purchase Invoice/Sales Invoice events recompute labor/parts/revenue values. The exact RO controller has priority over older overview descriptions.

Ready for Handover checks linked QC tasks for Completed/Closed. Closed checks the linked invoice only if present and accepts Paid or Submitted; it does not prove every linked cost is paid. Fuel approval currently takes a caller-provided role branch and can add consumption repeatedly; this is a required integrity/authorization fix, not an approved financial control.

Scheduler hooks: minute polling watchdog; hourly due report execution; daily job-costing snapshots. Redis and managed workers must be healthy. Scheduled inspection records and UI schedules should be validated for the desired reminders/automation; merely storing a recurrence does not establish every external notification.

## 8. Failure, Validation and Test Specification

| Case | Expected check / limitation |
| --- | --- |
| Unauthenticated request | Framework denies protected methods; guest bootstrap returns no protected data |
| Wrong role/vehicle | Integration methods deny; legacy business endpoints need separate negative tests |
| Invalid/duplicate IMEI | Mapping denied; database uniqueness and Vehicle validation exercised |
| Invalid time/GPS/nonfinite fuel | Shared parser rejects; no partial ordinary request ingestion |
| Missing optional channel | Other valid data can be interpreted without assuming zero |
| Non-JSON/empty/provider 4xx/5xx | Preview errors displayed; sync/poll does not count invalid sample as success |
| Private/loopback/link-local target | Denied by fetch address check; also test IPv6, redirects and DNS changes |
| Large/slow response | Size/connect/read limits tested; infrastructure deadline needed for slow streams |
| Old/unchanged/future sample | Old live overwrite guarded; poll unchanged skipped; future-time policy outstanding |
| Repeated approval/update/delete | No duplicate financial posting or unauthorized history change; current gaps recorded |
| Worker outage/site separation | Recovery, backlog and cross-site credential/data isolation tested |
| Clean Docker install/upgrade | All schema/role/import checks and user workflows pass with consistent assets |

Focused automated tests exist for hardware parsing, configuration and polling. Execute those without contacting a live provider. Full Frappe tests require an isolated test site and separate permission/UAT/load/security exercises. Never enable destructive tests on the Commission production site. `verification.md` records what was actually run for this dossier.

## 9. Source-Derived Inventory

The following content is generated from Git objects at the evaluated revision. It excludes installed-site values, private configuration and fixture records. Shipped DocType permission rows are declarations only; site overrides, user permissions, shares, core ERPNext schemas and custom API bypasses can change effective access. Setup field inventory is a static declaration inventory, not a live database schema comparison.

<!-- BEGIN GENERATED INVENTORY -->

### 9.1 Inventory Summary

| Item | Count / baseline |
| --- | --- |
| Source revision | 5974cf7addfef5d5cfc8fde325fc964343557a2f |
| Shipped DocTypes (including child tables) | 29 |
| Declared whitelisted functions in API modules and RO controller | 135 |
| Frontend route path declarations | 59 |

Source SHA-256 values and machine-readable definitions are in `source-inventory.json`. Runtime telemetry DocTypes are created by install.py, separately from shipped JSON. Inherited Frappe/ERPNext APIs and permissions are outside this application-only inventory.

### 9.2 Shipped DocType Data Dictionary

#### Customer Update

Source: `car_repair_management/car_repair_management/doctype/customer_update/customer_update.json`. Child: True. Submittable: False. Naming: `format:CSTMR-UPDT-{MM}-{YY}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| update_type | Select: Status<br>Note<br>Attachment | - |
| message | Small Text | - |
| attachment | Attach | - |
| visible_on_portal | Check | - |

#### Fleet Replacement Settings

Source: `car_repair_management/car_repair_management/doctype/fleet_replacement_settings/fleet_replacement_settings.json`. Child: False. Submittable: False. Naming: `framework default`.

Declared permissions: System Manager: read, write, create, print (level 0); Fleet Manager: read, write, print (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| age_threshold | Int | reqd |
| mileage_threshold | Int | reqd |
| cost_to_value_ratio_threshold | Float | reqd |
| downtime_threshold | Int | reqd |
| maintenance_frequency_threshold | Int | reqd |
| weight_age | Int | reqd |
| weight_mileage | Int | reqd |
| weight_cost_ratio | Int | reqd |
| weight_downtime | Int | reqd |
| weight_maintenance_frequency | Int | reqd |
| total_weight | Int | read_only |
| keep_max_score | Int | reqd |
| monitor_max_score | Int | reqd |

#### Handover Checklist Item

Source: `car_repair_management/car_repair_management/doctype/handover_checklist_item/handover_checklist_item.json`. Child: False. Submittable: False. Naming: `field:item_name`.

Declared permissions: System Manager: read, write, create, delete (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| item_name | Data | reqd, unique |
| type | Select: Pass/Fail<br>Scale<br>Notes Required | reqd |

#### Hardware Test Configuration

Source: `car_repair_management/car_repair_management/doctype/hardware_test_configuration/hardware_test_configuration.json`. Child: False. Submittable: False. Naming: `field:configuration_name`.

Declared permissions: System Manager: read, write, create, delete, report, export, print, email, share (level 0); Telemetry Integration Manager: read, write, create, delete, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| auto_poll_enabled | Check | - |
| running_poll_seconds | Int | - |
| idle_poll_seconds | Int | - |
| off_poll_seconds | Int | - |
| is_active | Check | - |
| configuration_name | Data | reqd, unique |
| enabled | Check | - |
| endpoint_url | Data | reqd |
| http_method | Select: GET<br>POST | reqd |
| api_key_header | Data | reqd |
| api_key | Password | - |
| request_body_json | Code: JSON | - |
| response_root | Data | - |
| ingest_on_run | Check | - |
| max_records_per_run | Int | - |
| last_run | Datetime | read_only |
| last_status | Data | read_only |
| last_ingested_count | Int | read_only |
| last_error | Small Text | read_only |
| last_response_sample | Code: JSON | read_only |

#### Inspection Form Item

Source: `car_repair_management/car_repair_management/doctype/inspection_form_item/inspection_form_item.json`. Child: True. Submittable: False. Naming: `framework default`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| item_label | Data | reqd |
| item_type | Select: Pass/Fail<br>N-A<br>Rating<br>Numeric<br>Text | reqd |
| section_name | Data | - |
| is_required | Check | - |
| fail_triggers_severity | Select: <br>Low<br>Medium<br>High<br>Critical | - |
| numeric_min | Float | - |
| numeric_max | Float | - |
| photo_required | Check | - |
| signature_required | Check | - |
| description | Small Text | - |

#### Inspection Form Template

Source: `car_repair_management/car_repair_management/doctype/inspection_form_template/inspection_form_template.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: IFT-.YYYY.-.##### | reqd |
| title | Data | reqd |
| category | Select: <br>Pre-Trip<br>Post-Trip<br>Safety<br>Regulatory<br>Custom | - |
| status | Select: Draft<br>Active<br>Archived | reqd |
| description | Small Text | - |
| version | Int | - |
| usage_count | Int | read_only |
| items | Table: Inspection Form Item | - |

#### Inspection Item Failure

Source: `car_repair_management/car_repair_management/doctype/inspection_item_failure/inspection_item_failure.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: IF-.YYYY.-.##### | reqd |
| item_name | Data | reqd |
| vehicle | Link: Vehicle | reqd |
| inspection | Link: Vehicle Inspection | - |
| severity | Select: Low<br>Medium<br>High<br>Critical | reqd |
| status | Select: Open<br>Converted<br>Resolved<br>Ignored | reqd |
| failure_reason | Small Text | - |
| resolution_type | Select: <br>Work Order<br>Quick Fix<br>Deferred<br>N/A | - |
| linked_work_order | Link: Repair Order | - |
| assigned_to | Link: User | - |
| reported_date | Date | - |
| resolved_date | Date | - |
| is_recurring | Check | - |
| evidence | Attach Image | - |
| notes | Text Editor | - |

#### Inspection Schedule

Source: `car_repair_management/car_repair_management/doctype/inspection_schedule/inspection_schedule.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: IS-.YYYY.-.##### | reqd |
| title | Data | reqd |
| vehicle | Link: Vehicle | reqd |
| form_template | Link: Inspection Form Template | - |
| assigned_to | Link: Employee | - |
| status | Select: Active<br>Paused<br>Completed<br>Cancelled | reqd |
| frequency | Select: <br>Daily<br>Weekly<br>Bi-Weekly<br>Monthly<br>Quarterly<br>Semi-Annually<br>Annually<br>One-Time | - |
| scheduled_date | Date | reqd |
| next_due | Date | - |
| last_completed | Date | - |
| last_inspection | Link: Vehicle Inspection | - |
| auto_create_inspection | Check | - |
| notify_before_days | Int | - |
| notes | Small Text | - |

#### Job Costing

Source: `car_repair_management/car_repair_management/doctype/job_costing/job_costing.json`. Child: False. Submittable: False. Naming: `format:JB-COST-{repair_order}-{YY}`.

Declared permissions: System Manager: read, write, create, delete (level 0); Projects Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| repair_order | Link: Repair Order | - |
| project | Link: Project | - |
| vehicle | Link: Vehicle | - |
| parts_cost | Currency | - |
| labor_cost | Currency | - |
| other_charges | Currency | - |
| total_job_cost | Currency | read_only |
| margin_snapshot | Currency | - |

#### Repair Checklist

Source: `car_repair_management/car_repair_management/doctype/repair_checklist/repair_checklist.json`. Child: False. Submittable: False. Naming: `field:title`.

Declared permissions: System Manager: read, write, create, delete (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| title | Data | reqd, unique |
| check_items | Table: Repair Checklist Item | - |

#### Repair Checklist Item

Source: `car_repair_management/car_repair_management/doctype/repair_checklist_item/repair_checklist_item.json`. Child: True. Submittable: False. Naming: `format:RPR-CHK-ITM-{check_item}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| check_item | Data | - |
| type | Select: Pass/Fail<br>Scale<br>Notes Required | - |

#### Repair Checklist Response

Source: `car_repair_management/car_repair_management/doctype/repair_checklist_response/repair_checklist_response.json`. Child: True. Submittable: False. Naming: `format:RPR-CHK-RSPN-{check_item}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| check_item | Link: Handover Checklist Item | - |
| type | Data | read_only |
| value | Data | - |
| notes | Small Text | - |
| passed | Check | - |

#### Repair Operation Line

Source: `car_repair_management/car_repair_management/doctype/repair_operation_line/repair_operation_line.json`. Child: True. Submittable: False. Naming: `format:RPR-OP-{task}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| task | Link: Task | - |
| operation_name | Link: Operation | - |
| planned_minutes | Int | - |
| assigned_to | Link: User | - |
| workstation | Link: Workstation | - |
| is_qc | Check | - |
| status | Select: Open<br>Working<br>Pending Review<br>Completed<br>Rejected<br>Cancelled | - |

#### Repair Order

Source: `car_repair_management/car_repair_management/doctype/repair_order/repair_order.json`. Child: False. Submittable: True. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete, submit, cancel, amend (level 0); Projects Manager: read, write, create, delete, submit, cancel, amend (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: RO-.YYYY.-.##### | reqd |
| amended_from | Link: Repair Order | read_only |
| status | Select: Draft<br>Scheduled<br>In Progress<br>Awaiting Parts<br>Ready for Handover<br>Delivered<br>Closed<br>On Hold<br>Cancelled | reqd |
| order_for | Select: Customer<br>Company | reqd |
| company | Link: Company | - |
| customer | Link: Customer | - |
| vehicle | Link: Vehicle | reqd |
| intake_channel | Select: Walk-in<br>Web Intake<br>Phone<br>Partner | - |
| problem_summary | Small Text | - |
| problem_details | Long Text | - |
| priority | Select: Low<br>Normal<br>High<br>Urgent | - |
| sla_response_by | Datetime | - |
| sla_delivery_by | Datetime | - |
| expected_delivery_datetime | Datetime | - |
| entry_datetime | Datetime | - |
| sla_template | Link: SLA Template | - |
| project | Link: Project | read_only |
| service_template | Link: Service Template | - |
| quotation | Link: Quotation | read_only |
| sales_order | Link: Sales Order | read_only |
| sales_invoice | Link: Sales Invoice | read_only |
| operations | Table: Repair Operation Line | - |
| parts_plan | Table: Repair Parts Plan | - |
| handover_checklist | Table: Repair Checklist Response | - |
| customer_updates | Table: Customer Update | - |
| parts_cost | Currency | read_only |
| labor_cost | Currency | read_only |
| other_charges | Currency | - |
| total_job_cost | Currency | read_only |
| quoted_amount | Currency | read_only |
| invoiced_amount | Currency | read_only |
| gross_margin | Currency | read_only |
| feedback_score | Int | read_only |
| feedback_notes | Small Text | read_only |

#### Repair Parts Plan

Source: `car_repair_management/car_repair_management/doctype/repair_parts_plan/repair_parts_plan.json`. Child: True. Submittable: False. Naming: `format:RPR-PRT-{item_code}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| item_code | Link: Item | - |
| item_name | Data | - |
| uom | Link: UOM | - |
| qty_planned | Float | - |
| is_billable | Check | - |
| is_foc | Check | - |
| notes | Small Text | - |

#### SLA Template

Source: `car_repair_management/car_repair_management/doctype/sla_template/sla_template.json`. Child: False. Submittable: False. Naming: `field:template_name`.

Declared permissions: System Manager: read, write, create, delete (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| template_name | Data | reqd, unique |
| enabled | Check | - |
| description | Small Text | - |
| priority | Select: <br>Low<br>Normal<br>High<br>Urgent | - |
| intake_channel | Select: <br>Walk-in<br>Web Intake<br>Phone<br>Partner | - |
| service_template | Link: Service Template | - |
| response_time_hours | Float | - |
| resolution_time_hours | Float | - |
| response_time_jinja | Code: Jinja | - |
| resolution_time_jinja | Code: Jinja | - |
| escalation_after_hours | Float | - |
| escalate_to | Link: User | - |

#### Service Template

Source: `car_repair_management/car_repair_management/doctype/service_template/service_template.json`. Child: False. Submittable: False. Naming: `field:template_name`.

Declared permissions: System Manager: read, write, create, delete (level 0); Maintenance Manager: read, write, create, delete, report, export, print, email, share (level 0); Maintenance User: read, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| template_name | Data | reqd, unique |
| default_operations | Table: Service Template Operation | - |
| default_parts | Table: Service Template Part | - |
| default_checklist | Table: Service Template Checklist Item | - |

#### Service Template Checklist Item

Source: `car_repair_management/car_repair_management/doctype/service_template_checklist_item/service_template_checklist_item.json`. Child: True. Submittable: False. Naming: `format:CHK-{check_item}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| check_item | Link: Handover Checklist Item | - |
| type | Select: Pass/Fail<br>Scale<br>Notes Required | read_only |

#### Service Template Operation

Source: `car_repair_management/car_repair_management/doctype/service_template_operation/service_template_operation.json`. Child: True. Submittable: False. Naming: `format:SERV-OP-{operation}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| operation_name | Link: Operation | - |
| planned_minutes | Int | - |
| workstation | Link: Workstation | - |
| is_qc | Check | - |

#### Service Template Part

Source: `car_repair_management/car_repair_management/doctype/service_template_part/service_template_part.json`. Child: True. Submittable: False. Naming: `format:SERV-PART-{item_code}-{#####}`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| item_code | Link: Item | - |
| item_name | Data | read_only |
| uom | Link: UOM | - |
| qty_planned | Float | - |
| is_billable | Check | - |
| is_foc | Check | - |
| price_list | Link: Price List | - |
| price_list_rate | Currency | - |
| notes | Small Text | - |

#### Vehicle Driver

Source: `car_repair_management/car_repair_management/doctype/vehicle_driver/vehicle_driver.json`. Child: True. Submittable: False. Naming: `framework default`.

Declared permissions: None on this JSON; child access inherits parent context..

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| employee | Link: Employee | reqd |
| employee_name | Data | read_only |
| assigned_date | Date | - |
| assigned_by | Link: Employee | read_only |
| status | Select: Active<br>Removal Requested<br>Removed | - |
| ended_date | Date | read_only |
| ended_by | Link: Employee | read_only |
| removal_reason | Small Text | - |

#### Vehicle Expense

Source: `car_repair_management/car_repair_management/doctype/vehicle_expense/vehicle_expense.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete, report, export, print, email, share (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: VE-.YYYY.-.##### | reqd |
| title | Data | reqd |
| expense_date | Date | reqd |
| category | Select: Fuel<br>Parts<br>Labor<br>External Service<br>Insurance<br>Taxes<br>Other | reqd |
| amount | Currency | reqd |
| vehicle | Link: Vehicle | reqd |
| vendor | Data | - |
| payment_method | Select: <br>Cash<br>Bank Transfer<br>Credit Card<br>Check<br>Other | - |
| work_order | Link: Repair Order | - |
| quantity | Float | - |
| unit_cost | Currency | - |
| odometer_reading | Int | - |
| payment_status | Select: Unpaid<br>Paid<br>Partially Paid | - |
| receipt_required | Check | - |
| notes | Small Text | - |
| receipt_attachment | Attach Image | - |
| amended_from | Link: Vehicle Expense | read_only |

#### Vehicle Fault

Source: `car_repair_management/car_repair_management/doctype/vehicle_fault/vehicle_fault.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: VF-.YYYY.-.##### | reqd |
| title | Data | reqd |
| vehicle | Link: Vehicle | reqd |
| fault_code | Data | - |
| detection_type | Select: <br>OBD Scan<br>Manual Inspection<br>Driver Report<br>Sensor Alert<br>Other | - |
| severity | Select: Low<br>Medium<br>High<br>Critical | reqd |
| component_system | Data | - |
| confirmed | Select: Unconfirmed<br>Confirmed<br>False Positive | - |
| status | Select: Open<br>In Progress<br>Resolved<br>Closed | reqd |
| reported_by | Link: User | - |
| reported_date | Date | - |
| resolved_date | Date | - |
| description | Text Editor | - |
| linked_work_order | Link: Repair Order | - |
| linked_inspection | Link: Vehicle Inspection | - |
| evidence | Attach Image | - |
| notes | Small Text | - |

#### Vehicle Fuel Quota

Source: `car_repair_management/car_repair_management/doctype/vehicle_fuel_quota/vehicle_fuel_quota.json`. Child: False. Submittable: False. Naming: `format:FQ-{vehicle}-{quota_month}`.

Declared permissions: System Manager: read, write, create, delete (level 0); Fleet Manager: read, write, create (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| vehicle | Link: Vehicle | reqd |
| quota_month | Data | reqd |
| fuel_capacity_liters | Float | - |
| km_per_liter | Float | - |
| quota_liters | Float | reqd |
| consumed_liters | Float | read_only |
| remaining_liters | Float | read_only |
| status | Select: Active<br>Exhausted<br>Closed | - |

#### Vehicle Inspection

Source: `car_repair_management/car_repair_management/doctype/vehicle_inspection/vehicle_inspection.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: VI-.YYYY.-.##### | reqd |
| title | Data | reqd |
| vehicle | Link: Vehicle | reqd |
| inspection_date | Datetime | reqd |
| inspection_type | Select: Pre-Trip<br>Post-Trip<br>Periodic<br>Ad-Hoc<br>Regulatory | reqd |
| form_template | Link: Inspection Form Template | - |
| inspector | Link: Employee | - |
| result | Select: <br>Pass<br>Conditional<br>Fail | - |
| score | Percent | - |
| status | Select: Draft<br>In Progress<br>Completed<br>Cancelled | reqd |
| findings | Text Editor | - |
| notes | Small Text | - |
| follow_up_required | Check | - |
| follow_up_due_date | Date | - |
| follow_up_assigned_to | Link: User | - |
| linked_work_order | Link: Repair Order | - |
| handover_checklist_item | Link: Handover Checklist Item | - |
| failures_count | Int | read_only |

#### Vehicle Recall

Source: `car_repair_management/car_repair_management/doctype/vehicle_recall/vehicle_recall.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: VR-.YYYY.-.##### | reqd |
| title | Data | reqd |
| manufacturer | Data | reqd |
| affected_models | Data | - |
| affected_years | Data | - |
| issue_type | Select: <br>Safety<br>Emissions<br>Mechanical<br>Electrical<br>Software<br>Other | - |
| status | Select: Active<br>In Progress<br>Completed<br>Cancelled | reqd |
| priority | Select: Low<br>Medium<br>High<br>Critical | - |
| recall_start_date | Date | - |
| deadline | Date | - |
| external_reference | Data | - |
| description | Text Editor | - |
| vehicles_affected | Int | read_only |
| vehicles_completed | Int | read_only |
| compliance_pct | Percent | read_only |
| notes | Small Text | - |

#### Vehicle Refueling Record

Source: `car_repair_management/car_repair_management/doctype/vehicle_refueling_record/vehicle_refueling_record.json`. Child: False. Submittable: False. Naming: `hash`.

Declared permissions: System Manager: read, write, create, delete (level 0); Fleet Manager: read, write, create (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| vehicle | Link: Vehicle | reqd |
| refuel_date | Date | reqd |
| driver | Link: Employee | - |
| odometer_reading | Float | - |
| liters | Float | reqd |
| cost_per_liter | Currency | - |
| total_cost | Currency | read_only |
| fuel_station | Data | - |
| quota_link | Link: Vehicle Fuel Quota | - |
| consumed_before | Float | read_only |
| consumed_after | Float | read_only |
| is_over_quota | Check | read_only |
| over_quota_liters | Float | read_only |
| approval_status | Select: Approved<br>Pending Dept Head Approval<br>Pending Depot Manager Approval<br>Dept Head Approved<br>Rejected | - |
| dept_head_approved_by | Link: Employee | read_only |
| dept_head_approved_on | Datetime | read_only |
| depot_manager_approved_by | Link: Employee | read_only |
| depot_manager_approved_on | Datetime | read_only |
| rejection_reason | Small Text | - |
| notes | Small Text | - |

#### Workshop Report Schedule

Source: `car_repair_management/car_repair_management/doctype/workshop_report_schedule/workshop_report_schedule.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete, report, export, print, email, share (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: WRSC-.YYYY.-.##### | reqd |
| title | Data | reqd |
| report_id | Data | reqd |
| report_title | Data | read_only |
| frequency | Select: Daily<br>Weekly<br>Monthly | reqd |
| delivery_method | Select: Email<br>In-App<br>Download Link | reqd |
| export_format | Select: CSV<br>PDF<br>Excel | reqd |
| enabled | Check | - |
| recipients | Small Text | - |
| filters_json | Small Text | - |
| date_from | Date | - |
| date_to | Date | - |
| delivery_time | Time | - |
| next_run | Datetime | read_only |
| last_sent | Datetime | read_only |
| last_status | Data | read_only |

#### Workshop Saved Report

Source: `car_repair_management/car_repair_management/doctype/workshop_saved_report/workshop_saved_report.json`. Child: False. Submittable: False. Naming: `naming_series:`.

Declared permissions: System Manager: read, write, create, delete, report, export, print, email, share (level 0); All: read (level 0).

| Field | Type / target or choices | Flags |
| --- | --- | --- |
| naming_series | Select: WSR-.YYYY.-.##### | reqd |
| title | Data | reqd |
| report_id | Data | reqd |
| report_title | Data | read_only |
| category | Data | - |
| report_type | Data | - |
| filters_json | Small Text | - |
| date_from | Date | - |
| date_to | Date | - |
| shared_with | Small Text | - |
| last_run | Datetime | - |
| description | Small Text | - |

### 9.3 Declared Application API Functions

Paths below are Python source modules; remove `.py` and replace `/` with `.` to form the module prefix. Append the function name after `/api/method/`. `framework default` means no explicit methods restriction is declared, not that GET mutations are recommended. This inventory includes only direct module-level whitelist decorators.

#### car_repair_management/api/activity.py

| Function and arguments | Declared transport |
| --- | --- |
| get_document_activity(doctype, name, limit=50) | framework default |

#### car_repair_management/api/aging_analysis.py

| Function and arguments | Declared transport |
| --- | --- |
| get_aging_analysis(vehicles=None, department=None) | framework default |

#### car_repair_management/api/customer.py

| Function and arguments | Declared transport |
| --- | --- |
| get_customers(search=None, customer_group=None, customer_type=None, territory=None, status=None, limit_start=0, limit_page_length=20) | framework default |
| get_customer_detail(name) | framework default |

#### car_repair_management/api/employee.py

| Function and arguments | Declared transport |
| --- | --- |
| get_employees(search=None, department=None, designation=None, status=None, supervisor=None, limit_start=0, limit_page_length=20) | framework default |
| get_employee_detail(name) | framework default |

#### car_repair_management/api/expense.py

| Function and arguments | Declared transport |
| --- | --- |
| get_expenses(date_from=None, date_to=None, vehicle=None, category=None, vendor=None, work_order=None, payment_status=None, has_receipt=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_expense_detail(name) | framework default |
| create_expense(**kwargs) | framework default |
| update_expense(name, **kwargs) | framework default |

#### car_repair_management/api/expense_history.py

| Function and arguments | Declared transport |
| --- | --- |
| get_expense_history(date_from=None, date_to=None, vehicles=None, category=None) | framework default |

#### car_repair_management/api/fuel.py

| Function and arguments | Declared transport |
| --- | --- |
| get_vehicle_quota_status(vehicle, month=None) | framework default |
| get_refueling_records(vehicle=None, month=None, status=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_refueling_detail(name) | framework default |
| create_refueling_record(vehicle, liters, refuel_date=None, odometer_reading=None, cost_per_liter=None, fuel_station=None, notes=None) | framework default |
| approve_refueling(name, role) | framework default |
| reject_refueling(name, reason) | framework default |
| get_fuel_quotas(vehicle=None, month=None, status=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| update_fuel_quota(name, quota_liters=None, status=None) | framework default |

#### car_repair_management/api/hardware.py

| Function and arguments | Declared transport |
| --- | --- |
| vehicle_hardware(vehicle, action=&#x27;read&#x27;, imei=None, configuration=None, enabled=1) | {&quot;methods&quot;: [&quot;POST&quot;]} |

#### car_repair_management/api/health.py

| Function and arguments | Declared transport |
| --- | --- |
| audit_site(repair=False) | framework default |

#### car_repair_management/api/inspection.py

| Function and arguments | Declared transport |
| --- | --- |
| get_inspection_history(date_from=None, date_to=None, vehicles=None, inspector=None, inspection_type=None, result=None, form_template=None, has_failures=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_inspection_detail(name) | framework default |
| update_inspection(name, updates) | framework default |
| get_item_failures(date_from=None, date_to=None, vehicle=None, component=None, severity=None, status=None, form_template=None, is_recurring=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_failure_detail(name) | framework default |
| get_schedules(date_from=None, date_to=None, vehicle=None, form_template=None, inspector=None, status=None, frequency=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_schedule_detail(name) | framework default |
| get_form_templates(search=None, category=None, status=None, limit_start=0, limit_page_length=20) | framework default |
| get_form_template_detail(name) | framework default |
| create_schedule(data) | framework default |
| update_schedule(name, updates) | framework default |
| generate_inspection_now(schedule_name) | framework default |
| cancel_schedule(name) | framework default |
| update_failure(name, updates) | framework default |
| create_work_order_from_failure(name) | framework default |

#### car_repair_management/api/invoice.py

| Function and arguments | Declared transport |
| --- | --- |
| get_invoices(date_from=None, date_to=None, invoice_type=None, status=None, customer=None, supplier=None, work_order_linked=None, amount_min=None, amount_max=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_invoice_detail(name, invoice_type=&#x27;Sales&#x27;) | framework default |

#### car_repair_management/api/issue.py

| Function and arguments | Declared transport |
| --- | --- |
| get_issues(date_from=None, date_to=None, vehicle=None, source=None, category=None, severity=None, status=None, assigned_to=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_issue_detail(name) | framework default |
| get_faults(date_from=None, date_to=None, vehicle=None, detection_type=None, fault_code=None, component_system=None, confirmed=None, severity=None, status=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_fault_detail(name) | framework default |
| convert_issue_to_work_order(issue_name, order_for=&#x27;Company&#x27;, customer=None, company=None) | framework default |
| mark_issue_duplicate(issue_name, duplicate_of) | framework default |
| close_issue_with_reason(issue_name, reason) | framework default |
| get_recalls(manufacturer=None, model=None, year_from=None, year_to=None, status=None, priority=None, search=None, limit_start=0, limit_page_length=20) | framework default |
| get_recall_detail(name) | framework default |
| search_vehicles(txt=None, limit_page_length=20) | framework default |
| search_link_options(doctype, txt=None, limit_page_length=20) | framework default |
| create_issue(subject, vehicle, severity=None, category=None, source=None, description=None, assigned_to=None) | framework default |
| approve_issue(issue_name) | framework default |
| reject_issue(issue_name, reason=None) | framework default |

#### car_repair_management/api/meter_history.py

| Function and arguments | Declared transport |
| --- | --- |
| get_meter_history(date_from=None, date_to=None, vehicles=None, source=None) | framework default |

#### car_repair_management/api/notification.py

| Function and arguments | Declared transport |
| --- | --- |
| get_notifications(limit=20) | framework default |
| mark_as_read(name=None) | framework default |

#### car_repair_management/api/parts.py

| Function and arguments | Declared transport |
| --- | --- |
| get_parts(search=None, item_group=None, stock_status=None, is_stock_item=None, uom=None, limit_start=0, limit_page_length=20) | framework default |
| get_part_detail(name) | framework default |
| create_part(**kwargs) | framework default |

#### car_repair_management/api/replacement_analysis.py

| Function and arguments | Declared transport |
| --- | --- |
| get_replacement_analysis(vehicles=None, department=None) | framework default |
| run_financial_simulation(vehicle, resale_value=0, acquisition_cost=0, maintenance_reduction_pct=0, downtime_reduction_pct=0) | framework default |

#### car_repair_management/api/reports.py

| Function and arguments | Declared transport |
| --- | --- |
| get_reports_home() | framework default |
| get_reports_library(search=None, category=None, report_type=None, limit_start=0, limit_page_length=50) | framework default |
| get_report_data(report_id, date_from=None, date_to=None, filters=None, limit_start=0, limit_page_length=50) | framework default |
| get_saved_reports(search=None, limit_start=0, limit_page_length=20) | framework default |
| save_report(title, report_id, filters_json=None, date_from=None, date_to=None, description=None, shared_with=None) | framework default |
| delete_saved_report(name) | framework default |
| duplicate_saved_report(name) | framework default |
| get_scheduled_reports(search=None, limit_start=0, limit_page_length=20) | framework default |
| create_report_schedule(title, report_id, frequency, delivery_method=&#x27;Email&#x27;, export_format=&#x27;CSV&#x27;, recipients=None, filters_json=None, date_from=None, date_to=None, delivery_time=None) | framework default |
| toggle_report_schedule(name, enabled) | framework default |
| delete_report_schedule(name) | framework default |
| run_report_now(name) | framework default |
| get_pinned_reports() | framework default |
| toggle_pin_report(report_id) | framework default |

#### car_repair_management/api/settings.py

| Function and arguments | Declared transport |
| --- | --- |
| get_settings_home() | framework default |
| get_settings_category(category) | framework default |
| update_setting(category, key, value) | framework default |
| reset_setting(category, key) | framework default |
| get_audit_log(doctype=None, name=None, limit=20) | framework default |
| get_system_health() | framework default |
| seed_demo() | framework default |
| clear_demo() | framework default |
| demo_status() | framework default |

#### car_repair_management/api/setup_fuel_fields.py

| Function and arguments | Declared transport |
| --- | --- |
| setup_fuel_custom_fields() | framework default |

#### car_repair_management/api/setup_issue_fields.py

| Function and arguments | Declared transport |
| --- | --- |
| setup_issue_custom_fields() | framework default |

#### car_repair_management/api/telemetry.py

| Function and arguments | Declared transport |
| --- | --- |
| telemetry(action=&#x27;create&#x27;, payload=None, batch_id=None, vehicle=None, imei=None, date_from=None, date_to=None, limit_start=0, limit_page_length=20) | {&quot;methods&quot;: [&quot;POST&quot;, &quot;GET&quot;]} |
| hardware_test_configuration(action=&#x27;list&#x27;, name=None, data=None) | {&quot;methods&quot;: [&quot;POST&quot;, &quot;GET&quot;]} |

#### car_repair_management/api/vehicle.py

| Function and arguments | Declared transport |
| --- | --- |
| get_vehicle_dashboard(vehicle_name) | framework default |
| get_vehicle_specs(vehicle_name) | framework default |
| get_vehicle_financial(vehicle_name) | framework default |
| get_vehicle_work_orders(vehicle_name, limit=20, offset=0) | framework default |
| scrap_vehicle(vehicle_name) | framework default |
| delete_vehicle(vehicle_name) | framework default |
| get_vehicle_specs_full(vehicle_name) | framework default |
| get_vehicle_financials_full(vehicle_name) | framework default |
| get_vehicle_sensor_data(vehicle_name, timeframe=&#x27;30d&#x27;) | framework default |
| get_vehicle_service_history(vehicle_name) | framework default |
| get_vehicle_inspection_history(vehicle_name) | framework default |
| get_vehicle_work_orders_full(vehicle_name, status_filter=None, limit=20, offset=0) | framework default |
| get_vehicle_reminders_full(vehicle_name) | framework default |
| create_vehicle_reminder(vehicle_name, remind_at, description, reminder_type=&#x27;General&#x27;) | framework default |
| dismiss_vehicle_reminder(reminder_name) | framework default |
| snooze_vehicle_reminder(reminder_name, days=7) | framework default |
| get_vehicle_issues_full(vehicle_name) | framework default |
| get_vehicle_attachments(vehicle_name) | framework default |
| upload_vehicle_attachment(vehicle_name, file_url, category=None) | framework default |
| move_vehicle_attachment(file_name, vehicle_name, target_category) | framework default |
| set_custodian(vehicle_name, employee) | framework default |
| add_driver(vehicle_name, employee) | framework default |
| remove_driver(vehicle_name, driver_row_name) | framework default |
| request_driver_removal(vehicle_name, driver_row_name) | framework default |
| get_vehicle_assignments_data(vehicle_name) | framework default |
| get_vehicle_driver_history(vehicle_name) | framework default |

#### car_repair_management/api/vehicle_assignments.py

| Function and arguments | Declared transport |
| --- | --- |
| get_vehicle_assignments(range_start, range_end) | framework default |

#### car_repair_management/car_repair_management/doctype/repair_order/repair_order.py

| Function and arguments | Declared transport |
| --- | --- |
| make_quotation_from_repair_order(name: str) | framework default |
| make_material_request_from_repair_order(name: str) | framework default |
| apply_service_template(name: str, template: str) | framework default |
| make_sales_order_from_quotation(quotation_name: str) | framework default |
| make_sales_invoice_from_sales_order(sales_order_name: str) | framework default |
| set_status(name: str, status: str) | framework default |
| start_work(name: str) | framework default |
| get_repair_order_detail(name: str) | framework default |
| get_repair_order_timeline(name: str) | framework default |
| get_repair_order_attachments(name: str) | framework default |
| upload_repair_order_attachment(name: str, file_url: str, category: str=&#x27;other&#x27;) | framework default |
| add_repair_order_comment(name: str, content: str) | framework default |
| get_service_template_data(template_name: str) | framework default |
| get_vehicles_for_customer(customer) | framework default |
| get_vehicles_for_company(company) | framework default |
| get_operation_detail(repair_order: str, operation_idx: str) | framework default |
| update_operation_status(repair_order: str, operation_idx: str, status: str) | framework default |
| assign_operation(repair_order: str, operation_idx: str, user: str) | framework default |
| add_operation_comment(repair_order: str, operation_idx: str, content: str) | framework default |
| get_handover_checklist_status(repair_order: str) | framework default |
| create_handover_inspection(repair_order: str, checklist_item_name: str) | framework default |

### 9.4 Setup Field Declarations

Unique static declarations grouped by setup source, including base telemetry fields. A name can occur on more than one target DocType. Conditional/dynamically assembled values may require code inspection; target placement is not inferred from these flattened rows.

#### car_repair_management/install.py

| Field | Type / target | Flags |
| --- | --- | --- |
| acquisition_cost | Currency | - |
| altitude | Float | read_only |
| battery_capacity | Data | - |
| comprehensive_insurance | Data | - |
| country_of_origin | Data | - |
| custom_engine_hours | Float | read_only |
| custom_fuel_level | Percent | read_only |
| custom_hardware_configuration | Link: Hardware Test Configuration | - |
| custom_hardware_enabled | Check | - |
| custom_hardware_engine_condition | Data | read_only |
| custom_hardware_last_polled | Datetime | read_only |
| custom_hardware_next_poll | Datetime | read_only |
| custom_hardware_poll_error | Small Text | read_only |
| custom_hardware_poll_source | Data | read_only |
| custom_hardware_sample_hash | Data | read_only |
| custom_last_known_latitude | Float | read_only |
| custom_last_known_longitude | Float | read_only |
| custom_last_location_update | Datetime | read_only |
| custom_repair_order | Link: Repair Order | - |
| custom_telematics_imei | Data | unique |
| cylinders | Int | - |
| depreciation_method | Select: <br>Straight Line<br>Double Declining Balance<br>Written Down Value | - |
| depreciation_months | Int | - |
| device_name | Data | read_only |
| direction | Float | - |
| drivetrain | Data | - |
| engine_capacity | Int | - |
| engine_number | Data | - |
| engine_type | Data | - |
| entry_datetime | Datetime | - |
| entry_datetime_editable | Check | - |
| erpnext_asset | Link: Asset | read_only |
| expected_delivery_datetime | Datetime | - |
| fuel_level | Percent | reqd |
| fuel_tank_capacity | Data | - |
| gross_vehicle_weight | Data | - |
| insurance_expiry | Date | - |
| insurance_policy | Data | - |
| insurance_start_date | Date | - |
| insured_value | Currency | - |
| jobs_count | Int | read_only |
| last_service_date | Date | read_only |
| latitude | Float | - |
| location | Link: Vehicle Location | - |
| longitude | Float | - |
| next_service_due_date | Date | read_only |
| odometer_at_last_service | Int | - |
| ownership_type | Data | - |
| payload_capacity | Data | - |
| registration_authority | Data | - |
| registration_expiry | Date | - |
| repair_cost_to_date | Currency | read_only |
| repair_order | Link: Repair Order | - |
| revenue_billed_to_date | Currency | read_only |
| seating_capacity | Int | - |
| sensor_type | Data | reqd |
| source_imei | Data | read_only |
| speed | Float | - |
| telemetry_batch_id | Data | read_only |
| timestamp | Datetime | reqd |
| towing_capacity | Data | - |
| transmission | Select: Manual<br>Automatic<br>CVT | - |
| unit | Data | - |
| value | Data | reqd |
| variant | Data | - |
| vehicle | Link: Vehicle | - |
| vehicle_type | Data | - |
| year | Int | - |

#### car_repair_management/api/setup.py

| Field | Type / target | Flags |
| --- | --- | --- |
| custom_custodian | Link: Employee | - |
| custom_custodian_name | Data | read_only |
| custom_drivers | Table: Vehicle Driver | - |
| custom_image | Attach Image | - |
| custom_last_known_latitude | Float | - |
| custom_last_known_longitude | Float | - |
| custom_last_location_update | Datetime | - |
| custom_status | Select: Active<br>In Maintenance<br>Undergoing Tests<br>Delivered to Customer<br>Scrapped | - |
| custom_vehicle_type | Select: Car<br>SUV<br>Truck<br>Van<br>Motorcycle<br>Bus<br>Other | - |

#### car_repair_management/api/setup_fuel_fields.py

| Field | Type / target | Flags |
| --- | --- | --- |
| custom_column_break_fuel | Column Break | - |
| custom_fuel_capacity_liters | Float | - |
| custom_fuel_quota_section | Section Break | - |
| custom_km_per_liter | Float | - |
| custom_monthly_fuel_quota | Float | - |

#### car_repair_management/api/setup_issue_fields.py

| Field | Type / target | Flags |
| --- | --- | --- |
| custom_approved_by | Link: Employee | read_only |
| custom_approved_on | Datetime | read_only |
| custom_assigned_to | Link: User | - |
| custom_category | Select: <br>Mechanical<br>Electrical<br>Body/Paint<br>Interior<br>Safety<br>Compliance<br>Other | - |
| custom_linked_fault | Link: Vehicle Fault | - |
| custom_linked_inspection | Link: Vehicle Inspection | - |
| custom_linked_work_order | Link: Repair Order | - |
| custom_rejected_by | Link: Employee | read_only |
| custom_rejected_on | Datetime | read_only |
| custom_rejection_reason | Small Text | read_only |
| custom_requested_by_employee | Link: Employee | read_only |
| custom_resolution_notes | Text Editor | - |
| custom_severity | Select: <br>Low<br>Medium<br>High<br>Critical | - |
| custom_source | Select: <br>Inspection<br>Driver Report<br>Mechanic<br>Customer<br>Sensor<br>Other | - |
| custom_vehicle | Link: Vehicle | - |
| custom_workflow_state | Select: <br>Draft<br>Pending Custodian Approval<br>Rejected<br>Submitted<br>Work Order Created | - |

### 9.5 Frontend Route Inventory

All paths are relative to `/workshop`. Dynamic parameters identify records. Route declaration is not a role gate; backend authorization remains necessary.

- `/auth/login`
- `/auth/forgot`
- `/`
- `/repair-orders`
- `/repair-orders/new`
- `/repair-orders/:id`
- `/repair-orders/:id/edit`
- `/repair-orders/:roId/operations/:opId`
- `/vehicles`
- `/vehicles/new`
- `/vehicles/assignments`
- `/vehicles/meter-history`
- `/vehicles/expense-history`
- `/vehicles/replacement-analysis`
- `/vehicles/aging-analysis`
- `/vehicles/:id`
- `/vehicles/:id/edit`
- `/customers`
- `/customers/:id`
- `/employees`
- `/employees/:id`
- `/tasks`
- `/inspections`
- `/inspections/:id`
- `/inspections/item-failures`
- `/inspections/item-failures/:id`
- `/inspections/schedules`
- `/inspections/schedules/:id`
- `/inspections/forms`
- `/inspections/forms/:id`
- `/issues`
- `/issues/new`
- `/issues/:id`
- `/issues/faults`
- `/issues/faults/:id`
- `/issues/recalls`
- `/issues/recalls/:id`
- `/expenses`
- `/expenses/new`
- `/expenses/:id`
- `/expenses/:id/edit`
- `/parts`
- `/parts/new`
- `/parts/:id`
- `/parts/:id/edit`
- `/invoices`
- `/invoices/:id`
- `/reports`
- `/reports/library`
- `/reports/saved`
- `/reports/scheduled`
- `/reports/view/:id`
- `/settings`
- `/settings/:category`
- `/fuel`
- `/fuel/new`
- `/fuel/quotas`
- `/fuel/:id`
- `/:pathMatch(.*)*`

<!-- END GENERATED INVENTORY -->

## 10. Engineering Acceptance

Required release artifacts: exact app/Frappe/ERPNext revisions, resolved dependency SBOM, immutable image digest and scan, final Compose/network/volume specification, per-site audit, migration/rollback evidence, focused and end-to-end test reports, authorization fixes and independent security results. Engineering reviewer/signature/date: TO BE CONFIRMED.
