from frappe import _

def get_data():
    return [
        {
            "label": _("Car Repair Management"),
            "icon": "octicon octicon-tools",
            "items": [
                {
                    "type": "module",
                    "name": "Car Repair Management",
                    "label": _("Car Repair Management"),
                }
            ],
        }
    ]
