import frappe
from frappe.utils import getdate

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')

    conditions = []
    params = []
    if from_date:
        conditions.append("ro.creation >= %s")
        params.append(from_date)
    if to_date:
        conditions.append("ro.creation <= %s")
        params.append(to_date)
    where = (" where " + " and ".join(conditions)) if conditions else ""

    columns = [
        {"label": "Repair Order", "fieldname": "repair_order", "fieldtype": "Link", "options": "Repair Order", "width": 160},
        {"label": "Item Code", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 160},
        {"label": "Qty Issued", "fieldname": "qty", "fieldtype": "Float", "width": 100},
        {"label": "Valuation Rate", "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 120},
        {"label": "Extended Cost", "fieldname": "extended_cost", "fieldtype": "Currency", "width": 140},
        {"label": "Billable", "fieldname": "billable", "fieldtype": "Data", "width": 90},
    ]

    # Actual issued from Stock Entry Detail linked via reference to RO (if using custom field)
    # Fallback: use parts_plan as planned and assume valuation_rate from Item
    data = []

    # Try stock entries first
    issued = frappe.db.sql(
        """
        select sed.item_code, sum(sed.qty) as qty, avg(sed.valuation_rate) as valuation_rate, se.repair_order
        from `tabStock Entry` se
        join `tabStock Entry Detail` sed on sed.parent = se.name
        where coalesce(se.repair_order, '') != ''
        group by se.repair_order, sed.item_code
        """,
        as_dict=True,
    )
    billable_map = {}
    # Build billable map from parts_plan
    parts_flags = frappe.db.sql(
        """
        select parent as repair_order, item_code, max(case when is_billable=1 then 1 else 0 end) as is_billable
        from `tabRepair Parts Plan`
        group by parent, item_code
        """,
        as_dict=True,
    )
    for r in parts_flags:
        billable_map[(r.repair_order, r.item_code)] = 'Billable' if r.is_billable else 'FoC'

    total_billable = 0.0
    total_foc = 0.0

    for row in issued:
        bill = billable_map.get((row.repair_order, row.item_code), 'Billable')
        extended = float(row.qty or 0) * float(row.valuation_rate or 0)
        if bill == 'Billable':
            total_billable += extended
        else:
            total_foc += extended
        data.append({
            'repair_order': row.repair_order,
            'item_code': row.item_code,
            'qty': row.qty,
            'valuation_rate': row.valuation_rate,
            'extended_cost': extended,
            'billable': bill,
        })

    chart = {
        'data': {
            'labels': ['Billable', 'FoC'],
            'datasets': [{'name': 'Cost', 'values': [total_billable, total_foc]}]
        },
        'type': 'pie'
    }

    return columns, data, None, chart
