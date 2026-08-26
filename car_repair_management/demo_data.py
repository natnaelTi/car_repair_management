import frappe
import json
import os
import random
import string
from datetime import date, timedelta
from frappe.utils import getdate, nowdate, add_days, flt, now_datetime


REGISTRY_FILE = "demo_data_registry.json"
MOCK_HARDWARE_DEVICE = {
	"vehicle_plate": "P0325 AA",
	"imei": "354002391335211",
	"provider": "Mellatech",
}

# ── Data definitions ─────────────────────────────────────────────────────────

CUSTOMERS = [
	("Ethiopian Airlines Ground Services", "Commercial"),
	("Addis Bus PLC", "Commercial"),
	("Megenagna Taxi Association", "Commercial"),
	("Bole Transport Services", "Commercial"),
	("Blue Nile Logistics", "Commercial"),
	("Sheger City Bus Service", "Commercial"),
	("Golden Transport PLC", "Commercial"),
	("Abyssinia Delivery Services", "Commercial"),
	("Unity Taxi PLC", "Commercial"),
	("Lion Fleet Management", "Commercial"),
	("Meskel Square Auto", "Commercial"),
	("Entoto Car Rental", "Commercial"),
	("Sidama Transport Co.", "Commercial"),
	("Ambassador Garage", "Commercial"),
	("Capital City Logistics", "Commercial"),
]

VEHICLES = [
	("P0325 AA", "Toyota", "Land Cruiser", "SUV", 2022, "Diesel", "Automatic", "White"),
	("3-10234", "Toyota", "Land Cruiser", "SUV", 2019, "Diesel", "Automatic", "White"),
	("3-10567", "Toyota", "Land Cruiser", "SUV", 2020, "Diesel", "Automatic", "Silver"),
	("3-11023", "Toyota", "Hilux", "Truck", 2021, "Diesel", "Manual", "White"),
	("3-11456", "Toyota", "Hilux", "Truck", 2018, "Diesel", "Manual", "Gray"),
	("3-12089", "Toyota", "Corolla", "Car", 2022, "Petrol", "Automatic", "Black"),
	("3-12345", "Toyota", "Corolla", "Car", 2020, "Petrol", "CVT", "Blue"),
	("3-12890", "Toyota", "Yaris", "Car", 2021, "Petrol", "Automatic", "Red"),
	("3-13456", "Toyota", "RAV4", "SUV", 2023, "Petrol", "Automatic", "White"),
	("3-14012", "Nissan", "Patrol", "SUV", 2019, "Diesel", "Automatic", "Black"),
	("3-14567", "Nissan", "X-Trail", "SUV", 2020, "Petrol", "CVT", "Silver"),
	("3-15023", "Nissan", "Sunny", "Car", 2017, "Petrol", "Manual", "White"),
	("3-15890", "Hyundai", "Tucson", "SUV", 2022, "Diesel", "Automatic", "Gray"),
	("3-16345", "Hyundai", "Santa Fe", "SUV", 2021, "Diesel", "Automatic", "Blue"),
	("3-16901", "Hyundai", "Accent", "Car", 2019, "Petrol", "Automatic", "Silver"),
	("3-17456", "Hyundai", "Accent", "Car", 2018, "Petrol", "Manual", "White"),
	("3-18012", "Mitsubishi", "L200", "Truck", 2020, "Diesel", "Manual", "Silver"),
	("3-18567", "Mitsubishi", "L200", "Truck", 2019, "Diesel", "Automatic", "White"),
	("3-19023", "Mitsubishi", "Pajero", "SUV", 2017, "Diesel", "Automatic", "Black"),
	("3-19890", "Isuzu", "D-Max", "Truck", 2021, "Diesel", "Manual", "White"),
	("3-20345", "Isuzu", "D-Max", "Truck", 2020, "Diesel", "Manual", "Gray"),
	("3-20901", "Suzuki", "Vitara", "SUV", 2022, "Petrol", "Automatic", "Red"),
	("3-21456", "Suzuki", "Swift", "Car", 2021, "Petrol", "Automatic", "Blue"),
	("3-22012", "Toyota", "Hilux", "Truck", 2023, "Diesel", "Automatic", "White"),
	("3-22567", "Nissan", "Patrol", "SUV", 2018, "Diesel", "Automatic", "Silver"),
	("3-23123", "Hyundai", "Tucson", "SUV", 2020, "Petrol", "Automatic", "Black"),
	("3-23890", "Toyota", "Land Cruiser", "SUV", 2016, "Diesel", "Automatic", "White"),
	("3-24345", "Mitsubishi", "Pajero", "SUV", 2015, "Diesel", "Automatic", "Gray"),
	("3-24901", "Isuzu", "NPR", "Truck", 2019, "Diesel", "Manual", "White"),
	("3-25456", "Toyota", "Corolla", "Car", 2023, "Petrol", "CVT", "Silver"),
	("3-26012", "Nissan", "Sunny", "Car", 2016, "Petrol", "Manual", "White"),
]

EMPLOYEES = [
	("Abebe", "Kebede", "Male", "1988-03-15", "Technician"),
	("Tigist", "Haile", "Female", "1992-07-22", "Inspector"),
	("Dawit", "Mengistu", "Male", "1985-11-08", "Technician"),
	("Selam", "Tesfaye", "Female", "1990-05-30", "Technician"),
	("Yonas", "Bekele", "Male", "1993-01-12", "Technician"),
	("Marta", "Gebre", "Female", "1991-09-18", "Inspector"),
	("Solomon", "Tadesse", "Male", "1987-06-25", "Technician"),
	("Hana", "Worku", "Female", "1994-12-03", "Inspector"),
]

# (item_code, item_name, uom, reorder_level)
PARTS = [
	("DEMO-OIL-FILTER", "Oil Filter", "Nos", 15),
	("DEMO-AIR-FILTER", "Air Filter", "Nos", 12),
	("DEMO-FUEL-FILTER", "Fuel Filter", "Nos", 10),
	("DEMO-BRAKE-PAD", "Brake Pad Set", "Set", 8),
	("DEMO-BRAKE-DISC", "Brake Disc", "Nos", 6),
	("DEMO-SPARK-PLUG", "Spark Plug Set", "Set", 10),
	("DEMO-BATTERY-12V", "Car Battery 12V", "Nos", 5),
	("DEMO-ALTERNATOR", "Alternator", "Nos", 3),
	("DEMO-STARTER", "Starter Motor", "Nos", 3),
	("DEMO-RADIATOR", "Radiator", "Nos", 4),
	("DEMO-TIMING-BELT", "Timing Belt", "Nos", 6),
	("DEMO-FAN-BELT", "Fan Belt", "Nos", 8),
	("DEMO-CLUTCH-KIT", "Clutch Kit", "Set", 4),
	("DEMO-CV-JOINT", "CV Joint", "Nos", 5),
	("DEMO-SHOCK-ABS", "Shock Absorber", "Nos", 8),
	("DEMO-WIPER-BLADE", "Wiper Blade Set", "Set", 12),
	("DEMO-HEADLIGHT", "Headlight Bulb", "Nos", 15),
	("DEMO-TAILLIGHT", "Tail Light Assembly", "Nos", 6),
	("DEMO-THERMOSTAT", "Thermostat", "Nos", 5),
	("DEMO-WATER-PUMP", "Water Pump", "Nos", 4),
	("DEMO-PS-PUMP", "Power Steering Pump", "Nos", 3),
	("DEMO-AC-COMP", "AC Compressor", "Nos", 3),
	("DEMO-FUEL-PUMP", "Fuel Pump", "Nos", 4),
	("DEMO-O2-SENSOR", "Oxygen Sensor", "Nos", 6),
	("DEMO-TRANS-FLUID", "Transmission Fluid", "Litre", 20),
]

SERVICE_TEMPLATES = [
	("Full Vehicle Service", [
		("Oil & Filter Change", 45),
		("Multi-Point Inspection", 30),
		("Fluid Top-Up", 20),
		("Brake Inspection", 25),
	], ["DEMO-OIL-FILTER", "DEMO-AIR-FILTER", "DEMO-SPARK-PLUG", "DEMO-TRANS-FLUID"]),
	("Brake System Service", [
		("Brake Pad Replacement", 60),
		("Brake Disc Inspection", 30),
		("Brake Fluid Flush", 25),
	], ["DEMO-BRAKE-PAD", "DEMO-BRAKE-DISC"]),
	("Engine Tune-Up", [
		("Spark Plug Replacement", 40),
		("Timing Belt Check", 30),
		("Fuel System Cleaning", 45),
	], ["DEMO-SPARK-PLUG", "DEMO-FUEL-FILTER", "DEMO-TIMING-BELT"]),
	("AC System Service", [
		("Compressor Check", 30),
		("Refrigerant Recharge", 45),
		("Belt Inspection", 15),
	], ["DEMO-AC-COMP", "DEMO-FAN-BELT"]),
	("Transmission Service", [
		("Fluid Change", 40),
		("Filter Replacement", 25),
		("Linkage Adjustment", 20),
	], ["DEMO-TRANS-FLUID", "DEMO-FUEL-FILTER"]),
]

INSPECTION_TEMPLATES = [
	("Pre-Trip Safety Check", "Pre-Trip", [
		("Tire Condition & Pressure", "Pass/Fail", "Exterior", True, "High"),
		("All Lights Functional", "Pass/Fail", "Exterior", True, "Critical"),
		("Windshield & Wipers", "Pass/Fail", "Exterior", True, "Medium"),
		("Brake Pedal Response", "Pass/Fail", "Mechanical", True, "Critical"),
		("Horn Functional", "Pass/Fail", "Safety", True, "Medium"),
		("Mirrors Adjusted", "Pass/Fail", "Interior", True, "Low"),
		("Seat Belts Working", "Pass/Fail", "Safety", True, "Critical"),
		("Fluid Levels", "Pass/Fail", "Mechanical", False, "Medium"),
	]),
	("Post-Trip Condition Check", "Post-Trip", [
		("Body Damage Check", "Pass/Fail", "Exterior", True, "Medium"),
		("Tire Condition", "Pass/Fail", "Exterior", True, "High"),
		("Interior Cleanliness", "Rating", "Interior", False, "Low"),
		("Fuel Level", "Numeric", "Dashboard", True, "Low"),
		("Warning Lights", "Pass/Fail", "Dashboard", True, "High"),
		("Unusual Noises", "Text", "Mechanical", False, "Medium"),
	]),
	("Monthly Safety Inspection", "Safety", [
		("Brake System", "Pass/Fail", "Braking", True, "Critical"),
		("Steering Play", "Numeric", "Steering", True, "High"),
		("Suspension Condition", "Pass/Fail", "Suspension", True, "High"),
		("Exhaust System", "Pass/Fail", "Exhaust", True, "Medium"),
		("Battery Voltage", "Numeric", "Electrical", True, "Medium"),
		("Tire Tread Depth", "Numeric", "Tires", True, "High"),
		("All Lights", "Pass/Fail", "Electrical", True, "Medium"),
		("Fire Extinguisher", "Pass/Fail", "Safety", True, "Critical"),
		("First Aid Kit", "Pass/Fail", "Safety", True, "Medium"),
		("Reflective Triangle", "Pass/Fail", "Safety", True, "Low"),
	]),
	("Annual Regulatory Inspection", "Regulatory", [
		("Emissions Test", "Pass/Fail", "Emissions", True, "Critical"),
		("Brake Efficiency", "Numeric", "Braking", True, "Critical"),
		("Headlight Alignment", "Pass/Fail", "Electrical", True, "High"),
		("Horn dB Level", "Numeric", "Safety", True, "Medium"),
		("Windshield Integrity", "Pass/Fail", "Body", True, "Medium"),
		("Chassis Condition", "Pass/Fail", "Structural", True, "Critical"),
		("Seat Belt Test", "Pass/Fail", "Safety", True, "Critical"),
	]),
	("Vehicle Handover Checklist", "Custom", [
		("Exterior Condition", "Rating", "Exterior", True, "Medium"),
		("Interior Condition", "Rating", "Interior", True, "Medium"),
		("All Documents Present", "Pass/Fail", "Admin", True, "Low"),
		("Spare Tire Present", "Pass/Fail", "Equipment", True, "Low"),
		("Jack & Tools Present", "Pass/Fail", "Equipment", True, "Low"),
		("Odometer Reading", "Numeric", "Dashboard", True, "Low"),
	]),
]

INSURANCE_COMPANIES = [
	"Ethiopian Insurance Corporation",
	"Nyala Insurance",
	"Awash Insurance",
	"Nile Insurance",
	"United Insurance",
]

VARIANT_MAP = {
	"Toyota": ["GX", "VX", "GL", "SR5", ""],
	"Nissan": ["SE", "SV", "SL", ""],
	"Hyundai": ["GL", "GLS", "Limited", ""],
	"Mitsubishi": ["GLX", "GLS", "VGT", ""],
	"Isuzu": ["LS", "LX", ""],
	"Suzuki": ["GL", "GLX", ""],
}

EXPENSE_DESCRIPTIONS = {
	"Fuel": [
		"Diesel refill at Total Station",
		"Monthly fuel allowance",
		"Fuel top-up before long trip",
		"Petrol refill at NOC station",
	],
	"Parts": [
		"Replaced brake pads",
		"New battery installed",
		"Windshield wiper replacement",
		"New tire set installed",
	],
	"Labor": [
		"Engine diagnostic service",
		"Routine maintenance labor",
		"Electrical system troubleshooting",
		"Suspension repair labor",
	],
	"External Service": [
		"Windshield replacement at authorized dealer",
		"Body paint repair at Megenagna workshop",
		"AC recharge at specialist shop",
	],
	"Insurance": [
		"Annual comprehensive insurance renewal",
		"Insurance premium quarterly payment",
	],
	"Taxes": [
		"Annual vehicle registration tax",
		"Road usage levy payment",
	],
	"Other": [
		"Parking permit renewal",
		"Vehicle cleaning service",
	],
}

PROBLEM_SUMMARIES = [
	"Engine overheating, temperature gauge showing red",
	"Unusual grinding noise from front brakes",
	"AC not cooling, blowing warm air",
	"Check engine light on, rough idle",
	"Power steering fluid leak",
	"Transmission slipping in 3rd gear",
	"Battery not holding charge, slow cranking",
	"Suspension noise on bumpy roads",
	"Exhaust smoke on startup, blue-ish color",
	"Windshield wiper motor not working",
	"Headlight alignment off, poor visibility",
	"Oil leak underneath vehicle",
	"Clutch pedal feels soft, slipping",
	"ABS warning light on dashboard",
	"Water pump making whining noise",
	"Timing belt due for replacement",
	"Radiator leak, coolant loss",
	"Fuel pump intermittent failure",
	"Alternator not charging battery",
	"CV joint clicking on turns",
]

FAILURE_ITEMS = [
	"Brake Pads", "Tire Tread", "Headlight", "Windshield Wiper",
	"Oil Level", "Battery Voltage", "Exhaust System", "Steering Play",
	"Suspension", "Horn", "Seat Belt", "Fire Extinguisher",
]

FAULT_CODES = [
	("P0300", "Engine", "Random/Multiple Cylinder Misfire"),
	("P0171", "Engine", "System Too Lean Bank 1"),
	("P0420", "Exhaust", "Catalyst System Efficiency Below Threshold"),
	("P0442", "Exhaust", "Evaporative Emission System Leak Detected"),
	("P0455", "Exhaust", "EVAP System Large Leak Detected"),
	("B1234", "Electrical", "Instrument Cluster Communication Error"),
	("C0035", "Braking", "Left Front Wheel Speed Sensor Circuit"),
	("U0100", "Electrical", "Lost Communication with ECM/PCM"),
	("P0128", "Engine", "Coolant Thermostat Below Regulating Temperature"),
	("P0562", "Electrical", "System Voltage Low"),
]

ISSUE_SUBJECTS = [
	"Engine vibration at idle - needs diagnosis",
	"Driver reports unusual brake noise",
	"AC intermittent failure in hot weather",
	"Dashboard warning light - ABS sensor",
	"Power window stuck - driver side",
	"Fuel gauge reading incorrectly",
	"Rear suspension sagging under load",
	"Steering wheel vibration at highway speed",
	"Coolant temperature fluctuating",
	"Door lock actuator malfunction",
	"Wiper motor delayed response",
	"Battery drain overnight",
	"Transmission hard shift 2nd to 3rd",
	"Exhaust rattle on acceleration",
	"Headlight condensation inside lens",
	"Paint peeling on roof panel",
	"Wheel bearing noise - rear left",
	"Turbo lag increased significantly",
	"Windshield crack spreading",
	"Tail light water ingress",
	"Horn intermittent failure",
	"Radio/infotainment system frozen",
	"Key fob battery low warning",
	"Tire pressure sensor fault",
	"Oil consumption higher than normal",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_registry_path():
	return os.path.join(frappe.get_site_path(), "private", REGISTRY_FILE)


def _load_registry():
	path = _get_registry_path()
	if os.path.exists(path):
		with open(path) as f:
			return json.load(f)
	return {}


def _save_registry(registry):
	path = _get_registry_path()
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as f:
		json.dump(registry, f, indent=2)


def _reg(registry, doctype, name):
	registry.setdefault(doctype, []).append(name)


def _random_date(days_back_start, days_back_end=0):
	"""Random date between days_back_start and days_back_end days ago."""
	today = date.today()
	start = today - timedelta(days=days_back_start)
	end = today - timedelta(days=days_back_end)
	delta = (end - start).days
	if delta <= 0:
		return str(end)
	return str(start + timedelta(days=random.randint(0, delta)))


def _random_datetime(days_back_start, days_back_end=0):
	d = _random_date(days_back_start, days_back_end)
	h = random.randint(7, 17)
	m = random.randint(0, 59)
	return f"{d} {h:02d}:{m:02d}:00"


def _generate_chassis_no(make):
	"""Generate a realistic-looking 17-char VIN/chassis number."""
	prefixes = {
		"Toyota": "JTDKN", "Nissan": "JN1TB", "Hyundai": "KMHDU",
		"Mitsubishi": "JA4MT", "Isuzu": "JAANR", "Suzuki": "JS3TD",
	}
	prefix = prefixes.get(make, "JTDKN")
	mid = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
	suffix = "".join(random.choices(string.digits, k=8))
	return f"{prefix}{mid}{suffix}"


def _get_company():
	companies = frappe.get_all("Company", fields=["name", "default_currency"], limit=1)
	if companies:
		return companies[0].name
	return None


def _get_warehouse(company):
	wh = frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name")
	if not wh:
		wh = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
	return wh


def _ensure_item_group():
	if not frappe.db.exists("Item Group", "Auto Parts"):
		doc = frappe.get_doc({
			"doctype": "Item Group",
			"item_group_name": "Auto Parts",
			"parent_item_group": "All Item Groups",
			"is_group": 0,
		})
		doc.insert(ignore_permissions=True)
	return "Auto Parts"


def _ensure_designation(name):
	if not frappe.db.exists("Designation", name):
		frappe.get_doc({"doctype": "Designation", "designation_name": name}).insert(ignore_permissions=True)


def _ensure_territory():
	if not frappe.db.exists("Territory", "Ethiopia"):
		frappe.get_doc({
			"doctype": "Territory",
			"territory_name": "Ethiopia",
			"parent_territory": "All Territories",
			"is_group": 0,
		}).insert(ignore_permissions=True)


def _ensure_customer_group():
	if not frappe.db.exists("Customer Group", "Commercial"):
		frappe.get_doc({
			"doctype": "Customer Group",
			"customer_group_name": "Commercial",
			"parent_customer_group": "All Customer Groups",
			"is_group": 0,
		}).insert(ignore_permissions=True)


# ── Seed functions ───────────────────────────────────────────────────────────

def _seed_customers(registry):
	_ensure_territory()
	_ensure_customer_group()
	for name, group in CUSTOMERS:
		if frappe.db.exists("Customer", name):
			_reg(registry, "Customer", name)
			continue
		doc = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": name,
			"customer_type": "Company",
			"customer_group": group,
			"territory": "Ethiopia",
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Customer", doc.name)


def _seed_employees(registry, company):
	for first, last, gender, dob, desig in EMPLOYEES:
		_ensure_designation(desig)
		full_name = f"{first} {last}"
		existing = frappe.db.get_value("Employee",
			{"employee_name": full_name, "company": company}, "name")
		if existing:
			_reg(registry, "Employee", existing)
			continue
		doc = frappe.get_doc({
			"doctype": "Employee",
			"first_name": first,
			"last_name": last,
			"employee_name": full_name,
			"gender": gender,
			"date_of_birth": dob,
			"date_of_joining": "2020-01-15",
			"company": company,
			"designation": desig,
			"status": "Active",
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Employee", doc.name)


def _seed_items(registry, company):
	item_group = _ensure_item_group()
	warehouse = _get_warehouse(company)
	for code, name, uom, reorder_level in PARTS:
		if frappe.db.exists("Item", code):
			_reg(registry, "Item", code)
			continue
		doc = frappe.get_doc({
			"doctype": "Item",
			"item_code": code,
			"item_name": name,
			"item_group": item_group,
			"stock_uom": uom,
			"is_stock_item": 1,
			"reorder_levels": [{
				"warehouse": warehouse,
				"warehouse_reorder_level": reorder_level,
				"warehouse_reorder_qty": reorder_level * 2,
			}] if warehouse else [],
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Item", code)


def _seed_vehicles(registry, company=None):
	today = date.today()
	status_dist = (["Active"] * 24) + (["In Maintenance"] * 4) + (["Undergoing Tests"] * 2)

	for plate, make, model, vtype, year, fuel, trans, color in VEHICLES:
		if frappe.db.exists("Vehicle", plate):
			_apply_mock_hardware_mapping(plate)
			_reg(registry, "Vehicle", plate)
			continue

		last_odo = random.randint(10000, 150000)
		odo_at_service = max(0, last_odo - random.randint(500, 5000))
		last_svc = today - timedelta(days=random.randint(30, 120))
		next_svc = today + timedelta(days=random.randint(-30, 90))
		acq_date = today - timedelta(days=random.randint(365, 1825))
		ins_start = today - timedelta(days=random.randint(0, 365))
		ins_end = ins_start + timedelta(days=365)
		variants = VARIANT_MAP.get(make, [""])

		# Specs data
		engine_types = {"Diesel": ["Inline-4 Turbo", "V6 Turbo", "Inline-6"], "Petrol": ["Inline-4", "V6", "V4"], "Electric": ["AC Motor"], "Hybrid": ["Inline-4 + Motor"]}
		capacity_map = {"Inline-4 Turbo": 2800, "V6 Turbo": 4500, "Inline-6": 4200, "Inline-4": 1800, "V6": 3500, "V4": 1600, "AC Motor": 0, "Inline-4 + Motor": 2000}
		cylinder_map = {"Inline-4 Turbo": 4, "V6 Turbo": 6, "Inline-6": 6, "Inline-4": 4, "V6": 6, "V4": 4, "AC Motor": 0, "Inline-4 + Motor": 4}
		drivetrain_options = {"SUV": "4WD", "Truck": "4WD", "Car": "FWD"}
		country_map = {"Toyota": "Japan", "Nissan": "Japan", "Hyundai": "South Korea", "Mitsubishi": "Japan", "Isuzu": "Japan", "Suzuki": "Japan"}
		seating_map = {"SUV": 7, "Truck": 3, "Car": 5}
		fuel_tank_map = {"SUV": "80L", "Truck": "75L", "Car": "50L"}
		fuel_liters_map = {"SUV": 80, "Truck": 75, "Car": 50}
		km_per_liter_map_v = {"SUV": 8, "Truck": 7, "Car": 12}
		acq_cost = random.randint(800000, 6000000)

		eng_type = random.choice(engine_types.get(fuel, ["Inline-4"]))

		vehicle_data = {
			"doctype": "Vehicle",
			"license_plate": plate,
			"make": make,
			"model": model,
			"variant": random.choice(variants),
			"year": year,
			"fuel_type": fuel,
			"transmission": trans,
			"color": color,
			"uom": "Kilometer",
			"custom_vehicle_type": vtype,
			"vehicle_type": vtype,
			"custom_status": random.choice(status_dist),
			"last_odometer": last_odo,
			"vehicle_value": acq_cost,
			"acquisition_cost": acq_cost,
			"acquisition_date": str(acq_date),
			"chassis_no": _generate_chassis_no(make),
			"doors": random.choice([2, 4, 4, 4, 5]),
			"wheels": 4,
			"odometer_at_last_service": odo_at_service,
			"last_service_date": str(last_svc),
			"next_service_due_date": str(next_svc),
			"insurance_company": random.choice(INSURANCE_COMPANIES),
			"policy_no": f"POL-{random.randint(100000, 999999)}",
			"start_date": str(ins_start),
			"end_date": str(ins_end),
			# New spec fields
			"engine_type": eng_type,
			"engine_capacity": capacity_map.get(eng_type, 2000),
			"cylinders": cylinder_map.get(eng_type, 4),
			"drivetrain": drivetrain_options.get(vtype, "FWD"),
			"engine_number": f"ENG-{make[:3].upper()}-{random.randint(100000, 999999)}",
			"country_of_origin": country_map.get(make, "Japan"),
			"fuel_tank_capacity": fuel_tank_map.get(vtype, "50L"),
			"battery_capacity": "75 kWh" if fuel == "Electric" else "",
			"seating_capacity": seating_map.get(vtype, 5),
			"payload_capacity": f"{random.randint(500, 2000)} kg" if vtype == "Truck" else "",
			"towing_capacity": f"{random.randint(1500, 3500)} kg" if vtype in ("SUV", "Truck") else "",
			"gross_vehicle_weight": f"{random.randint(1800, 4500)} kg",
			"ownership_type": "Owned",
			"registration_authority": "Addis Ababa Transport Authority",
			"registration_expiry": str(today + timedelta(days=random.randint(30, 365))),
			"insurance_policy": f"POL-{random.randint(100000, 999999)}",
			"insurance_expiry": str(ins_end),
			"depreciation_method": random.choice(["Straight Line", "Written Down Value"]),
			"depreciation_months": random.choice([60, 84, 120]),
			# Fuel quota fields
			"custom_fuel_capacity_liters": fuel_liters_map.get(vtype, 50),
			"custom_km_per_liter": km_per_liter_map_v.get(vtype, 10),
		}
		vehicle_data.update(_get_mock_hardware_vehicle_fields(plate))
		doc = frappe.get_doc(vehicle_data)
		if company:
			doc.company = company
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle", plate)


def _get_mock_hardware_vehicle_fields(plate):
	if plate != MOCK_HARDWARE_DEVICE["vehicle_plate"]:
		return {}

	fields = {}
	if frappe.db.has_column("Vehicle", "custom_telematics_imei"):
		fields["custom_telematics_imei"] = MOCK_HARDWARE_DEVICE["imei"]
	if frappe.db.has_column("Vehicle", "custom_status"):
		fields["custom_status"] = "Active"
	if frappe.db.has_column("Vehicle", "custom_fuel_capacity_liters"):
		fields["custom_fuel_capacity_liters"] = 80
	return fields


def _apply_mock_hardware_mapping(vehicle_name):
	if vehicle_name != MOCK_HARDWARE_DEVICE["vehicle_plate"]:
		return
	if frappe.db.has_column("Vehicle", "custom_telematics_imei"):
		for duplicate in frappe.get_all(
			"Vehicle",
			filters={"custom_telematics_imei": MOCK_HARDWARE_DEVICE["imei"], "name": ["!=", vehicle_name]},
			pluck="name",
		):
			frappe.db.set_value("Vehicle", duplicate, "custom_telematics_imei", None, update_modified=False)
	for fieldname, value in _get_mock_hardware_vehicle_fields(vehicle_name).items():
		frappe.db.set_value("Vehicle", vehicle_name, fieldname, value, update_modified=False)


@frappe.whitelist()
def ensure_mock_hardware_demo_vehicle():
	"""Create/update the one demo vehicle mapped to the provider mock hardware IMEI."""
	plate = MOCK_HARDWARE_DEVICE["vehicle_plate"]
	if frappe.db.exists("Vehicle", plate):
		_apply_mock_hardware_mapping(plate)
		frappe.db.commit()
		return {"vehicle": plate, "created": False, "imei": MOCK_HARDWARE_DEVICE["imei"]}

	vehicle_data = {
		"doctype": "Vehicle",
		"license_plate": plate,
		"make": "Toyota",
		"model": "Land Cruiser",
		"variant": "VX",
		"year": 2022,
		"fuel_type": "Diesel",
		"transmission": "Automatic",
		"color": "White",
		"uom": "Kilometer",
		"custom_vehicle_type": "SUV",
		"vehicle_type": "SUV",
		"custom_status": "Active",
		"last_odometer": 0,
		"fuel_tank_capacity": "80L",
		"custom_fuel_capacity_liters": 80,
		"custom_km_per_liter": 8,
		"chassis_no": _generate_chassis_no("Toyota"),
		"engine_type": "V6 Turbo",
		"engine_capacity": 4500,
		"cylinders": 6,
		"drivetrain": "4WD",
		"engine_number": "ENG-TOY-MOCK",
		"country_of_origin": "Japan",
		"seating_capacity": 7,
		"ownership_type": "Owned",
		"registration_authority": "Addis Ababa Transport Authority",
	}
	vehicle_data.update(_get_mock_hardware_vehicle_fields(plate))
	doc = frappe.get_doc(vehicle_data)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"vehicle": doc.name, "created": True, "imei": MOCK_HARDWARE_DEVICE["imei"]}


def _seed_vehicle_assignments(registry):
	"""Assign custodians and drivers to vehicles with historical data."""
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	if not vehicles or not employees:
		return

	today = date.today()

	for i, v_name in enumerate(vehicles):
		custodian = employees[i % len(employees)]
		emp_name = frappe.db.get_value("Employee", custodian, "employee_name")

		v_doc = frappe.get_doc("Vehicle", v_name)
		v_doc.custom_custodian = custodian
		v_doc.custom_custodian_name = emp_name

		# Add 1-2 historical (removed) driver entries for history
		driver_pool = list(employees)
		random.shuffle(driver_pool)
		history_count = random.choice([0, 1, 1, 2])
		for h in range(history_count):
			if h >= len(driver_pool):
				break
			hist_emp = driver_pool[h]
			hist_emp_name = frappe.db.get_value("Employee", hist_emp, "employee_name")
			assigned = today - timedelta(days=random.randint(200, 600))
			ended = assigned + timedelta(days=random.randint(30, 180))
			v_doc.append("custom_drivers", {
				"employee": hist_emp,
				"employee_name": hist_emp_name,
				"assigned_date": str(assigned),
				"assigned_by": custodian,
				"status": "Removed",
				"ended_date": str(ended),
				"ended_by": custodian,
				"removal_reason": random.choice([
					"Replaced by new driver assignment",
					"Driver transferred to another department",
					"Vehicle reassigned",
					"Driver left the organization",
				]),
			})

		# Add exactly one active driver (skip those used in history)
		remaining = driver_pool[history_count:]
		if remaining:
			active_emp = remaining[0]
			active_emp_name = frappe.db.get_value("Employee", active_emp, "employee_name")
			v_doc.append("custom_drivers", {
				"employee": active_emp,
				"employee_name": active_emp_name,
				"assigned_date": str(today - timedelta(days=random.randint(5, 120))),
				"assigned_by": custodian,
				"status": "Active",
			})

		v_doc.save(ignore_permissions=True)


def _ensure_operation(name):
	if not frappe.db.exists("Operation", name):
		frappe.get_doc({"doctype": "Operation", "name": name}).insert(ignore_permissions=True)
	return name


def _seed_service_templates(registry):
	# Collect all unique operations and ensure they exist
	all_ops = set()
	for _, operations, _ in SERVICE_TEMPLATES:
		for op_name, _ in operations:
			all_ops.add(op_name)
	for op in all_ops:
		try:
			_ensure_operation(op)
			_reg(registry, "Operation", op)
		except Exception:
			pass

	for title, operations, part_codes in SERVICE_TEMPLATES:
		if frappe.db.exists("Service Template", title):
			_reg(registry, "Service Template", title)
			continue
		doc = frappe.get_doc({
			"doctype": "Service Template",
			"template_name": title,
		})
		for op_name, minutes in operations:
			doc.append("default_operations", {
				"operation_name": op_name,
				"planned_minutes": minutes,
			})
		for pc in part_codes:
			if frappe.db.exists("Item", pc):
				it = frappe.get_doc("Item", pc)
				doc.append("default_parts", {
					"item_code": pc,
					"item_name": it.item_name,
					"uom": it.stock_uom,
					"qty_planned": random.choice([1, 1, 2, 2, 4]),
					"is_billable": 1,
				})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Service Template", doc.name)


def _seed_inspection_templates(registry):
	for title, category, items in INSPECTION_TEMPLATES:
		existing = frappe.db.get_value("Inspection Form Template", {"title": title}, "name")
		if existing:
			_reg(registry, "Inspection Form Template", existing)
			continue
		doc = frappe.get_doc({
			"doctype": "Inspection Form Template",
			"title": title,
			"category": category,
			"status": "Active",
			"description": f"Standard {title.lower()} template for fleet vehicles",
		})
		for label, itype, section, required, sev in items:
			row = {
				"item_label": label,
				"item_type": itype,
				"section_name": section,
				"is_required": 1 if required else 0,
				"fail_triggers_severity": sev,
			}
			if itype == "Numeric":
				row["numeric_min"] = 0
				row["numeric_max"] = 100
			doc.append("items", row)
		doc.insert(ignore_permissions=True)
		_reg(registry, "Inspection Form Template", doc.name)


def _seed_repair_orders(registry):
	vehicles = registry.get("Vehicle", [])
	customers = registry.get("Customer", [])
	parts = registry.get("Item", [])
	if not vehicles or not customers:
		return

	statuses_dist = (
		[("Draft", 180, 30)] * 10
		+ [("Scheduled", 90, 7)] * 8
		+ [("In Progress", 60, 1)] * 12
		+ [("Awaiting Parts", 45, 1)] * 5
		+ [("On Hold", 60, 5)] * 3
		+ [("Ready for Handover", 14, 0)] * 5
		+ [("Delivered", 180, 14)] * 12
		+ [("Closed", 180, 30)] * 5
	)

	for i, (status, days_start, days_end) in enumerate(statuses_dist):
		vehicle = random.choice(vehicles)
		customer = random.choice(customers)
		creation_date = _random_date(days_start, days_end)

		doc = frappe.get_doc({
			"doctype": "Repair Order",
			"naming_series": "RO-.YYYY.-.#####",
			"status": status,
			"customer": customer,
			"vehicle": vehicle,
			"problem_summary": random.choice(PROBLEM_SUMMARIES),
			"priority": random.choice(["Low", "Normal", "Normal", "High", "Urgent"]),
			"creation": f"{creation_date} 08:00:00",
		})

		# Add 1-3 parts
		num_parts = random.randint(1, min(3, len(parts)))
		selected_parts = random.sample(parts, num_parts)
		for pc in selected_parts:
			if frappe.db.exists("Item", pc):
				it = frappe.get_doc("Item", pc)
				doc.append("parts_plan", {
					"item_code": pc,
					"item_name": it.item_name,
					"uom": it.stock_uom,
					"qty_planned": random.choice([1, 1, 2, 2, 3, 4]),
					"is_billable": random.choice([1, 1, 1, 0]),
				})

		# Set cost fields
		parts_cost = random.randint(500, 15000)
		labor_cost = random.randint(500, 10000)
		doc.parts_cost = parts_cost
		doc.labor_cost = labor_cost
		doc.total_job_cost = parts_cost + labor_cost

		doc.insert(ignore_permissions=True)

		# Override creation date for proper date distribution
		frappe.db.set_value("Repair Order", doc.name, "creation",
			f"{creation_date} {random.randint(7,17):02d}:{random.randint(0,59):02d}:00",
			update_modified=False)

		_reg(registry, "Repair Order", doc.name)


def _seed_expenses(registry):
	vehicles = registry.get("Vehicle", [])
	if not vehicles:
		return

	categories = ["Fuel", "Fuel", "Fuel", "Parts", "Parts", "Labor",
		"External Service", "Insurance", "Taxes", "Other"]
	payment_statuses = ["Paid", "Paid", "Paid", "Unpaid", "Partially Paid"]

	desc_map = {
		"Fuel": ["Diesel refill at Total Station", "Monthly fuel allowance", "Fuel top-up at NOC station", "Long-distance trip fuel"],
		"Parts": ["Replaced brake pads", "New battery installed", "Spare tire purchase", "Wiper blade replacement"],
		"Labor": ["Engine diagnostic service", "Routine maintenance labor", "Brake system overhaul labor", "AC repair labor"],
		"External Service": ["Windshield replacement at dealer", "Body panel repair", "Paint touch-up service", "Wheel alignment"],
		"Insurance": ["Annual comprehensive insurance renewal", "Third-party liability insurance", "Insurance premium payment"],
		"Taxes": ["Annual vehicle registration tax", "Road fund levy", "Emission test fee"],
		"Other": ["Car wash subscription", "Parking permit renewal", "Towing service charge"],
	}

	for i in range(100):
		vehicle = random.choice(vehicles)
		cat = random.choice(categories)
		if cat == "Fuel":
			amount = random.randint(500, 5000)
		elif cat in ("Insurance", "Taxes"):
			amount = random.randint(5000, 25000)
		else:
			amount = random.randint(1000, 15000)

		doc = frappe.get_doc({
			"doctype": "Vehicle Expense",
			"naming_series": "VE-.YYYY.-.#####",
			"title": f"{cat} - {vehicle}",
			"expense_date": _random_date(180, 0),
			"category": cat,
			"amount": amount,
			"vehicle": vehicle,
			"payment_status": random.choice(payment_statuses),
			"description": random.choice(desc_map.get(cat, ["General expense"])),
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle Expense", doc.name)


def _seed_inspections(registry):
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	templates = registry.get("Inspection Form Template", [])
	if not vehicles:
		return

	types = ["Pre-Trip", "Post-Trip", "Periodic", "Ad-Hoc", "Regulatory"]
	results_dist = (["Pass"] * 25) + (["Fail"] * 8) + (["Conditional"] * 7)

	for i in range(40):
		vehicle = random.choice(vehicles)
		result = random.choice(results_dist)

		if result == "Pass":
			score = random.randint(80, 100)
		elif result == "Conditional":
			score = random.randint(50, 79)
		else:
			score = random.randint(10, 49)

		insp_date = _random_datetime(180, 0)
		doc_data = {
			"doctype": "Vehicle Inspection",
			"naming_series": "VI-.YYYY.-.#####",
			"title": f"Inspection - {vehicle}",
			"vehicle": vehicle,
			"inspection_date": insp_date,
			"inspection_type": random.choice(types),
			"result": result,
			"score": score,
			"status": "Completed",
		}
		if result in ("Fail", "Conditional"):
			doc_data["failures_count"] = random.randint(1, 4)
			doc_data["follow_up_required"] = 1
			doc_data["follow_up_due_date"] = str(
				getdate(insp_date.split(" ")[0]) + timedelta(days=14))
		if employees:
			doc_data["inspector"] = random.choice(employees)
		if templates:
			doc_data["form_template"] = random.choice(templates)

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle Inspection", doc.name)


def _seed_schedules(registry):
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	templates = registry.get("Inspection Form Template", [])
	if not vehicles:
		return

	frequencies = ["Weekly", "Monthly", "Quarterly", "Semi-Annually", "Annually"]
	today = date.today()

	for i in range(15):
		vehicle = random.choice(vehicles)
		freq = random.choice(frequencies)
		# Some overdue, some upcoming
		if i < 8:
			next_due = str(today - timedelta(days=random.randint(1, 60)))
		else:
			next_due = str(today + timedelta(days=random.randint(1, 90)))

		doc_data = {
			"doctype": "Inspection Schedule",
			"naming_series": "IS-.YYYY.-.#####",
			"title": f"{freq} inspection - {vehicle}",
			"vehicle": vehicle,
			"frequency": freq,
			"status": "Active",
			"scheduled_date": _random_date(180, 90),
			"next_due": next_due,
		}
		if employees:
			doc_data["assigned_to"] = random.choice(employees)
		if templates:
			doc_data["form_template"] = random.choice(templates)

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		_reg(registry, "Inspection Schedule", doc.name)


def _seed_failures(registry):
	vehicles = registry.get("Vehicle", [])
	inspections = registry.get("Vehicle Inspection", [])
	if not vehicles:
		return

	statuses = ["Open", "Open", "Converted", "Resolved", "Resolved", "Ignored"]
	severities = ["Low", "Medium", "Medium", "High", "High", "Critical"]
	reasons = [
		"Worn beyond safe limit", "Below minimum threshold",
		"Cracked/damaged", "Not functioning", "Leaking",
		"Corroded", "Misaligned", "Expired", "Missing",
	]

	for i in range(25):
		vehicle = random.choice(vehicles)
		item = random.choice(FAILURE_ITEMS)
		status = random.choice(statuses)
		reported = _random_date(180, 5)

		doc_data = {
			"doctype": "Inspection Item Failure",
			"naming_series": "IF-.YYYY.-.#####",
			"item_name": item,
			"vehicle": vehicle,
			"severity": random.choice(severities),
			"status": status,
			"failure_reason": random.choice(reasons),
			"reported_date": reported,
			"is_recurring": 1 if random.random() < 0.25 else 0,
		}
		if inspections:
			doc_data["inspection"] = random.choice(inspections)
		if status == "Resolved":
			doc_data["resolved_date"] = _random_date(
				max(0, (date.today() - getdate(reported)).days), 0)
			doc_data["resolution_type"] = random.choice(["Work Order", "Quick Fix", "Deferred"])

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		_reg(registry, "Inspection Item Failure", doc.name)


def _seed_faults(registry):
	vehicles = registry.get("Vehicle", [])
	if not vehicles:
		return

	statuses = ["Open", "Open", "In Progress", "Resolved", "Resolved", "Closed"]
	severities = ["Low", "Medium", "Medium", "High", "High", "Critical"]
	detection_types = ["OBD Scan", "Manual Inspection", "Driver Report", "Sensor Alert"]

	for i in range(20):
		vehicle = random.choice(vehicles)
		code, system, desc = random.choice(FAULT_CODES)
		status = random.choice(statuses)
		reported = _random_date(180, 5)

		doc_data = {
			"doctype": "Vehicle Fault",
			"naming_series": "VF-.YYYY.-.#####",
			"title": f"{code} - {desc[:40]}",
			"vehicle": vehicle,
			"fault_code": code,
			"component_system": system,
			"severity": random.choice(severities),
			"status": status,
			"detection_type": random.choice(detection_types),
			"confirmed": random.choice(["Confirmed", "Confirmed", "Unconfirmed"]),
			"reported_date": reported,
			"description": desc,
		}
		if status in ("Resolved", "Closed"):
			doc_data["resolved_date"] = _random_date(
				max(0, (date.today() - getdate(reported)).days), 0)

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle Fault", doc.name)


def _seed_recalls(registry):
	recalls_data = [
		("Airbag Inflator Replacement", "Toyota", "Land Cruiser, Hilux", "2017-2020", "Safety", "High"),
		("Fuel Pump Defect", "Nissan", "Patrol, X-Trail", "2018-2020", "Mechanical", "Critical"),
		("Brake Caliper Bolt", "Hyundai", "Tucson, Santa Fe", "2019-2021", "Safety", "High"),
		("ECU Software Update", "Mitsubishi", "L200, Pajero", "2018-2020", "Software", "Medium"),
		("Seat Belt Pretensioner", "Isuzu", "D-Max, NPR", "2019-2021", "Safety", "Critical"),
	]

	for title, mfr, models, years, itype, priority in recalls_data:
		doc = frappe.get_doc({
			"doctype": "Vehicle Recall",
			"naming_series": "VR-.YYYY.-.#####",
			"title": title,
			"manufacturer": mfr,
			"affected_models": models,
			"affected_years": years,
			"issue_type": itype,
			"priority": priority,
			"status": random.choice(["Active", "Active", "In Progress", "Completed"]),
			"recall_start_date": _random_date(365, 60),
			"description": f"Manufacturer recall: {title} affecting {models} ({years})",
			"vehicles_affected": random.randint(5, 20),
			"vehicles_completed": random.randint(0, 5),
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle Recall", doc.name)


def _seed_issues(registry):
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	if not vehicles:
		return

	statuses = ["Open", "Open", "Open", "Replied", "Resolved", "Resolved", "Closed"]
	severities = ["Low", "Medium", "Medium", "High", "High", "Critical"]
	categories = ["Mechanical", "Electrical", "Body/Paint", "Interior", "Safety", "Compliance"]
	sources = ["Inspection", "Driver Report", "Mechanic", "Customer", "Sensor"]
	workflow_states = [
		"Draft", "Pending Custodian Approval", "Pending Custodian Approval",
		"Submitted", "Submitted", "Submitted", "Submitted",
		"Rejected", "Work Order Created",
	]

	for i in range(min(25, len(ISSUE_SUBJECTS))):
		vehicle = random.choice(vehicles)
		status = random.choice(statuses)
		creation_date = _random_date(180, 5)
		wf_state = random.choice(workflow_states)

		# Pick an employee as the requester
		requester = random.choice(employees) if employees else None

		doc_data = {
			"doctype": "Issue",
			"subject": ISSUE_SUBJECTS[i],
			"status": status,
			"priority": random.choice(["Low", "Medium", "Medium", "High"]),
			"custom_vehicle": vehicle,
			"custom_severity": random.choice(severities),
			"custom_category": random.choice(categories),
			"custom_source": random.choice(sources),
			"custom_workflow_state": wf_state,
		}

		if requester:
			doc_data["custom_requested_by_employee"] = requester

		# Add approval/rejection data for appropriate states
		if wf_state == "Submitted" and employees:
			approver = random.choice(employees)
			doc_data["custom_approved_by"] = approver
			doc_data["custom_approved_on"] = _random_datetime(90, 5)
		elif wf_state == "Rejected" and employees:
			rejector = random.choice(employees)
			doc_data["custom_rejected_by"] = rejector
			doc_data["custom_rejected_on"] = _random_datetime(90, 5)
			doc_data["custom_rejection_reason"] = random.choice([
				"Issue is not vehicle-related",
				"Duplicate of existing issue",
				"Insufficient information provided",
				"Not a priority at this time",
			])

		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)

		# Override creation and set resolution dates
		frappe.db.set_value("Issue", doc.name, "creation",
			f"{creation_date} {random.randint(7,17):02d}:{random.randint(0,59):02d}:00",
			update_modified=False)

		if status in ("Resolved", "Closed"):
			days_since = (date.today() - getdate(creation_date)).days
			resolve_date = _random_date(max(0, days_since), 0)
			frappe.db.set_value("Issue", doc.name,
				"sla_resolution_date", f"{resolve_date} 16:00:00",
				update_modified=False)

		if status != "Open":
			respond_date = str(getdate(creation_date) + timedelta(days=random.randint(0, 3)))
			frappe.db.set_value("Issue", doc.name, "first_responded_on",
				f"{respond_date} 10:00:00", update_modified=False)

		_reg(registry, "Issue", doc.name)


def _seed_fuel_quotas_and_records(registry):
	"""Seed fuel quotas and refueling records for demo vehicles."""
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	if not vehicles:
		return

	today = date.today()
	current_month = today.strftime("%Y-%m")
	prev_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

	fuel_stations = [
		"Total Station - Bole", "NOC Station - Megenagna", "Nile Petroleum - Sarbet",
		"OiLibya - CMC", "YBP Station - Arat Kilo", "Total Station - Mexico",
		"Shell Station - Gotera", "Kobil Station - Piassa",
	]

	fuel_tank_liters = {"SUV": 80, "Truck": 75, "Car": 50}
	km_per_liter_map = {"SUV": 8, "Truck": 7, "Car": 12}

	for v_name in vehicles[:20]:  # Limit to 20 vehicles
		v = frappe.get_doc("Vehicle", v_name)
		vtype = v.custom_vehicle_type or v.vehicle_type or "Car"
		capacity = fuel_tank_liters.get(vtype, 50)
		kpl = km_per_liter_map.get(vtype, 10)
		monthly_quota = capacity * 2  # 2 full tanks per month

		# Create quota for current and previous month
		for month in [prev_month, current_month]:
			quota_name = f"FQ-{v_name}-{month}"
			if frappe.db.exists("Vehicle Fuel Quota", quota_name):
				_reg(registry, "Vehicle Fuel Quota", quota_name)
				continue

			consumed = round(random.uniform(monthly_quota * 0.3, monthly_quota * 1.1), 1) if month == prev_month else 0
			remaining = round(monthly_quota - consumed, 1)
			q_status = "Exhausted" if remaining <= 0 else ("Closed" if month == prev_month else "Active")

			q_doc = frappe.get_doc({
				"doctype": "Vehicle Fuel Quota",
				"name": quota_name,
				"vehicle": v_name,
				"quota_month": month,
				"fuel_capacity_liters": capacity,
				"km_per_liter": kpl,
				"quota_liters": monthly_quota,
				"consumed_liters": max(0, consumed),
				"remaining_liters": max(0, remaining),
				"status": q_status,
			})
			q_doc.insert(ignore_permissions=True)
			_reg(registry, "Vehicle Fuel Quota", q_doc.name)

		# Create 3-6 refueling records per vehicle
		record_count = random.randint(3, 6)
		current_quota_name = f"FQ-{v_name}-{current_month}"
		prev_quota_name = f"FQ-{v_name}-{prev_month}"
		running_consumed = 0

		for r in range(record_count):
			liters = round(random.uniform(20, capacity * 0.7), 1)
			cost_per_liter = round(random.uniform(55, 72), 2)
			is_current = r >= record_count // 2
			refuel_date = _random_date(30 if is_current else 60, 0 if is_current else 30)
			quota_link = current_quota_name if is_current else prev_quota_name

			running_consumed += liters
			is_over = running_consumed > monthly_quota

			# Determine approval status
			if is_over and random.random() < 0.5:
				approval = random.choice([
					"Pending Dept Head Approval",
					"Pending Depot Manager Approval",
					"Dept Head Approved",
				])
			elif is_over:
				approval = random.choice(["Approved", "Rejected"])
			else:
				approval = "Approved"

			rec_data = {
				"doctype": "Vehicle Refueling Record",
				"vehicle": v_name,
				"refuel_date": refuel_date,
				"liters": liters,
				"cost_per_liter": cost_per_liter,
				"total_cost": round(liters * cost_per_liter, 2),
				"fuel_station": random.choice(fuel_stations),
				"approval_status": approval,
				"is_over_quota": 1 if is_over else 0,
				"over_quota_liters": round(running_consumed - monthly_quota, 1) if is_over else 0,
				"quota_link": quota_link if frappe.db.exists("Vehicle Fuel Quota", quota_link) else None,
				"consumed_before": round(max(0, running_consumed - liters), 1),
				"consumed_after": round(running_consumed, 1),
				"odometer_reading": (v.last_odometer or 50000) + random.randint(100, 500),
			}

			if employees:
				rec_data["driver"] = random.choice(employees)

			# Add approval details for approved over-quota records
			if approval == "Dept Head Approved" and employees:
				rec_data["dept_head_approved_by"] = random.choice(employees)
				rec_data["dept_head_approved_on"] = _random_datetime(30, 0)
			elif approval == "Rejected":
				rec_data["rejection_reason"] = random.choice([
					"Quota exceeded without justification",
					"Trip not authorized",
					"Previous refueling not reconciled",
				])

			rec_doc = frappe.get_doc(rec_data)
			rec_doc.insert(ignore_permissions=True)
			_reg(registry, "Vehicle Refueling Record", rec_doc.name)


def _seed_vehicle_telemetry(registry):
	"""Seed Vehicle Location, Fuel Level, and Sensor Data for demo vehicles."""
	vehicles = registry.get("Vehicle", [])
	if not vehicles:
		return

	# Addis Ababa center coordinates for GPS simulation
	base_lat = 9.0192
	base_lng = 38.7525

	for vehicle_name in vehicles[:15]:  # Limit to first 15 vehicles
		# Generate location history (last 30 days, ~3 points/day)
		for day_offset in range(30):
			for hour in [8, 13, 17]:
				ts = _random_datetime(day_offset, day_offset)
				lat = base_lat + random.uniform(-0.05, 0.05)
				lng = base_lng + random.uniform(-0.05, 0.05)
				speed = random.uniform(0, 80)
				direction = random.uniform(0, 360)

				loc = frappe.get_doc({
					"doctype": "Vehicle Location",
					"vehicle": vehicle_name,
					"timestamp": ts,
					"latitude": round(lat, 6),
					"longitude": round(lng, 6),
					"speed": round(speed, 1),
					"direction": round(direction, 1),
				})
				loc.insert(ignore_permissions=True)
				_reg(registry, "Vehicle Location", loc.name)

		# Generate fuel level data with realistic refueling patterns
		fuel_level = random.uniform(60, 90)
		for day_offset in range(30):
			# Consume fuel throughout the day
			fuel_level -= random.uniform(3, 8)
			if fuel_level < 0:
				fuel_level = 5

			ts = _random_datetime(day_offset, day_offset)
			fl = frappe.get_doc({
				"doctype": "Vehicle Fuel Level",
				"vehicle": vehicle_name,
				"timestamp": ts,
				"fuel_level": round(max(5, fuel_level), 1),
			})
			fl.insert(ignore_permissions=True)
			_reg(registry, "Vehicle Fuel Level", fl.name)

			# Refuel when below 25% (or randomly below 40%)
			if fuel_level < 25 or (fuel_level < 40 and random.random() < 0.3):
				fuel_level = random.uniform(70, 95)
				ts2 = _random_datetime(day_offset, day_offset)
				fl2 = frappe.get_doc({
					"doctype": "Vehicle Fuel Level",
					"vehicle": vehicle_name,
					"timestamp": ts2,
					"fuel_level": round(fuel_level, 1),
				})
				fl2.insert(ignore_permissions=True)
				_reg(registry, "Vehicle Fuel Level", fl2.name)

		# Generate sensor data
		sensor_types = [
			("Engine Temperature", "°C", 75, 105),
			("Battery Voltage", "V", 11.5, 14.5),
			("Oil Pressure", "PSI", 25, 65),
			("Coolant Temperature", "°C", 70, 100),
			("RPM", "rpm", 700, 4500),
		]
		for sensor_type, unit, min_val, max_val in sensor_types:
			for day_offset in range(0, 30, 3):  # Every 3 days
				ts = _random_datetime(day_offset, day_offset)
				value = round(random.uniform(min_val, max_val), 1)
				sd = frappe.get_doc({
					"doctype": "Vehicle Sensor Data",
					"vehicle": vehicle_name,
					"timestamp": ts,
					"sensor_type": sensor_type,
					"value": str(value),
					"unit": unit,
				})
				sd.insert(ignore_permissions=True)
				_reg(registry, "Vehicle Sensor Data", sd.name)


def _seed_vehicle_logs(registry):
	vehicles = registry.get("Vehicle", [])
	employees = registry.get("Employee", [])
	if not vehicles or not employees:
		return

	# Track odometers per vehicle to ensure ascending values
	vehicle_odos = {}
	for v in vehicles:
		last = frappe.db.get_value("Vehicle", v, "last_odometer") or 0
		vehicle_odos[v] = int(last) if last else random.randint(10000, 50000)

	for i in range(80):
		vehicle = random.choice(vehicles)
		last_odo = vehicle_odos[vehicle]
		distance = random.randint(200, 2000)
		odo = last_odo + distance
		vehicle_odos[vehicle] = odo
		fuel = round(random.uniform(20, 80), 1)

		doc = frappe.get_doc({
			"doctype": "Vehicle Log",
			"naming_series": "HR-VLOG-.YYYY.-",
			"license_plate": vehicle,
			"employee": random.choice(employees),
			"date": _random_date(180, 0),
			"last_odometer": last_odo,
			"odometer": odo,
			"fuel_qty": fuel,
			"price": round(fuel * random.uniform(50, 70), 2),
		})
		doc.insert(ignore_permissions=True)
		_reg(registry, "Vehicle Log", doc.name)


def _seed_reminders(registry):
	vehicles = registry.get("Vehicle", [])
	if not vehicles:
		return

	reminder_configs = [
		("Oil Change", "Engine oil and filter replacement due"),
		("Oil Change", "Synthetic oil change service"),
		("Tire Rotation", "Rotate and balance all four tires"),
		("Tire Rotation", "Check tire tread depth and rotate"),
		("Brake Inspection", "Inspect brake pads, rotors, and fluid level"),
		("Brake Inspection", "Front brake pads wearing thin — inspect soon"),
		("General Service", "Scheduled maintenance — 10,000 km service"),
		("General Service", "Annual comprehensive vehicle checkup"),
		("General Service", "Pre-rainy season vehicle inspection"),
		("Filter Replacement", "Replace cabin air filter"),
		("Filter Replacement", "Engine air filter replacement due"),
		("Fluid Change", "Transmission fluid change at 60,000 km"),
		("Fluid Change", "Coolant flush and replacement"),
		("Fluid Change", "Power steering fluid top-up"),
		("Belt/Chain", "Timing belt replacement at 100,000 km"),
		("Belt/Chain", "Serpentine belt showing cracks — replace"),
		("Other", "Windshield wiper blade replacement"),
		("Other", "Battery health check — 3 years old"),
		("Other", "Wheel alignment after pothole damage"),
		("Other", "AC system recharge before summer"),
	]

	today = date.today()
	user = frappe.session.user
	# A future placeholder used to pass validation for past-date reminders
	future_placeholder = f"{today + timedelta(days=30)} 12:00:00"

	for i, (rtype, desc) in enumerate(reminder_configs):
		vehicle = vehicles[i % len(vehicles)]

		# Mix: 5 overdue, 7 due soon (within 14 days), 5 upcoming, 3 already notified
		if i < 5:
			# Overdue: 1–30 days in the past
			days_offset = -random.randint(1, 30)
			notified = 0
		elif i < 12:
			# Due soon: within next 14 days
			days_offset = random.randint(1, 13)
			notified = 0
		elif i < 17:
			# Upcoming: 15–90 days in the future
			days_offset = random.randint(15, 90)
			notified = 0
		else:
			# History: already notified, 10–60 days in the past
			days_offset = -random.randint(10, 60)
			notified = 1

		remind_date = today + timedelta(days=days_offset)
		h = random.randint(7, 17)
		m = random.choice([0, 15, 30, 45])
		target_remind_at = f"{remind_date} {h:02d}:{m:02d}:00"
		is_past = days_offset < 0

		# Frappe Reminder.validate() blocks past dates, so insert with
		# a future date first, then backdate via db_set for past reminders.
		doc = frappe.get_doc({
			"doctype": "Reminder",
			"user": user,
			"remind_at": future_placeholder if is_past else target_remind_at,
			"description": f"[{rtype}] {desc}",
			"reminder_doctype": "Vehicle",
			"reminder_docname": vehicle,
		})
		doc.insert(ignore_permissions=True)

		if is_past:
			frappe.db.set_value("Reminder", doc.name, {
				"remind_at": target_remind_at,
				"notified": notified,
			}, update_modified=False)

		_reg(registry, "Reminder", doc.name)


# ── Main API ─────────────────────────────────────────────────────────────────

@frappe.whitelist()
def seed_demo_data():
	"""Seed complete demo data for the workshop app."""
	existing = _load_registry()
	if existing:
		return {
			"success": False,
			"message": "Demo data already loaded. Clear it first before re-seeding.",
			"summary": {k: len(v) for k, v in existing.items()},
		}

	random.seed(42)
	registry = {}
	company = _get_company()
	if not company:
		frappe.throw("No company found. Please set up a company first.")

	frappe.flags.ignore_permissions = True
	errors = []

	steps = [
		("Customers", lambda: _seed_customers(registry)),
		("Employees", lambda: _seed_employees(registry, company)),
		("Items", lambda: _seed_items(registry, company)),
		("Vehicles", lambda: _seed_vehicles(registry)),
		("Vehicle Assignments", lambda: _seed_vehicle_assignments(registry)),
		("Service Templates", lambda: _seed_service_templates(registry)),
		("Inspection Form Templates", lambda: _seed_inspection_templates(registry)),
		("Repair Orders", lambda: _seed_repair_orders(registry)),
		("Vehicle Expenses", lambda: _seed_expenses(registry)),
		("Vehicle Inspections", lambda: _seed_inspections(registry)),
		("Inspection Schedules", lambda: _seed_schedules(registry)),
		("Inspection Item Failures", lambda: _seed_failures(registry)),
		("Vehicle Faults", lambda: _seed_faults(registry)),
		("Vehicle Recalls", lambda: _seed_recalls(registry)),
		("Issues", lambda: _seed_issues(registry)),
		("Fuel Quotas & Records", lambda: _seed_fuel_quotas_and_records(registry)),
		("Vehicle Logs", lambda: _seed_vehicle_logs(registry)),
		("Vehicle Telemetry", lambda: _seed_vehicle_telemetry(registry)),
		("Reminders", lambda: _seed_reminders(registry)),
	]

	for step_name, fn in steps:
		try:
			fn()
		except Exception as e:
			errors.append(f"{step_name}: {str(e)}")
			frappe.log_error(frappe.get_traceback(), f"Demo Data Seed: {step_name}")

	frappe.flags.ignore_permissions = False
	_save_registry(registry)
	frappe.db.commit()

	summary = {k: len(v) for k, v in registry.items()}
	result = {"success": True, "summary": summary}
	if errors:
		result["errors"] = errors
	return result


@frappe.whitelist()
def clear_demo_data():
	"""Clear all demo data created by the seeder."""
	registry = _load_registry()
	if not registry:
		return {"success": False, "message": "No demo data found to clear."}

	frappe.flags.ignore_permissions = True
	cleared = {}

	# Deletion order: dependents first
	delete_order = [
		"Reminder",
		"Vehicle Location", "Vehicle Fuel Level", "Vehicle Sensor Data",
		"Vehicle Refueling Record", "Vehicle Fuel Quota",
		"Issue", "Vehicle Recall", "Vehicle Fault", "Inspection Item Failure",
		"Vehicle Inspection", "Inspection Schedule",
		"Vehicle Expense", "Vehicle Log",
		"Repair Order",
		"Inspection Form Template", "Service Template", "Operation",
		"Item", "Vehicle", "Employee", "Customer",
	]

	for doctype in delete_order:
		names = registry.get(doctype, [])
		count = 0
		for name in names:
			try:
				if doctype == "Item":
					# Clean up Bin records for demo items
					frappe.db.sql("DELETE FROM tabBin WHERE item_code=%s", name)
				if frappe.db.exists(doctype, name):
					frappe.delete_doc(doctype, name, force=True,
						ignore_permissions=True, delete_permanently=True)
					count += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(),
					f"Demo Data Clear: {doctype}/{name}")
		if count:
			cleared[doctype] = count

	# Clean up Item Group if empty
	if frappe.db.exists("Item Group", "Auto Parts"):
		item_count = frappe.db.count("Item", {"item_group": "Auto Parts"})
		if item_count == 0:
			try:
				frappe.delete_doc("Item Group", "Auto Parts", force=True,
					ignore_permissions=True, delete_permanently=True)
				cleared["Item Group"] = 1
			except Exception:
				pass

	frappe.flags.ignore_permissions = False

	# Remove registry file
	path = _get_registry_path()
	if os.path.exists(path):
		os.remove(path)

	frappe.db.commit()
	return {"success": True, "cleared": cleared}


@frappe.whitelist()
def get_demo_data_status():
	"""Get current demo data status."""
	registry = _load_registry()
	if not registry:
		return {"is_loaded": False, "summary": None}

	# Verify some records still exist
	total = 0
	summary = {}
	for doctype, names in registry.items():
		existing = sum(1 for n in names if frappe.db.exists(doctype, n))
		if existing:
			summary[doctype] = existing
			total += existing

	return {
		"is_loaded": total > 0,
		"summary": summary if total > 0 else None,
		"total_records": total,
	}
