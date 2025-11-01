import frappe

def get_context(context):
    name = frappe.form_dict.get('name') or context.get('name')
    ro = frappe.get_doc('Repair Order', name)
    tasks = []
    if ro.project:
        tasks = frappe.get_all('Task', filters={'project': ro.project}, fields=['name','subject','status','exp_start_date','exp_end_date'])
    updates = [d for d in ro.customer_updates if d.visible_on_portal]
    context.repair_order = ro
    context.tasks = tasks
    context.updates = updates
    return context
