frappe.ui.form.on('Task', {
    refresh(frm) {
        if (frm.doc.repair_order && frm.perm[0].write) {
            frm.add_custom_button(__('Start Timesheet'), () => start_timesheet(frm), __('Timesheet'));
        }
    }
});

function start_timesheet(frm) {
    frappe.call('frappe.client.insert', {
        doc: {
            doctype: 'Timesheet',
            start_date: frappe.datetime.now_date(),
            time_logs: [{
                activity_type: 'Repair Work',
                from_time: frappe.datetime.now_datetime(),
                hours: 0,
                task: frm.doc.name,
                completed: 0
            }],
            repair_order: frm.doc.repair_order,
            project: frm.doc.project
        }
    }).then(r => {
        if (r.message) {
            frappe.show_alert({message: __('Timesheet started'), indicator: 'green'});
        }
    });
}
