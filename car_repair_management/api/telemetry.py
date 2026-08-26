import json
from urllib.parse import urlparse

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


READ_ROLES = {"Telemetry Integration User", "Telemetry Integration Manager", "System Manager"}
WRITE_ROLES = {"Telemetry Integration User", "Telemetry Integration Manager", "System Manager"}
ADMIN_ROLES = {"Telemetry Integration Manager", "System Manager"}


SENSOR_MAP = {
	"odometer": ("Odometer", "km"),
	"engine": ("Engine State", ""),
	"status": ("Tracker Status", ""),
	"altitude": ("Altitude", "m"),
	"angle": ("Heading", "deg"),
	"speed": ("Speed", "km/h"),
	"fuel_1": ("Fuel 1", ""),
	"fuel_2": ("Fuel 2", ""),
	"fuel_can_level_percent": ("Fuel CAN Level Percent", "%"),
	"fuel_can_level_value": ("Fuel CAN Level Value", "mL"),
	"group": ("Group", ""),
}


@frappe.whitelist(methods=["POST", "GET"])
def telemetry(
	action="create",
	payload=None,
	batch_id=None,
	vehicle=None,
	imei=None,
	date_from=None,
	date_to=None,
	limit_start=0,
	limit_page_length=20,
):
	"""Central CRUD endpoint for hardware telemetry ingestion.

	Endpoint:
	    /api/method/car_repair_management.api.telemetry.telemetry

	Supported actions:
	    create, read, list, update, delete
	"""
	action = (action or "create").lower()

	if action in ("create",):
		_require_role(WRITE_ROLES)
		return _create(payload, batch_id=batch_id)
	if action in ("read", "get"):
		_require_role(READ_ROLES)
		if not batch_id:
			frappe.throw(_("batch_id is required for read"))
		return _read(batch_id)
	if action == "list":
		_require_role(READ_ROLES)
		return _list(
			vehicle=vehicle,
			imei=imei,
			date_from=date_from,
			date_to=date_to,
			limit_start=limit_start,
			limit_page_length=limit_page_length,
		)
	if action == "update":
		_require_role(ADMIN_ROLES)
		if not batch_id:
			frappe.throw(_("batch_id is required for update"))
		_delete(batch_id)
		return _create(payload, batch_id=batch_id)
	if action == "delete":
		_require_role(ADMIN_ROLES)
		if not batch_id:
			frappe.throw(_("batch_id is required for delete"))
		return _delete(batch_id)

	frappe.throw(_("Unsupported telemetry action: {0}").format(action))


def _require_role(allowed_roles):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.PermissionError)
	if not (set(frappe.get_roles()) & set(allowed_roles)):
		frappe.throw(_("Not permitted for telemetry API"), frappe.PermissionError)


def _parse_json(value):
	if not value:
		return {}
	if isinstance(value, dict):
		return value
	if isinstance(value, str):
		try:
			return json.loads(value)
		except ValueError:
			frappe.throw(_("payload must be valid JSON"))
	frappe.throw(_("payload must be a JSON object"))


def _create(payload, batch_id=None):
	data = _parse_json(payload)
	_validate_payload(data)

	batch_id = batch_id or _new_batch_id()
	vehicle_name = _resolve_vehicle(data)
	timestamp = data.get("dt_tracker") or data.get("dt_server") or now_datetime()
	imei = str(data.get("imei") or "").strip()
	device_name = str(data.get("name") or "").strip()

	created = {"location": None, "fuel_level": None, "sensor_data": []}

	location = _create_location(data, vehicle_name, timestamp, batch_id, imei, device_name)
	if location:
		created["location"] = location.name

	fuel_level = _create_fuel_level(data, vehicle_name, timestamp, batch_id, imei, device_name, location)
	if fuel_level:
		created["fuel_level"] = fuel_level.name

	for sensor_name in _create_sensor_data(data, vehicle_name, timestamp, batch_id, imei, device_name):
		created["sensor_data"].append(sensor_name)

	_update_vehicle_live_status(data, vehicle_name, timestamp)

	return {
		"ok": True,
		"action": "create",
		"batch_id": batch_id,
		"vehicle": vehicle_name,
		"created": created,
	}


def _validate_payload(data):
	if not data.get("imei"):
		frappe.throw(_("imei is required"))
	if not (data.get("dt_tracker") or data.get("dt_server")):
		frappe.throw(_("dt_tracker or dt_server is required"))


def _resolve_vehicle(data):
	imei = str(data.get("imei") or "").strip()
	device_name = str(data.get("name") or "").strip()

	vehicle = None
	if imei and frappe.db.has_column("Vehicle", "custom_telematics_imei"):
		vehicle = frappe.db.get_value("Vehicle", {"custom_telematics_imei": imei}, "name")

	if not vehicle and device_name:
		vehicle = frappe.db.get_value("Vehicle", {"license_plate": device_name}, "name")
	if not vehicle and device_name and frappe.db.exists("Vehicle", device_name):
		vehicle = device_name

	if not vehicle:
		frappe.throw(
			_("No Vehicle found for telemetry imei '{0}'. Set Vehicle.custom_telematics_imei first.").format(imei)
		)
	return vehicle


def _create_location(data, vehicle_name, timestamp, batch_id, imei, device_name):
	if not (frappe.db.exists("DocType", "Vehicle Location") and data.get("lat") and data.get("lng")):
		return None

	doc = frappe.new_doc("Vehicle Location")
	doc.vehicle = vehicle_name
	doc.timestamp = timestamp
	doc.latitude = flt(data.get("lat"))
	doc.longitude = flt(data.get("lng"))
	doc.direction = flt(data.get("angle"))
	doc.speed = flt(data.get("speed"))
	_set_if_exists(doc, "altitude", flt(data.get("altitude")))
	_set_common_fields(doc, batch_id, imei, device_name)
	doc.insert(ignore_permissions=True)
	return doc


def _create_fuel_level(data, vehicle_name, timestamp, batch_id, imei, device_name, location):
	if not frappe.db.exists("DocType", "Vehicle Fuel Level"):
		return None

	level = data.get("fuel_can_level_percent")
	if level in (None, ""):
		level = _fuel_percent_from_volume(vehicle_name, data.get("fuel_can_level_value"))
	if level in (None, ""):
		return None

	doc = frappe.new_doc("Vehicle Fuel Level")
	doc.vehicle = vehicle_name
	doc.timestamp = timestamp
	doc.fuel_level = flt(level)
	if location:
		doc.location = location.name
	_set_common_fields(doc, batch_id, imei, device_name)
	doc.insert(ignore_permissions=True)
	return doc


def _fuel_percent_from_volume(vehicle_name, fuel_volume_ml):
	if fuel_volume_ml in (None, ""):
		return None

	capacity_liters = _get_vehicle_fuel_capacity_liters(vehicle_name)
	if not capacity_liters:
		return None

	percent = (flt(fuel_volume_ml) / 1000) / capacity_liters * 100
	return max(0, min(round(percent, 2), 100))


def _get_vehicle_fuel_capacity_liters(vehicle_name):
	fields = []
	if frappe.db.has_column("Vehicle", "custom_fuel_capacity_liters"):
		fields.append("custom_fuel_capacity_liters")
	if frappe.db.has_column("Vehicle", "fuel_tank_capacity"):
		fields.append("fuel_tank_capacity")
	if not fields:
		return 0

	values = frappe.db.get_value("Vehicle", vehicle_name, fields, as_dict=True) or {}
	for fieldname in fields:
		capacity = _parse_capacity_liters(values.get(fieldname))
		if capacity:
			return capacity
	return 0


def _parse_capacity_liters(value):
	if value in (None, ""):
		return 0
	if isinstance(value, (int, float)):
		return flt(value)
	text = str(value)
	digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
	return flt(digits)


def _create_sensor_data(data, vehicle_name, timestamp, batch_id, imei, device_name):
	if not frappe.db.exists("DocType", "Vehicle Sensor Data"):
		return []

	created = []
	for fieldname, sensor_def in SENSOR_MAP.items():
		value = data.get(fieldname)
		if value in (None, ""):
			continue
		sensor_type, unit = sensor_def
		created.append(
			_insert_sensor(vehicle_name, timestamp, sensor_type, value, unit, batch_id, imei, device_name)
		)

	custom_fields = data.get("custom_fields")
	if isinstance(custom_fields, str):
		try:
			custom_fields = json.loads(custom_fields)
		except ValueError:
			custom_fields = None
	if isinstance(custom_fields, dict):
		for key, value in custom_fields.items():
			if value in (None, ""):
				continue
			created.append(
				_insert_sensor(
					vehicle_name,
					timestamp,
					"Custom Field: {0}".format(key),
					value,
					"",
					batch_id,
					imei,
					device_name,
				)
			)

	return created


def _insert_sensor(vehicle_name, timestamp, sensor_type, value, unit, batch_id, imei, device_name):
	doc = frappe.new_doc("Vehicle Sensor Data")
	doc.vehicle = vehicle_name
	doc.timestamp = timestamp
	doc.sensor_type = sensor_type
	doc.value = str(value)
	doc.unit = unit
	_set_common_fields(doc, batch_id, imei, device_name)
	doc.insert(ignore_permissions=True)
	return doc.name


def _update_vehicle_live_status(data, vehicle_name, timestamp):
	updates = {}
	if data.get("lat") and data.get("lng"):
		updates["custom_last_known_latitude"] = flt(data.get("lat"))
		updates["custom_last_known_longitude"] = flt(data.get("lng"))
		updates["custom_last_location_update"] = timestamp
	if data.get("odometer") not in (None, ""):
		updates["last_odometer"] = flt(data.get("odometer"))
	if data.get("fuel_can_level_percent") not in (None, ""):
		updates["custom_fuel_level"] = flt(data.get("fuel_can_level_percent"))
	else:
		computed_fuel_level = _fuel_percent_from_volume(vehicle_name, data.get("fuel_can_level_value"))
		if computed_fuel_level not in (None, ""):
			updates["custom_fuel_level"] = computed_fuel_level

	for fieldname, value in updates.items():
		if frappe.db.has_column("Vehicle", fieldname):
			frappe.db.set_value("Vehicle", vehicle_name, fieldname, value, update_modified=False)


def _set_common_fields(doc, batch_id, imei, device_name):
	_set_if_exists(doc, "telemetry_batch_id", batch_id)
	_set_if_exists(doc, "source_imei", imei)
	_set_if_exists(doc, "device_name", device_name)


def _set_if_exists(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


def _read(batch_id):
	return {
		"batch_id": batch_id,
		"location": _get_records("Vehicle Location", batch_id),
		"fuel_level": _get_records("Vehicle Fuel Level", batch_id),
		"sensor_data": _get_records("Vehicle Sensor Data", batch_id),
	}


def _list(vehicle=None, imei=None, date_from=None, date_to=None, limit_start=0, limit_page_length=20):
	batches = {}
	for doctype in ("Vehicle Location", "Vehicle Fuel Level", "Vehicle Sensor Data"):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, "telemetry_batch_id"):
			continue
		filters = _build_filters(vehicle, imei, date_from, date_to)
		rows = frappe.get_all(
			doctype,
			filters=filters,
			fields=["name", "vehicle", "timestamp", "telemetry_batch_id", "source_imei", "device_name"],
			order_by="timestamp desc",
			limit=500,
		)
		for row in rows:
			if not row.telemetry_batch_id:
				continue
			entry = batches.setdefault(
				row.telemetry_batch_id,
				{
					"batch_id": row.telemetry_batch_id,
					"vehicle": row.vehicle,
					"timestamp": row.timestamp,
					"source_imei": row.source_imei,
					"device_name": row.device_name,
					"record_counts": {"location": 0, "fuel_level": 0, "sensor_data": 0},
				},
			)
			if str(row.timestamp) > str(entry["timestamp"]):
				entry["timestamp"] = row.timestamp
			entry["record_counts"][_record_key(doctype)] += 1

	records = sorted(batches.values(), key=lambda x: str(x["timestamp"]), reverse=True)
	start = int(limit_start or 0)
	limit = int(limit_page_length or 20)
	return {"records": records[start : start + limit], "total": len(records)}


def _delete(batch_id):
	deleted = {"location": 0, "fuel_level": 0, "sensor_data": 0}
	for doctype in ("Vehicle Location", "Vehicle Fuel Level", "Vehicle Sensor Data"):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, "telemetry_batch_id"):
			continue
		names = frappe.get_all(doctype, filters={"telemetry_batch_id": batch_id}, pluck="name")
		for name in names:
			frappe.delete_doc(doctype, name, ignore_permissions=True)
			deleted[_record_key(doctype)] += 1
	return {"ok": True, "action": "delete", "batch_id": batch_id, "deleted": deleted}


def _get_records(doctype, batch_id):
	if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, "telemetry_batch_id"):
		return []
	return frappe.get_all(
		doctype,
		filters={"telemetry_batch_id": batch_id},
		fields=["*"],
		order_by="timestamp asc",
	)


def _build_filters(vehicle=None, imei=None, date_from=None, date_to=None):
	filters = {}
	if vehicle:
		filters["vehicle"] = vehicle
	if imei:
		filters["source_imei"] = imei
	if date_from and date_to:
		filters["timestamp"] = ["between", [date_from, date_to]]
	elif date_from:
		filters["timestamp"] = [">=", date_from]
	elif date_to:
		filters["timestamp"] = ["<=", date_to]
	return filters


def _record_key(doctype):
	return {
		"Vehicle Location": "location",
		"Vehicle Fuel Level": "fuel_level",
		"Vehicle Sensor Data": "sensor_data",
	}[doctype]


def _new_batch_id():
	return "TLM-{0}".format(frappe.generate_hash(length=12).upper())


@frappe.whitelist(methods=["POST", "GET"])
def hardware_test_configuration(action="list", name=None, data=None):
	"""CRUD and run endpoint for external mock hardware API configurations."""
	_require_role(ADMIN_ROLES)
	action = (action or "list").lower()

	if action == "list":
		return _list_test_configurations()
	if action in ("read", "get"):
		if not name:
			frappe.throw(_("name is required"))
		return _get_test_configuration(name)
	if action == "create":
		return _save_test_configuration(data)
	if action == "update":
		if not name:
			frappe.throw(_("name is required"))
		return _save_test_configuration(data, name=name)
	if action == "delete":
		if not name:
			frappe.throw(_("name is required"))
		frappe.delete_doc("Hardware Test Configuration", name, ignore_permissions=True)
		return {"ok": True, "deleted": name}
	if action == "run":
		if not name:
			frappe.throw(_("name is required"))
		return _run_test_configuration(name)

	frappe.throw(_("Unsupported hardware test configuration action: {0}").format(action))


def _list_test_configurations():
	if not frappe.db.exists("DocType", "Hardware Test Configuration"):
		return {"records": [], "total": 0}

	records = frappe.get_all(
		"Hardware Test Configuration",
		fields=[
			"name",
			"configuration_name",
			"enabled",
			"endpoint_url",
			"http_method",
			"api_key_header",
			"response_root",
			"ingest_on_run",
			"max_records_per_run",
			"last_run",
			"last_status",
			"last_ingested_count",
			"last_error",
			"modified",
		],
		order_by="modified desc",
	)
	return {"records": records, "total": len(records)}


def _get_test_configuration(name):
	doc = frappe.get_doc("Hardware Test Configuration", name)
	data = doc.as_dict()
	data.pop("api_key", None)
	data["has_api_key"] = bool(doc.get_password("api_key") if doc.get("api_key") else None)
	return data


def _save_test_configuration(data, name=None):
	data = _parse_json(data)
	allowed_fields = {
		"configuration_name",
		"enabled",
		"endpoint_url",
		"http_method",
		"api_key_header",
		"api_key",
		"request_body_json",
		"response_root",
		"ingest_on_run",
		"max_records_per_run",
	}

	if name:
		doc = frappe.get_doc("Hardware Test Configuration", name)
	else:
		doc = frappe.new_doc("Hardware Test Configuration")

	for fieldname, value in data.items():
		if fieldname in allowed_fields:
			doc.set(fieldname, value)

	if not doc.configuration_name:
		frappe.throw(_("configuration_name is required"))
	if not doc.endpoint_url:
		frappe.throw(_("endpoint_url is required"))
	if not doc.api_key_header:
		doc.api_key_header = "key"
	if not doc.http_method:
		doc.http_method = "GET"
	if not doc.max_records_per_run:
		doc.max_records_per_run = 50

	_validate_test_endpoint_url(doc.endpoint_url)
	_validate_request_body(doc.request_body_json)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return _get_test_configuration(doc.name)


def _run_test_configuration(name):
	import requests

	doc = frappe.get_doc("Hardware Test Configuration", name)
	if not doc.enabled:
		frappe.throw(_("Hardware test configuration is disabled"))

	_validate_test_endpoint_url(doc.endpoint_url)
	headers = {}
	api_key = doc.get_password("api_key") if doc.get("api_key") else None
	if api_key:
		headers[doc.api_key_header or "key"] = api_key

	method = (doc.http_method or "GET").upper()
	body = _parse_optional_json(doc.request_body_json)

	try:
		if method == "POST":
			response = requests.post(doc.endpoint_url, headers=headers, json=body or None, timeout=20)
		else:
			response = requests.get(doc.endpoint_url, headers=headers, timeout=20)
		response.raise_for_status()
		response_data = response.json()
	except Exception as exc:
		_update_test_configuration_status(doc, "Failed", 0, str(exc), None)
		frappe.throw(_("Hardware test request failed: {0}").format(exc))

	payloads = _extract_response_payloads(response_data, doc.response_root)
	limit = int(doc.max_records_per_run or 50)
	payloads = payloads[:limit]

	ingested = []
	errors = []
	if doc.ingest_on_run:
		for payload in payloads:
			try:
				ingested.append(_create(payload))
			except Exception as exc:
				errors.append(str(exc))

	status = "Success" if not errors else "Partial Success"
	error_text = "\n".join(errors[:5])
	_update_test_configuration_status(doc, status, len(ingested), error_text, response_data)

	return {
		"ok": not errors,
		"configuration": doc.name,
		"fetched_count": len(payloads),
		"ingested_count": len(ingested),
		"errors": errors,
		"sample": payloads[:3],
	}


def _validate_test_endpoint_url(url):
	parsed = urlparse(url or "")
	if parsed.scheme not in ("http", "https") or not parsed.netloc:
		frappe.throw(_("Endpoint URL must be an absolute http or https URL"))


def _validate_request_body(value):
	if value:
		_parse_optional_json(value)


def _parse_optional_json(value):
	if not value:
		return None
	if isinstance(value, dict):
		return value
	if isinstance(value, str):
		try:
			return json.loads(value)
		except ValueError:
			frappe.throw(_("Request Body JSON must be valid JSON"))
	frappe.throw(_("Request Body JSON must be a JSON object"))


def _extract_response_payloads(response_data, response_root=None):
	data = response_data
	if response_root:
		for part in response_root.split("."):
			if isinstance(data, dict):
				data = data.get(part)
			else:
				data = None
			if data is None:
				break

	if isinstance(data, list):
		return [row for row in data if isinstance(row, dict)]
	if isinstance(data, dict):
		for key in ("data", "objects", "items", "results"):
			value = data.get(key)
			if isinstance(value, list):
				return [row for row in value if isinstance(row, dict)]
		return [data]
	return []


def _update_test_configuration_status(doc, status, ingested_count, error_text, response_data):
	doc.last_run = now_datetime()
	doc.last_status = status
	doc.last_ingested_count = ingested_count
	doc.last_error = error_text
	if response_data is not None:
		doc.last_response_sample = json.dumps(response_data, indent=2, default=str)[:5000]
	doc.save(ignore_permissions=True)
