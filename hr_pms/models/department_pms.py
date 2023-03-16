from datetime import datetime, timedelta
import time
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import http
import logging
from lxml import etree

_logger = logging.getLogger(__name__)


class PMS_Department_SectionLine(models.Model):
    _name = "pms.department.section.line"
    _inherit = "pms.section.line"
    _description= "Department Section lines"

    pms_department_section_id = fields.Many2one(
        'pms.department.section', 
        string="PMS Department section ID"
        )

class PMS_Department_Section(models.Model):
    _name = "pms.department.section"
    _inherit = "pms.section"
    _description= "Department Sections"

    name = fields.Char(
        string="Description", 
        required=True)
    pms_department_id = fields.Many2one(
        'pms.department', 
        string="PMS Department ID"
        )
    section_line_ids = fields.One2many(
        "pms.department.section.line",
        "pms_department_section_id",
        string="epartment Section Lines"
    )
    section_id = fields.Many2one(
        'pms.section', 
        string="Section ID"
        )


class PMSDepartment(models.Model):
    _name = "pms.department"
    _description= "Department PMS to hold templates sent by HR  team for Appraisal conduct."
    _inherit = ['mail.thread']

    department_id = fields.Many2one(
        'hr.department', 
        string="Department ID"
        )
    
    hr_category_id = fields.Many2one(
        'pms.category', 
        string="Job category ID",
        required=True
        )
    sequence = fields.Char(
        string="Sequence")
    
    name = fields.Char(
        string="Description"
        )
    
    department_manager_id = fields.Many2one(
        'hr.employee', 
        string="Manager"
        )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('published', 'Published'),
        ('cancel', 'Cancel'),
        ], string="Status", default = "draft", readonly=True)
    pms_year_id = fields.Many2one(
        'pms.year', 
        string="Period"
        )
    date_from = fields.Date(
        string="Date From", 
        readonly=True, 
        store=True)
    date_end = fields.Date(
        string="Date End", 
        readonly=True,
        store=True
        )
    deadline = fields.Date(
        string="Deadline Date", 
        readonly=True,
        store=True)

    is_department_head = fields.Boolean(
        'Is department Head',
        help="Determines if the user is a department head",
        store=True,
        # compute="check_department_head"
        )
    section_line_ids = fields.One2many(
        "pms.department.section",
        "pms_department_id",
        string="Department Section Lines"
    )
    active = fields.Boolean(
        string="Active", 
        readonly=True, 
        default=True, 
        store=True)
    
    @api.onchange('department_id')
    def onchange_department_id(self):
        if self.department_id:
            self.department_manager_id = self.department_id.parent_id.id
    
    # TODO If is_department_head is set to true, display the buttons to them
    # @api.depends('department_id')
    # def check_department_head(self):
    #     """Checks if the current user is the departmental Manager"""
    #     for rec in self:
    #         if rec.department_id.parent_id.user_id.id == self.env.user.id:
    #             rec.is_department_head = True 
    #         else:
    #             rec.is_department_head = False 

    # TODO Add publish button with security as PMS Officer,
    # Ensure all the appraisals sent to employees will be activated or published
    def button_publish(self):
        '''Publishing the records to employees of the department'''
        Employee = self.env['hr.employee']
        PMS_Appraisee = self.env['pms.appraisee']
        employees = Employee.search([('department_id', '=', self.department_id.id)])
        if employees:
            for emp in employees:
                pms_appraisee = PMS_Appraisee.create({
                    'name': self.name, 
                    'department_id': self.department_id.id, 
                    'employee_id': emp.id, 
                    'pms_department_id': self.id,
                }) 
                kra_pms_department_section = self.mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
                if kra_pms_department_section:
                    kra_section = kra_pms_department_section[0]
                    kra_section_lines = kra_section.section_line_ids
                    pms_appraisee.write({
                        'kra_section_line_ids': [(0, 0, {
                                                    'kra_section_id': pms_appraisee.id,
                                                    'name': secline.name,
                                                    'is_required': secline.is_required,
                                                    'section_avg_scale': kra_section.section_id.section_avg_scale,
                                                    'weightage': 0,
                                                    'administrative_supervisor_rating': 0,
                                                    'functional_supervisor_rating': 0,
                                                    'self_rating': 0,
                                                    }) for secline in kra_section_lines] 
                    })
                fc_pms_department_section = self.mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "FC")
                if fc_pms_department_section:
                    fc_section = fc_pms_department_section[0]
                    fc_section_lines = fc_section.section_line_ids
                    if fc_section_lines:
                        pms_appraisee.write({
                            'fc_section_line_ids': [(0, 0, {
                                                        'fc_section_id': pms_appraisee.id,
                                                        'name': sec.name,
                                                        'is_required': sec.is_required,
                                                        'section_avg_scale': fc_section.section_id.section_avg_scale,
                                                        'administrative_supervisor_rating': 0,
                                                        'functional_supervisor_rating': 0,
                                                        'reviewer_rating': 0,
                                                        }) for sec in fc_section_lines] 
                        })
                    else:
                        pms_appraisee.write({
                            'fc_section_line_ids': [(0, 0, {
                                                        'fc_section_id': pms_appraisee.id,
                                                        'name': 'Functional Competency',
                                                        'is_required': False,
                                                        'section_avg_scale': fc_section.section_id.section_avg_scale,
                                                        'administrative_supervisor_rating': 0,
                                                        'functional_supervisor_rating': 0,
                                                        'reviewer_rating': 0,
                                                        })] 
                        })


                lc_pms_department_section = self.mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "LC")
                if lc_pms_department_section:
                    lc_section = lc_pms_department_section[0]
                    lc_section_lines = lc_section.section_line_ids
                    pms_appraisee.write({
                        'lc_section_line_ids': [(0, 0, {
                                                    'lc_section_id': pms_appraisee.id,
                                                    'name': secline.name,
                                                    'is_required': secline.is_required,
                                                    'section_avg_scale': lc_section.section_id.section_avg_scale,
                                                    'weightage': lc_section.section_id.input_weightage,
                                                    'administrative_supervisor_rating': 0,
                                                    'functional_supervisor_rating': 0,
                                                    # 'self_rating': 0,
                                                    }) for secline in lc_section_lines] 
                    })
        self.write({
            'state':'published'
        })
    
    # TODO Add cancel button as with security Departmental heads sees this button,
    # Ensure all the appraisals sent to employees will be deactivated or cancelled
    def button_cancel(self):
        for rec in self:
            rec.write({
                'state' 'cancel'
            })

    def button_set_to_draft(self):
        self.write({
                'state' 'draft'
            })
