import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RepairOrder(Document):
    pass


def _mutual_exclusion_parts(doc):
    for d in doc.parts_plan or []:
        if d.is_billable and d.is_foc:
            frappe.throw("Parts Plan row cannot be both Billable and FoC")
        if d.item_code and not d.item_name:
            d.item_name = frappe.db.get_value("Item", d.item_code, "item_name")


def on_validate(doc, method=None):
    _mutual_exclusion_parts(doc)
    # Basic SLA validations
    if doc.sla_delivery_by and doc.sla_response_by and doc.sla_delivery_by < doc.sla_response_by:
        frappe.throw("SLA Delivery By cannot be before SLA Response By")


def before_save(doc, method=None):
    # Recompute cost aggregates
    _recompute_costs(doc)


def after_save(doc, method=None):
    pass


def on_submit(doc, method=None):
    # Set default status to Scheduled on submit
    if not doc.status:
        doc.status = "Scheduled"
    
    # Expand from Service Template if provided (simple copy)
    if doc.service_template:
        _apply_service_template(doc)
    
    # Create project and tasks (only if not already created)
    if not doc.project:
        _create_project_and_tasks(doc)


def _create_project_and_tasks(doc):
    """Create project and tasks for a submitted RO."""
    # Create Project
    project = frappe.get_doc({
        "doctype": "Project",
        "project_name": f"RO {doc.name} - {doc.customer}",
        "repair_order": doc.name,
        "expected_start_date": now_datetime(),
    }).insert(ignore_permissions=True)
    
    # Create Tasks for each operation
    task_names = []
    for idx, op in enumerate(doc.operations or [], start=1):
        task = frappe.get_doc({
            "doctype": "Task",
            "subject": op.operation_name or f"Operation {idx}",
            "project": project.name,
            "repair_order": doc.name,
            "exp_start_date": now_datetime(),
            "is_group": 0,
        }).insert(ignore_permissions=True)
        task_names.append((op.name, task.name))
    
    # Update operation rows with task links and reload doc to get updated child rows
    for op_name, task_name in task_names:
        frappe.db.set_value("Repair Operation Line", op_name, "task", task_name, update_modified=False)
    
    # Update RO with project using db_set which will trigger update after submit
    doc.db_set("project", project.name, update_modified=False)
    frappe.db.commit()
    
    frappe.msgprint(f"Created Project {project.name} and {len(task_names)} tasks", alert=True, indicator="green")


def before_update_after_submit(doc, method=None):
    # Recompute costs on status changes
    _recompute_costs(doc)
    
    # Guard: Ready for Handover requires all QC tasks completed
    if doc.status == "Ready for Handover":
        qc_incomplete = []
        for op in doc.operations or []:
            if op.is_qc and op.task:
                status = frappe.db.get_value("Task", op.task, "status")
                if status != "Closed":
                    qc_incomplete.append(op.operation_name or op.task)
        if qc_incomplete:
            frappe.throw("Cannot set Ready for Handover. QC tasks incomplete: " + ", ".join(qc_incomplete))

    # Guard: Close requires Sales Invoices fully paid
    if doc.status in ("Closed",):
        if doc.sales_invoice:
            status = frappe.db.get_value("Sales Invoice", doc.sales_invoice, "status")
            if status not in ("Paid", "Submitted"):
                frappe.throw("Cannot Close. Linked Sales Invoice not fully paid.")
    
    # Snapshot to Job Costing on status transitions
    _update_job_costing_snapshot(doc)


@frappe.whitelist()
def make_quotation_from_repair_order(name: str):
    doc = frappe.get_doc("Repair Order", name)
    quotation = frappe.new_doc("Quotation")
    quotation.quotation_to = "Customer"
    quotation.party_name = doc.customer
    quotation.order_type = "Maintenance"
    quotation.custom_repair_order = doc.name
    # Add operations as service items (zero rate)
    for op in doc.operations or []:
        quotation.append("items", {
            "item_code": None,
            "item_name": op.operation_name or "Service Operation",
            "description": (op.operation_name or "Service Operation"),
            "qty": 1,
            "uom": "Nos",
            "rate": 0,
            "repair_order": doc.name,
            "vehicle": doc.vehicle,
        })
    # Add billable parts
    for part in doc.parts_plan or []:
        if part.is_billable:
            quotation.append("items", {
                "item_code": part.item_code,
                "item_name": part.item_name,
                "description": part.item_name,
                "qty": part.qty_planned or 0,
                "uom": part.uom or frappe.db.get_value("Item", part.item_code, "stock_uom"),
                "repair_order": doc.name,
                "vehicle": doc.vehicle,
            })
    quotation.flags.ignore_permissions = True
    quotation.insert()
    return quotation.as_dict()


@frappe.whitelist()
def make_material_request_from_repair_order(name: str):
    doc = frappe.get_doc("Repair Order", name)
    mr = frappe.new_doc("Material Request")
    mr.material_request_type = "Material Issue"
    mr.company = frappe.defaults.get_user_default("Company")
    # determine a warehouse
    wh = None
    if mr.company:
        try:
            wh = frappe.db.get_value("Company", mr.company, "default_warehouse")
        except Exception:
            wh = None
    if not wh:
        wh = frappe.db.get_value("Warehouse", {"is_group": 0, "company": mr.company})
    for part in doc.parts_plan or []:
        if part.is_billable:
            mr.append("items", {
                "item_code": part.item_code,
                "qty": part.qty_planned or 0,
                "schedule_date": now_datetime(),
                "uom": part.uom or frappe.db.get_value("Item", part.item_code, "stock_uom"),
                "warehouse": wh,
            })
    mr.flags.ignore_permissions = True
    mr.insert()
    return mr.as_dict()


def _apply_service_template(doc):
    template = frappe.get_doc("Service Template", doc.service_template)
    if not doc.operations:
        doc.set("operations", [])
    for d in template.default_operations or []:
        doc.append("operations", {
            "operation_name": d.operation_name,
            "planned_minutes": d.planned_minutes,
            "workstation": d.workstation,
            "is_qc": d.is_qc,
        })
    if not doc.parts_plan:
        doc.set("parts_plan", [])
    for d in template.default_parts or []:
        doc.append("parts_plan", {
            "item_code": d.item_code,
            "item_name": d.item_name or frappe.db.get_value("Item", d.item_code, "item_name"),
            "uom": d.uom,
            "qty_planned": d.qty_planned,
            "is_billable": d.is_billable,
            "is_foc": d.is_foc,
            "notes": d.notes,
        })
    if not doc.handover_checklist:
        doc.set("handover_checklist", [])
    for d in template.default_checklist or []:
        doc.append("handover_checklist", {
            "check_item": d.check_item,
            "type": d.type,
        })


@frappe.whitelist()
def apply_service_template(name: str, template: str):
    """Apply service template to an existing Repair Order (before submit)."""
    doc = frappe.get_doc("Repair Order", name)
    if doc.docstatus != 0:
        frappe.throw("Cannot apply template to submitted Repair Order")
    doc.service_template = template
    _apply_service_template(doc)
    doc.save(ignore_permissions=True)
    return doc.as_dict()


@frappe.whitelist()
def make_sales_order_from_quotation(quotation_name: str):
    """Create Sales Order from Quotation, carrying over RO link and project."""
    from erpnext.selling.doctype.quotation.quotation import _make_sales_order
    quotation = frappe.get_doc("Quotation", quotation_name)
    so_doc = _make_sales_order(quotation_name)
    
    # Carry over RO link from quotation
    if hasattr(quotation, 'custom_repair_order') and quotation.custom_repair_order:
        so_doc.custom_repair_order = quotation.custom_repair_order
        
        # Get and set project from RO
        ro = frappe.get_doc("Repair Order", quotation.custom_repair_order)
        if ro.project:
            so_doc.project = ro.project
        
        # Also set RO link on items (for tracking)
        for item in so_doc.items:
            item.repair_order = quotation.custom_repair_order
            if ro.vehicle:
                item.vehicle = ro.vehicle
    
    return so_doc


@frappe.whitelist()
def make_sales_invoice_from_sales_order(sales_order_name: str):
    """Create Sales Invoice from Sales Order, carrying over RO link."""
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    si = make_sales_invoice(sales_order_name)
    
    # Carry over RO link from sales order
    if hasattr(sales_order, 'custom_repair_order') and sales_order.custom_repair_order:
        si.custom_repair_order = sales_order.custom_repair_order
        
        # Get RO for additional info
        ro = frappe.get_doc("Repair Order", sales_order.custom_repair_order)
        
        # Set RO link on items (for tracking)
        for item in si.items:
            item.repair_order = sales_order.custom_repair_order
            if ro.vehicle:
                item.vehicle = ro.vehicle
    
    return si


def _recompute_costs(doc):
    """Compute parts_cost, labor_cost, other_charges, total_job_cost, quoted_amount, invoiced_amount, gross_margin."""
    # Parts cost from planned parts (valuation rate)
    parts_cost = 0
    for d in doc.parts_plan or []:
        rate = frappe.db.get_value("Item", d.item_code, "valuation_rate") if d.item_code else 0
        try:
            rate = float(rate or 0)
        except Exception:
            rate = 0
        parts_cost += (float(d.qty_planned or 0) * rate)
    
    # Labor cost from actual timesheets linked to this RO or its project/tasks
    labor_cost = 0.0
    if doc.name:
        # Direct RO link
        ts_hours = frappe.db.sql(
            """
            select sum(tl.hours * tl.billing_rate) as cost
            from `tabTimesheet` ts
            join `tabTimesheet Detail` tl on tl.parent = ts.name
            where ts.docstatus = 1 and ts.repair_order = %s
            """,
            doc.name
        )
        if ts_hours and ts_hours[0][0]:
            labor_cost += float(ts_hours[0][0])
        
        # Via project link (project is in Timesheet Detail, not Timesheet parent)
        if doc.project:
            ts_proj = frappe.db.sql(
                """
                select sum(tl.hours * tl.billing_rate) as cost
                from `tabTimesheet` ts
                join `tabTimesheet Detail` tl on tl.parent = ts.name
                where ts.docstatus = 1 and tl.project = %s
                """,
                doc.project
            )
            if ts_proj and ts_proj[0][0]:
                labor_cost += float(ts_proj[0][0])
        
        # Via tasks (find tasks linked to RO)
        task_names = [op.task for op in (doc.operations or []) if op.task]
        if task_names:
            placeholders = ','.join(['%s'] * len(task_names))
            ts_task = frappe.db.sql(
                f"""
                select sum(tl.hours * tl.billing_rate) as cost
                from `tabTimesheet` ts
                join `tabTimesheet Detail` tl on tl.parent = ts.name
                where ts.docstatus = 1 and tl.task in ({placeholders})
                """,
                tuple(task_names)
            )
            if ts_task and ts_task[0][0]:
                labor_cost += float(ts_task[0][0])
    
    # Other charges from Purchase Invoices linked to RO
    other_charges_auto = 0.0
    if doc.name:
        pi_total = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabPurchase Invoice`
            where docstatus = 1 and repair_order = %s
            """,
            doc.name
        )
        if pi_total and pi_total[0][0]:
            other_charges_auto = float(pi_total[0][0])
    
    # If other_charges manually set, keep it; else use auto
    if not doc.other_charges:
        doc.other_charges = other_charges_auto
    
    doc.parts_cost = parts_cost
    doc.labor_cost = labor_cost
    doc.total_job_cost = (doc.parts_cost or 0) + (doc.labor_cost or 0) + (doc.other_charges or 0)
    
    # Quoted amount from linked quotation or any quotation with this RO
    quoted = 0.0
    if doc.quotation:
        q_total = frappe.db.get_value("Quotation", doc.quotation, "grand_total")
        quoted = float(q_total or 0)
    elif doc.name:
        # Find quotations linked via parent field
        q_totals = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabQuotation`
            where docstatus = 1 and custom_repair_order = %s
            """,
            doc.name
        )
        if q_totals and q_totals[0][0]:
            quoted = float(q_totals[0][0])
    doc.quoted_amount = quoted
    
    # Invoiced amount from linked sales invoice or any SI with this RO
    invoiced = 0.0
    if doc.sales_invoice:
        si_total = frappe.db.get_value("Sales Invoice", doc.sales_invoice, "grand_total")
        invoiced = float(si_total or 0)
    elif doc.name:
        # Find sales invoices linked via parent field
        si_totals = frappe.db.sql(
            """
            select sum(grand_total) as total
            from `tabSales Invoice`
            where docstatus = 1 and custom_repair_order = %s
            """,
            doc.name
        )
        if si_totals and si_totals[0][0]:
            invoiced = float(si_totals[0][0])
    doc.invoiced_amount = invoiced
    
    # Gross margin
    doc.gross_margin = (doc.invoiced_amount or 0) - (doc.total_job_cost or 0)


def update_ro_from_timesheet(timesheet_doc, method=None):
    """Update RO labor cost when timesheet is submitted/cancelled."""
    ro_name = getattr(timesheet_doc, 'repair_order', None)
    if not ro_name:
        # Try via task in time_logs (project is in Timesheet Detail, not parent)
        for d in (timesheet_doc.time_logs or []):
            if d.task:
                ro_name = frappe.db.get_value("Task", d.task, "repair_order")
                if ro_name:
                    break
            # Try via project in time_logs
            if not ro_name and hasattr(d, 'project') and d.project:
                ro_name = frappe.db.get_value("Project", d.project, "repair_order")
                if ro_name:
                    break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_purchase_invoice(pi_doc, method=None):
    """Update RO other_charges when PI is submitted/cancelled."""
    if pi_doc.repair_order:
        ro = frappe.get_doc("Repair Order", pi_doc.repair_order)
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_quotation(quotation_doc, method=None):
    """Update RO quoted_amount and quotation field when Quotation is submitted/cancelled."""
    # Find RO via parent field or quotation items
    ro_name = quotation_doc.custom_repair_order if hasattr(quotation_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (quotation_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update quotation field if not already set (for first quotation only)
        if not ro.quotation and quotation_doc.docstatus == 1:
            ro.quotation = quotation_doc.name
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_sales_order(so_doc, method=None):
    """Update RO sales_order field when SO is submitted."""
    # Find RO via parent field or sales order items
    ro_name = so_doc.custom_repair_order if hasattr(so_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (so_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update sales_order field if not already set (for first SO only)
        if not ro.sales_order and so_doc.docstatus == 1:
            ro.sales_order = so_doc.name
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def update_ro_from_sales_invoice(si_doc, method=None):
    """Update RO invoiced_amount and sales_invoice field when SI is submitted/cancelled."""
    # Find RO via parent field or sales invoice items
    ro_name = si_doc.custom_repair_order if hasattr(si_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (si_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    if ro_name:
        ro = frappe.get_doc("Repair Order", ro_name)
        # Update sales_invoice field if not already set (for first invoice only)
        if not ro.sales_invoice and si_doc.docstatus == 1:
            ro.sales_invoice = si_doc.name
        _recompute_costs(ro)
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)


def _update_job_costing_snapshot(doc):
    """Create or update Job Costing record for this RO."""
    if not doc.name:
        return
    jc_name = frappe.db.get_value("Job Costing", {"repair_order": doc.name})
    if jc_name:
        jc = frappe.get_doc("Job Costing", jc_name)
    else:
        jc = frappe.get_doc({
            "doctype": "Job Costing",
            "repair_order": doc.name,
            "project": doc.project,
            "vehicle": doc.vehicle,
        })
    jc.parts_cost = doc.parts_cost or 0
    jc.labor_cost = doc.labor_cost or 0
    jc.other_charges = doc.other_charges or 0
    jc.total_job_cost = doc.total_job_cost or 0
    jc.margin_snapshot = doc.gross_margin or 0
    if jc.name:
        jc.save(ignore_permissions=True)
    else:
        jc.insert(ignore_permissions=True)


@frappe.whitelist()
def set_status(name: str, status: str):
    """Manually set RO status (for Scheduled, On Hold, Cancelled)."""
    allowed_statuses = ["Scheduled", "On Hold", "Cancelled"]
    if status not in allowed_statuses:
        frappe.throw(f"Cannot manually set status to {status}. Use buttons for: {', '.join(allowed_statuses)}")
    
    doc = frappe.get_doc("Repair Order", name)
    doc.status = status
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)
    frappe.msgprint(f"Status updated to {status}", alert=True, indicator="blue")
    return doc.as_dict()
