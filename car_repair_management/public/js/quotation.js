frappe.ui.form.on('Quotation', {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.custom_repair_order) {
			frm.add_custom_button(__('RO Sales Order'), () => {
				frappe.call({
					method: 'car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_sales_order_from_quotation',
					args: {quotation_name: frm.doc.name},
					callback: function(r) {
						if (r.message) {
							frappe.model.sync(r.message);
							frappe.set_route('Form', 'Sales Order', r.message.name);
						}
					}
				});
			}, __('Create'));
		}
	}
});
