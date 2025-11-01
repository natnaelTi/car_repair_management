"""Auto-update RO status based on task and document states."""
import frappe


def update_ro_status_from_task(task_doc, method=None):
    """Auto-update RO status when tasks change."""
    if not task_doc.repair_order:
        return
    
    ro = frappe.get_doc("Repair Order", task_doc.repair_order)
    
    # Skip if RO is in hold/cancelled/closed states
    if ro.status in ("On Hold", "Delivered", "Closed", "Cancelled"):
        return
    
    # Auto transition: Scheduled -> In Progress when any task starts
    if task_doc.status in ("Working", "Open") and ro.status == "Scheduled":
        ro.status = "In Progress"
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)
        frappe.msgprint(f"Repair Order {ro.name} status updated to In Progress", alert=True, indicator="blue")
    
    # Auto transition: In Progress -> Completed when all tasks are closed
    elif task_doc.status == "Completed" or task_doc.status == "Closed":
        check_and_complete_ro(ro)


def check_and_complete_ro(ro):
    """Check if all tasks are completed and transition RO to Completed."""
    if ro.status != "In Progress":
        return
    
    # Get all tasks for this RO
    task_names = [op.task for op in (ro.operations or []) if op.task]
    if not task_names:
        return
    
    # Check if all tasks are completed
    open_tasks = frappe.db.count("Task", {
        "name": ["in", task_names],
        "status": ["not in", ["Completed", "Closed", "Cancelled"]]
    })
    
    if open_tasks == 0:
        ro.status = "Completed"
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)
        frappe.msgprint(f"Repair Order {ro.name} status updated to Completed", alert=True, indicator="green")


def update_ro_status_from_sales_invoice(si_doc, method=None):
    """Auto-update RO status when Sales Invoice is submitted."""
    ro_name = si_doc.custom_repair_order if hasattr(si_doc, 'custom_repair_order') else None
    if not ro_name:
        for item in (si_doc.items or []):
            if hasattr(item, 'repair_order') and item.repair_order:
                ro_name = item.repair_order
                break
    
    if not ro_name:
        return
    
    ro = frappe.get_doc("Repair Order", ro_name)
    
    # Skip if already in final states
    if ro.status in ("Delivered", "Closed", "Cancelled"):
        return
    
    # Auto transition: Completed -> Invoiced when SI is submitted
    if si_doc.docstatus == 1 and ro.status == "Completed":
        ro.status = "Invoiced"
        ro.flags.ignore_validate_update_after_submit = True
        ro.save(ignore_permissions=True)
        frappe.msgprint(f"Repair Order {ro.name} status updated to Invoiced", alert=True, indicator="green")
