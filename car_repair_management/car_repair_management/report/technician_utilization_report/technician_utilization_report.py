import frappe

def execute(filters=None):
    filters = filters or {}
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    employee = filters.get('employee')

    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 180},
        {"label": "Hours Booked", "fieldname": "hours", "fieldtype": "Float", "width": 120},
        {"label": "Capacity Hours", "fieldname": "capacity", "fieldtype": "Float", "width": 120},
        {"label": "Utilization %", "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
    ]

    conditions = " where ts.docstatus = 1 and tl.from_time >= %s and tl.to_time <= %s"
    params = [from_date, to_date]
    if employee:
        conditions += " and tl.employee = %s"
        params.append(employee)

    res = frappe.db.sql(
        f"""
        select tl.employee, sum(tl.hours) as hours
        from `tabTimesheet` ts
        join `tabTimesheet Detail` tl on tl.parent = ts.name
        {conditions}
        group by tl.employee
        """,
        params,
        as_dict=True,
    )

    data = []
    for row in res:
        # Assume 8 hours/day capacity between range
        days = frappe.utils.date_diff(to_date, from_date) + 1
        capacity = days * 8.0
        utilization = (float(row.hours or 0) / capacity * 100.0) if capacity else 0
        data.append({
            "employee": row.employee,
            "hours": row.hours or 0,
            "capacity": capacity,
            "utilization": utilization,
        })

    return columns, data
