frappe.ui.form.on('Repair Order', {
    service_template: function(frm) {
        if (!frm.doc.service_template) return;
        frappe.model.with_doc('Service Template', frm.doc.service_template, function() {
            let template = frappe.model.get_doc('Service Template', frm.doc.service_template);
            if (!template) return;
            
            // Populate operations
            (template.default_operations || []).forEach(op => {
                let row = frm.add_child('operations');
                row.operation_name = op.operation_name;
                row.planned_minutes = op.planned_minutes;
                row.workstation = op.workstation;
                row.is_qc = op.is_qc;
            });
            
            // Populate parts
            (template.default_parts || []).forEach(part => {
                let row = frm.add_child('parts_plan');
                row.item_code = part.item_code;
                row.item_name = part.item_name;
                row.uom = part.uom;
                row.qty_planned = part.qty_planned;
                row.is_billable = part.is_billable;
                row.is_foc = part.is_foc;
                row.notes = part.notes;
            });
            
            // Populate checklist
            (template.default_checklist || []).forEach(check => {
                let row = frm.add_child('handover_checklist');
                row.check_item = check.check_item;
                row.type = check.type;
            });
            
            frm.refresh_fields(['operations', 'parts_plan', 'handover_checklist']);
        });
    },
    refresh(frm) {
        // Buttons to create Quotation and Material Request
        if (!frm.is_new()) {
            frm.add_custom_button(__('Make Quotation'), () => {
                frappe.call('car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_quotation_from_repair_order', {
                    name: frm.doc.name,
                }).then(r => {
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frappe.show_alert({message: __('Quotation created'), indicator: 'green'});
                    }
                });
            }, __('Create'));

            frm.add_custom_button(__('Material Request'), () => {
                frappe.call('car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_material_request_from_repair_order', {
                    name: frm.doc.name,
                }).then(r => {
                    if (r.message) {
                        frappe.model.sync(r.message);
                        frappe.show_alert({message: __('Material Request created'), indicator: 'green'});
                    }
                });
            }, __('Create'));
        }

        // Color code parts plan rows
        if (frm.fields_dict.parts_plan) {
            (frm.doc.parts_plan || []).forEach((d) => {
                const row = frm.fields_dict.parts_plan.grid.get_row(d.name);
                if (row) {
                    row.wrapper.style.background = d.is_foc ? '#fdf6e3' : d.is_billable ? '#e8f5e9' : '';
                }
            });
        }
    },

    // Live cost recompute placeholder
    parts_plan_add: recompute_costs,
    parts_plan_remove: recompute_costs,
    operations_add: recompute_costs,
    operations_remove: recompute_costs,
});

function recompute_costs(frm) {
    // Server-driven recompute on save; here we just refresh preview fields
    frm.refresh_fields(["parts_cost", "labor_cost", "other_charges", "total_job_cost"]);
}
