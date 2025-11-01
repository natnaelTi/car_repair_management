import frappe
from frappe.utils import nowdate

def execute(filters=None):
    today = nowdate()
    columns = [
        {"label": "RO ID", "fieldname": "repair_order", "fieldtype": "Link", "options": "Repair Order", "width": 150},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 140},
        {"label": "Days in Status", "fieldname": "days_in_status", "fieldtype": "Int", "width": 120},
        {"label": "SLA Due", "fieldname": "sla_delivery_by", "fieldtype": "Datetime", "width": 180},
        {"label": "Advisor", "fieldname": "advisor", "fieldtype": "Link", "options": "User", "width": 160},
        {"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 160},
    ]

    # Approximate days in status using last modified timestamp since last_status_change is not tracked
    rows = frappe.db.sql(
        """
        select name as repair_order, status, vehicle, sla_delivery_by,
               TIMESTAMPDIFF(DAY, modified, %(today)s) as days_in_status,
               owner as advisor
        from `tabRepair Order`
        where status not in ('Closed', 'Cancelled')
        """,
        {"today": today}, as_dict=True
    )

    data = list(rows)

    # histogram-like chart buckets
    buckets = [0,0,0,0,0]
    for r in data:
        d = int(r.days_in_status or 0)
        if d <= 1: buckets[0]+=1
        elif d <=3: buckets[1]+=1
        elif d <=7: buckets[2]+=1
        elif d <=14: buckets[3]+=1
        else: buckets[4]+=1
    chart = {
        'data': {
            'labels': ['<=1d','2-3d','4-7d','8-14d','>14d'],
            'datasets': [{'name': 'ROs', 'values': buckets}]
        },
        'type': 'bar'
    }

    return columns, data, None, chart
