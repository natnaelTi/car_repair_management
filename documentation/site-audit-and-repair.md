# Site Audit, Patch, and Repair Runbook

This runbook explains how to verify and repair a `car_repair_management` installation on any Frappe site.

Use it when installing the app on a new site, after pulling app updates, after restoring a backup, or when the frontend starts showing errors such as:

- DocType does not exist
- Missing field or unknown column
- Error 400 or Error 500 from app APIs
- Page works on one site but fails on another
- Settings, vehicles, telemetry, fuel, inspections, or issues modules load inconsistently

## Why This Exists

The app depends on a mix of standard shipped DocTypes, custom DocTypes, roles, workspace records, and custom fields added to ERPNext DocTypes such as `Vehicle`, `Issue`, `Asset`, `Quotation`, `Sales Order`, and `Sales Invoice`.

If a site was installed before a field existed, was manually repaired, had a failed migration, or received code without running patches, it can drift away from the expected schema. That drift causes scattered runtime failures that are hard to trace from the browser alone.

The app now has a single idempotent setup path:

```text
car_repair_management.install.setup_site
```

It is run by:

- `after_install`
- `after_migrate`
- patch `car_repair_management.patches.v0_0_1.ensure_site_setup`
- optional manual audit repair

Idempotent means it is safe to run repeatedly. It should converge the site to the expected shape without duplicating fields or records.

## Who Should Run These Commands

Run these commands only from the Frappe bench server shell.

Appropriate users:

- System administrator
- Frappe/ERPNext developer
- DevOps engineer
- Technical maintainer with bench access

Do not ask normal Desk users, service advisors, technicians, or workshop operators to run these commands.

## Basic Variables

Replace `<site>` with the real site name:

```bash
SITE=aap.selfmadecs.com
```

Examples:

```bash
SITE=aap.selfmadecs.com
SITE=demo.selfmadecs.com
SITE=staging.example.com
```

All commands below assume you are in the bench root:

```bash
cd /home/smcs/frappe-bench
```

## 1. Confirm the App Is Installed

```bash
bench --site "$SITE" list-apps
```

What it does:

- Lists apps installed on the selected site.
- Confirms whether `car_repair_management` is actually installed on that site.

Expected result:

```text
car_repair_management 0.0.1
```

If the app is not listed, install it first:

```bash
bench --site "$SITE" install-app car_repair_management
```

Then run migrate:

```bash
bench --site "$SITE" migrate
```

## 2. Run the Health Audit

```bash
bench --site "$SITE" execute car_repair_management.api.health.audit_site
```

What it does:

- Checks required DocTypes.
- Checks required roles.
- Checks required custom fields.
- Checks that frontend-facing API modules can be imported.
- Reports the current site name and a clear `ok` status.

Healthy output:

```json
{
  "ok": true,
  "issues": {
    "missing_doctypes": [],
    "missing_roles": [],
    "missing_custom_fields": {},
    "import_errors": {}
  }
}
```

Unhealthy output example:

```json
{
  "ok": false,
  "issues": {
    "missing_doctypes": ["Vehicle Sensor Data"],
    "missing_roles": ["Telemetry Integration User"],
    "missing_custom_fields": {
      "Vehicle": ["custom_status", "custom_drivers"]
    },
    "import_errors": {}
  }
}
```

## 3. Repair a Site

```bash
bench --site "$SITE" execute car_repair_management.api.health.audit_site --kwargs '{"repair": true}'
```

What it does:

- Runs the same audit.
- Before auditing, executes the app setup routine.
- Recreates missing custom fields.
- Recreates missing telemetry DocTypes.
- Recreates missing app roles.
- Reapplies workspace/Kanban/dashboard setup.
- Clears cache after repair.

After repair, run the audit again:

```bash
bench --site "$SITE" execute car_repair_management.api.health.audit_site
```

Expected result:

```json
{"ok": true}
```

## 4. Run Migrations After Code Updates

After pulling or deploying app code, always run:

```bash
bench --site "$SITE" migrate
```

What it does:

- Runs pending patches from `patches.txt`.
- Syncs DocTypes from JSON files.
- Syncs fixtures and customizations.
- Runs `after_migrate`, which calls the app's canonical setup routine.

This is the preferred repair path after deploying new code because it runs Frappe's full migration lifecycle.

## 5. Manually Run the Setup Routine

Usually you should prefer `migrate` or `audit_site --kwargs '{"repair": true}'`.

If you specifically need to run only the app setup routine:

```bash
bench --site "$SITE" execute car_repair_management.install.setup_site
```

What it does:

- Creates app-specific custom DocTypes used for telemetry.
- Ensures roles exist.
- Ensures Vehicle custom fields exist.
- Ensures Issue custom fields exist.
- Ensures fuel quota custom fields exist.
- Ensures telemetry fields exist.
- Ensures required asset master data exists where possible.
- Rebuilds workspace/KPI/Kanban records.

## 6. Clear Cache

Use this after repairing fields or if Desk/frontend metadata appears stale:

```bash
bench --site "$SITE" clear-cache
```

What it does:

- Clears Frappe metadata and site cache.
- Helps the frontend and Desk see newly created fields and DocTypes.

## 7. Smoke Test Important APIs

After repair, run a few high-value API checks.

Settings:

```bash
bench --site "$SITE" execute car_repair_management.api.settings.get_settings_home
```

Issues:

```bash
bench --site "$SITE" execute car_repair_management.api.issue.get_issues
```

Fuel:

```bash
bench --site "$SITE" execute car_repair_management.api.fuel.get_fuel_quotas
```

Vehicle assignments:

```bash
bench --site "$SITE" execute car_repair_management.api.vehicle_assignments.get_vehicle_assignments --kwargs '{"range_start":"2026-01-01","range_end":"2026-12-31"}'
```

Telemetry list:

```bash
bench --site "$SITE" execute car_repair_management.api.telemetry.telemetry --kwargs '{"action":"list","limit_page_length":1}'
```

Vehicle dashboard:

```bash
bench --site "$SITE" execute car_repair_management.api.vehicle.get_vehicle_dashboard --kwargs '{"vehicle_name":"P0325 AA"}'
```

Use a real vehicle name on sites that do not have the mock hardware demo vehicle.

## 8. Build Frontend Assets

If frontend files changed, build assets:

```bash
cd apps/car_repair_management/frontend
npm run build
cd /home/smcs/frappe-bench
bench --site "$SITE" clear-cache
```

What it does:

- Builds the Vue frontend bundle.
- Writes assets into the app public frontend directory.
- Makes the latest frontend available through the Frappe site.

## 9. Recommended New Site Install Flow

For a new site:

```bash
cd /home/smcs/frappe-bench
bench --site "$SITE" install-app car_repair_management
bench --site "$SITE" migrate
bench --site "$SITE" execute car_repair_management.api.health.audit_site
bench --site "$SITE" clear-cache
```

If the audit is not clean:

```bash
bench --site "$SITE" execute car_repair_management.api.health.audit_site --kwargs '{"repair": true}'
bench --site "$SITE" execute car_repair_management.api.health.audit_site
```

## 10. Recommended Deployment Flow

For an existing site after pulling new code:

```bash
cd /home/smcs/frappe-bench
bench --site "$SITE" migrate
bench --site "$SITE" execute car_repair_management.api.health.audit_site
bench --site "$SITE" clear-cache
```

If frontend code changed:

```bash
cd apps/car_repair_management/frontend
npm run build
cd /home/smcs/frappe-bench
bench --site "$SITE" clear-cache
```

## 11. What Not To Do

Avoid fixing production sites by manually adding random Custom Fields in Desk unless you also add the field to the app setup code.

Avoid relying on one working site as proof that the app installs cleanly everywhere. A working site may contain historical manual fixes that a fresh site does not have.

Avoid skipping `bench --site "$SITE" migrate` after pulling changes. Patches and `after_migrate` are part of the supported installation contract.

Avoid running repair commands as a substitute for backups. Before major deployment work, take a normal site backup.

## 12. Troubleshooting Guide

If `audit_site` says a DocType is missing:

- Run `bench --site "$SITE" migrate`.
- Run `audit_site --kwargs '{"repair": true}'`.
- Check whether the app is installed with `list-apps`.

If `audit_site` says custom fields are missing:

- Run `audit_site --kwargs '{"repair": true}'`.
- Run `bench --site "$SITE" clear-cache`.
- Re-run the audit.

If API modules have import errors:

- Read the import error in the audit output.
- Run `python -m compileall -q car_repair_management` from `apps/car_repair_management`.
- Fix the Python import or syntax issue before migrating production.

If the browser still shows errors after a clean audit:

- Clear site cache.
- Hard refresh the browser.
- Rebuild frontend assets if frontend code changed.
- Check Frappe Error Log for the specific failing API method.

## 13. Source Files

Primary setup files:

- `car_repair_management/install.py`
- `car_repair_management/hooks.py`
- `car_repair_management/patches.txt`
- `car_repair_management/patches/v0_0_1/ensure_site_setup.py`
- `car_repair_management/api/health.py`

Manual setup helpers folded into the canonical setup:

- `car_repair_management/api/setup.py`
- `car_repair_management/api/setup_fuel_fields.py`
- `car_repair_management/api/setup_issue_fields.py`
