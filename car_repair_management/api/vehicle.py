import re

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, flt
from datetime import datetime, timedelta


@frappe.whitelist()
def get_vehicle_dashboard(vehicle_name):
    """Get comprehensive vehicle dashboard data for the frontend."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    
    # Get custodian employee details
    custodian = None
    custodian_id = vehicle.custom_custodian or vehicle.employee
    if custodian_id:
        try:
            emp = frappe.get_doc("Employee", custodian_id)
            custodian = {
                "name": emp.name,
                "employee_name": emp.employee_name,
                "image": emp.image,
                "designation": emp.designation,
            }
        except frappe.DoesNotExistError:
            pass

    # Get drivers (separate active from historical)
    drivers = []
    driver_history = []
    for d in vehicle.custom_drivers or []:
        driver_data = _build_driver_data(d)
        if d.status == "Removed":
            driver_history.append(driver_data)
        else:
            drivers.append(driver_data)
    
    # Get cost of ownership data (last 6 months)
    cost_of_ownership = get_cost_of_ownership(vehicle_name)
    
    # Get service reminders
    service_reminders = get_service_reminders(vehicle_name)
    
    # Get open issues
    open_issues = get_open_issues(vehicle_name)
    
    # Get recent work orders
    work_orders = get_recent_work_orders(vehicle_name)

    telemetry_summary = get_vehicle_telemetry_summary(vehicle_name, vehicle=vehicle)
    
    return {
        "vehicle": {
            "name": vehicle.name,
            "license_plate": vehicle.license_plate,
            "make": vehicle.make,
            "model": vehicle.model,
            "variant": vehicle.variant,
            "year": vehicle.year,
            "chassis_no": vehicle.chassis_no,
            "color": vehicle.color,
            "transmission": vehicle.transmission,
            "fuel_type": vehicle.fuel_type,
            "doors": vehicle.doors,
            "wheels": vehicle.wheels,
            "vehicle_value": vehicle.vehicle_value,
            "acquisition_date": vehicle.acquisition_date,
            "last_odometer": vehicle.last_odometer,
            "odometer_at_last_service": vehicle.odometer_at_last_service,
            "last_service_date": vehicle.last_service_date,
            "next_service_due_date": vehicle.next_service_due_date,
            "jobs_count": vehicle.jobs_count,
            "repair_cost_to_date": vehicle.repair_cost_to_date,
            "revenue_billed_to_date": vehicle.revenue_billed_to_date,
            "company": vehicle.company,
            "location": vehicle.location,
            "insurance_company": vehicle.insurance_company,
            "policy_no": vehicle.policy_no,
            "start_date": vehicle.start_date,
            "end_date": vehicle.end_date,
            "status": vehicle.custom_status or "Active",
            "vehicle_type": vehicle.vehicle_type or getattr(vehicle, "custom_vehicle_type", None) or "Car",
            "image": getattr(vehicle, "custom_image", None),
            "telematics_imei": getattr(vehicle, "custom_telematics_imei", None),
            "last_known_latitude": getattr(vehicle, "custom_last_known_latitude", None),
            "last_known_longitude": getattr(vehicle, "custom_last_known_longitude", None),
            "last_location_update": getattr(vehicle, "custom_last_location_update", None),
            "fuel_level": getattr(vehicle, "custom_fuel_level", None),
        },
        "custodian": custodian,
        "drivers": drivers,
        "driver_history": driver_history,
        "cost_of_ownership": cost_of_ownership,
        "service_reminders": service_reminders,
        "open_issues": open_issues,
        "work_orders": work_orders,
        "telemetry": telemetry_summary,
    }


def get_cost_of_ownership(vehicle_name):
    """Get fuel, maintenance, and repair costs for the last 6 months."""
    today = getdate(nowdate())
    six_months_ago = add_days(today, -180)
    
    # Initialize monthly data
    months = []
    for i in range(5, -1, -1):
        month_date = add_days(today, -30 * i)
        months.append({
            "month": month_date.strftime("%b"),
            "fuel": 0,
            "maintenance": 0,
            "repair": 0,
        })
    
    # Get repair costs from Repair Orders
    repair_orders = frappe.get_all(
        "Repair Order",
        filters={
            "vehicle": vehicle_name,
            "creation": [">=", six_months_ago],
        },
        fields=["creation", "total_job_cost", "parts_cost", "labor_cost"],
    )
    
    for ro in repair_orders:
        month_idx = get_month_index(ro.creation, today)
        if 0 <= month_idx < 6:
            months[5 - month_idx]["repair"] += flt(ro.total_job_cost)
    
    return months


def get_month_index(date, today):
    """Get the month index (0 = current month, 5 = 6 months ago)."""
    if isinstance(date, str):
        date = getdate(date)
    if isinstance(date, datetime):
        date = date.date()
    
    diff = (today.year - date.year) * 12 + (today.month - date.month)
    return diff


def get_service_reminders(vehicle_name):
    """Get service reminder counts and list."""
    today = getdate(nowdate())
    soon_threshold = add_days(today, 14)
    
    # Check if Service Reminder doctype exists
    if not frappe.db.exists("DocType", "Service Reminder"):
        return {
            "overdue": 0,
            "due_soon": 0,
            "snoozed": 0,
            "items": [],
        }
    
    reminders = frappe.get_all(
        "Service Reminder",
        filters={"vehicle": vehicle_name},
        fields=["name", "reminder_type", "due_date", "status", "description"],
        order_by="due_date asc",
    )
    
    overdue = 0
    due_soon = 0
    snoozed = 0
    
    for r in reminders:
        if r.status == "Snoozed":
            snoozed += 1
        elif r.due_date and getdate(r.due_date) < today:
            overdue += 1
        elif r.due_date and getdate(r.due_date) <= soon_threshold:
            due_soon += 1
    
    return {
        "overdue": overdue,
        "due_soon": due_soon,
        "snoozed": snoozed,
        "items": reminders[:5],
    }


def get_open_issues(vehicle_name):
    """Get open issues count and list for the vehicle."""
    today = getdate(nowdate())
    
    # Check if Vehicle Issue doctype exists, otherwise use Issue
    doctype = "Vehicle Issue" if frappe.db.exists("DocType", "Vehicle Issue") else "Issue"
    
    if doctype == "Issue":
        # Standard Issue doctype may not have vehicle field
        return {
            "open": 0,
            "overdue": 0,
            "items": [],
        }
    
    issues = frappe.get_all(
        doctype,
        filters={
            "vehicle": vehicle_name,
            "status": ["not in", ["Closed", "Resolved", "Cancelled"]],
        },
        fields=["name", "subject", "status", "priority", "creation", "resolution_by"],
        order_by="creation desc",
    )
    
    open_count = len(issues)
    overdue = sum(1 for i in issues if i.resolution_by and getdate(i.resolution_by) < today)
    
    return {
        "open": open_count,
        "overdue": overdue,
        "items": issues[:5],
    }


def get_recent_work_orders(vehicle_name):
    """Get recent work orders for the vehicle."""
    work_orders = frappe.get_all(
        "Repair Order",
        filters={"vehicle": vehicle_name},
        fields=["name", "status", "priority", "problem_summary", "creation", "modified", "total_job_cost"],
        order_by="modified desc",
        limit=10,
    )
    return work_orders


def get_vehicle_telemetry_summary(vehicle_name, vehicle=None):
    """Return dashboard-ready latest telemetry for a vehicle."""
    vehicle = vehicle or frappe.get_doc("Vehicle", vehicle_name)
    latest_location = _latest_vehicle_location(vehicle_name)
    latest_fuel = _latest_vehicle_fuel(vehicle_name)
    latest_sensors = _latest_vehicle_sensor_values(vehicle_name)

    last_sync_candidates = [
        latest_location.get("timestamp") if latest_location else None,
        latest_fuel.get("timestamp") if latest_fuel else None,
    ]
    last_sync_candidates.extend(v.get("timestamp") for v in latest_sensors.values())
    last_sync = max([str(v) for v in last_sync_candidates if v], default=None)

    fuel_level = getattr(vehicle, "custom_fuel_level", None)
    if fuel_level in (None, "") and latest_fuel:
        fuel_level = latest_fuel.get("fuel_level")

    return {
        "device_id": getattr(vehicle, "custom_telematics_imei", None),
        "device_name": _first_sensor_value(latest_sensors, "Device Name") or (latest_location or {}).get("device_name"),
        "last_sync": last_sync,
        "sensor_health": "Connected" if last_sync else "Not Linked",
        "odometer": vehicle.last_odometer,
        "fuel_level": fuel_level,
        "fuel_volume_ml": _first_sensor_value(latest_sensors, "Fuel CAN Level Value"),
        "engine_state": _first_sensor_value(latest_sensors, "Engine State"),
        "tracker_status": _first_sensor_value(latest_sensors, "Tracker Status"),
        "speed": (latest_location or {}).get("speed") or _first_sensor_value(latest_sensors, "Speed"),
        "heading": (latest_location or {}).get("direction") or _first_sensor_value(latest_sensors, "Heading"),
        "altitude": (latest_location or {}).get("altitude") or _first_sensor_value(latest_sensors, "Altitude"),
        "latitude": (latest_location or {}).get("latitude") or getattr(vehicle, "custom_last_known_latitude", None),
        "longitude": (latest_location or {}).get("longitude") or getattr(vehicle, "custom_last_known_longitude", None),
        "location_record": (latest_location or {}).get("name"),
        "fuel_record": (latest_fuel or {}).get("name"),
        "record_counts": _vehicle_telemetry_record_counts(vehicle_name),
    }


def _latest_vehicle_location(vehicle_name):
    if not frappe.db.exists("DocType", "Vehicle Location"):
        return None

    fields = ["name", "latitude", "longitude", "timestamp", "direction", "speed"]
    for fieldname in ("source_imei", "device_name", "altitude", "telemetry_batch_id"):
        if frappe.db.has_column("Vehicle Location", fieldname):
            fields.append(fieldname)

    rows = frappe.get_all(
        "Vehicle Location",
        filters={"vehicle": vehicle_name},
        fields=fields,
        order_by="timestamp desc",
        limit=1,
    )
    return rows[0] if rows else None


def _latest_vehicle_fuel(vehicle_name):
    if not frappe.db.exists("DocType", "Vehicle Fuel Level"):
        return None

    fields = ["name", "fuel_level", "timestamp"]
    for fieldname in ("source_imei", "device_name", "telemetry_batch_id"):
        if frappe.db.has_column("Vehicle Fuel Level", fieldname):
            fields.append(fieldname)

    rows = frappe.get_all(
        "Vehicle Fuel Level",
        filters={"vehicle": vehicle_name},
        fields=fields,
        order_by="timestamp desc",
        limit=1,
    )
    return rows[0] if rows else None


def _latest_vehicle_sensor_values(vehicle_name):
    if not frappe.db.exists("DocType", "Vehicle Sensor Data"):
        return {}

    fields = ["name", "sensor_type", "value", "unit", "timestamp"]
    for fieldname in ("source_imei", "device_name", "telemetry_batch_id"):
        if frappe.db.has_column("Vehicle Sensor Data", fieldname):
            fields.append(fieldname)

    rows = frappe.get_all(
        "Vehicle Sensor Data",
        filters={"vehicle": vehicle_name},
        fields=fields,
        order_by="timestamp desc",
        limit=200,
    )

    latest = {}
    for row in rows:
        latest.setdefault(row.sensor_type, row)
    return latest


def _first_sensor_value(latest_sensors, sensor_type):
    row = latest_sensors.get(sensor_type)
    return row.get("value") if row else None


def _vehicle_telemetry_record_counts(vehicle_name):
    counts = {}
    for doctype, key in (
        ("Vehicle Location", "locations"),
        ("Vehicle Fuel Level", "fuel_levels"),
        ("Vehicle Sensor Data", "sensor_readings"),
    ):
        counts[key] = frappe.db.count(doctype, {"vehicle": vehicle_name}) if frappe.db.exists("DocType", doctype) else 0
    return counts


@frappe.whitelist()
def get_vehicle_specs(vehicle_name):
    """Get detailed vehicle specifications."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    
    return {
        "basic": {
            "make": vehicle.make,
            "model": vehicle.model,
            "variant": vehicle.variant,
            "year": vehicle.year,
            "color": vehicle.color,
        },
        "identifiers": {
            "license_plate": vehicle.license_plate,
            "chassis_no": vehicle.chassis_no,
        },
        "mechanical": {
            "transmission": vehicle.transmission,
            "fuel_type": vehicle.fuel_type,
            "doors": vehicle.doors,
            "wheels": vehicle.wheels,
        },
        "odometer": {
            "current": vehicle.last_odometer,
            "at_last_service": vehicle.odometer_at_last_service,
        },
    }


@frappe.whitelist()
def get_vehicle_financial(vehicle_name):
    """Get financial data for the vehicle."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    
    # Get all repair orders for cost breakdown
    repair_orders = frappe.get_all(
        "Repair Order",
        filters={"vehicle": vehicle_name},
        fields=["name", "parts_cost", "labor_cost", "other_charges", "total_job_cost", "creation"],
    )
    
    total_parts = sum(flt(ro.parts_cost) for ro in repair_orders)
    total_labor = sum(flt(ro.labor_cost) for ro in repair_orders)
    total_other = sum(flt(ro.other_charges) for ro in repair_orders)
    total_repair = sum(flt(ro.total_job_cost) for ro in repair_orders)
    
    return {
        "vehicle_value": vehicle.vehicle_value,
        "acquisition_date": vehicle.acquisition_date,
        "repair_cost_to_date": vehicle.repair_cost_to_date or total_repair,
        "revenue_billed_to_date": vehicle.revenue_billed_to_date,
        "cost_breakdown": {
            "parts": total_parts,
            "labor": total_labor,
            "other": total_other,
        },
        "insurance": {
            "company": vehicle.insurance_company,
            "policy_no": vehicle.policy_no,
            "start_date": vehicle.start_date,
            "end_date": vehicle.end_date,
        },
    }


@frappe.whitelist()
def get_vehicle_work_orders(vehicle_name, limit=20, offset=0):
    """Get paginated work orders for the vehicle."""
    work_orders = frappe.get_all(
        "Repair Order",
        filters={"vehicle": vehicle_name},
        fields=[
            "name", "status", "priority", "customer", "problem_summary",
            "creation", "modified", "parts_cost", "labor_cost", "total_job_cost"
        ],
        order_by="creation desc",
        limit_start=offset,
        limit_page_length=limit,
    )
    
    total = frappe.db.count("Repair Order", {"vehicle": vehicle_name})
    
    return {
        "items": work_orders,
        "total": total,
    }


@frappe.whitelist()
def scrap_vehicle(vehicle_name):
    """Mark a vehicle as scrapped."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    vehicle.db_set("custom_status", "Scrapped")
    frappe.db.commit()
    return {"success": True, "message": _("Vehicle marked as scrapped")}


@frappe.whitelist()
def delete_vehicle(vehicle_name):
    """Delete a vehicle (if no linked records)."""
    # Check for linked repair orders
    linked_orders = frappe.db.count("Repair Order", {"vehicle": vehicle_name})
    if linked_orders > 0:
        frappe.throw(_("Cannot delete vehicle with {0} linked repair orders").format(linked_orders))
    
    frappe.delete_doc("Vehicle", vehicle_name)
    return {"success": True, "message": _("Vehicle deleted successfully")}


# ============================================================================
# TAB 2: SPECS - Full specifications grouped by section
# ============================================================================

@frappe.whitelist()
def get_vehicle_specs_full(vehicle_name):
    """Get comprehensive vehicle specifications grouped by section."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    
    return {
        "vehicle_identity": {
            "data": {
                "vin_chassis": vehicle.chassis_no,
                "plate_number": vehicle.license_plate,
                "engine_number": vehicle.engine_number,
                "make": vehicle.make,
                "model": vehicle.model,
                "variant": vehicle.variant,
                "vehicle_type": vehicle.vehicle_type or getattr(vehicle, "custom_vehicle_type", None) or "Car",
                "manufacture_year": vehicle.year,
                "country_of_origin": vehicle.country_of_origin,
            },
            "last_updated": str(vehicle.modified),
            "updated_by": vehicle.modified_by,
        },
        "technical_specs": {
            "data": {
                "engine_type": vehicle.engine_type,
                "engine_capacity": vehicle.engine_capacity,
                "cylinders": vehicle.cylinders,
                "transmission": vehicle.transmission,
                "drivetrain": vehicle.drivetrain,
                "fuel_type": vehicle.fuel_type,
                "fuel_tank_capacity": vehicle.fuel_tank_capacity,
                "battery_capacity": vehicle.battery_capacity,
            },
            "last_updated": str(vehicle.modified),
            "updated_by": vehicle.modified_by,
        },
        "capacity_limits": {
            "data": {
                "seating_capacity": vehicle.seating_capacity,
                "payload_capacity": vehicle.payload_capacity,
                "towing_capacity": vehicle.towing_capacity,
                "gross_vehicle_weight": vehicle.gross_vehicle_weight,
            },
            "last_updated": str(vehicle.modified),
            "updated_by": vehicle.modified_by,
        },
        "ownership_registration": {
            "data": {
                "ownership_type": vehicle.ownership_type or "Owned",
                "registration_authority": vehicle.registration_authority,
                "registration_expiry": vehicle.registration_expiry,
                "insurance_policy": vehicle.insurance_policy or vehicle.policy_no,
                "insurance_company": vehicle.insurance_company,
                "insurance_expiry": vehicle.insurance_expiry or vehicle.end_date,
            },
            "last_updated": str(vehicle.modified),
            "updated_by": vehicle.modified_by,
        },
    }


# ============================================================================
# TAB 3: FINANCIALS - Full financial data with KPIs
# ============================================================================

@frappe.whitelist()
def get_vehicle_financials_full(vehicle_name):
	"""Get comprehensive financial data for the vehicle."""
	vehicle = frappe.get_doc("Vehicle", vehicle_name)
	today = getdate(nowdate())

	# Get company currency
	company = vehicle.company or frappe.defaults.get_global_default("company")
	currency = frappe.db.get_value("Company", company, "default_currency") if company else None
	currency = currency or frappe.defaults.get_global_default("currency") or "ETB"

	# Get all repair orders
	repair_orders = frappe.get_all(
		"Repair Order",
		filters={"vehicle": vehicle_name},
		fields=["name", "parts_cost", "labor_cost", "other_charges", "total_job_cost", "creation", "status"],
	)

	total_parts = sum(flt(ro.parts_cost) for ro in repair_orders)
	total_labor = sum(flt(ro.labor_cost) for ro in repair_orders)
	total_other = sum(flt(ro.other_charges) for ro in repair_orders)
	total_repair = sum(flt(ro.total_job_cost) for ro in repair_orders)

	# Calculate lifetime spend - prefer acquisition_cost, fallback to vehicle_value
	acquisition_cost = flt(vehicle.acquisition_cost) or flt(vehicle.vehicle_value)

	# Try to get data from linked Asset
	asset_name = vehicle.get("erpnext_asset")
	asset_data = None
	total_depreciation = 0
	current_book_value = acquisition_cost

	if asset_name and frappe.db.exists("Asset", asset_name):
		asset_fields = ["gross_purchase_amount", "purchase_date", "status", "value_after_depreciation"]
		asset_data = frappe.db.get_value("Asset", asset_name, asset_fields, as_dict=True)

	if asset_data:
		acquisition_cost = flt(asset_data.gross_purchase_amount) or acquisition_cost
		current_book_value = flt(asset_data.value_after_depreciation)
		total_depreciation = acquisition_cost - current_book_value
	else:
		# Fallback estimate: 30% depreciation
		current_book_value = acquisition_cost * 0.7
		total_depreciation = acquisition_cost * 0.3

	total_lifetime_spend = acquisition_cost + total_repair

	# Calculate average monthly cost
	acq_date = asset_data.purchase_date if asset_data and asset_data.purchase_date else vehicle.acquisition_date
	avg_monthly = 0
	if acq_date:
		months_owned = max(1, (today.year - getdate(acq_date).year) * 12 +
						  (today.month - getdate(acq_date).month))
		avg_monthly = total_repair / months_owned

	# Cost per km
	odometer = flt(vehicle.last_odometer) or 1
	cost_per_km = total_repair / odometer if odometer > 0 else 0

	# Build cost breakdown
	total_costs = total_parts + total_labor + total_other
	cost_breakdown = []
	if total_costs > 0:
		cost_breakdown = [
			{"category": "Parts", "amount": total_parts, "percentage": round(total_parts / total_costs * 100, 1)},
			{"category": "Labor", "amount": total_labor, "percentage": round(total_labor / total_costs * 100, 1)},
			{"category": "Other", "amount": total_other, "percentage": round(total_other / total_costs * 100, 1)},
		]

	# Get depreciation details
	dep_method = vehicle.depreciation_method or "Straight Line"
	residual_value = acquisition_cost * 0.1

	if asset_name and frappe.db.exists("Asset", asset_name):
		# Read finance_books child table for depreciation method
		finance_books = frappe.get_all(
			"Asset Finance Book",
			filters={"parent": asset_name, "parenttype": "Asset"},
			fields=["depreciation_method", "expected_value_after_useful_life"],
			limit=1,
		)
		if finance_books:
			dep_method = finance_books[0].depreciation_method or dep_method
			residual_value = flt(finance_books[0].expected_value_after_useful_life) or residual_value

	depreciation_info = {
		"method": dep_method,
		"start_date": acq_date,
		"current_value": current_book_value,
		"residual_value": residual_value,
		"total_depreciated": total_depreciation,
	}

	return {
		"currency": currency,
		"overview": {
			"current_odometer": vehicle.last_odometer,
		},
		"kpi_cards": {
			"acquisition_cost": acquisition_cost,
			"total_lifetime_spend": total_lifetime_spend,
			"average_monthly_cost": round(avg_monthly, 2),
			"cost_per_km": round(cost_per_km, 2),
			"current_book_value": current_book_value,
			"total_depreciation": total_depreciation,
		},
		"cost_breakdown": cost_breakdown,
		"depreciation": depreciation_info,
		"linked_records": {
			"work_orders_count": len(repair_orders),
			"work_orders_total": total_repair,
			"asset_link": asset_name,
			"completed_orders": sum(1 for ro in repair_orders if ro.status in ["Closed", "Delivered"]),
		},
		"insurance": {
			"company": vehicle.insurance_company,
			"policy_no": vehicle.insurance_policy or vehicle.policy_no,
			"start_date": vehicle.start_date,
			"end_date": vehicle.insurance_expiry or vehicle.end_date,
		},
	}


# ============================================================================
# TAB 4: SENSOR DATA - Telemetry and usage monitoring
# ============================================================================

@frappe.whitelist()
def get_vehicle_sensor_data(vehicle_name, timeframe="30d"):
    """Get sensor/telemetry data for the vehicle."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    telemetry_summary = get_vehicle_telemetry_summary(vehicle_name, vehicle=vehicle)

    # Calculate date filter from timeframe
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(timeframe, 30)
    from_date = add_days(nowdate(), -days)

    # Check if we have a sensor data doctype
    has_sensor_doctype = bool(frappe.db.exists("DocType", "Vehicle Sensor Data"))

    live_status = {
        "odometer": vehicle.last_odometer,
        "fuel_level": telemetry_summary.get("fuel_level") or getattr(vehicle, "custom_fuel_level", None),
        "fuel_volume_ml": telemetry_summary.get("fuel_volume_ml"),
        "engine_state": telemetry_summary.get("engine_state"),
        "tracker_status": telemetry_summary.get("tracker_status"),
        "speed": telemetry_summary.get("speed"),
        "heading": telemetry_summary.get("heading"),
        "altitude": telemetry_summary.get("altitude"),
        "device_id": telemetry_summary.get("device_id"),
        "device_name": telemetry_summary.get("device_name"),
        "engine_hours": getattr(vehicle, "custom_engine_hours", None),
        "last_sync": telemetry_summary.get("last_sync") or getattr(vehicle, "custom_last_location_update", None),
        "sensor_health": telemetry_summary.get("sensor_health") if has_sensor_doctype else "No Sensors",
    }

    alerts = []
    raw_data = []

    # Populate live_status fields when sensor_health is OK but values are empty
    if has_sensor_doctype:
        # fuel_level: get latest from Vehicle Fuel Level if not set
        if not live_status["fuel_level"] and frappe.db.exists("DocType", "Vehicle Fuel Level"):
            latest_fuel = frappe.get_all(
                "Vehicle Fuel Level",
                filters={"vehicle": vehicle_name},
                fields=["fuel_level"],
                order_by="timestamp desc",
                limit=1,
            )
            if latest_fuel:
                live_status["fuel_level"] = latest_fuel[0].fuel_level

        # engine_hours: estimate from RPM sensor readings or odometer
        if not live_status["engine_hours"]:
            rpm_count = frappe.db.count(
                "Vehicle Sensor Data",
                filters={"vehicle": vehicle_name, "sensor_type": "RPM"},
            )
            if rpm_count:
                live_status["engine_hours"] = round(rpm_count * 3, 1)
            elif vehicle.last_odometer:
                live_status["engine_hours"] = round(flt(vehicle.last_odometer) / 40, 1)

        # last_sync: latest timestamp from location, fuel, or sensor data
        if not live_status["last_sync"]:
            sync_candidates = []
            for dt_name, ts_field in [
                ("Vehicle Location", "timestamp"),
                ("Vehicle Fuel Level", "timestamp"),
                ("Vehicle Sensor Data", "timestamp"),
            ]:
                if frappe.db.exists("DocType", dt_name):
                    latest = frappe.get_all(
                        dt_name,
                        filters={"vehicle": vehicle_name},
                        fields=[ts_field],
                        order_by=f"{ts_field} desc",
                        limit=1,
                    )
                    if latest and latest[0].get(ts_field):
                        sync_candidates.append(str(latest[0].get(ts_field)))
            if sync_candidates:
                live_status["last_sync"] = max(sync_candidates)

    if has_sensor_doctype:
        readings = frappe.get_all(
            "Vehicle Sensor Data",
            filters={"vehicle": vehicle_name, "timestamp": [">=", from_date]},
            fields=["name", "sensor_type", "value", "timestamp", "unit"],
            order_by="timestamp desc",
            limit=200,
        )

        raw_data = [{
            "timestamp": r.timestamp,
            "sensor": r.sensor_type,
            "value": r.value,
            "unit": r.unit or "",
            "source": "Vehicle Sensor Data",
            "record_name": r.name,
        } for r in readings]

        for r in readings:
            try:
                if r.sensor_type == "Engine Temperature" and float(r.value) > 100.0:
                    alerts.append({
                        "type": r.sensor_type,
                        "timestamp": r.timestamp,
                        "value": f"{r.value} {r.unit or '°C'}",
                        "severity": "Warning",
                    })
            except (ValueError, TypeError):
                pass

    # Fuel level data
    fuel_readings = []
    if frappe.db.exists("DocType", "Vehicle Fuel Level"):
        fuel_readings = frappe.get_all(
            "Vehicle Fuel Level",
            filters={"vehicle": vehicle_name, "timestamp": [">=", from_date]},
            fields=["name", "fuel_level", "timestamp"],
            order_by="timestamp asc",
        )
        for f in fuel_readings:
            raw_data.append({
                "timestamp": f.timestamp,
                "sensor": "Fuel Level",
                "value": f.fuel_level,
                "unit": "%",
                "source": "Vehicle Fuel Level",
                "record_name": f.name,
            })

    raw_data.sort(key=lambda x: str(x["timestamp"]), reverse=True)

    # Location history
    location_history = []
    if frappe.db.exists("DocType", "Vehicle Location"):
        location_history = frappe.get_all(
            "Vehicle Location",
            filters={"vehicle": vehicle_name, "timestamp": [">=", from_date]},
            fields=["latitude", "longitude", "timestamp", "direction", "speed"],
            order_by="timestamp desc",
            limit=200,
        )

    # Fuel analysis - detect refueling events
    fuel_analysis = _analyze_fuel_patterns(fuel_readings)

    return {
        "live_status": live_status,
        "location_history": location_history,
        "alerts": alerts[:10],
        "raw_data": raw_data,
        "fuel_analysis": fuel_analysis,
        "has_sensors": has_sensor_doctype,
        "telemetry_summary": telemetry_summary,
    }


def _analyze_fuel_patterns(fuel_readings):
    """Analyze fuel readings to detect refueling events and efficiency."""
    if not fuel_readings or len(fuel_readings) < 2:
        return {
            "refuel_events": [],
            "summary": {
                "refuel_count": 0,
                "avg_refuel_level": 0,
                "lowest_refuel_level": 0,
                "pct_below_25": 0,
                "pct_above_50": 0,
            },
        }

    # Sort by timestamp ascending
    sorted_readings = sorted(fuel_readings, key=lambda x: str(x.timestamp))

    refuel_events = []
    refuel_threshold = 10  # 10% jump = refuel

    for i in range(1, len(sorted_readings)):
        prev_level = flt(sorted_readings[i - 1].fuel_level)
        curr_level = flt(sorted_readings[i].fuel_level)
        delta = curr_level - prev_level

        if delta >= refuel_threshold:
            refuel_events.append({
                "timestamp": sorted_readings[i].timestamp,
                "before_level": prev_level,
                "after_level": curr_level,
                "delta": round(delta, 1),
            })

    refuel_count = len(refuel_events)
    if refuel_count > 0:
        before_levels = [e["before_level"] for e in refuel_events]
        avg_refuel_level = round(sum(before_levels) / len(before_levels), 1)
        lowest_refuel_level = round(min(before_levels), 1)
        below_25 = sum(1 for lvl in before_levels if lvl < 25)
        above_50 = sum(1 for lvl in before_levels if lvl > 50)
        pct_below_25 = round(below_25 / refuel_count * 100, 1)
        pct_above_50 = round(above_50 / refuel_count * 100, 1)
    else:
        avg_refuel_level = 0
        lowest_refuel_level = 0
        pct_below_25 = 0
        pct_above_50 = 0

    return {
        "refuel_events": refuel_events[-10:],  # Last 10
        "summary": {
            "refuel_count": refuel_count,
            "avg_refuel_level": avg_refuel_level,
            "lowest_refuel_level": lowest_refuel_level,
            "pct_below_25": pct_below_25,
            "pct_above_50": pct_above_50,
        },
    }


# ============================================================================
# TAB 5: SERVICE HISTORY - Chronological service record
# ============================================================================

@frappe.whitelist()
def get_vehicle_service_history(vehicle_name):
    """Get complete service history for the vehicle."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    
    # Get all completed repair orders as services
    services = frappe.get_all(
        "Repair Order",
        filters={
            "vehicle": vehicle_name,
            "status": ["in", ["Closed", "Delivered", "Completed"]],
        },
        fields=[
            "name", "status", "problem_summary", "creation", "modified",
            "total_job_cost", "parts_cost", "labor_cost", "customer"
        ],
        order_by="creation desc",
    )
    
    # Build timeline
    timeline = []
    for s in services:
        timeline.append({
            "date": str(s.creation)[:10],
            "service_type": "Corrective",  # Could be enhanced with service type field
            "summary": s.problem_summary or "Service completed",
            "performed_by": s.customer,
            "cost": flt(s.total_job_cost),
            "odometer": None,  # Would need to be captured in RO
            "linked_work_order": s.name,
        })
    
    # Calculate summary
    total_services = len(services)
    last_service = services[0] if services else None
    
    avg_interval = 0
    if len(services) > 1:
        dates = [getdate(s.creation) for s in services]
        intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
    
    return {
        "summary": {
            "total_services": total_services,
            "avg_interval_days": round(avg_interval),
            "last_service_date": vehicle.last_service_date,
            "next_expected": vehicle.next_service_due_date,
        },
        "timeline": timeline,
    }


# ============================================================================
# TAB 6: INSPECTION HISTORY - Compliance and safety tracking
# ============================================================================

@frappe.whitelist()
def get_vehicle_inspection_history(vehicle_name):
    """Get inspection history and compliance status."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    today = getdate(nowdate())
    
    # Check if Vehicle Inspection doctype exists
    has_inspection_doctype = frappe.db.exists("DocType", "Vehicle Inspection")
    
    inspections = []
    if has_inspection_doctype:
        try:
            inspections = frappe.get_all(
                "Vehicle Inspection",
                filters={"vehicle": vehicle_name},
                fields=["name", "inspection_date", "inspection_type", "inspector", 
                        "result", "score", "valid_until", "findings", "notes", "status"],
                order_by="inspection_date desc",
            )
        except Exception:
            # Fallback if some fields don't exist
            inspections = frappe.get_all(
                "Vehicle Inspection",
                filters={"vehicle": vehicle_name},
                fields=["name", "inspection_date", "inspection_type", "inspector", 
                        "result", "score", "status"],
                order_by="inspection_date desc",
            )
            for insp in inspections:
                insp["valid_until"] = None
                insp["findings"] = None
                insp["notes"] = None
    
    # Determine compliance status
    valid_inspections = [i for i in inspections if i.get("valid_until") and getdate(i.valid_until) >= today]
    is_compliant = len(valid_inspections) > 0
    
    next_required = None
    is_overdue = False
    if inspections:
        last = inspections[0]
        if last.get("valid_until"):
            next_required = last.valid_until
            is_overdue = getdate(last.valid_until) < today
    
    return {
        "compliance_summary": {
            "status": "Compliant" if is_compliant else "Non-Compliant",
            "next_required": next_required,
            "is_overdue": is_overdue,
        },
        "inspections": [{
            "name": i.name,
            "date": str(i.inspection_date) if i.inspection_date else None,
            "type": i.inspection_type,
            "inspector": i.inspector,
            "status": i.status,
            "result": i.result,
            "score": i.score,
            "valid_until": str(i.valid_until) if i.get("valid_until") else None,
            "findings": i.get("findings"),
            "notes": i.get("notes"),
        } for i in inspections],
    }


# ============================================================================
# TAB 7: WORK ORDERS - Enhanced with filters and metrics
# ============================================================================

@frappe.whitelist()
def get_vehicle_work_orders_full(vehicle_name, status_filter=None, limit=20, offset=0):
    """Get work orders with full details, filters, and metrics."""
    filters = {"vehicle": vehicle_name}
    if status_filter and status_filter != "all":
        filters["status"] = status_filter
    
    work_orders = frappe.get_all(
        "Repair Order",
        filters=filters,
        fields=[
            "name", "status", "priority", "customer", "problem_summary",
            "creation", "modified", "parts_cost", "labor_cost", "total_job_cost",
            "sla_delivery_by"
        ],
        order_by="creation desc",
        limit_start=int(offset),
        limit_page_length=int(limit),
    )
    
    total = frappe.db.count("Repair Order", filters)
    
    # Calculate metrics
    all_orders = frappe.get_all(
        "Repair Order",
        filters={"vehicle": vehicle_name},
        fields=["status", "creation", "modified", "total_job_cost"],
    )
    
    completed = [o for o in all_orders if o.status in ["Closed", "Delivered"]]
    avg_resolution = 0
    if completed:
        resolutions = [(getdate(o.modified) - getdate(o.creation)).days for o in completed]
        avg_resolution = sum(resolutions) / len(resolutions) if resolutions else 0
    
    # Calculate downtime for each order
    for wo in work_orders:
        if wo.creation and wo.modified:
            wo["downtime_days"] = (getdate(wo.modified) - getdate(wo.creation)).days
        else:
            wo["downtime_days"] = 0
    
    return {
        "items": work_orders,
        "total": total,
        "metrics": {
            "avg_resolution_days": round(avg_resolution, 1),
            "total_cost": sum(flt(o.total_job_cost) for o in all_orders),
            "open_count": sum(1 for o in all_orders if o.status not in ["Closed", "Delivered", "Cancelled"]),
            "completed_count": len(completed),
        },
    }


# ============================================================================
# TAB 8: SERVICE REMINDERS - Full reminder management
# ============================================================================

@frappe.whitelist()
def get_vehicle_reminders_full(vehicle_name):
    """Get comprehensive service reminders using the Reminder doctype."""
    now = datetime.now()
    today = getdate(nowdate())
    soon_threshold = add_days(today, 14)

    all_reminders = frappe.get_all(
        "Reminder",
        filters={
            "reminder_doctype": "Vehicle",
            "reminder_docname": vehicle_name,
        },
        fields=["name", "user", "remind_at", "description", "notified", "creation"],
        order_by="remind_at asc",
    )

    active = []
    history = []

    for r in all_reminders:
        # Parse reminder_type from description prefix "[Type] ..."
        reminder_type = "General"
        description = r.description or ""
        if description.startswith("[") and "]" in description:
            bracket_end = description.index("]")
            reminder_type = description[1:bracket_end]
            description = description[bracket_end + 1:].strip()

        remind_date = getdate(r.remind_at) if r.remind_at else today

        if r.notified:
            history.append({
                "name": r.name,
                "reminder_type": reminder_type,
                "description": description,
                "remind_at": str(r.remind_at),
                "trigger_date": str(r.creation),
                "action_taken": "Notified",
                "status": "Completed",
            })
        else:
            if r.remind_at and r.remind_at < now:
                status = "Overdue"
            elif remind_date <= soon_threshold:
                status = "Due"
            else:
                status = "Upcoming"

            active.append({
                "name": r.name,
                "reminder_type": reminder_type,
                "description": description,
                "remind_at": str(r.remind_at),
                "next_due": str(r.remind_at),
                "status": status,
                "user": r.user,
            })

    return {
        "active": active,
        "history": history,
        "counts": {
            "overdue": sum(1 for a in active if a["status"] == "Overdue"),
            "due": sum(1 for a in active if a["status"] == "Due"),
            "upcoming": sum(1 for a in active if a["status"] == "Upcoming"),
        },
    }


@frappe.whitelist()
def create_vehicle_reminder(vehicle_name, remind_at, description, reminder_type="General"):
    """Create a service reminder for a vehicle."""
    reminder = frappe.get_doc({
        "doctype": "Reminder",
        "user": frappe.session.user,
        "remind_at": remind_at,
        "description": f"[{reminder_type}] {description}",
        "reminder_doctype": "Vehicle",
        "reminder_docname": vehicle_name,
    })
    reminder.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"name": reminder.name, "success": True}


@frappe.whitelist()
def dismiss_vehicle_reminder(reminder_name):
    """Dismiss a vehicle reminder by marking it as notified."""
    reminder = frappe.get_doc("Reminder", reminder_name)
    reminder.notified = 1
    reminder.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist()
def snooze_vehicle_reminder(reminder_name, days=7):
    """Snooze a vehicle reminder by pushing remind_at forward."""
    days = int(days)
    reminder = frappe.get_doc("Reminder", reminder_name)
    new_remind_at = datetime.now() + timedelta(days=days)
    reminder.remind_at = new_remind_at
    reminder.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "new_remind_at": str(new_remind_at)}


# ============================================================================
# TAB 9: ISSUES - Full issue tracking
# ============================================================================

@frappe.whitelist()
def get_vehicle_issues_full(vehicle_name):
    """Get comprehensive issues list for the vehicle."""
    today = getdate(nowdate())
    
    open_issues = []
    closed_issues = []
    
    all_issues = frappe.get_all(
        "Issue",
        filters={"custom_vehicle": vehicle_name},
        fields=[
            "name", "subject", "description", "custom_severity", "status",
            "raised_by", "creation", "sla_resolution_by", "custom_linked_work_order",
            "custom_resolution_notes", "modified"
        ],
        order_by="creation desc",
    )
    
    for issue in all_issues:
        item = {
            "name": issue.name,
            "title": issue.subject,
            "description": issue.description,
            "severity": issue.custom_severity or "Medium",
            "status": issue.status,
            "reported_by": issue.raised_by,
            "date": str(issue.creation)[:10],
            "linked_work_order": issue.custom_linked_work_order,
            "resolution_notes": issue.custom_resolution_notes,
        }
        
        if issue.status in ["Closed", "Resolved"]:
            closed_issues.append(item)
        else:
            item["is_overdue"] = issue.sla_resolution_by and getdate(issue.sla_resolution_by) < today
            open_issues.append(item)
    
    return {
        "open_issues": open_issues,
        "closed_issues": closed_issues[:10],  # Limit closed
        "counts": {
            "open": len(open_issues),
            "overdue": sum(1 for i in open_issues if i.get("is_overdue")),
            "closed": len(closed_issues),
        },
    }


# ============================================================================
# TAB 10: ATTACHMENTS - Document management
# ============================================================================

@frappe.whitelist()
def get_vehicle_attachments(vehicle_name):
    """Get all attachments linked to the vehicle."""
    
    # Get files attached to the Vehicle document
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Vehicle",
            "attached_to_name": vehicle_name,
        },
        fields=["name", "file_name", "file_url", "file_type", "file_size",
                "creation", "owner", "is_private"],
        order_by="creation desc",
    )
    
    # Categorize files by extension/type
    categories = {
        "registration": [],
        "insurance": [],
        "contracts": [],
        "certificates": [],
        "reports": [],
        "other": [],
    }
    
    for f in files:
        file_ext = (f.file_name or "").split(".")[-1].lower()
        category = "other"
        
        fname_lower = (f.file_name or "").lower()
        
        # Check for explicit category prefix first: [category] filename.ext
        prefix_match = re.match(r'^\[([\w\s/]+)\]\s*', fname_lower)
        if prefix_match:
            prefix_cat = prefix_match.group(1).strip().lower()
            prefix_map = {
                'registration': 'registration',
                'insurance': 'insurance',
                'contracts': 'contracts',
                'certificates': 'certificates',
                'reports': 'reports',
                'other': 'other',
            }
            if prefix_cat in prefix_map:
                category = prefix_map[prefix_cat]
        # Fall back to keyword-based categorization
        elif any(kw in fname_lower for kw in ["registration", "license", "plate"]):
            category = "registration"
        elif any(kw in fname_lower for kw in ["insurance", "policy"]):
            category = "insurance"
        elif any(kw in fname_lower for kw in ["contract", "lease", "purchase"]):
            category = "contracts"
        elif any(kw in fname_lower for kw in ["certificate", "cert", "inspection"]):
            category = "certificates"
        elif any(kw in fname_lower for kw in ["report"]):
            category = "reports"
        
        categories[category].append({
            "name": f.name,
            "file_name": f.file_name,
            "file_url": f.file_url,
            "type": file_ext.upper(),
            "size": f.file_size,
            "uploaded_by": f.owner,
            "upload_date": str(f.creation)[:10],
            "is_private": f.is_private,
        })
    
    # Flatten for table view
    all_files = []
    for cat, cat_files in categories.items():
        for cf in cat_files:
            cf["category"] = cat.title()
            all_files.append(cf)
    
    return {
        "folders": categories,
        "files": all_files,
        "counts": {cat: len(files) for cat, files in categories.items()},
        "total": len(all_files),
    }


@frappe.whitelist()
def upload_vehicle_attachment(vehicle_name, file_url, category=None):
    """Categorize an uploaded file by renaming with category prefix."""
    if not category or category == 'other':
        return {"success": True}

    file_name = frappe.db.get_value("File", {
        "file_url": file_url,
        "attached_to_doctype": "Vehicle",
        "attached_to_name": vehicle_name,
    })

    if file_name:
        file_doc = frappe.get_doc("File", file_name)
        clean_name = re.sub(r'^\[[\w\s/]+\]\s*', '', file_doc.file_name or '')
        file_doc.file_name = f"[{category}] {clean_name}"
        file_doc.save(ignore_permissions=True)
        frappe.db.commit()

    return {"success": True}


@frappe.whitelist()
def move_vehicle_attachment(file_name, vehicle_name, target_category):
    """Move an attachment to a different category by updating the filename prefix."""
    category_map = {
        'registration': 'registration',
        'insurance': 'insurance',
        'contracts': 'contracts',
        'certificates': 'certificates',
        'reports': 'reports',
        'other': 'other',
    }

    prefix = category_map.get(target_category, 'other')
    file_doc = frappe.get_doc("File", file_name)

    # Remove any existing category prefix
    clean_name = re.sub(r'^\[[\w\s/]+\]\s*', '', file_doc.file_name or '')

    # Add new category prefix
    new_name = f"[{prefix}] {clean_name}"
    file_doc.file_name = new_name
    file_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "new_name": new_name}


# ============================================================================
# CUSTODIAN & DRIVER MANAGEMENT
# ============================================================================

def _get_current_employee():
    """Get the Employee linked to the current session user."""
    return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


def _is_custodian(vehicle_doc, employee_id=None):
    """Check if the given employee (or current user's employee) is the custodian.
    System Managers can always manage assignments."""
    if "System Manager" in frappe.get_roles():
        return True
    if not employee_id:
        employee_id = _get_current_employee()
    custodian_id = vehicle_doc.custom_custodian or vehicle_doc.employee
    return custodian_id and custodian_id == employee_id


def _build_driver_data(d):
    """Build a single driver data dict with employee details."""
    driver_data = {
        "name": d.name,
        "employee": d.employee,
        "employee_name": d.employee_name,
        "assigned_date": str(d.assigned_date) if d.assigned_date else None,
        "assigned_by": d.assigned_by,
        "status": d.status or "Active",
        "ended_date": str(d.ended_date) if d.ended_date else None,
        "ended_by": d.ended_by,
        "removal_reason": d.removal_reason,
    }
    try:
        emp_doc = frappe.db.get_value("Employee", d.employee, ["image", "designation"], as_dict=True)
        if emp_doc:
            driver_data["image"] = emp_doc.image
            driver_data["designation"] = emp_doc.designation
    except Exception:
        pass
    return driver_data


def _build_assignment_response(vehicle_doc):
    """Build the response with custodian and driver data."""
    custodian = None
    custodian_id = vehicle_doc.custom_custodian or vehicle_doc.employee
    if custodian_id:
        try:
            emp = frappe.db.get_value(
                "Employee", custodian_id,
                ["name", "employee_name", "image", "designation"], as_dict=True,
            )
            if emp:
                custodian = dict(emp)
        except Exception:
            pass

    drivers = []
    driver_history = []
    for d in vehicle_doc.custom_drivers or []:
        driver_data = _build_driver_data(d)
        if d.status == "Removed":
            driver_history.append(driver_data)
        else:
            drivers.append(driver_data)

    return {"custodian": custodian, "drivers": drivers, "driver_history": driver_history}


@frappe.whitelist()
def set_custodian(vehicle_name, employee):
    """Set the custodian for a vehicle."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    vehicle.custom_custodian = employee
    if employee:
        vehicle.custom_custodian_name = frappe.db.get_value("Employee", employee, "employee_name")
    else:
        vehicle.custom_custodian_name = None
    vehicle.save(ignore_permissions=True)

    return _build_assignment_response(vehicle)


@frappe.whitelist()
def add_driver(vehicle_name, employee):
    """Add a driver to a vehicle. Only custodian can add drivers.
    Auto-closes any existing Active driver assignment before adding the new one."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)

    if not _is_custodian(vehicle):
        frappe.throw(_("Only the vehicle custodian can assign drivers."))

    # Check if this employee already has an Active assignment
    for d in vehicle.custom_drivers or []:
        if d.employee == employee and d.status == "Active":
            frappe.throw(_("This employee is already assigned as an active driver."))

    # Auto-close any existing Active driver
    assigner = _get_current_employee()
    for d in vehicle.custom_drivers or []:
        if d.status == "Active":
            d.status = "Removed"
            d.ended_date = nowdate()
            d.ended_by = assigner
            d.removal_reason = "Replaced by new driver assignment"

    vehicle.append("custom_drivers", {
        "employee": employee,
        "assigned_date": nowdate(),
        "assigned_by": assigner,
        "status": "Active",
    })
    vehicle.save(ignore_permissions=True)

    return _build_assignment_response(vehicle)


@frappe.whitelist()
def remove_driver(vehicle_name, driver_row_name):
    """Remove a driver from a vehicle. Marks as Removed instead of deleting to preserve history."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)

    if not _is_custodian(vehicle):
        frappe.throw(_("Only the vehicle custodian can remove drivers."))

    target = None
    for d in vehicle.custom_drivers:
        if d.name == driver_row_name:
            target = d
            break

    if not target:
        frappe.throw(_("Driver assignment not found."))

    target.status = "Removed"
    target.ended_date = nowdate()
    target.ended_by = _get_current_employee()
    vehicle.save(ignore_permissions=True)

    return _build_assignment_response(vehicle)


@frappe.whitelist()
def request_driver_removal(vehicle_name, driver_row_name):
    """A driver can request to be removed. Sets status to 'Removal Requested'."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)

    current_emp = _get_current_employee()
    target = None
    for d in vehicle.custom_drivers:
        if d.name == driver_row_name:
            target = d
            break

    if not target:
        frappe.throw(_("Driver assignment not found."))

    # Only the driver themselves or the custodian can request removal
    if target.employee != current_emp and not _is_custodian(vehicle, current_emp):
        frappe.throw(_("You can only request removal for your own driver assignment."))

    target.status = "Removal Requested"
    vehicle.save(ignore_permissions=True)

    return _build_assignment_response(vehicle)


@frappe.whitelist()
def get_vehicle_assignments_data(vehicle_name):
    """Get custodian, active drivers, and driver history for a vehicle."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)
    return _build_assignment_response(vehicle)


@frappe.whitelist()
def get_vehicle_driver_history(vehicle_name):
    """Return both current active driver and historical (Removed) drivers with employee details."""
    vehicle = frappe.get_doc("Vehicle", vehicle_name)

    current_driver = None
    driver_history = []
    for d in vehicle.custom_drivers or []:
        driver_data = _build_driver_data(d)
        if d.status == "Active":
            current_driver = driver_data
        elif d.status == "Removed":
            driver_history.append(driver_data)

    return {"current_driver": current_driver, "driver_history": driver_history}
