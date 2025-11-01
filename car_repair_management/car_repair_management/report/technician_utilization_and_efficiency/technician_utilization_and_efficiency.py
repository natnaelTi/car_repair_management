import frappe

def execute(filters=None):
    # Reuse logic similar to technician_utilization_report but add efficiency column
    filters = filters or {}
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    employee = filters.get('employee')

    columns = [
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 180},
        {"label": "Planned Hours", "fieldname": "planned", "fieldtype": "Float", "width": 140},
        {"label": "Logged Hours", "fieldname": "logged", "fieldtype": "Float", "width": 140},
        {"label": "Utilization %", "fieldname": "utilization", "fieldtype": "Percent", "width": 120},
        {"label": "Efficiency %", "fieldname": "efficiency", "fieldtype": "Percent", "width": 120}
    ]

    conditions = " where ts.docstatus = 1"
    params = []
    if from_date:
        conditions += " and tl.from_time >= %s"
        params.append(from_date)
    if to_date:
        conditions += " and tl.to_time <= %s"
        params.append(to_date)
    if employee:
        conditions += " and ts.employee = %s"
        params.append(employee)

    res = frappe.db.sql(
        f"""
        select ts.employee, sum(tl.hours) as logged
        from `tabTimesheet` ts
        join `tabTimesheet Detail` tl on tl.parent = ts.name
        {conditions}
        group by ts.employee
        """,
        params,
        as_dict=True,
    )

    # Planned hours approximation from Task planned minutes linked via Timesheet Details if available
    # If not linkable, consider 8h/day capacity over selected period
    data = []
    days = None
    if from_date and to_date:
        days = frappe.utils.date_diff(to_date, from_date) + 1
    for row in res:
        capacity = (days * 8.0) if days else 40.0
        planned = capacity
        logged = float(row.logged or 0)
        utilization = (logged / capacity * 100.0) if capacity else 0
        efficiency = utilization  # placeholder; can refine by comparing against planned task-level hours
        data.append({
            "employee": row.employee,
            "planned": planned,
            "logged": logged,
            "utilization": utilization,
            "efficiency": efficiency,
        })

    # simple grouped bar style
    chart = {
        'data': {
            'labels': [d['employee'] for d in data],
            'datasets': [
                {'name': 'Utilization %', 'values': [round(d['utilization'], 2) for d in data]},
                {'name': 'Efficiency %', 'values': [round(d['efficiency'], 2) for d in data]},
            ]
        },
        'type': 'bar'
    }

    return columns, data, None, chart
