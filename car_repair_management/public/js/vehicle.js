// Vehicle customizations - uses vehicle_dashboard.py for connections and heatmap
frappe.ui.form.on('Vehicle', {
	refresh(frm) {
		// Connections and heatmap are automatically handled by vehicle_dashboard.py
		// No custom code needed
	}
});
