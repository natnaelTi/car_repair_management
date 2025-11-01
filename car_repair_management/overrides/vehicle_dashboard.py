"""Dashboard configuration for Vehicle doctype - adds Repair Order connections and heatmap."""

import frappe
from frappe import _
from frappe.query_builder.functions import Count, CurDate, Date, UnixTimestamp
from frappe.query_builder import Interval


def get_data(data=None):
	"""
	Override Vehicle dashboard to add Repair Order, Project, Task connections
	and enable heatmap based on Repair Order creation.
	
	This extends the default ERPNext Vehicle dashboard with car repair management features.
	"""
	return {
		"heatmap": True,
		"heatmap_message": _("This is based on the Repair Orders created for this vehicle"),
		"fieldname": "vehicle",
		"method": "car_repair_management.overrides.vehicle_dashboard.get_timeline_data",
		"non_standard_fieldnames": {
			"Delivery Trip": "vehicle",
		},
		"transactions": [
			{
				"label": _("Vehicle Logs"),
				"items": ["Vehicle Log"]
			},
			{
				"label": _("Delivery"),
				"items": ["Delivery Trip"]
			},
			{
				"label": _("Repair & Service"),
				"items": ["Repair Order"]
			},
			{
				"label": _("Sales"),
				"items": ["Quotation", "Sales Order", "Sales Invoice"]
			},
		],
	}


@frappe.whitelist()
def get_timeline_data(doctype, name):
	"""Return timeline data for Repair Orders created for this vehicle."""
	
	repair_order = frappe.qb.DocType("Repair Order")
	
	# Get RO creation dates for the past year
	timeline_data = dict(
		frappe.qb.from_(repair_order)
		.select(UnixTimestamp(repair_order.creation), Count("*"))
		.where(repair_order.vehicle == name)
		.where(repair_order.creation > CurDate() - Interval(years=1))
		.where(repair_order.docstatus < 2)
		.groupby(Date(repair_order.creation))
		.run()
	)
	
	return timeline_data
