// Copyright (c) 2025, Selfmade Cloud Solutions and contributors
// For license information, please see license.txt

frappe.ui.form.on("Repair Order", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status !== "Cancelled" && frm.doc.status !== "Closed") {
			// Add status change buttons
			frm.add_custom_button(__('Set as Scheduled'), function() {
				set_ro_status(frm, 'Scheduled');
			}, __('Change Status'));

			frm.add_custom_button(__('Put On Hold'), function() {
				set_ro_status(frm, 'On Hold');
			}, __('Change Status'));

			frm.add_custom_button(__('Cancel'), function() {
				frappe.confirm(
					__('Are you sure you want to cancel this Repair Order?'),
					function() {
						set_ro_status(frm, 'Cancelled');
					}
				);
			}, __('Change Status'));
		}
	}
});

function set_ro_status(frm, new_status) {
	frappe.call({
		method: 'car_repair_management.car_repair_management.doctype.repair_order.repair_order.set_status',
		args: {
			name: frm.doc.name,
			status: new_status
		},
		callback: function(r) {
			if (!r.exc) {
				frm.reload_doc();
				frappe.show_alert({message: __('Status updated to {0}', [new_status]), indicator: 'green'});
			}
		}
	});
}
