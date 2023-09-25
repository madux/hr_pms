from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class EmployeeAgregation(models.Model):
    _name = "employee.aggregation"
    _description = "Employee aggregation"
    _rec_name = "name"

    name = fields.Char(
        string="Name", 
        readonly=True
        )
    
    staff_id = fields.Char(
        string="Staff", 
        related="employee_id.employee_number"
        )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee", 
        required=True
        )
    
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        )
    total = fields.Char(
        string="Total", 
        readonly=True,
        help="Total of all raters scores",
        compute="employee_hr_competency"
        )
    date_of_submission = fields.Datetime(
        string="Date of submission",
        )
     
    hr_competency_ids = fields.Many2many(
    'hr.competency',
    'hr_competency_aggregation_rel',
    'employee_competency_id',
    'hr_competency_aggregation_id',
    string="Competencies")

    period_id = fields.Many2one(
    'pms.year',
    string="Period")

    hr_competency_config_id = fields.Many2one(
    'hr.competency.config',
    string="Competency config")

    @api.depends('hr_competency_ids')
    def employee_hr_competency(self):
        '''Gets all the Employee competencies average scores'''
        for tec in self:
            competency_line_average_score = 0
            for rec in tec.hr_competency_ids:
                # competency_line_average_score = sum([r.average_total for r in rec.competency_ids])
                competency_line_average_score = sum(rec.competency_ids.mapped('average_total'))
            tec.total = competency_line_average_score / len(tec.hr_competency_ids.ids)
