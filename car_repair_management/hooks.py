app_name = "car_repair_management"
app_title = "Car Repair Management"
app_publisher = "Selfmade Cloud Solutions"
app_description = "Car Repair Management app compatible with ERPNext v15."
app_email = "support@selfmadecs.com"
app_license = "mit"

required_apps = ["erpnext"]

# Include client scripts
doctype_js = {
    "Repair Order": "public/js/repair_order.js",
    "Task": "public/js/task.js",
    "Service Template": "public/js/service_template.js",
    "Quotation": "public/js/quotation.js",
    "Sales Order": "public/js/sales_order.js",
    "Vehicle": "public/js/vehicle.js",
}

# Document Events for Repair Order
# Methods are defined in the controller

doc_events = {
    "Repair Order": {
        "validate": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.on_validate",
        "on_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.on_submit",
        "before_update_after_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.before_update_after_submit",
        "before_save": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.before_save",
        "after_save": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.after_save",
    },
    "Timesheet": {
        "on_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_timesheet",
        "on_cancel": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_timesheet",
    },
    "Purchase Invoice": {
        "on_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_purchase_invoice",
        "on_cancel": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_purchase_invoice",
    },
    "Quotation": {
        "on_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_quotation",
        "on_cancel": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_quotation",
    },
    "Sales Order": {
        "on_submit": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_sales_order",
        "on_cancel": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_sales_order",
    },
    "Sales Invoice": {
        "on_submit": [
            "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_sales_invoice",
            "car_repair_management.car_repair_management.doctype.repair_order.auto_status.update_ro_status_from_sales_invoice",
        ],
        "on_cancel": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.update_ro_from_sales_invoice",
    },
    "Task": {
        "on_update": "car_repair_management.car_repair_management.doctype.repair_order.auto_status.update_ro_status_from_task",
    },
}

# Whitelisted methods exposure (explicit mapping, though not required)
override_whitelisted_methods = {
    "car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_quotation_from_repair_order": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_quotation_from_repair_order",
    "car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_material_request_from_repair_order": "car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_material_request_from_repair_order",
}

# Scheduler
scheduler_events = {
    "daily": [
        "car_repair_management.tasks.update_job_costing_snapshots"
    ]
}

# Installation hooks
# Run custom field creation and dashboard links
after_install = "car_repair_management.install.create_customizations"

# Fixtures: export workspace, charts, number cards, reports under our module
fixtures = [
    {"doctype": "Workspace", "filters": [["module", "=", "Car Repair Management"]]},
    {"doctype": "Dashboard Chart", "filters": [["module", "=", "Car Repair Management"], ["is_standard", "=", 0]]},
    {"doctype": "Number Card", "filters": [["module", "=", "Car Repair Management"]]},
    {"doctype": "Report", "filters": [["module", "=", "Car Repair Management"]]},
    {"doctype": "Custom Field", "filters": [["module", "=", "Car Repair Management"]]},
    {"doctype": "Module Onboarding", "filters": [["module", "=", "Car Repair Management"]]},
]

# Override dashboard for Vehicle doctype
override_doctype_dashboards = {
    "Vehicle": "car_repair_management.overrides.vehicle_dashboard.get_data"
}

