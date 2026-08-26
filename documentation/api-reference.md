# Backend API Reference

All API endpoints are called via `POST /api/method/{method_path}` with JSON body, or `GET /api/method/{method_path}?params`.

---

## Vehicle API — `car_repair_management.api.vehicle`

### `get_vehicle_dashboard(vehicle_name)`
Returns comprehensive vehicle dashboard data.

**Returns**: `{ custodian, drivers, driver_history, cost_of_ownership, service_reminders, open_issues, work_orders, insurance_status, depreciation, linked_asset, ... }`

### `get_vehicles(search, status, vehicle_type, make, fuel_type, limit_start, limit_page_length)`
Paginated vehicle list with KPIs.

**Returns**: `{ kpis: { total, active, in_maintenance, avg_age }, records: [...], total }`

### `create_vehicle(license_plate, make, model, ...)` / `update_vehicle(name, ...)`
CRUD operations. Accepts all standard Vehicle fields plus custom fields.

### `get_cost_of_ownership(vehicle_name)`
6-month cost breakdown: parts, labor, fuel, insurance costs.

### `get_service_reminders(vehicle_name)`
Upcoming service due dates based on odometer and time intervals.

### `get_open_issues(vehicle_name)` / `get_recent_work_orders(vehicle_name)`
Related records for vehicle dashboard.

---

## Telemetry API — `car_repair_management.api.telemetry`

### Central CRUD endpoint

All hardware telemetry integrations should use this endpoint:

`/api/method/car_repair_management.api.telemetry.telemetry`

Use a Frappe API user with one of these roles:

- `Telemetry Integration User`: create/read/list telemetry batches.
- `Telemetry Integration Manager`: create/read/list/update/delete telemetry batches.
- `System Manager`: full access.

Authentication:

```http
Authorization: token API_KEY:API_SECRET
Content-Type: application/json
```

#### `action="create"`

Accepts the provider payload format directly:

```json
{
  "action": "create",
  "payload": {
    "imei": "354002391335211",
    "name": "P0325 AA",
    "group": null,
    "odometer": "185691",
    "engine": "off",
    "status": "Stopped 4 h 38 min 34 s",
    "dt_server": "2026-08-14 07:19:10",
    "dt_tracker": "2026-08-14 07:14:14",
    "lat": "9.006303",
    "lng": "38.89531",
    "altitude": "2408",
    "angle": "267",
    "speed": "0",
    "fuel_1": "0.00",
    "fuel_2": "0.00",
    "fuel_can_level_percent": null,
    "fuel_can_level_value": 560,
    "custom_fields": null
  }
}
```

Vehicle resolution:

1. Preferred: match `payload.imei` to `Vehicle.custom_telematics_imei`.
2. Fallback: match `payload.name` to `Vehicle.license_plate`.
3. Fallback: match `payload.name` to `Vehicle.name`.

Creates one telemetry batch containing:

- `Vehicle Location` when `lat` and `lng` are present.
- `Vehicle Fuel Level` when `fuel_can_level_percent` is present.
- `Vehicle Sensor Data` rows for odometer, engine, status, altitude, angle, speed, fuel_1, fuel_2, fuel_can_level_percent, fuel_can_level_value, group, and any `custom_fields` key/value pairs.

Also updates the Vehicle's latest GPS fields and `last_odometer` when those values are present.

Returns:

```json
{
  "ok": true,
  "action": "create",
  "batch_id": "TLM-XXXXXXXXXXXX",
  "vehicle": "VEHICLE-001",
  "created": {
    "location": "abc123",
    "fuel_level": null,
    "sensor_data": ["..."]
  }
}
```

#### `action="read"`

```json
{ "action": "read", "batch_id": "TLM-XXXXXXXXXXXX" }
```

Returns all `Vehicle Location`, `Vehicle Fuel Level`, and `Vehicle Sensor Data` records for that batch.

#### `action="list"`

```json
{
  "action": "list",
  "vehicle": "VEHICLE-001",
  "imei": "354002391335211",
  "date_from": "2026-08-01 00:00:00",
  "date_to": "2026-08-31 23:59:59",
  "limit_start": 0,
  "limit_page_length": 20
}
```

Returns recent telemetry batches with record counts.

#### `action="update"`

Manager-only. Deletes records in the target batch and recreates the batch from the supplied payload:

```json
{
  "action": "update",
  "batch_id": "TLM-XXXXXXXXXXXX",
  "payload": { "...": "..." }
}
```

#### `action="delete"`

Manager-only:

```json
{ "action": "delete", "batch_id": "TLM-XXXXXXXXXXXX" }
```

### Hardware test configuration endpoint

Use this endpoint to configure external mock hardware APIs and optionally ingest their responses through the central telemetry endpoint:

`/api/method/car_repair_management.api.telemetry.hardware_test_configuration`

Required role:

- `Telemetry Integration Manager` or `System Manager`

#### `action="create"`

```json
{
  "action": "create",
  "data": {
    "configuration_name": "Mellatech Mock Hardware",
    "enabled": 1,
    "endpoint_url": "https://mellatech.et/et/api/api.php?api=user&ver=1.0&cmd=USER_GET_OBJECTS",
    "http_method": "GET",
    "api_key_header": "key",
    "api_key": "API_KEY_VALUE",
    "response_root": "",
    "ingest_on_run": 1,
    "max_records_per_run": 50
  }
}
```

#### `action="list"`

```json
{ "action": "list" }
```

Returns saved mock hardware configurations without exposing API keys.

#### `action="read"`

```json
{ "action": "read", "name": "Mellatech Mock Hardware" }
```

#### `action="update"`

```json
{
  "action": "update",
  "name": "Mellatech Mock Hardware",
  "data": {
    "enabled": 1,
    "max_records_per_run": 100
  }
}
```

#### `action="run"`

```json
{
  "action": "run",
  "name": "Mellatech Mock Hardware"
}
```

The run action:

- Calls the configured external endpoint.
- Sends the API key as the configured header, defaulting to `key`.
- Extracts a payload array/object from `response_root` if set, or from common response keys like `data`, `objects`, `items`, or `results`.
- Ingests each returned hardware payload when `ingest_on_run = 1`.
- Updates last-run status, ingested count, error text, and a response sample on the configuration.

#### `action="delete"`

```json
{ "action": "delete", "name": "Mellatech Mock Hardware" }
```

---

## Repair Order API — `car_repair_management.car_repair_management.doctype.repair_order.repair_order`

### `make_quotation_from_repair_order(name)`
Creates an ERPNext Quotation from RO operations (as service items) + billable parts.

**Returns**: Quotation dict

### `make_material_request_from_repair_order(name)`
Creates a Material Request (type: Material Issue) for all billable parts in the RO.

**Returns**: Material Request dict

### `get_operation_detail(repair_order, operation_idx)`
Returns detailed operation info including linked Task data, Workstation details, comments, related issues, and assigned user info.

**Returns**: `{ operation, task, workstation, comments, issues, assigned_user, repair_order }`

### `update_operation_status(repair_order, operation_idx, status)`
Updates operation status (Open/Working/Pending Review/Completed/Rejected/Cancelled) and syncs to linked Task.

### `assign_operation(repair_order, operation_idx, user)`
Assigns a User to an operation and its linked Task.

### `add_operation_comment(repair_order, operation_idx, content)`
Adds a comment to the operation's linked Task.

### `get_handover_checklist_status(repair_order)`
Returns all checklist items with their linked Vehicle Inspection status.

**Returns**: `{ items: [...], all_passed, total, passed_count }`

### `create_handover_inspection(repair_order, checklist_item_name)`
Creates a Vehicle Inspection linked to a specific handover checklist item.

---

## Employee API — `car_repair_management.api.employee`

### `get_employees(search, department, designation, status, supervisor, limit_start, limit_page_length)`
Paginated list with KPIs: total, active, assigned WOs, avg resolution time.

**Returns**: `{ kpis, records: [...], total }`

### `get_employee_detail(name)`
Employee detail with vehicle assignments (from Vehicle Driver child table + custodian field), repair orders (via Repair Operation Line → User mapping), performance stats, audit trail.

Vehicle assignments include `role` (Driver/Custodian), `assignment_status` (Active/Removed), dates, and vehicle details.

**Returns**: `{ doc, vehicle_assignments: [...], repair_orders: [...], performance, audit_trail }`

---

## Issue API — `car_repair_management.api.issue`

### `get_issues(date_from, date_to, vehicle, source, category, severity, status, assigned_to, search, limit_start, limit_page_length)`
Paginated issues (uses core Frappe Issue DocType with custom fields).

### `get_issue_detail(name)`
Issue detail with comments, audit trail, and computed `available_actions` list (approve/reject/create_work_order/close/mark_duplicate).

### `create_issue(subject, vehicle, severity, category, source, description, assigned_to)`
Creates an issue with role-based workflow:
- **Driver** → workflow_state = "Pending Custodian Approval"
- **Custodian/Other** → workflow_state = "Submitted"
- Works without Employee record (admin users get role "other")

### `search_vehicles(txt, limit_page_length)`
Vehicle search using `ignore_permissions` to bypass User Permission restrictions. Returns `[{ name, license_plate, make, model }]`.

### `search_link_options(doctype, txt, limit_page_length)`
Generic search for Customer or Company records with `ignore_permissions`. Only allows these two doctypes.

### `convert_issue_to_work_order(issue_name, order_for, customer, company)`
Converts issue to Repair Order. Parameters:
- `order_for`: "Customer" or "Company"
- `customer`: required if order_for = "Customer"
- `company`: auto-falls-back to default company if not provided
Maps issue severity → RO priority (Critical→Urgent, High→High, Medium→Normal, Low→Low).

### `approve_issue(issue_name)` / `reject_issue(issue_name, reason)`
Custodian approval workflow actions.

### `close_issue_with_reason(issue_name, reason)` / `mark_issue_duplicate(issue_name, duplicate_of)`
Issue lifecycle management.

### Fault APIs
- `get_faults(vehicle, severity, status, search, ...)` — paginated fault list
- `get_fault_detail(name)` — fault detail with occurrence history
- `create_fault(vehicle, fault_code, title, ...)` / `update_fault(name, ...)`

### Recall APIs
- `get_recalls(search, status, ...)` — paginated recalls
- `get_recall_detail(name)` — recall detail with affected vehicles

---

## Fuel API — `car_repair_management.api.fuel`

### `get_vehicle_quota_status(vehicle, month=None)`
Gets or auto-creates a Vehicle Fuel Quota for the given vehicle and month (defaults to current month).

**Quota Calculation**:
1. `custom_monthly_fuel_quota` if > 0
2. `custom_fuel_capacity_liters × 2`
3. `0`

**Returns**: `{ name, vehicle, quota_month, fuel_capacity_liters, km_per_liter, quota_liters, consumed_liters, remaining_liters, status }`

### `create_refueling_record(vehicle, liters, refuel_date, odometer_reading, cost_per_liter, fuel_station, notes)`
Creates a refueling record. Automatically:
- Gets/creates quota for the refueling month
- Checks if refueling would exceed quota
- Sets `is_over_quota` and `approval_status` accordingly

**Returns**: `{ name, approval_needed, approval_status, over_quota_liters }`

### `approve_refueling(name, role)` / `reject_refueling(name, reason)`
Two-tier approval: `role="dept_head"` → `role="depot_manager"` (for significant over-quota).

### `get_refueling_records(vehicle, month, status, search, limit_start, limit_page_length)`
Paginated refueling records.

### `get_fuel_quotas(vehicle, month, status, search, limit_start, limit_page_length)`
Paginated fuel quotas.

### `update_fuel_quota(name, quota_liters, status)`
Manual quota adjustment.

---

## Inspection API — `car_repair_management.api.inspection`

### `get_inspection_history(date_from, date_to, vehicles, inspector, inspection_type, result, form_template, has_failures, search, limit_start, limit_page_length)`
Paginated inspections with KPIs: total, pass count, fail count, avg score, overdue follow-ups.

### `get_inspection_schedules(...)` / `get_schedule_detail(name)` / `create_inspection_schedule(...)` / `update_inspection_schedule(...)`
CRUD for recurring inspection schedules.

### `get_inspection_forms(...)` / `get_form_detail(name)`
Inspection form template management.

### `get_item_failures(...)` / `get_item_failure_detail(name)`
Inspection failure tracking with severity and follow-up actions.

---

## Expense API — `car_repair_management.api.expense`

### `get_expenses(date_from, date_to, vehicle, category, vendor, work_order, payment_status, has_receipt, search, limit_start, limit_page_length)`
Paginated expenses with KPIs: total amount, count, avg per expense, category breakdown.

### `get_expense_detail(name)` / `create_expense(...)` / `update_expense(...)`
CRUD for vehicle expenses.

---

## Customer API — `car_repair_management.api.customer`

### `get_customers(search, customer_group, customer_type, territory, status, limit_start, limit_page_length)`
Paginated customers with KPIs.

### `get_customer_detail(name)`
Customer detail with repair orders, invoices, revenue stats.

---

## Invoice API — `car_repair_management.api.invoice`

### `get_invoices(date_from, date_to, invoice_type, status, customer, supplier, work_order_linked, amount_min, amount_max, search, limit_start, limit_page_length)`
Combined Sales + Purchase Invoices with KPIs.

### `get_invoice_detail(name, invoice_type)`
Single invoice detail.

---

## Parts API — `car_repair_management.api.parts`

### `get_parts(search, item_group, stock_status, is_stock_item, uom, limit_start, limit_page_length)`
Paginated items with stock levels, reorder status, and KPIs.

### `get_part_detail(name)` / `create_part(...)` / `update_part(...)`
CRUD for items/parts.

---

## Reports API — `car_repair_management.api.reports`

### `get_reports_home()`
Dashboard KPIs: open WOs, overdue inspections, fleet size, monthly expenses, etc.

### `get_report_library()`
Returns 30+ standard reports organized by 9 categories:

| Category | Reports |
|---|---|
| Fleet Overview | Fleet Health Score, Age Distribution, Utilization Overview, Downtime Summary |
| Utilization & Meter | Mileage by Vehicle, Low-Use Vehicles, Fuel vs Mileage Efficiency |
| Work Orders & Repairs | WO Volume Trend, Avg Resolution Time, Backlog by Status, Cost vs Estimate Variance, Repeat Repairs |
| Parts & Inventory | Low Stock, Fast-Moving Items, WO Consumption |
| Inspections | Pass/Fail Trends, Overdue Schedules, Failure Hotspots, Inspector Productivity |
| Issues & Faults | New vs Resolved Trend, Mean Time to Resolve, Top Fault Codes, High Severity Open |
| Financials | Expenses by Category, Cost per Vehicle, Cost per KM, Invoice Aging |
| Customers | Top Customers by Revenue, Outstanding Balance |
| Employees | Work Orders Completed, Avg Completion Time, Workload Distribution |

### `run_report(report_id, filters)`
Execute any standard report by ID.

### `save_report(...)` / `get_saved_reports()` / `delete_saved_report(name)`
User-saved report configuration CRUD.

### `get_scheduled_reports()` / `create_schedule(...)` / `update_schedule(...)` / `delete_schedule(...)` / `run_report_now(name)`
Scheduled report execution system.

---

## Settings API — `car_repair_management.api.settings`

### `get_settings_home()`
System info (Frappe/ERPNext versions, site name), scheduled jobs count, integration status, and 14 settings categories.

### `get_settings_category(category)`
Returns settings data for one of 14 categories: organization, vehicles, work_orders, inspections, issues, expenses, inventory, customers, users, notifications, integrations, data_audit, branding, maintenance.

### `update_settings(category, settings)`
Update settings for a category.

---

## Utility APIs

| Module | Key Methods |
|---|---|
| `api.activity` | Activity timeline for any doctype/document |
| `api.notification` | Notification preference management |
| `api.vehicle_assignments` | Driver/custodian assignment CRUD |
| `api.meter_history` | Odometer reading history tracking |
| `api.expense_history` | Vehicle expense history analysis |
| `api.aging_analysis` | Fleet aging analysis with scores |
| `api.replacement_analysis` | Vehicle replacement scoring algorithm |
