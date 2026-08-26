import frappe
from frappe.utils import nowdate, now_datetime, cstr, getdate


SETTINGS_CATEGORIES = [
	{"id": "organization", "title": "Organization & Locations", "description": "Company profile, currency, fiscal year", "icon": "Building2"},
	{"id": "vehicles", "title": "Vehicles Configuration", "description": "Vehicle types, service reminders, thresholds", "icon": "Car"},
	{"id": "work_orders", "title": "Work Orders & Workflow", "description": "Statuses, SLA targets, numbering rules", "icon": "ClipboardList"},
	{"id": "inspections", "title": "Inspections", "description": "Inspection types, schedules, form templates", "icon": "ClipboardCheck"},
	{"id": "issues", "title": "Issues & Faults", "description": "Severity scales, categories, fault codes", "icon": "AlertTriangle"},
	{"id": "expenses", "title": "Expenses & Finance", "description": "Expense categories, receipt policies", "icon": "Receipt"},
	{"id": "inventory", "title": "Inventory", "description": "Warehouses, reorder defaults, stock policies", "icon": "Package"},
	{"id": "customers", "title": "Customers & CRM", "description": "Customer groups, territories, templates", "icon": "Users"},
	{"id": "users", "title": "Users, Roles & Permissions", "description": "Roles, permission sets, access control", "icon": "Shield"},
	{"id": "notifications", "title": "Notifications", "description": "Channels, rules, recipient mapping", "icon": "Bell"},
	{"id": "integrations", "title": "Integrations", "description": "Email, APIs, webhooks, external modules", "icon": "Plug"},
	{"id": "data_audit", "title": "Data & Audit", "description": "Import tools, audit logs, activity history", "icon": "Database"},
	{"id": "branding", "title": "Branding & Documents", "description": "Logo, print formats, PDF and email templates", "icon": "Palette"},
	{"id": "maintenance", "title": "System Maintenance", "description": "Scheduled jobs, cache, health checks", "icon": "Wrench"},
]


@frappe.whitelist()
def get_settings_home():
	"""Get settings home page data."""
	# System info
	system_info = {
		"frappe_version": frappe.__version__,
		"site_name": frappe.local.site,
	}
	try:
		import erpnext
		system_info["erpnext_version"] = erpnext.__version__
	except Exception:
		system_info["erpnext_version"] = "N/A"

	# Scheduled jobs
	scheduled_jobs_count = 0
	try:
		scheduled_jobs_count = frappe.db.count("Scheduled Job Type", {"stopped": 0})
	except Exception:
		pass

	# Integrations status
	integrations = []
	try:
		email_accounts = frappe.get_all("Email Account",
			filters={"enabled": 1},
			fields=["name", "email_id", "email_account_name"],
			limit=5)
		for ea in email_accounts:
			integrations.append({"name": ea.email_account_name or ea.name, "type": "Email", "status": "Connected"})
	except Exception:
		pass
	try:
		hardware_configs = frappe.get_all("Hardware Test Configuration",
			filters={"enabled": 1},
			fields=["name", "configuration_name", "last_status"],
			limit=5)
		for config in hardware_configs:
			integrations.append({
				"name": config.configuration_name or config.name,
				"type": "Mock Hardware",
				"status": config.last_status or "Configured",
			})
	except Exception:
		pass

	return {
		"system_info": system_info,
		"scheduled_jobs_count": scheduled_jobs_count,
		"integrations": integrations,
		"categories": SETTINGS_CATEGORIES,
	}


@frappe.whitelist()
def get_settings_category(category):
	"""Get settings data for a specific category."""
	handlers = {
		"organization": _cat_organization,
		"vehicles": _cat_vehicles,
		"work_orders": _cat_work_orders,
		"inspections": _cat_inspections,
		"issues": _cat_issues,
		"expenses": _cat_expenses,
		"inventory": _cat_inventory,
		"customers": _cat_customers,
		"users": _cat_users,
		"notifications": _cat_notifications,
		"integrations": _cat_integrations,
		"data_audit": _cat_data_audit,
		"branding": _cat_branding,
		"maintenance": _cat_maintenance,
	}

	handler = handlers.get(category)
	if not handler:
		frappe.throw(f"Unknown settings category: {category}")

	result = handler()
	result["category"] = category
	return result


@frappe.whitelist()
def update_setting(category, key, value):
	"""Update a specific setting (limited safe settings)."""
	ALLOWED = {
		"vehicles": {
			"doctype": "Fleet Replacement Settings",
			"fields": None,  # any field
		},
		"organization": {
			"defaults": ["company", "default_currency"],
		},
		"inventory": {
			"doctype": "Stock Settings",
			"fields": ["allow_negative_stock", "auto_indent", "default_warehouse"],
		},
		"branding": {
			"defaults": ["letter_head"],
		},
		"notifications": {
			"defaults": ["notifications_enabled"],
		},
	}

	cat_config = ALLOWED.get(category)
	if not cat_config:
		frappe.throw("Setting update not supported for this category")

	# Handle global defaults
	if "defaults" in cat_config:
		if key not in cat_config["defaults"]:
			frappe.throw(f"Setting '{key}' is not editable in {category}")
		frappe.defaults.set_global_default(key, value)
		return {"success": True, "value": value,
				"modified_by": frappe.session.user, "modified": str(now_datetime())}

	# Handle DocType-based settings
	doctype = cat_config.get("doctype")
	allowed_fields = cat_config.get("fields")
	if doctype:
		doc = frappe.get_doc(doctype)
		if allowed_fields and key not in allowed_fields:
			frappe.throw(f"Setting '{key}' is not editable")
		if not hasattr(doc, key):
			frappe.throw(f"Setting '{key}' does not exist")
		doc.set(key, value)
		doc.save()
		return {"success": True, "value": doc.get(key),
				"modified_by": doc.modified_by, "modified": str(doc.modified)}

	frappe.throw("Setting update not supported for this category/key")


@frappe.whitelist()
def reset_setting(category, key):
	"""Reset a setting to its default value. Requires System Manager role."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Only System Managers can reset settings")

	RESET_DEFAULTS = {
		"organization": {"company": "", "default_currency": "ETB"},
		"inventory": {"allow_negative_stock": 0, "auto_indent": 0, "default_warehouse": ""},
		"branding": {"letter_head": ""},
	}

	cat_defaults = RESET_DEFAULTS.get(category)
	if not cat_defaults or key not in cat_defaults:
		frappe.throw(f"No default value defined for {category}/{key}")

	default_val = cat_defaults[key]
	return update_setting(category, key, default_val)


@frappe.whitelist()
def get_audit_log(doctype=None, name=None, limit=20):
	"""Get audit log entries."""
	filters = {}
	if doctype:
		filters["ref_doctype"] = doctype
	if name:
		filters["ref_name"] = name

	versions = frappe.get_all("Version",
		filters=filters,
		fields=["name", "ref_doctype", "ref_name", "owner", "creation", "data"],
		order_by="creation desc",
		limit=int(limit))

	return {"entries": versions, "total": len(versions)}


@frappe.whitelist()
def get_system_health():
	"""Get system health status."""
	health = {
		"scheduler_status": "Unknown",
		"background_jobs": {"pending": 0, "running": 0, "failed": 0},
		"cache_status": "Unknown",
		"database_status": "Unknown",
	}

	# Scheduler
	try:
		from frappe.utils.scheduler import is_scheduler_inactive
		health["scheduler_status"] = "Inactive" if is_scheduler_inactive() else "Active"
	except Exception:
		pass

	# Background jobs
	try:
		from frappe.utils.background_jobs import get_queue_list
		for q_name in ["default", "short", "long"]:
			try:
				from frappe.utils.background_jobs import get_queue
				q = get_queue(q_name)
				health["background_jobs"]["pending"] += q.count
			except Exception:
				pass
	except Exception:
		pass

	# Cache
	try:
		frappe.cache.ping()
		health["cache_status"] = "Connected"
	except Exception:
		health["cache_status"] = "Disconnected"

	# Database
	try:
		frappe.db.sql("SELECT 1")
		health["database_status"] = "Connected"
	except Exception:
		health["database_status"] = "Disconnected"

	return health


# ── Category handlers ────────────────────────────────────────────────────────

def _cat_organization():
	companies = frappe.get_all("Company",
		fields=["name", "company_name", "default_currency", "country", "creation", "modified", "modified_by"],
		limit=10)
	return {
		"settings": {
			"companies": companies,
			"default_company": frappe.defaults.get_global_default("company") or "",
			"default_currency": frappe.defaults.get_global_default("default_currency") or "",
		},
		"last_modified_by": companies[0].modified_by if companies else None,
		"last_modified_on": str(companies[0].modified) if companies else None,
	}


def _cat_vehicles():
	# Vehicle types
	vehicle_types = frappe.db.sql("""
		SELECT DISTINCT custom_vehicle_type as vehicle_type, COUNT(*) as count
		FROM `tabVehicle` WHERE custom_vehicle_type IS NOT NULL AND custom_vehicle_type != ''
		GROUP BY custom_vehicle_type ORDER BY count DESC
	""", as_dict=True)

	# Fleet Replacement Settings
	frs = {}
	frs_modified_by = None
	frs_modified = None
	try:
		doc = frappe.get_doc("Fleet Replacement Settings")
		frs = doc.as_dict()
		frs_modified_by = doc.modified_by
		frs_modified = str(doc.modified)
	except Exception:
		pass

	return {
		"settings": {
			"vehicle_types": vehicle_types,
			"fleet_replacement_settings": frs,
		},
		"last_modified_by": frs_modified_by,
		"last_modified_on": frs_modified,
	}


def _cat_work_orders():
	statuses = ["Draft", "Scheduled", "In Progress", "Awaiting Parts",
				"Ready for Handover", "Delivered", "Closed", "On Hold", "Cancelled"]

	# Auto-numbering
	naming_series = ""
	try:
		meta = frappe.get_meta("Repair Order")
		ns_field = meta.get_field("naming_series")
		if ns_field:
			naming_series = ns_field.options or ""
	except Exception:
		pass

	total_wo = frappe.db.count("Repair Order", {"docstatus": ["!=", 2]})

	return {
		"settings": {
			"statuses": statuses,
			"naming_series": naming_series,
			"total_work_orders": total_wo,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_inspections():
	# Inspection types
	types = frappe.db.sql("""
		SELECT DISTINCT inspection_type, COUNT(*) as count
		FROM `tabVehicle Inspection`
		WHERE inspection_type IS NOT NULL AND inspection_type != ''
		GROUP BY inspection_type ORDER BY count DESC
	""", as_dict=True)

	# Form templates
	templates_count = 0
	try:
		templates_count = frappe.db.count("Inspection Form Template")
	except Exception:
		pass

	# Schedules
	schedules_count = 0
	try:
		schedules_count = frappe.db.count("Inspection Schedule")
	except Exception:
		pass

	return {
		"settings": {
			"inspection_types": types,
			"templates_count": templates_count,
			"schedules_count": schedules_count,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_issues():
	severity_scales = ["Low", "Medium", "High", "Critical"]
	categories = frappe.db.sql("""
		SELECT DISTINCT custom_category as category, COUNT(*) as count
		FROM `tabIssue` WHERE custom_category IS NOT NULL AND custom_category != ''
		GROUP BY custom_category ORDER BY count DESC
	""", as_dict=True)

	return {
		"settings": {
			"severity_scales": severity_scales,
			"categories": categories,
			"total_issues": frappe.db.count("Issue"),
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_expenses():
	categories = ["Fuel", "Parts", "Labor", "External Service", "Insurance", "Taxes", "Other"]
	total = 0
	try:
		total = frappe.db.count("Vehicle Expense")
	except Exception:
		pass

	return {
		"settings": {
			"categories": categories,
			"total_expenses": total,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_inventory():
	warehouses = frappe.get_all("Warehouse",
		fields=["name", "warehouse_name", "is_group", "company"],
		order_by="name", limit=50)

	item_groups = frappe.get_all("Item Group",
		fields=["name", "is_group", "parent_item_group"],
		order_by="name", limit=50)

	# Stock Settings
	stock_settings = {}
	try:
		ss = frappe.get_single("Stock Settings")
		stock_settings = {
			"allow_negative_stock": ss.allow_negative_stock,
			"auto_indent": ss.auto_indent if hasattr(ss, "auto_indent") else 0,
			"default_warehouse": ss.default_warehouse if hasattr(ss, "default_warehouse") else "",
		}
	except Exception:
		pass

	return {
		"settings": {
			"warehouses": warehouses,
			"item_groups": item_groups,
			"stock_settings": stock_settings,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_customers():
	groups = frappe.get_all("Customer Group",
		fields=["name", "is_group", "parent_customer_group"],
		order_by="name", limit=50)

	territories = frappe.get_all("Territory",
		fields=["name", "is_group", "parent_territory"],
		order_by="name", limit=50)

	return {
		"settings": {
			"customer_groups": groups,
			"territories": territories,
			"total_customers": frappe.db.count("Customer"),
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_users():
	roles = frappe.get_all("Role",
		filters={"disabled": 0, "is_custom": 0},
		fields=["name", "desk_access"],
		order_by="name", limit=100)

	user_count = frappe.db.count("User", {"enabled": 1, "user_type": "System User"})

	return {
		"settings": {
			"roles": roles,
			"total_users": user_count,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_notifications():
	recent_notifications = frappe.get_all("Notification Log",
		fields=["name", "subject", "type", "creation"],
		order_by="creation desc", limit=10)

	email_accounts = frappe.get_all("Email Account",
		fields=["name", "email_id", "email_account_name", "enabled"],
		limit=10)

	return {
		"settings": {
			"recent_notifications": recent_notifications,
			"email_accounts": email_accounts,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_integrations():
	email_accounts = frappe.get_all("Email Account",
		filters={"enabled": 1},
		fields=["name", "email_account_name", "email_id"],
		limit=10)

	webhooks = []
	try:
		webhooks = frappe.get_all("Webhook",
			fields=["name", "webhook_doctype", "request_url", "enabled"],
			limit=20)
	except Exception:
		pass

	hardware_test_configurations = []
	try:
		hardware_test_configurations = frappe.get_all("Hardware Test Configuration",
			fields=[
				"name", "configuration_name", "enabled", "endpoint_url", "http_method",
				"api_key_header", "response_root", "ingest_on_run",
				"max_records_per_run", "last_run", "last_status",
				"last_ingested_count", "last_error"
			],
			order_by="modified desc",
			limit=20)
	except Exception:
		pass

	return {
		"settings": {
			"email_accounts": email_accounts,
			"webhooks": webhooks,
			"hardware_test_configurations": hardware_test_configurations,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_data_audit():
	recent_activity = frappe.get_all("Activity Log",
		fields=["name", "subject", "user", "creation", "operation"],
		order_by="creation desc", limit=20)

	data_imports = []
	try:
		data_imports = frappe.get_all("Data Import",
			fields=["name", "reference_doctype", "status", "creation"],
			order_by="creation desc", limit=10)
	except Exception:
		pass

	return {
		"settings": {
			"recent_activity": recent_activity,
			"data_imports": data_imports,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


def _cat_branding():
	print_formats = frappe.get_all("Print Format",
		fields=["name", "doc_type", "standard", "creation", "modified"],
		order_by="modified desc", limit=20)

	email_templates = frappe.get_all("Email Template",
		fields=["name", "subject", "creation", "modified"],
		order_by="modified desc", limit=20)

	letter_heads = frappe.get_all("Letter Head",
		fields=["name", "is_default", "creation", "modified"],
		order_by="modified desc", limit=10)

	return {
		"settings": {
			"print_formats": print_formats,
			"email_templates": email_templates,
			"letter_heads": letter_heads,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}


@frappe.whitelist()
def seed_demo():
	"""Seed demo data."""
	from car_repair_management.demo_data import seed_demo_data
	return seed_demo_data()


@frappe.whitelist()
def clear_demo():
	"""Clear demo data."""
	from car_repair_management.demo_data import clear_demo_data
	return clear_demo_data()


@frappe.whitelist()
def demo_status():
	"""Get demo data status."""
	from car_repair_management.demo_data import get_demo_data_status
	return get_demo_data_status()


def _cat_maintenance():
	# Scheduler
	scheduler_status = "Unknown"
	try:
		from frappe.utils.scheduler import is_scheduler_inactive
		scheduler_status = "Inactive" if is_scheduler_inactive() else "Active"
	except Exception:
		pass

	# Scheduled jobs
	scheduled_jobs = frappe.get_all("Scheduled Job Type",
		fields=["name", "method", "frequency", "last_execution", "stopped"],
		order_by="last_execution desc", limit=20)

	return {
		"settings": {
			"scheduler_status": scheduler_status,
			"scheduled_jobs": scheduled_jobs,
		},
		"last_modified_by": None,
		"last_modified_on": None,
	}
