import importlib

import frappe


EXPECTED_DOCTYPES = [
    "Repair Order",
    "Repair Operation Line",
    "Repair Parts Plan",
    "Repair Checklist",
    "Repair Checklist Item",
    "Repair Checklist Response",
    "Service Template",
    "Service Template Operation",
    "Service Template Part",
    "Service Template Checklist Item",
    "SLA Template",
    "Job Costing",
    "Vehicle Expense",
    "Vehicle Fuel Quota",
    "Vehicle Refueling Record",
    "Vehicle Fault",
    "Vehicle Recall",
    "Vehicle Inspection",
    "Inspection Schedule",
    "Inspection Form Template",
    "Inspection Form Item",
    "Inspection Item Failure",
    "Workshop Saved Report",
    "Workshop Report Schedule",
    "Hardware Test Configuration",
    "Vehicle Location",
    "Vehicle Fuel Level",
    "Vehicle Sensor Data",
]

EXPECTED_ROLES = [
    "Fleet Manager",
    "Maintenance Manager",
    "Maintenance User",
    "Telemetry Integration User",
    "Telemetry Integration Manager",
]

EXPECTED_CUSTOM_FIELDS = {
    "Vehicle": [
        "custom_status",
        "custom_vehicle_type",
        "custom_image",
        "custom_custodian",
        "custom_custodian_name",
        "custom_drivers",
        "custom_fuel_capacity_liters",
        "custom_km_per_liter",
        "custom_monthly_fuel_quota",
        "custom_telematics_imei",
        "custom_last_known_latitude",
        "custom_last_known_longitude",
        "custom_last_location_update",
        "custom_fuel_level",
        "custom_engine_hours",
    ],
    "Issue": [
        "custom_vehicle",
        "custom_category",
        "custom_severity",
        "custom_source",
        "custom_assigned_to",
        "custom_linked_work_order",
        "custom_linked_inspection",
        "custom_linked_fault",
        "custom_resolution_notes",
        "custom_workflow_state",
        "custom_requested_by_employee",
        "custom_approved_by",
        "custom_approved_on",
        "custom_rejected_by",
        "custom_rejected_on",
        "custom_rejection_reason",
    ],
    "Vehicle Location": [
        "telemetry_batch_id",
        "source_imei",
        "device_name",
        "altitude",
    ],
    "Vehicle Fuel Level": [
        "telemetry_batch_id",
        "source_imei",
        "device_name",
    ],
    "Vehicle Sensor Data": [
        "telemetry_batch_id",
        "source_imei",
        "device_name",
    ],
}

EXPECTED_METHOD_MODULES = [
    "car_repair_management.api.activity",
    "car_repair_management.api.aging_analysis",
    "car_repair_management.api.customer",
    "car_repair_management.api.employee",
    "car_repair_management.api.expense",
    "car_repair_management.api.expense_history",
    "car_repair_management.api.fuel",
    "car_repair_management.api.inspection",
    "car_repair_management.api.invoice",
    "car_repair_management.api.issue",
    "car_repair_management.api.meter_history",
    "car_repair_management.api.notification",
    "car_repair_management.api.parts",
    "car_repair_management.api.replacement_analysis",
    "car_repair_management.api.reports",
    "car_repair_management.api.settings",
    "car_repair_management.api.telemetry",
    "car_repair_management.api.vehicle",
    "car_repair_management.api.vehicle_assignments",
]


@frappe.whitelist()
def audit_site(repair=False):
    """Return the install health of the current site; optionally self-repair."""
    if str(repair).lower() in ("1", "true", "yes"):
        from car_repair_management.install import setup_site

        setup_site()
        frappe.clear_cache()

    missing_doctypes = [
        doctype for doctype in EXPECTED_DOCTYPES if not frappe.db.exists("DocType", doctype)
    ]
    missing_roles = [role for role in EXPECTED_ROLES if not frappe.db.exists("Role", role)]
    missing_custom_fields = _get_missing_custom_fields()
    import_errors = _get_import_errors()

    issues = {
        "missing_doctypes": missing_doctypes,
        "missing_roles": missing_roles,
        "missing_custom_fields": missing_custom_fields,
        "import_errors": import_errors,
    }
    ok = not any(issues.values())

    return {
        "ok": ok,
        "site": frappe.local.site,
        "issues": issues,
        "summary": {
            "missing_doctypes": len(missing_doctypes),
            "missing_roles": len(missing_roles),
            "missing_custom_field_groups": len(missing_custom_fields),
            "import_errors": len(import_errors),
        },
    }


def _get_missing_custom_fields():
    missing = {}
    for doctype, fields in EXPECTED_CUSTOM_FIELDS.items():
        if not frappe.db.exists("DocType", doctype):
            missing[doctype] = fields
            continue

        missing_fields = [fieldname for fieldname in fields if not _has_meta_field(doctype, fieldname)]
        if missing_fields:
            missing[doctype] = missing_fields
    return missing


def _has_meta_field(doctype, fieldname):
    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return False
    return meta.has_field(fieldname) or fieldname in ("name", "owner", "creation", "modified")


def _get_import_errors():
    errors = {}
    for module_name in EXPECTED_METHOD_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            errors[module_name] = str(exc)
    return errors
