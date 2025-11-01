import frappe
from frappe.utils import add_days, nowdate

def execute(filters=None):
    filters = filters or {}
    days = int(filters.get('days') or 30)
    since = add_days(nowdate(), -days)

    columns = [
        {"label": "Vehicle", "fieldname": "vehicle", "fieldtype": "Link", "options": "Vehicle", "width": 160},
        {"label": "First RO", "fieldname": "first_ro", "fieldtype": "Link", "options": "Repair Order", "width": 150},
        {"label": "First Handover", "fieldname": "first_date", "fieldtype": "Date", "width": 120},
        {"label": "Return RO", "fieldname": "return_ro", "fieldtype": "Link", "options": "Repair Order", "width": 150},
        {"label": "Return Date", "fieldname": "return_date", "fieldtype": "Date", "width": 120},
        {"label": "Issue Category", "fieldname": "issue_category", "fieldtype": "Data", "width": 160},
    ]

    # Rough heuristic: vehicle with at least 2 ROs in last X days
    ros = frappe.db.sql(
        """
        select vehicle, name, status, owner, creation
        from `tabRepair Order`
        where creation >= %s
        order by vehicle, creation
        """,
        since, as_dict=True
    )

    data = []
    by_vehicle = {}
    for r in ros:
        by_vehicle.setdefault(r.vehicle, []).append(r)

    for v, lst in by_vehicle.items():
        if len(lst) >= 2:
            first = lst[0]
            for ret in lst[1:]:
                data.append({
                    'vehicle': v,
                    'first_ro': first.name,
                    'first_date': first.creation.date(),
                    'return_ro': ret.name,
                    'return_date': ret.creation.date(),
                    'issue_category': None
                })

    chart = {
        'data': {
            'labels': [d['vehicle'] for d in data],
            'datasets': [{'name': 'Returns', 'values': [1 for _ in data]}]
        },
        'type': 'bar'
    }

    return columns, data, None, chart
