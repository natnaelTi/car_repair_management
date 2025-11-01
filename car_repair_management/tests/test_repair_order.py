import frappe
import unittest

class TestRepairOrder(unittest.TestCase):
    def setUp(self):
        frappe.flags.test_roles = ['System Manager']

    def test_repair_order_flow(self):
        # Ensure Customer
        if not frappe.db.exists('Customer', 'Test Car Customer'):
            frappe.get_doc({
                'doctype': 'Customer',
                'customer_name': 'Test Car Customer',
                'customer_type': 'Individual'
            }).insert()

        # Ensure Vehicle (from ERPNext vehicle doctype)
        vehicle_name = 'TEST-VEH-001'
        if not frappe.db.exists('Vehicle', vehicle_name):
            # Ensure UOM for odometer
            if not frappe.db.exists('UOM', 'Km'):
                frappe.get_doc({'doctype': 'UOM', 'uom_name': 'Km'}).insert()
            frappe.get_doc({
                'doctype': 'Vehicle',
                'license_plate': vehicle_name,
                'make': 'TestMake',
                'model': 'TestModel',
                'owner': 'Test Car Customer',
                'uom': 'Km',
                'last_odometer': 0,
            }).insert()

        # Service Template
        st_name = 'Basic Service'
        if not frappe.db.exists('Service Template', st_name):
            st = frappe.get_doc({
                'doctype': 'Service Template',
                'template_name': st_name,
            })
            op_name = _ensure_operation('Inspection')
            st.append('default_operations', {
                'operation_name': op_name,
                'planned_minutes': 30,
            })
            st.append('default_parts', {
                'item_code': _ensure_stock_item('Test Item A'),
                'uom': 'Nos',
                'qty_planned': 2,
                'is_billable': 1,
                'is_foc': 0,
            })
            st.insert()
        else:
            st = frappe.get_doc('Service Template', st_name)

        # Create Repair Order
        ro = frappe.get_doc({
            'doctype': 'Repair Order',
            'customer': 'Test Car Customer',
            'vehicle': vehicle_name,
            'priority': 'Normal',
            'service_template': st.name,
        })
        ro.append('operations', {
            'operation_name': 'Engine Check',
            'planned_minutes': 60,
        })
        ro.append('parts_plan', {
            'item_code': _ensure_stock_item('Test Item B'),
            'uom': 'Nos',
            'qty_planned': 1,
            'is_billable': 1,
            'is_foc': 0,
        })
        ro.insert()
        ro.submit()

        # Project and Tasks created
        self.assertTrue(ro.project)
        tasks = frappe.get_all('Task', filters={'project': ro.project})
        self.assertGreaterEqual(len(tasks), 1)

        # Make Quotation
        q = frappe.get_doc(frappe.call('car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_quotation_from_repair_order', name=ro.name))
        self.assertEqual(q.quotation_to, 'Customer')
        self.assertGreater(len(q.items), 0)

        # Material Request
        mr = frappe.get_doc(frappe.call('car_repair_management.car_repair_management.doctype.repair_order.repair_order.make_material_request_from_repair_order', name=ro.name))
        self.assertGreater(len(mr.items), 0)


def _ensure_operation(operation_name: str) -> str:
    if not frappe.db.exists('Operation', operation_name):
        frappe.get_doc({
            'doctype': 'Operation',
            'name': operation_name,
            'operation': operation_name
        }).insert()
    return operation_name


def _ensure_stock_item(item_name: str) -> str:
    # Ensure UOM exists
    if not frappe.db.exists('UOM', 'Nos'):
        frappe.get_doc({'doctype': 'UOM', 'uom_name': 'Nos'}).insert()
    item_code = item_name
    if not frappe.db.exists('Item', item_code):
        frappe.get_doc({
            'doctype': 'Item',
            'item_code': item_code,
            'item_name': item_name,
            'stock_uom': 'Nos',
            'is_stock_item': 1,
            'item_group': 'All Item Groups'
        }).insert()
    return item_code
