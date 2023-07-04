from odoo import api, models, fields

class Marketer(models.Model):
    _name = "marketer"
    _description = "Marketers"
    _sql_constraints = [
        ("check_name", "UNIQUE(employee_id)", "Employee must be unique"),
    ]

    employee_id = fields.Many2one('hr.employee')
    # emp_no = fields.Char(related=employee_id.employee_number, string='Employee ID')
    emp_no = fields.Char(compute='_compute_emp_no', string='Employee ID')
    # name = fields.Char(related=employee_id.name, string='Marketer Name')
    name = fields.Char(compute='_compute_name', string='Marketer Name')
    code = fields.Char(required=True, string='Marketer Code')
    # emp_phone = fields.Char(related=employee_id.phone, string='Phone Number')
    emp_phone = fields.Char(compute='_compute_emp_phone', string='Phone Number')
    # emp_address = fields.Char(related=employee_id.address_home, string='Marketer Name')
    emp_address = fields.Char(compute='_compute_emp_address', string='Marketer Address')
    service_center_id = fields.Many2one('service.center')
    book_feeder_ids = fields.One2many('book.feeder', 'marketer_id')
    # same_employee_id = fields.Many2one('hr.employee', string='Marketers with the same Employee ID', compute='_compute_same_vat_partner_id', store=False)

    # def _compute_same_vat_partner_id(self):
    #     for marketer in self:
    #         # use _origin to deal with onchange()
    #         marketer_id = marketer._origin.id
    #         Marketer = self.with_context(active_test=False).sudo()
    #         domain = [
    #             ('employee_id', '=', marketer_id.employee_id),
    #         ]
    #         if marketer_id:
    #             domain += [('id', '!=', marketer_id)]
    #         marketer.same_employee_id = bool(marketer.employee_id) and Marketer.search(domain, limit=1)

    def _compute_name(self):
        for emp in self:
            emp.name = emp.employee_id.name if emp.employee_id else ''

    def _compute_emp_address(self):
        for emp in self:
            emp.emp_address = emp.employee_id.address_home if emp.employee_id else ''

    
    def _compute_emp_no(self):
        for emp in self:
            emp.emp_no = emp.employee_id.employee_number if emp.employee_id else ''

    def _compute_emp_phone(self):
        for emp in self:
            emp.emp_phone = emp.employee_id.work_phone if emp.employee_id else ''
