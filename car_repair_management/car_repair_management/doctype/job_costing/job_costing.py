from frappe.model.document import Document

class JobCosting(Document):
    def validate(self):
        self.total_job_cost = (self.parts_cost or 0) + (self.labor_cost or 0) + (self.other_charges or 0)
