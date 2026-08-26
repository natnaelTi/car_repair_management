import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _ensure_asset_master_data():
    """Ensure Asset Category and fixed-asset Item exist for vehicle asset creation."""
    # Asset Category: Vehicles
    if not frappe.db.exists("Asset Category", "Vehicles"):
        try:
            company = frappe.defaults.get_global_default("company")
            fixed_asset_acct = frappe.db.get_value("Account", {
                "company": company, "account_name": "Capital Equipments", "is_group": 0
            }, "name")
            if not fixed_asset_acct:
                fixed_asset_acct = frappe.db.get_value("Account", {
                    "company": company, "parent_account": ["like", "%Fixed Asset%"], "is_group": 0
                }, "name")
            depreciation_acct = frappe.db.get_value("Account", {
                "company": company, "account_name": "Depreciation", "is_group": 0
            }, "name")
            accum_dep_acct = frappe.db.get_value("Account", {
                "company": company, "account_name": "Accumulated Depreciation", "is_group": 0
            }, "name")

            cat_data = {
                "doctype": "Asset Category",
                "asset_category_name": "Vehicles",
                "enable_cwip_accounting": 0,
            }
            if fixed_asset_acct and depreciation_acct and accum_dep_acct:
                cat_data["accounts"] = [{
                    "company_name": company,
                    "fixed_asset_account": fixed_asset_acct,
                    "accumulated_depreciation_account": accum_dep_acct,
                    "depreciation_expense_account": depreciation_acct,
                }]
            cat = frappe.get_doc(cat_data)
            cat.insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Car Repair Management: Asset Category")

    # Fixed-asset Item: VEHICLE-ASSET
    if not frappe.db.exists("Item", "VEHICLE-ASSET"):
        try:
            item_group = "All Item Groups"
            if frappe.db.exists("Item Group", "Fixed Asset"):
                item_group = "Fixed Asset"
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": "VEHICLE-ASSET",
                "item_name": "Vehicle (Fixed Asset)",
                "item_group": item_group,
                "is_fixed_asset": 1,
                "is_stock_item": 0,
                "asset_category": "Vehicles",
            })
            item.insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Car Repair Management: Vehicle Asset Item")


def after_install():
    create_doctypes()
    setup_telemetry_integration()
    _ensure_asset_master_data()
    create_customizations()
    # Seed demo data on fresh install
    try:
        from car_repair_management.demo_data import seed_demo_data
        seed_demo_data()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Car Repair Management: Demo data seeding")



def create_doctypes():
    def create_custom_doctype(name, fields, module="Car Repair Management"):
        if frappe.db.exists("DocType", name):
            return
        
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": name,
            "module": module,
            "custom": 1,
            "autoname": "hash",
            "naming_rule": "Random",
            "fields": fields,
            "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]
        })
        doc.insert(ignore_permissions=True)

    # 1. Vehicle Location
    create_custom_doctype("Vehicle Location", [
        {"fieldname": "vehicle", "label": "Vehicle", "fieldtype": "Link", "options": "Vehicle", "reqd": 1, "in_list_view": 1},
        {"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
        {"fieldname": "latitude", "label": "Latitude", "fieldtype": "Float"},
        {"fieldname": "longitude", "label": "Longitude", "fieldtype": "Float"},
        {"fieldname": "direction", "label": "Direction (Bearing)", "fieldtype": "Float"},
        {"fieldname": "speed", "label": "Speed", "fieldtype": "Float"}
    ])

    # 2. Vehicle Fuel Level
    create_custom_doctype("Vehicle Fuel Level", [
        {"fieldname": "vehicle", "label": "Vehicle", "fieldtype": "Link", "options": "Vehicle", "reqd": 1, "in_list_view": 1},
        {"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
        {"fieldname": "fuel_level", "label": "Fuel Level (%)", "fieldtype": "Percent", "reqd": 1, "in_list_view": 1},
        {"fieldname": "location", "label": "Location", "fieldtype": "Link", "options": "Vehicle Location"}
    ])

    # 3. Vehicle Sensor Data
    create_custom_doctype("Vehicle Sensor Data", [
        {"fieldname": "vehicle", "label": "Vehicle", "fieldtype": "Link", "options": "Vehicle", "reqd": 1, "in_list_view": 1},
        {"fieldname": "timestamp", "label": "Timestamp", "fieldtype": "Datetime", "reqd": 1, "in_list_view": 1},
        {"fieldname": "sensor_type", "label": "Sensor Type", "fieldtype": "Data", "reqd": 1, "in_list_view": 1},
        {"fieldname": "value", "label": "Value", "fieldtype": "Data", "reqd": 1},
        {"fieldname": "unit", "label": "Unit", "fieldtype": "Data"}
    ])


def _ensure_telemetry_roles():
    """Create narrow roles for hardware telemetry API users."""
    roles = [
        {
            "role_name": "Telemetry Integration User",
            "desk_access": 0,
        },
        {
            "role_name": "Telemetry Integration Manager",
            "desk_access": 1,
        },
    ]
    for role in roles:
        if not frappe.db.exists("Role", role["role_name"]):
            frappe.get_doc({"doctype": "Role", **role}).insert(ignore_permissions=True)


def setup_telemetry_integration():
    """Ensure hardware telemetry API roles and traceability fields exist."""
    create_doctypes()
    _ensure_telemetry_roles()
    create_custom_fields(_get_telemetry_custom_fields(), ignore_validate=True)


def _get_telemetry_custom_fields():
    return {
        "Vehicle": [
            dict(fieldname="custom_telematics_imei", label="Telematics IMEI", fieldtype="Data", insert_after="license_plate", unique=1),
            dict(fieldname="custom_last_known_latitude", label="Last Known Latitude", fieldtype="Float", insert_after="custom_telematics_imei", read_only=1),
            dict(fieldname="custom_last_known_longitude", label="Last Known Longitude", fieldtype="Float", insert_after="custom_last_known_latitude", read_only=1),
            dict(fieldname="custom_last_location_update", label="Last Location Update", fieldtype="Datetime", insert_after="custom_last_known_longitude", read_only=1),
            dict(fieldname="custom_fuel_level", label="Latest Fuel Level (%)", fieldtype="Percent", insert_after="custom_last_location_update", read_only=1),
            dict(fieldname="custom_engine_hours", label="Engine Hours", fieldtype="Float", insert_after="custom_fuel_level", read_only=1),
        ],
        "Vehicle Location": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="speed", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
            dict(fieldname="altitude", label="Altitude", fieldtype="Float", insert_after="device_name", read_only=1),
        ],
        "Vehicle Fuel Level": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="location", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
        ],
        "Vehicle Sensor Data": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="unit", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
        ],
    }


def create_customizations():
    # Custom Fields definitions
    custom_fields = {
        "Vehicle": [
            dict(fieldname="custom_telematics_imei", label="Telematics IMEI", fieldtype="Data", insert_after="license_plate", unique=1),
            dict(fieldname="custom_last_known_latitude", label="Last Known Latitude", fieldtype="Float", insert_after="custom_telematics_imei", read_only=1),
            dict(fieldname="custom_last_known_longitude", label="Last Known Longitude", fieldtype="Float", insert_after="custom_last_known_latitude", read_only=1),
            dict(fieldname="custom_last_location_update", label="Last Location Update", fieldtype="Datetime", insert_after="custom_last_known_longitude", read_only=1),
            dict(fieldname="custom_fuel_level", label="Latest Fuel Level (%)", fieldtype="Percent", insert_after="custom_last_location_update", read_only=1),
            dict(fieldname="custom_engine_hours", label="Engine Hours", fieldtype="Float", insert_after="custom_fuel_level", read_only=1),
            dict(fieldname="variant", label="Variant", fieldtype="Data", insert_after="model"),
            dict(fieldname="year", label="Year", fieldtype="Int", insert_after="variant"),
            dict(fieldname="transmission", label="Transmission", fieldtype="Select", options="Manual\nAutomatic\nCVT", insert_after="year"),
            dict(fieldname="acquisition_cost", label="Acquisition Cost", fieldtype="Currency", insert_after="transmission"),
            dict(fieldname="engine_type", label="Engine Type", fieldtype="Data", insert_after="acquisition_date"),
            dict(fieldname="engine_capacity", label="Engine Capacity (cc)", fieldtype="Int", insert_after="engine_type"),
            dict(fieldname="cylinders", label="Cylinders", fieldtype="Int", insert_after="engine_capacity"),
            dict(fieldname="drivetrain", label="Drivetrain", fieldtype="Data", insert_after="cylinders"),
            dict(fieldname="engine_number", label="Engine Number", fieldtype="Data", insert_after="drivetrain"),
            dict(fieldname="vehicle_type", label="Vehicle Type", fieldtype="Data", insert_after="engine_number"),
            dict(fieldname="country_of_origin", label="Country of Origin", fieldtype="Data", insert_after="vehicle_type"),
            dict(fieldname="fuel_tank_capacity", label="Fuel Tank Capacity", fieldtype="Data", insert_after="country_of_origin"),
            dict(fieldname="battery_capacity", label="Battery Capacity", fieldtype="Data", insert_after="fuel_tank_capacity"),
            dict(fieldname="seating_capacity", label="Seating Capacity", fieldtype="Int", insert_after="battery_capacity"),
            dict(fieldname="payload_capacity", label="Payload Capacity", fieldtype="Data", insert_after="seating_capacity"),
            dict(fieldname="towing_capacity", label="Towing Capacity", fieldtype="Data", insert_after="payload_capacity"),
            dict(fieldname="gross_vehicle_weight", label="Gross Vehicle Weight (GVW)", fieldtype="Data", insert_after="towing_capacity"),
            dict(fieldname="ownership_type", label="Ownership Type", fieldtype="Data", insert_after="gross_vehicle_weight"),
            dict(fieldname="registration_authority", label="Registration Authority", fieldtype="Data", insert_after="ownership_type"),
            dict(fieldname="registration_expiry", label="Registration Expiry", fieldtype="Date", insert_after="registration_authority"),
            dict(fieldname="insurance_policy", label="Insurance Policy Ref", fieldtype="Data", insert_after="registration_expiry"),
            dict(fieldname="insurance_expiry", label="Insurance Expiry", fieldtype="Date", insert_after="insurance_policy"),
            dict(fieldname="insured_value", label="Insured Value", fieldtype="Currency", insert_after="insurance_expiry"),
            dict(fieldname="insurance_start_date", label="Insurance Start Date", fieldtype="Date", insert_after="insured_value"),
            dict(fieldname="comprehensive_insurance", label="Comprehensive Insurance", fieldtype="Data", insert_after="insurance_start_date"),
            dict(fieldname="odometer_at_last_service", label="Odometer at Last Service", fieldtype="Int", insert_after="comprehensive_insurance"),
            dict(fieldname="last_service_date", label="Last Service Date", fieldtype="Date", insert_after="odometer_at_last_service", read_only=1),
            dict(fieldname="next_service_due_date", label="Next Service Due Date", fieldtype="Date", insert_after="last_service_date", read_only=1),
            dict(fieldname="jobs_count", label="Jobs Count", fieldtype="Int", insert_after="next_service_due_date", read_only=1),
            dict(fieldname="repair_cost_to_date", label="Repair Cost To Date", fieldtype="Currency", insert_after="jobs_count", read_only=1),
            dict(fieldname="revenue_billed_to_date", label="Revenue Billed To Date", fieldtype="Currency", insert_after="repair_cost_to_date", read_only=1),
            dict(fieldname="erpnext_asset", label="Linked Asset", fieldtype="Link", options="Asset", insert_after="revenue_billed_to_date", read_only=1),
            dict(fieldname="depreciation_method", label="Depreciation Method", fieldtype="Select", options="\nStraight Line\nDouble Declining Balance\nWritten Down Value", insert_after="erpnext_asset"),
            dict(fieldname="depreciation_months", label="Useful Life (Months)", fieldtype="Int", insert_after="depreciation_method", default="60"),
        ],
        "Asset": [
            dict(fieldname="vehicle", label="Vehicle", fieldtype="Link", options="Vehicle", insert_after="asset_name"),
        ],
        "Quotation": [
            dict(fieldname="custom_repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="customer", print_hide=1),
        ],
        "Sales Order": [
            dict(fieldname="custom_repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="customer", print_hide=1),
        ],
        "Sales Invoice": [
            dict(fieldname="custom_repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="customer", print_hide=1),
        ],
        "Sales Invoice Item": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="item_code", hidden=1),
            dict(fieldname="vehicle", label="Vehicle", fieldtype="Link", options="Vehicle", insert_after="repair_order", hidden=1),
        ],
        "Sales Order Item": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="item_code", hidden=1),
            dict(fieldname="vehicle", label="Vehicle", fieldtype="Link", options="Vehicle", insert_after="repair_order", hidden=1),
        ],
        "Quotation Item": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="item_code", hidden=1),
            dict(fieldname="vehicle", label="Vehicle", fieldtype="Link", options="Vehicle", insert_after="repair_order", hidden=1),
        ],
        "Repair Order": [
            dict(fieldname="entry_datetime", label="Entry Date/Time", fieldtype="Datetime", insert_after="intake_channel"),
            dict(fieldname="entry_datetime_editable", label="Edit Entry Date/Time", fieldtype="Check", insert_after="entry_datetime"),
            dict(fieldname="expected_delivery_datetime", label="Expected Delivery", fieldtype="Datetime", insert_after="sla_delivery_by"),
        ],
        "Project": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="cost_center", hidden=1),
        ],
        "Task": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="project", hidden=1),
        ],
        "Timesheet": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="project", hidden=1),
        ],
        "Stock Entry": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="company", hidden=1),
        ],
        "Purchase Invoice": [
            dict(fieldname="repair_order", label="Repair Order", fieldtype="Link", options="Repair Order", insert_after="company", hidden=1),
        ],
        "Vehicle Location": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="speed", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
            dict(fieldname="altitude", label="Altitude", fieldtype="Float", insert_after="device_name", read_only=1),
        ],
        "Vehicle Fuel Level": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="location", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
        ],
        "Vehicle Sensor Data": [
            dict(fieldname="telemetry_batch_id", label="Telemetry Batch ID", fieldtype="Data", insert_after="unit", read_only=1, in_standard_filter=1),
            dict(fieldname="source_imei", label="Source IMEI", fieldtype="Data", insert_after="telemetry_batch_id", read_only=1, in_standard_filter=1),
            dict(fieldname="device_name", label="Device Name", fieldtype="Data", insert_after="source_imei", read_only=1),
        ],
    }

    # Idempotent creation
    create_custom_fields(custom_fields, ignore_validate=True)

    # Create Workspace assets (Number Cards, Charts, Workspace, Kanban)
    try:
        _create_kpis_and_charts()
        _create_workspace()
        _ensure_kanban_board()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Car Repair Management: Workspace setup")

    # Dashboard Links for Vehicle
    try:
        _add_vehicle_dashboard_links()
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Car Repair Management: Vehicle dashboard links")


def _create_kpis_and_charts():
    """Create Number Cards and Dashboard Charts for the Workshop workspace (idempotent)."""
    module = "Car Repair Management"

    def upsert_number_card(name, label, doctype, function="Count", filters=None, is_public=1):
        doc = frappe.db.exists("Number Card", name)
        filters_json = frappe.as_json(filters or [])
        args = dict(
            name=name,
            label=label,
            type="Document Type",
            document_type=doctype,
            function=function,
            filters_json=filters_json,
            is_public=is_public,
            is_standard=1,
            module=module,
        )
        if doc:
            nc = frappe.get_doc("Number Card", name)
            nc.update(args)
            nc.save(ignore_permissions=True)
        else:
            nc = frappe.get_doc({"doctype": "Number Card", **args}).insert(ignore_permissions=True)
        return nc.name

    def upsert_dashboard_chart(name, chart_type, **kwargs):
        exists = frappe.db.exists("Dashboard Chart", name)
        args = dict(chart_name=name, is_standard=1, module=module, chart_type=chart_type)
        args.update(kwargs)
        if exists:
            ch = frappe.get_doc("Dashboard Chart", name)
            ch.update(args)
            ch.save(ignore_permissions=True)
        else:
            ch = frappe.get_doc({"doctype": "Dashboard Chart", **args}).insert(ignore_permissions=True)
        return ch.name

    # Dates
    today = frappe.utils.today()
    # Open statuses
    open_statuses = ["Scheduled", "In Progress", "Awaiting Parts"]

    # Number Cards
    upsert_number_card(
        name="ROs Today",
        label="ROs Today",
        doctype="Repair Order",
        filters=[["Repair Order", "creation", ">=", today]],
    )
    upsert_number_card(
        name="ROs In Progress",
        label="In Progress",
        doctype="Repair Order",
        filters=[["Repair Order", "status", "=", "In Progress"]],
    )
    upsert_number_card(
        name="ROs Awaiting Parts",
        label="Awaiting Parts",
        doctype="Repair Order",
        filters=[["Repair Order", "status", "=", "Awaiting Parts"]],
    )
    upsert_number_card(
        name="ROs Ready for Handover",
        label="Ready for Handover",
        doctype="Repair Order",
        filters=[["Repair Order", "status", "=", "Ready for Handover"]],
    )
    upsert_number_card(
        name="ROs Due Today",
        label="Due Today",
        doctype="Repair Order",
        filters=[["Repair Order", "sla_delivery_by", "<=", today], ["Repair Order", "status", "in", open_statuses]],
    )
    upsert_number_card(
        name="ROs Overdue",
        label="Overdue",
        doctype="Repair Order",
        filters=[["Repair Order", "sla_delivery_by", "<", today], ["Repair Order", "status", "in", open_statuses]],
    )

    # Charts
    # ROs by Status (last 30 days)
    filters_json = frappe.as_json([["Repair Order", "creation", ">=", frappe.utils.add_days(today, -30)]])
    upsert_dashboard_chart(
        name="ROs by Status (30d)",
        chart_type="Group By",
        document_type="Repair Order",
        based_on="creation",
        group_by_type="Count",
        group_by_based_on="status",
        type="Bar",
        timeseries=0,
        filters_json=filters_json,
    )

    # Parts Billable vs FoC (30 days) - from report chart
    upsert_dashboard_chart(
        name="Billable vs FoC Parts (30d)",
        chart_type="Report",
        report_name="Parts Consumption Billable vs FoC",
        use_report_chart=1,
        type="Pie",
        filters_json=frappe.as_json([]),
    )
    
    # Most Repaired Vehicles (Top 10)
    upsert_dashboard_chart(
        name="Most Repaired Vehicles",
        chart_type="Group By",
        document_type="Repair Order",
        based_on="creation",
        group_by_type="Count",
        group_by_based_on="vehicle",
        type="Bar",
        timeseries=0,
        number_of_groups=10,
        filters_json=frappe.as_json([["Repair Order", "docstatus", "=", "1"]]),
    )


def _create_workspace():
    module = "Car Repair Management"
    label = "Workshop"
    ws = frappe.db.exists("Workspace", label)
    number_cards = [
        "ROs Today",
        "ROs In Progress",
        "ROs Awaiting Parts",
        "ROs Ready for Handover",
        "ROs Due Today",
        "ROs Overdue",
    ]
    charts = [
        "ROs by Status (30d)",
        "Billable vs FoC Parts (30d)",
        "Most Repaired Vehicles",
    ]
    shortcuts = [
        # Quick Actions
        dict(type="DocType", link_to="Repair Order", label="New Repair Order", doc_view="New"),
        dict(type="URL", url="/app/List/Repair%20Order/Kanban/Repair%20Order%20by%20Status", label="Open WIP Kanban"),
        dict(type="Report", link_to="Job Profitability Report", label="Job Profitability Report"),
        dict(type="Report", link_to="Parts Consumption Billable vs FoC", label="Parts Consumption"),
        # Work in Progress
        dict(type="URL", url="/app/project?view=Gantt", label="Project Gantt"),
        dict(type="URL", url="/app/task/view/calendar/Task?repair_order=!%3D%2C", label="Technician Calendar"),
        # My Work
        dict(type="DocType", link_to="Repair Order", label="My Assigned ROs", stats_filter="{\n    \"_assign\": [\"like\", '%' + frappe.session.user + '%']\n}"),
        dict(type="DocType", link_to="Task", label="My Tasks", stats_filter="{\n    \"_assign\": [\"like\", '%' + frappe.session.user + '%']\n}"),
        dict(type="URL", url="/app/List/Repair%20Order/List?status=Ready%20for%20Handover", label="Ready for Handover"),
        dict(type="URL", url="/app/List/Repair%20Order/List?status=Awaiting%20Parts", label="Waiting for Parts"),
        dict(type="URL", url="/app/List/Quotation/List", label="Approvals Needed"),
        # Reports & Analytics
        dict(type="Report", link_to="Technician Utilization and Efficiency", label="Technician Utilization and Efficiency"),
        dict(type="Report", link_to="WIP Aging", label="WIP Aging"),
        dict(type="Report", link_to="Repeat Repairs and Warranty Returns", label="Repeat Repairs and Warranty Returns"),
        # Masters & Setup
        dict(type="DocType", link_to="Vehicle", label="Vehicle"),
        dict(type="DocType", link_to="Service Template", label="Service Template"),
        dict(type="DocType", link_to="Repair Checklist", label="Repair Checklist"),
        dict(type="DocType", link_to="Item", label="Item"),
        dict(type="DocType", link_to="Workstation", label="Workstation"),
        dict(type="DocType", link_to="Activity Type", label="Activity Type"),
        dict(type="DocType", link_to="Employee", label="Employee"),
        dict(type="DocType", link_to="Notification", label="Notification"),
        # Stores & Inventory
        dict(type="URL", url="/app/List/Material%20Request/List", label="Material Requests (Issue)"),
        dict(type="URL", url="/app/List/Stock%20Entry/List", label="Stock Entries (Issue)"),
        dict(type="Report", link_to="Stock Ledger", label="Stock Ledger"),
        dict(type="Report", link_to="Item-wise Recommended Reorder Level", label="Reorder Report"),
        # Commercials
        dict(type="DocType", link_to="Quotation", label="Quotations"),
        dict(type="DocType", link_to="Sales Order", label="Sales Orders"),
        dict(type="DocType", link_to="Sales Invoice", label="Sales Invoices"),
        dict(type="Report", link_to="Accounts Receivable", label="Outstanding Invoices"),
        # Admin & Utilities
        dict(type="DocType", link_to="Job Costing", label="Job Costing"),
        dict(type="URL", url="/app/List/Error%20Log/List", label="Error Log (RO/Costing)"),
        dict(type="DocType", link_to="Scheduled Job Log", label="Scheduler Log"),
    ]
    ws_args = dict(
        label=label,
        title=label,
        module=module,
        public=1,
    )
    roles = [
        "Service Advisor",
        "Workshop Manager",
        "Technician",
        "Stores User",
        "Accounts User",
        "System Manager",
    ]
    # Build Workspace content blocks for UI rendering
    blocks = []
    # Header KPIs
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Workshop KPIs</b></span>", "col": 12}})
    for nc in number_cards:
        if frappe.db.exists("Number Card", nc):
            blocks.append({"type": "number_card", "data": {"number_card_name": nc, "col": 3}})
    # Charts
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Analytics</b></span>", "col": 12}})
    for ch in charts:
        if frappe.db.exists("Dashboard Chart", ch):
            blocks.append({"type": "chart", "data": {"chart_name": ch, "col": 6}})
    # Shortcuts
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Quick Actions</b></span>", "col": 12}})
    for qa in ["New Repair Order", "Open WIP Kanban", "Job Profitability Report", "Parts Consumption"]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": qa, "col": 3}})
    # Work in Progress
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Work in Progress</b></span>", "col": 12}})
    for name in ["Open WIP Kanban", "Project Gantt", "Technician Calendar"]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": name, "col": 3}})
    # My Work
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>My Work</b></span>", "col": 12}})
    for name in ["My Assigned ROs", "My Tasks", "Ready for Handover", "Waiting for Parts", "Approvals Needed"]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": name, "col": 3}})
    # Reports & Analytics
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Reports & Analytics</b></span>", "col": 12}})
    for report_name in [
        "Job Profitability Report",
        "Parts Consumption Billable vs FoC",
        "Technician Utilization & Efficiency",
        "WIP Aging",
        "Repeat Repairs / Warranty Returns",
    ]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": report_name, "col": 3}})
    # Masters & Setup
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Masters & Setup</b></span>", "col": 12}})
    for m in [
        "Vehicle", "Service Template", "Repair Checklist", "Item", "Workstation", "Activity Type", "Employee Grade", "Notification"
    ]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": m, "col": 3}})
    # Stores & Inventory
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Stores & Inventory</b></span>", "col": 12}})
    for s in [
        "Material Requests (Issue)", "Stock Entries (Issue)", "Stock Ledger", "Reorder Report"
    ]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": s, "col": 3}})
    # Commercials
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Commercials</b></span>", "col": 12}})
    for s in [
        "Quotations", "Sales Orders", "Sales Invoices", "Outstanding Invoices"
    ]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": s, "col": 3}})
    # Admin & Utilities
    blocks.append({"type": "spacer", "data": {"col": 12}})
    blocks.append({"type": "header", "data": {"text": "<span class=\"h4\"><b>Admin & Utilities</b></span>", "col": 12}})
    for s in [
        "Job Costing", "Error Log (RO/Costing)", "Scheduler Log"
    ]:
        blocks.append({"type": "shortcut", "data": {"shortcut_name": s, "col": 3}})
    # Ensure shortcuts exist as child records; content references them by name
    if ws:
        doc = frappe.get_doc("Workspace", label)
        doc.update(ws_args)
        doc.set("number_cards", [])
        for nc in number_cards:
            if frappe.db.exists("Number Card", nc):
                doc.append("number_cards", {"number_card_name": nc, "label": nc})
        doc.set("charts", [])
        for ch in charts:
            if frappe.db.exists("Dashboard Chart", ch):
                doc.append("charts", {"chart_name": ch, "label": ch})
        doc.set("shortcuts", [])
        for sc in shortcuts:
            doc.append("shortcuts", sc)
        # add roles
        doc.set("roles", [])
        for r in roles:
            if frappe.db.exists("Role", r):
                doc.append("roles", {"role": r})
        # append shortcut blocks using the label (Workspace Shortcut name is label by default)
        for s in doc.shortcuts:
            blocks.append({"type": "shortcut", "data": {"shortcut_name": s.label, "col": 3}})
        doc.content = frappe.as_json(blocks)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": "Workspace", **ws_args})
        for nc in number_cards:
            if frappe.db.exists("Number Card", nc):
                doc.append("number_cards", {"number_card_name": nc, "label": nc})
        for ch in charts:
            if frappe.db.exists("Dashboard Chart", ch):
                doc.append("charts", {"chart_name": ch, "label": ch})
        for sc in shortcuts:
            doc.append("shortcuts", sc)
        for r in roles:
            if frappe.db.exists("Role", r):
                doc.append("roles", {"role": r})
        # shortcut blocks
        for s in doc.shortcuts:
            blocks.append({"type": "shortcut", "data": {"shortcut_name": s.label, "col": 3}})
        doc.content = frappe.as_json(blocks)
        doc.insert(ignore_permissions=True)


def _ensure_kanban_board():
    name = "Repair Order by Status"
    if frappe.db.exists("Kanban Board", name):
        return
    kb = frappe.get_doc({
        "doctype": "Kanban Board",
        "kanban_board_name": name,
        "reference_doctype": "Repair Order",
        "field_name": "status",
        "private": 0,
        "show_labels": 1,
    })
    statuses = [
        "Scheduled",
        "In Progress",
        "Awaiting Parts",
        "Ready for Handover",
        "Delivered",
        "Closed",
        "On Hold",
        "Cancelled",
    ]
    for s in statuses:
        kb.append("columns", {"column_name": s, "status": "Active"})
    kb.insert(ignore_permissions=True)


def _add_vehicle_dashboard_links():
    # Placeholder: no-op, reserved for future dashboard link additions
    pass


def _patch_workspace_shortcuts():
    """Ensure Workshop shortcuts point to the right resources (idempotent)."""
    label = "Workshop"
    if not frappe.db.exists("Workspace", label):
        return
    doc = frappe.get_doc("Workspace", label)
    changed = False
    for sc in doc.shortcuts:
        # Fix Kanban to URL pointing to existing board
        if sc.label == "Open WIP Kanban":
            sc.type = "URL"
            sc.url = "/app/List/Repair%20Order/Kanban/Repair%20Order%20by%20Status"
            sc.doc_view = None
            sc.kanban_board = None
            sc.link_to = None
            changed = True
        # Fix Parts Consumption report link
        if sc.label == "Parts Consumption":
            sc.type = "Report"
            sc.link_to = "Parts Consumption Billable vs FoC"
            changed = True
    if changed:
        doc.save(ignore_permissions=True)
