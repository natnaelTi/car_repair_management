frappe.ui.form.on('Service Template Part', {
	item_code: function(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.item_code) return;
		frappe.db.get_value('Item', row.item_code, ['item_name', 'stock_uom']).then(r => {
			if (r.message) {
				frappe.model.set_value(cdt, cdn, 'item_name', r.message.item_name);
				if (!row.uom) {
					frappe.model.set_value(cdt, cdn, 'uom', r.message.stock_uom);
				}
			}
		});
		let price_list = frappe.boot.sysdefaults && frappe.boot.sysdefaults.selling_price_list;
		if (!price_list) {
			frappe.db.get_value('Selling Settings', 'Selling Settings', 'selling_price_list').then(r => {
				if (r.message && r.message.selling_price_list) {
					price_list = r.message.selling_price_list;
					fetch_price(row, cdt, cdn, price_list);
				}
			});
		} else {
			fetch_price(row, cdt, cdn, price_list);
		}
	}
});

function fetch_price(row, cdt, cdn, price_list) {
	frappe.db.get_value('Item Price', {item_code: row.item_code, price_list}, ['price_list_rate']).then(r => {
		if (r.message) {
			frappe.model.set_value(cdt, cdn, 'price_list', price_list);
			frappe.model.set_value(cdt, cdn, 'price_list_rate', r.message.price_list_rate);
		}
	});
}

frappe.ui.form.on('Service Template Operation', {
	operation_name: function(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.operation_name) return;
		frappe.db.get_value('Operation', row.operation_name, ['workstation']).then(r => {
			if (r.message && r.message.workstation && !row.workstation) {
				frappe.model.set_value(cdt, cdn, 'workstation', r.message.workstation);
			}
		});
	}
});

frappe.ui.form.on('Service Template Checklist Item', {
	check_item: function(frm, cdt, cdn) {
		const row = frappe.get_doc(cdt, cdn);
		if (!row.check_item) return;
		frappe.db.get_value('Handover Checklist Item', row.check_item, ['type']).then(r => {
			if (r.message && r.message.type) {
				frappe.model.set_value(cdt, cdn, 'type', r.message.type);
			}
		});
	}
});
