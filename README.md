# Car Repair Management System (Frappe/ERPNext)

A production-ready workshop management solution built on Frappe/ERPNext v15. It adds a Repair Order workflow that leverages ERPNext Projects, Tasks, Timesheets, Stock/Buying, and Selling to manage automotive service jobs end-to-end, with KPIs, dashboards, and reports for daily operations.

- Core app package: `car_repair_management`
- Minimum versions: Frappe 15.x, ERPNext 15.x
- Target audience: Service Advisors, Workshop Managers, Technicians, Stores/Inventory, Accounts, and Executives.

---

## Table of Contents

1. Overview
2. Installation & Setup
3. Data Model & Extensions
4. Workspace (Workshop)
5. Workflow & Daily Operations
6. Customer-Facing Flows (Portal)
7. Reporting & Analytics
8. Roles & Permissions
9. Configuration & Admin Notes
10. Troubleshooting & FAQs
11. Developer Notes (structure, hooks, tests)

---

## 1) Overview

The system centers around a custom Repair Order (RO):

- A Repair Order records the vehicle intake, problem summary, planned operations (Tasks), and planned parts.
- On submit, the app creates a Project and Tasks, enabling technicians to log work via Timesheets.
- Parts planning drives Material Requests and Stock transactions while tagging all consumption to the RO.
- Commercials flow via Quotation → Sales Order → Sales Invoice, linked to the RO + Vehicle.
- The Workshop workspace provides KPIs, WIP controls (Kanban/Gantt/Calendar), team-specific lists, and reports.

---

## 2) Installation & Setup

### Prerequisites

- Frappe Bench working environment
- Installed apps: `frappe`, `erpnext`
- Node ≥ 18 installed for asset builds

### Install the app

```bash
# From bench root
bench pip install -e apps/car_repair_management
bench --site <your_site> install-app car_repair_management
bench --site <your_site> migrate
bench build --app car_repair_management
```

The installer adds custom fields and seeds KPIs/charts/workspace content.

### Post-install (idempotent) seeding

If you need to recreate workspace artifacts safely:

```bash
bench --site <your_site> execute car_repair_management.install._create_kpis_and_charts
bench --site <your_site> execute car_repair_management.install._ensure_kanban_board
bench --site <your_site> execute car_repair_management.install._create_workspace
```

If after installing you updated the app and need to rewire shortcuts:

```bash
bench --site <your_site> execute car_repair_management.install._patch_workspace_shortcuts
```

### Multi-site notes

- Install the app on each site where you want the features.
- Fixtures (workspace, charts, number cards, reports) are versioned and installed with the app.

---

## 3) Data Model & Extensions

### Custom DocTypes

- Repair Order (parent)
  - Key fields: `customer`, `vehicle`, `status`, `priority`, `sla_delivery_by`, `project`, commercial links
  - Child tables:
    - Operations (Repair Operation Line): operation name, planned minutes, workstation, QC flag, Task link
    - Parts Plan (Repair Parts Plan): item, qty, UOM, billable vs FoC
    - Handover Checklist (Repair Checklist Response)
    - Customer Updates (Customer Update)
  - Computed fields (read-only previews): parts_cost, labor_cost, total_job_cost, invoiced_amount, etc.

- Service Template (parent): default operations, parts, and checklist for common services.
- Repair Checklist (parent) + items
- Repair Checklist Response (child)
- Job Costing (parent): parts_cost, labor_cost, other_charges, total_job_cost, margin snapshot

### Server logic (highlights)

- Validate: billable/FoC mutual exclusivity; SLA sanity checks.
- On Submit: creates Project and Tasks for operations; applies Service Template defaults.
- Whitelisted actions:
  - Make Quotation from RO (labor lines + billable parts)
  - Make Material Request from RO (billable parts)

### ERPNext core extensions (Custom Fields)

- Vehicle: variant, year, transmission, odometer_at_last_service, KPI rollups (read-only)
- Sales Doc Items (Quotation/SO/SI): hidden links to Repair Order and Vehicle
- Project, Task, Timesheet: hidden link to Repair Order
- Stock Entry: hidden link to Repair Order

Reference implementation (developers):
- `apps/car_repair_management/car_repair_management/hooks.py`
- `apps/car_repair_management/car_repair_management/install.py`
- `apps/car_repair_management/car_repair_management/doctype/...`

---

## 4) Workspace: “Workshop”

Open Desk → Workspace → Workshop. Sections include:

- Header KPIs (Number Cards): ROs Today, In Progress, Awaiting Parts, Ready for Handover, Due Today, Overdue
- Quick Actions: New Repair Order, Open WIP Kanban, Job Profitability Report, Parts Consumption
- Work In Progress: WIP Kanban (status board), Project Gantt, Technician Calendar
- My Work: My Assigned ROs, My Tasks, Ready for Handover, Waiting for Parts, Approvals Needed
- Reports & Analytics: Job Profitability, Parts Consumption (Billable vs FoC), Technician Utilization & Efficiency, WIP Aging, Repeat Repairs/Warranty
- Masters & Setup: Vehicle, Service Template, Repair Checklist, Item, Workstation, Activity Type, Employee, Notification
- Stores & Inventory: Material Requests (Issue), Stock Entries (Issue), Stock Ledger, Reorder Report
- Commercials: Quotations, Sales Orders, Sales Invoices, Outstanding Invoices
- Admin & Utilities: Job Costing, Error Log, Scheduler Log

Notes:
- Some links use list routes for reliability across sites and avoid overly long URLs. Saved Views can be configured later for more specific defaults (e.g., “assigned to me”).

---

## 5) Workflow & Daily Operations

### 5.1 Intake & Creating a Repair Order

1. Go to Workshop → Quick Actions → “New Repair Order”.
2. Fill in:
   - Customer and Vehicle (required)
   - Problem Summary/Details
   - Priority, SLAs if applicable
   - Optional: pick a Service Template (e.g., Oil Change, Inspection) to preload tasks/parts
3. Add Operations (tasks you plan to perform) with planned minutes, workstation, and QC flag.
4. Add Parts Plan (planned items/qty, flag as Billable or FoC).
5. Save the RO. When ready to start work, Submit it.

Effects on Submit:
- A Project is created and linked to the RO.
- Tasks are created (one per operation) and linked to the Project & RO.

### 5.2 Scheduling & Execution

- WIP Kanban: Move ROs across statuses (Scheduled → In Progress → Awaiting Parts → Ready for Handover).
- Project Gantt / Technician Calendar: Visualize work distribution.
- Task form: Assign to a technician; technicians can log work via Timesheets.

### 5.3 Parts & Stores

- From the RO, create a Material Request (Issue) for billable parts.
- Stores process MR → Stock Entry (Material Issue), linking back to the RO automatically.

### 5.4 Commercials

- From the RO, create Quotation (labor lines + billable parts). Get customer approval.
- If needed, convert Quotation → Sales Order → Sales Invoice.
- The RO can link Quotation/SO/SI and Vehicle; profits/costs reflect in reports.

### 5.5 Handover & Closure

- RO status “Ready for Handover”: QC tasks must be completed.
- Deliver vehicle, record final notes, and set status.
- Only close the RO if invoices are fully settled.

---

## 6) Customer-Facing Flows (Portal)

Planned/Configurable (patterns supported by Frappe):
- Intake Web Form → creates Draft RO
- Repair Status page → Progress, SLA, costs preview, customer updates
- Feedback → score + notes onto the RO

These can be added as Web Forms/Pages and linked into the app as needed.

---

## 7) Reporting & Analytics

All reports live under the module “Car Repair Management” and in the Workshop workspace.

- Job Profitability Report
  - Source: Repair Orders and Job Costing
  - Columns: RO, Customer, Vehicle, Parts Cost, Labor Cost, Other, Total Cost, Invoiced, Gross Margin

- Parts Consumption: Billable vs FoC
  - Source: Stock Entries + RO Parts Plan (billable flag)
  - Pie chart showing Billable vs FoC cost split

- Technician Utilization and Efficiency
  - Source: Timesheets (+ capacity approximation)
  - Columns: Employee, Planned Hours (approx), Logged Hours, Utilization %, Efficiency %

- WIP Aging
  - Source: Repair Orders (days in current state approximated by last modified)
  - Histogram: Days in Status buckets

- Repeat Repairs and Warranty Returns
  - Source: ROs per Vehicle within X days
  - Identify returns (first handover vs return date); count by vehicle

---

## 8) Roles & Permissions

Recommended roles:
- Service Advisor: intake, submit RO, create quotations
- Workshop Manager: schedule, assign, approve parts, close RO
- Technician: view tasks assigned, log timesheets
- Stores: process Material Requests & Stock Entries
- Accounts: manage invoices/payments
- Executives: KPIs, WIP, profitability

Permissions use ERPNext defaults and Frappe DocType permissions; hide advanced Admin/Developer pages from non-admin users.

---

## 9) Configuration & Admin Notes

- KPIs, Charts, Workspace are seeded by the installer.
- To re-run seeding safely:
  - `bench --site <site> execute car_repair_management.install._create_kpis_and_charts`
  - `bench --site <site> execute car_repair_management.install._ensure_kanban_board`
  - `bench --site <site> execute car_repair_management.install._create_workspace`
- If you change report names (to avoid special characters), update workspace shortcuts accordingly (use `_patch_workspace_shortcuts`).

---

## 10) Troubleshooting & FAQs

- “Internal Server Error after installing”: Restart supervisor/web workers so Python path reflects the new app.
- “Workspace blank despite shortcuts”: Ensure the workspace `content` has blocks. Re-run the workspace creation function.
- “Kanban asks to create a new board”: Use the provided shortcut (or open: `/app/List/Repair Order/Kanban/Repair Order by Status`).
- “Report ‘ModuleNotFoundError’ with colon/& in name”: Use reports without special characters in names and update workspace shortcuts.
- “Technician Calendar shows all tasks”: Edit the workspace shortcut to include your preferred department or owner filters; or create a Saved View and link to it.

---

## 11) Developer Notes

Project layout (key paths):
- App hooks: `apps/car_repair_management/car_repair_management/hooks.py`
- Install/seeding: `apps/car_repair_management/car_repair_management/install.py`
- Server/Client scripts:
  - RO Controller: `apps/car_repair_management/car_repair_management/car_repair_management/doctype/repair_order/repair_order.py`
  - Client scripts: `apps/car_repair_management/car_repair_management/public/js/repair_order.js`, `.../public/js/task.js`
- Reports (examples):
  - `.../report/job_profitability_report/`
  - `.../report/parts_consumption_billable_vs_foc/`
  - `.../report/technician_utilization_and_efficiency/`
  - `.../report/wip_aging/`
  - `.../report/repeat_repairs_and_warranty_returns/`

### Commands

- Build assets (app only):

```bash
bench build --app car_repair_management
```

- Migrate site:

```bash
bench --site <your_site> migrate
```

- Run tests (app):

```bash
bench --site <your_site> run-tests --app car_repair_management
```

### Notes on conventions

- Avoid special characters in report names and doctype identifiers that become part of import paths.
- Keep workspace links short (Workspace Shortcut URL max length applies); prefer list routes or Saved Views.

---

## Changelog (highlights)

- v0.0.1: Initial release
  - Repair Order flow with Projects/Tasks/Timesheets
  - Parts planning and Material Requests
  - Quotation generation from RO
  - Workshop workspace, KPIs, charts
  - Core reports (Profitability, WIP, Technician Utilization, Parts Consumption, Repeat Repairs)
