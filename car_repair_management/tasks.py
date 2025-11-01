import frappe

def update_job_costing_snapshots():
    # Iterate Repair Orders and update/create Job Costing snapshot
    ros = frappe.get_all("Repair Order", fields=["name", "project", "vehicle", "parts_cost", "labor_cost", "other_charges", "total_job_cost"])
    for ro in ros:
        jc = frappe.get_all("Job Costing", filters={"repair_order": ro.name}, limit=1)
        if jc:
            doc = frappe.get_doc("Job Costing", jc[0].name)
        else:
            doc = frappe.get_doc({"doctype": "Job Costing"})
            doc.repair_order = ro.name
        doc.project = ro.project
        doc.vehicle = ro.vehicle
        doc.parts_cost = ro.parts_cost
        doc.labor_cost = ro.labor_cost
        doc.other_charges = ro.other_charges
        doc.margin_snapshot = 0
        doc.save(ignore_permissions=True)
