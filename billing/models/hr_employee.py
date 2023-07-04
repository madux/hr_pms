from odoo import api, models, fields

class HrEmployee(models.Model):
    _inherit = "hr.employee" 


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base" 

    address_home = fields.Char(string='Home Address')
    employee_number = fields.Char(string="Staff Number")