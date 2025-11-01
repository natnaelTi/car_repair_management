import frappe

def execute(filters=None):
    filters = filters or {}
    columns = [
        {"label": "Repair Order", "fieldname": "repair_order", "fieldtype": "Link", "options": "Repair Order", "width": 180},
        {"label": "Invoiced Amount", "fieldname": "invoiced", "fieldtype": "Currency", "width": 150},
        {"label": "Actual Cost", "fieldname": "actual", "fieldtype": "Currency", "width": 150},
        {"label": "Profit", "fieldname": "profit", "fieldtype": "Currency", "width": 150}
    ]
    data = []
    ros = frappe.get_all("Repair Order", fields=["name", "total_job_cost"], filters={})
    for ro in ros:
        inv = frappe.db.sql(
            """
            SELECT COALESCE(SUM(net_amount), 0) FROM `tabSales Invoice Item`
            WHERE repair_order=%s
            """,
            ro.name,
        )[0][0]
        actual = ro.total_job_cost or 0
        data.append({
            "repair_order": ro.name,
            "invoiced": inv,
            "actual": actual,
            "profit": (inv - actual)
        })
    return columns, data
