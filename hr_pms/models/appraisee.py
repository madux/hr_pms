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


class KRA_SectionLine(models.Model):
    _name = "kra.section.line"
    _description= "Employee appraisee KRA Section lines"

     
    kra_section_id = fields.Many2one(
        'pms.appraisee',
        string="LC Section"
    )

    name = fields.Char(
        string='Description', 
        
        )
    weightage = fields.Integer(
        string='Weight (Total 100%) by Appraisee', 
        
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    self_rating = fields.Integer(
        string='Self Rating', 
        )
        
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        )
    is_functional_manager = fields.Boolean(
        string="is functional manager", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_administrative_supervisor = fields.Boolean(
        string="is administrative supervisor", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_reviewer = fields.Boolean(
        string="is Reviewer", 
        default=False,
        compute="compute_user_rating_role"
        )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True, related="kra_section_id.state")
    
    weighted_score = fields.Float(
        string='Weighted (%) Score of specific KRA', 
        store=True,
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale',
        help="Takes in the default scale",
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )
    
    @api.onchange(
        'self_rating', 
        'functional_supervisor_rating', 
        'administrative_supervisor_rating')
    def onchange_rating(self):
        if self.state == 'functional_rating':
            if self.kra_section_id.employee_id.parent_id and self.env.user.id != self.kra_section_id.employee_id.parent_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's functional manager"
                )
        if self.state == 'admin_rating':
            if self.kra_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.kra_section_id.employee_id.administrative_supervisor_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's administrative supervisor"
                )
            
        if self.self_rating > 5:
            self.self_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Self rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
        if self.functional_supervisor_rating > 5:

            message = {
                    'title': 'Invalid Scale',
                    'message': 'Functional supervisor rating Scale should be in the range of 1 - 5'
                }
            self.self_rating = False
            return {'warning': message}
        
        if self.administrative_supervisor_rating > 5:
            self.self_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
    
    @api.depends('kra_section_id')
    def compute_user_rating_role(self):
        """
        Used to determine if the current user
        is a functional/department mmanager,
        administrative supervisor or reviewer
        """
        current_user = self.env.uid 
        if self.kra_section_id:
            self.is_functional_manager = True if current_user == self.kra_section_id.employee_id.parent_id.user_id.id else False
            self.is_administrative_supervisor = True if current_user == self.kra_section_id.employee_id.administrative_supervisor_id.user_id.id else False
            self.is_reviewer = True if current_user == self.kra_section_id.employee_id.reviewer_id.user_id.id else False
        else:
            self.is_functional_manager,self.is_administrative_supervisor,self.is_reviewer = False, False, False
    
    @api.depends(
        'weightage',
        'administrative_supervisor_rating',
        'functional_supervisor_rating')
    def compute_weighted_score(self):
        # =(((admin_rating*40 )+(functional_rating *60))/4) * (weightage /100)
        for rec in self:
            fc_avg_scale = rec.section_avg_scale or 4 # or 5 is set as default in case nothing was provided
            if rec.administrative_supervisor_rating or rec.functional_supervisor_rating:

                ar = rec.administrative_supervisor_rating * 40
                f_rating = 60 if rec.administrative_supervisor_rating > 0 else 100
                fr = rec.functional_supervisor_rating * f_rating
                ratings = (ar + fr) / fc_avg_scale
                rec.weighted_score = ratings * (rec.weightage / 100)
            else:
                rec.weighted_score = 0


class LC_SectionLine(models.Model):
    _name = "lc.section.line"
    _description= "Employee appraisee LC Section lines"

    lc_section_id = fields.Many2one(
        'pms.appraisee',
        string="LC Section"
    )

    name = fields.Char(
        string='Description',
        )
    weightage = fields.Integer(
        string='Weight (Total 100%)', 
        default=20,
        readonly=True
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    functional_supervisor_rating = fields.Integer(
        string='FA Rating',
        )
    reviewer_rating = fields.Integer(
        string='RA Rating',
        ) 
        
    is_functional_manager = fields.Boolean(
        string="is functional manager", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_administrative_supervisor = fields.Boolean(
        string="is administrative supervisor", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_reviewer = fields.Boolean(
        string="is Reviewer", 
        default=False,
        compute="compute_user_rating_role"
        )
    weighted_score = fields.Float(
        string='Weighted (%) Score of specific KRA', 
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        help="Takes in the default scale",
        store=True,
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True, related="lc_section_id.state")
    
    @api.onchange(
        'functional_supervisor_rating', 
        'administrative_supervisor_rating',
        'reviewer_rating'
        )
    def onchange_rating(self):
        if self.state == 'functional_rating':
            if self.lc_section_id.employee_id.parent_id and self.env.user.id != self.lc_section_id.employee_id.parent_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's functional manager"
                )
        if self.state == 'admin_rating':
            if self.lc_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.lc_section_id.employee_id.administrative_supervisor_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's administrative supervisor"
                )
        if self.state == 'reviewer_rating':
            if self.lc_section_id.employee_id.reviewer_id and self.env.user.id != self.lc_section_id.employee_id.reviewer_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's reviewer"
                )
            
        if self.functional_supervisor_rating > 5:
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Functional supervisor rating Scale should be in the range of 1 - 5'
                }
            self.functional_supervisor_rating = False
            return {'warning': message}
        if self.administrative_supervisor_rating > 5:
            self.administrative_supervisor_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
        if self.reviewer_rating > 5:
            self.reviewer_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
    
    
    @api.depends('lc_section_id')
    def compute_user_rating_role(self):
        """
        Used to determine if the current user
        is a functional/department mmanager,
        administrative supervisor or reviewer
        """
        current_user = self.env.uid 
        if self.lc_section_id:
            self.is_functional_manager = True if current_user == self.lc_section_id.employee_id.parent_id.user_id.id else False
            self.is_administrative_supervisor = True if current_user == self.lc_section_id.employee_id.administrative_supervisor_id.user_id.id else False
            self.is_reviewer = True if current_user == self.lc_section_id.employee_id.reviewer_id.user_id.id else False
        else:
            self.is_functional_manager,self.is_administrative_supervisor,self.is_reviewer = False, False, False
    
    @api.depends(
        'administrative_supervisor_rating',
        'functional_supervisor_rating',
        'reviewer_rating',
        'weightage')
    def compute_weighted_score(self):
        for rec in self:
            fc_avg_scale = rec.section_avg_scale or 5 # or 5 is set as default in case nothing was provided
            if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
                ar = rec.administrative_supervisor_rating * 30
                f_rating = 30 if rec.administrative_supervisor_rating > 0 else 60
                fr = rec.functional_supervisor_rating * f_rating
                rr = rec.reviewer_rating * 40
                ratings = (ar + fr + rr) / fc_avg_scale
                rec.weighted_score = ratings * (rec.weightage / 100)
            else:
                rec.weighted_score = 0


class FC_SectionLine(models.Model):
    _name = "fc.section.line"
    _description= "Employee appraisee FC Section lines"


    fc_section_id = fields.Many2one(
        'pms.appraisee',
        string="KRA Section"
    )

    name = fields.Char(
        string='Description', 
        )
    weightage = fields.Integer(
        string='Weight (Total 100%)', 
        required=False,
        readonly=True
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        )
    reviewer_rating = fields.Integer(
        string='RA Rating',
        )
    is_functional_manager = fields.Boolean(
        string="is functional manager", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_administrative_supervisor = fields.Boolean(
        string="is administrative supervisor", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_reviewer = fields.Boolean(
        string="is Reviewer", 
        default=False,
        compute="compute_user_rating_role"
        )
    
    weighted_score = fields.Float(
        string='Weighted (%) Score of specific KRA', 
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        help="Takes in the default scale",
        store=True,
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True, related="fc_section_id.state")
    
    @api.onchange(
        'functional_supervisor_rating', 
        'administrative_supervisor_rating',
        'reviewer_rating'
        )
    def onchange_rating(self):
        if self.state == 'functional_rating':
            if self.fc_section_id.employee_id.parent_id and self.env.user.id != self.fc_section_id.employee_id.parent_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's functional manager"
                )
        if self.state == 'admin_rating':
            if self.fc_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.fc_section_id.employee_id.administrative_supervisor_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's administrative supervisor"
                )
        if self.state == 'reviewer_rating':
            if self.fc_section_id.employee_id.reviewer_id and self.env.user.id != self.fc_section_id.employee_id.reviewer_id.user_id.id:
                raise ValidationError(
                "Ops ! You are not entitled to add a rating \
                    because you are not the employee's reviewer"
                )
        if self.functional_supervisor_rating > 5:
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Functional supervisor rating Scale should be in the range of 1 - 5'
                }
            self.functional_supervisor_rating = False
            return {'warning': message}
        if self.administrative_supervisor_rating > 5:
            self.administrative_supervisor_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
        if self.reviewer_rating > 5:
            self.reviewer_rating = False
            message = {
                    'title': 'Invalid Scale',
                    'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
                }
            return {'warning': message}
    
    @api.depends('fc_section_id')
    def compute_user_rating_role(self):
        """
        Used to determine if the current user
        is a functional/department mmanager,
        administrative supervisor or reviewer
        """
        current_user = self.env.uid 
        if self.fc_section_id:
            self.is_functional_manager = True if current_user == self.fc_section_id.employee_id.parent_id.user_id.id else False
            self.is_administrative_supervisor = True if current_user == self.fc_section_id.employee_id.administrative_supervisor_id.user_id.id else False
            self.is_reviewer = True if current_user == self.fc_section_id.employee_id.reviewer_id.user_id.id else False
        else:
            self.is_functional_manager,self.is_administrative_supervisor,self.is_reviewer = False, False, False
    
    @api.depends('administrative_supervisor_rating','functional_supervisor_rating','reviewer_rating')
    def compute_weighted_score(self):
        '''
        ar: adminitrative rating
        fr: functional manager rating
        rr: reviewers rating
        section_avg_scale: scale configured to be used to divide the ratings
        '''
        for rec in self:
            fc_avg_scale = rec.section_avg_scale or 5 # or 5 is set as default in case nothing was provided
            if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
                ar = rec.administrative_supervisor_rating * 30
                f_rating = 30 if rec.administrative_supervisor_rating > 0 else 60
                fr = rec.functional_supervisor_rating * f_rating
                rr = rec.reviewer_rating * 40
                ratings = (ar + fr + rr) / fc_avg_scale
                rec.weighted_score = ratings
            else:
                rec.weighted_score = 0


class PMS_Appraisee(models.Model):
    _name = "pms.appraisee"
    _description= "Employee appraisee"
    _inherit = "mail.thread"

    name = fields.Char(
        string="Description Name", 
        required=True
        )
    department_id = fields.Many2one(
        'hr.department', 
        string="Department ID"
        )
    pms_department_id = fields.Many2one(
        'pms.department', 
        string="PMS Department ID"
        )
    section_id = fields.Many2one(
        'pms.section', 
        string="Section ID",
        )
    
    dummy_kra_section_scale = fields.Integer(
        string="Dummy KRA Section scale",
        help="Used to get the actual kra section scale because it wasnt setup",
        compute="get_kra_section_scale"
        )
    
    @api.depends('pms_department_id')
    def get_kra_section_scale(self):
        if self.pms_department_id:
            kra_scale = self.pms_department_id.mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
            scale = kra_scale[0].section_avg_scale if kra_scale else 4
            self.dummy_kra_section_scale = scale 
        else:
            self.dummy_kra_section_scale = 4
            
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee"
        )
    
    reviewer_id = fields.Many2one(
        'hr.employee', 
        string="Reviewer"
        )
    
    administrative_supervisor_id = fields.Many2one(
        'hr.employee', 
        string="Administrative Supervisor"
        )
    
    manager_id = fields.Many2one(
        'hr.employee', 
        string="Functional Manager"
        )
    approver_ids = fields.Many2many(
        'hr.employee', 
        string="Approvers",
        readonly=True
        )
    appraisee_comment = fields.Text(
        string="Appraisee Comment", 
        )
    supervisor_comment = fields.Text(
        string="Supervisor Comment", 
        )
    manager_comment = fields.Text(
        string="Manager Comment", 
        )
    reviewer_comment = fields.Text(
        string="Appraisee Comment", 
        )
    appraisee_satisfaction = fields.Selection([
        ('none', ''),
        ('satisfied', 'Satisfied'),
        ('not_satisfied', 'Not Satisfied'),
        ('agreed', 'Agreed'),
        ('disagreed', 'Disagreed'),
        ('agreed', 'Agreed'),
        ('agreed', 'Agreed'),
        ], string="Satisfaction", default = "none")
    
    line_manager_id = fields.Many2one(
        'hr.employee', 
        string="Line Manager"
        )
    
    directed_user_id = fields.Many2one(
        'res.users', 
        string="Appraisal with ?", 
        readonly=True
        )
    
    kra_section_line_ids = fields.One2many(
        "kra.section.line",
        "kra_section_id",
        string="KRAs"
    )
    lc_section_line_ids = fields.One2many(
        "lc.section.line",
        "lc_section_id",
        string="Leadership Competence"
    )
    fc_section_line_ids = fields.One2many(
        "fc.section.line",
        "fc_section_id",
        string="Functional Competence"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True)
    
    pms_year_id = fields.Many2one(
        'pms.year', string="Period")
    date_from = fields.Date(
        string="Date From", 
        readonly=False, 
        store=True)
    date_end = fields.Date(
        string="Date End", 
        readonly=False,
        store=True
        )
    deadline = fields.Date(
        string="Deadline Date", 
        # compute="get_appraisal_deadline", 
        store=True)

    overall_score = fields.Float(
        string="Overall score", 
        compute="compute_overall_score", 
        store=True)

    final_kra_score = fields.Float(
        string='Final KRA Score', 
        store=True,
        compute="compute_final_kra_score"
        )
    
    final_fc_score = fields.Float(
        string='Final FC Score', 
        store=True,
        compute="compute_final_fc_score"
        )
    
    final_lc_score = fields.Float(
        string='Final LC Score', 
        store=True,
        compute="compute_final_lc_score"
        )
    
    # consider removing
    kra_section_weighted_score = fields.Float(
        string='KRA Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    fc_section_weighted_score = fields.Integer(
        string='Functional Competency Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    lc_section_weighted_score = fields.Integer(
        string='Leadership Competency Weight', 
        readonly=True,
        store=True,
        )
    # consider removing
    kra_section_avg_scale = fields.Integer(
        string='KRA Scale', 
        readonly=True,
        store=True,
        )
     
    # consider removing
    fc_section_avg_scale = fields.Integer(
        string='Functional Competency Scale', 
        store=True,
        )
      
    @api.depends('kra_section_line_ids')
    def compute_final_kra_score(self):
        for rec in self:
            if rec.kra_section_line_ids:
                kra_total = sum([
                    weight.weighted_score for weight in rec.mapped('kra_section_line_ids')
                    ])
                rec.final_kra_score = kra_total
            else:
                rec.final_kra_score = 0

    @api.depends('fc_section_line_ids')
    def compute_final_fc_score(self):
        for rec in self:
            if rec.fc_section_line_ids:
                fc_total = sum([
                    weight.weighted_score for weight in rec.mapped('fc_section_line_ids')
                    ])
                rec.final_fc_score = fc_total
            else:
                rec.final_fc_score = 0

    @api.depends('lc_section_line_ids')
    def compute_final_lc_score(self):
        for rec in self:
            if rec.lc_section_line_ids:
                fc_total = sum([
                    weight.weighted_score for weight in rec.mapped('lc_section_line_ids')
                    ])
                rec.final_lc_score = fc_total 
            else:
                rec.final_lc_score = 0

    @api.depends(
            'final_kra_score',
            'final_lc_score',
            'final_fc_score'
            ) 
    def compute_overall_score(self):
        for rec in self:
            if rec.final_kra_score and rec.final_lc_score and rec.final_fc_score:
                kra_section_weighted_score = rec.pms_department_id.hr_category_id.kra_weighted_score 
                fc_section_weighted_score = rec.pms_department_id.hr_category_id.fc_weighted_score
                lc_section_weighted_score = rec.pms_department_id.hr_category_id.lc_weighted_score 

                # rec.section_id.weighted_score
                # e.g 35 % * kra_final + 60% * lc_final * 15% + fc_final * 45%
                # e.g 35 % * kra_final + 0.60% * lc_final * 0.15% + fc_final * 0.45

                rec.overall_score = (kra_section_weighted_score / 100) * rec.final_kra_score + \
                (fc_section_weighted_score/ 100) * rec.final_fc_score + \
                (lc_section_weighted_score/ 100) * rec.final_lc_score
            else:
                rec.overall_score = 0
        
    def check_kra_section_lines(self):
        # if the employee has administrative reviewer, 
        # system should validate to see if they have rated
        if self.state == "admin_rating":
            if self.mapped('kra_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor rating is above 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('kra_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager rating is above 1"
                ) 
            
    def check_fc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor rating is above 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager rating is above 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager rating is above 1"
                ) 
            
    def check_lc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating is above 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating is above 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating is above 1"
                ) 
    
    def _get_group_users(self):
        group_obj = self.env['res.groups']
        hr_administrator = self.env.ref('hr.group_hr_manager').id
        pms_manager = self.env.ref('hr_pms.group_pms_manager_id').id
        pms_officer = self.env.ref('hr_pms.group_pms_officer_id').id
        hr_administrator_user = group_obj.browse([hr_administrator])
        pms_manager_user = group_obj.browse([pms_manager])
        pms_officer_user = group_obj.browse([pms_officer])

        hr_admin = hr_administrator_user.mapped('users') if hr_administrator_user else False
        pms_mgr = pms_manager_user.mapped('users') if pms_manager_user else False
        pms_off = pms_officer_user.mapped('users') if pms_officer_user else False
        return hr_admin, pms_mgr, pms_off
    
    def submit_mail_notification(self): 
        subject = "Appraisal Notification"
        department_manager = self.employee_id.parent_id or self.employee_id.parent_id
        supervisor = self.employee_id.administrative_supervisor_id
        reviewer_id = self.employee_id.reviewer_id
        hr_admin, pms_mgr, pms_off = self._get_group_users()
        hr_emails = [rec.login for rec in hr_admin]
        pms_mgr_emails = [rec.login for rec in pms_mgr]
        pms_off_emails = [rec.login for rec in hr_admin]
        hr_logins = hr_emails + pms_mgr_emails + pms_off_emails
        if not hr_logins:
            raise ValidationError('Please ensure there is a user with HR addmin settings')
        if self.state in ['draft']:
            if department_manager and department_manager.work_email:
                msg = """Dear {}, <br/>
                I wish to notify you that my appraisal has been submitted to you for rating(s) \
                <br/>Kindly {} to proceed with the ratings <br/>\
                Yours Faithfully<br/>{}<br/>Department: ({})""".format(
                    department_manager.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    self.employee_id.department_id.name,
                    )
                email_to = department_manager.work_email
                email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
            else:
                raise ValidationError(
                    'Please ensure that employee / department \
                    manager has an email address')
        elif self.state in ['rating']:
            msg = """HR, <br/>
                I wish to notify you that an appraisal for {} \
                has been submitted for HR processing\
                <br/>Kindly {} to review the appraisal<br/>\
                Yours Faithfully<br/>{}<br/>""".format(
                    self.employee_id.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    )
            email_to = ','.join(hr_logins)
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
        elif self.state in ['wating_approval']:
            msg = """HR, <br/>
                I wish to notify you that an appraisal for {} has been completed.\
                <br/>Kindly {} to review the appraisal. <br/> \
                For further Inquiry, contact HR Department<br/>\
                Yours Faithfully<br/>{}<br/>""".format(
                    self.employee_id.name,
                    self.get_url(self.id, self._name),
                    self.env.user.name,
                    )
            email_to = self.employee_id.work_email
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                    department_manager.work_email
                ]
        else:
            msg = "-"
            email_to = department_manager.work_email
            email_cc = [
                    supervisor.work_email, 
                    reviewer_id.work_email,
                ]
        self.action_notify(
            subject, 
            msg, 
            email_to, 
            email_cc)
        
    def action_notify(self, subject, msg, email_to, email_cc):
        email_from = self.env.user.email
        email_ccs = list(filter(bool, email_cc))
        reciepients = (','.join(items for items in email_ccs)) if email_ccs else False
        mail_data = {
                'email_from': email_from,
                'subject': subject,
                'email_to': email_to,
                'reply_to': email_from,
                'email_cc': reciepients,
                'body_html': msg,
                'state': 'sent'
            }
        mail_id = self.env['mail.mail'].sudo().create(mail_data)
        self.env['mail.mail'].sudo().send(mail_id)
        self.message_post(body=msg)
    
    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>. ".format(base_url)

    def send_mail_notification(self, msg):
        subject = "Appraisal Notification"
        administrative_supervisor = self.employee_id.administrative_supervisor_id
        reviewer_id = self.employee_id.reviewer_id
        # doing this to avoid making calls that will impact optimization
        department_manager = self.employee_id.parent_id
        if self.state == "draft":
            email_to = administrative_supervisor.work_email if self.administrative_supervisor_id.work_email else department_manager.work_email
            email_cc = [
            department_manager.work_email,
            reviewer_id.work_email, 
            administrative_supervisor.work_email,
        ]
        elif self.state == "admin_rating":
            email_to = department_manager.work_email
            email_cc = [
                department_manager.work_email,
                self.employee_id.work_email
                ]
        elif self.state == "functional_rating":
            email_to = reviewer_id.work_email
            email_cc = [
                department_manager.work_email,
                self.employee_id.work_email,
                administrative_supervisor.work_email,
                ]
        elif self.state == "reviewer_rating":
            email_to = self.employee_id.work_email,
            email_cc = [
                department_manager.work_email,
                administrative_supervisor.work_email,
                ]
        else:
            email_to = department_manager.work_email,
            email_cc = [
                department_manager.work_email,
                administrative_supervisor.work_email,
                ]
        self.action_notify(subject, msg, email_to, email_cc)

    def button_submit(self):
        # send notification
        admin_or_functional_user = self.administrative_supervisor_id.name or self.manager_id.name
        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            admin_or_functional_user,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.department_id.name,
            )
        self.send_mail_notification(msg)
        
        if self.employee_id.administrative_supervisor_id:
            self.write({
                'state': 'admin_rating',
                'administrative_supervisor_id': self.employee_id.administrative_supervisor_id.id,
            })
        else:
            self.write({
                'state': 'functional_rating',
                'manager_id': self.employee_id.parent_id.id,
            })
            
    def button_admin_supervisor_rating(self): 
        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for functional manager's ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.parent_id.name,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.administrative_supervisor_id.department_id.name,
            )
        if not self.employee_id.parent_id:
            raise ValidationError(
                'Ops ! please ensure that a manager is assigned to the employee'
                )
        if self.employee_id.administrative_supervisor_id and self.env.user.id != self.administrative_supervisor_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's administrative supervisor"
                )
        self.check_kra_section_lines()
        self.check_fc_section_lines()
        self.check_lc_section_lines()
        self.send_mail_notification(msg)
        self.write({
                'state': 'functional_rating',
                'manager_id': self.employee_id.parent_id.id,
            })
        
    def button_functional_manager_rating(self):
        if not self.employee_id.reviewer_id:
            raise ValidationError(
                "Ops ! please ensure that a reviewer is assigned to the employee"
                )
        if self.employee_id.parent_id and self.env.user.id != self.employee_id.parent_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's functional manager"
                )
        self.check_kra_section_lines()
        self.check_fc_section_lines()
        self.check_lc_section_lines()

        msg = """Dear {}, <br/> 
        I wish to notify you that an appraisal for {} \
        has been submitted for reviewer's ratings.\
        <br/>Kindly {} to review <br/>\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.parent_id.name,
            self.employee_id.name,
            self.get_url(self.department_id.id, self._name),
            self.env.user.name,
            self.manager_id.department_id.name,
            )
        self.send_mail_notification(msg)
        self.write({
                'state': 'reviewer_rating',
                'reviewer_id': self.employee_id.reviewer_id.id,
            })
    
    def button_reviewer_manager_rating(self):
        if self.employee_id.reviewer_id and self.env.user.id != self.employee_id.reviewer_id.user_id.id:
            raise ValidationError(
                "Ops ! You are not entitled to submit this rating because you are not the employee's reviewing manager"
                )
        self.check_fc_section_lines()
        self.check_lc_section_lines()
        msg = """Dear {}, <br/> 
        I wish to notify you that your appraisal has been reviewed successfully.\
        Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
            self.employee_id.name,
            self.env.user.name,
            self.reviewer_id.department_id.name,
            )
        self.send_mail_notification(msg)
        self.write({
                'state': 'done',
            })
        
    def button_withdraw(self):
        self.write({
                'state':'withdraw',
            })
        
    def button_set_to_draft(self):
        self.write({
                'state':'draft',
            })