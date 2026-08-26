import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def setup_vehicle_custom_fields():
    """Add custom fields to Vehicle doctype for car repair management."""
    custom_fields = {
        "Vehicle": [
            {
                "fieldname": "custom_status",
                "label": "Status",
                "fieldtype": "Select",
                "options": "Active\nIn Maintenance\nUndergoing Tests\nDelivered to Customer\nScrapped",
                "default": "Active",
                "insert_after": "license_plate",
                "in_list_view": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "custom_vehicle_type",
                "label": "Vehicle Type",
                "fieldtype": "Select",
                "options": "Car\nSUV\nTruck\nVan\nMotorcycle\nBus\nOther",
                "default": "Car",
                "insert_after": "custom_status",
            },
            {
                "fieldname": "custom_image",
                "label": "Vehicle Image",
                "fieldtype": "Attach Image",
                "insert_after": "custom_vehicle_type",
            },
            {
                "fieldname": "custom_custodian",
                "label": "Custodian",
                "fieldtype": "Link",
                "options": "Employee",
                "insert_after": "custom_image",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "custom_custodian_name",
                "label": "Custodian Name",
                "fieldtype": "Data",
                "insert_after": "custom_custodian",
                "read_only": 1,
            },
            {
                "fieldname": "custom_drivers",
                "label": "Drivers",
                "fieldtype": "Table",
                "options": "Vehicle Driver",
                "insert_after": "custom_custodian_name",
            },
            {
                "fieldname": "custom_last_known_latitude",
                "label": "Last Known Latitude",
                "fieldtype": "Float",
                "precision": 8,
                "insert_after": "location",
                "hidden": 1,
            },
            {
                "fieldname": "custom_last_known_longitude",
                "label": "Last Known Longitude",
                "fieldtype": "Float",
                "precision": 8,
                "insert_after": "custom_last_known_latitude",
                "hidden": 1,
            },
            {
                "fieldname": "custom_last_location_update",
                "label": "Last Location Update",
                "fieldtype": "Datetime",
                "insert_after": "custom_last_known_longitude",
                "hidden": 1,
            },
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    return {"success": True, "message": "Custom fields created successfully"}
