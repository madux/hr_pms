from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class CategoryRole(models.Model):
    _name = "category.role"
    _description = "Roles"

    name = fields.Char(
        string="Name"
        )

class HrCompetencyRole(models.Model):
    _name = "hr.competency.role"
    _description = "Place to link employees to the category role"

    category_role_id = fields.Many2one(
        "category.role"
        )
    
    competency_reviewer_id = fields.Many2one(
        "hr.competency.reviewer"
        )
    employee_ids = fields.Many2many(
        'hr.employee', 
        'hr_competency_role_rel',
        'hr_competency_role_id',
        'hr_competency_role_employee_id',
        string="Employees", 
        )
    
class CompetencyReview(models.Model):
    _name = "hr.competency.reviewer"
    _description = "Competency Reviewers"
    _rec_name = "employee_id"

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
        required=False,
        store=True
        )
    
    category_role_ids = fields.One2many(
        'hr.competency.role', 
        'competency_reviewer_id',
        string="Category Role", 
        )
    
    employee_ids = fields.Many2many(
        'hr.employee', 
        'hr_competency_reviewer_rel',
        'hr_competency_reviewer_id',
        'hr_competency_reviewer_employee_id',
        string="Employee", 
        )
    active = fields.Boolean(
        string="Active", 
        default=True
        )
    
    def get_employee_superior(self, employee_id):
        list_ids = [employee_id.administrative_supervisor_id.id,
            employee_id.parent_id.id,
            employee_id.administrative_supervisor_id.administrative_supervisor_id.id,
            employee_id.administrative_supervisor_id.parent_id.id,
            employee_id.parent_id.administrative_supervisor_id.id,
            employee_id.parent_id.parent_id.id,
        ]
        return list_ids
    
    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            list_ids = self.get_employee_superior(self.employee_id)
            self.employee_ids = [(6, 0, list_ids)]

