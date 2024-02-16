from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base" 

     
    rating_role = fields.Selection([
        ('senior', 'Senior'),
        ('peers', 'Peers'),
        ('junior', 'Junior'),
        ], 
        string="Role", 
    )