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
        required=True
        )
    weightage = fields.Integer(
        string='Weight (Total 100%) by Appraisee', 
        required=True
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    self_rating = fields.Integer(
        string='Self Rating', 
        )
    
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        required=True
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
    
    weighted_score = fields.Integer(
        string='Weighted (%) Score of specific KRA', 
        required=True,
        store=True,
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        required=True,
        help="Takes in the default scale",
        store=True,
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )

    @api.depends(
        'administrative_supervisor_rating',
        'functional_supervisor_rating')
    def compute_weighted_score(self):
        # =((admin_rating*0.4 )+(functional_rating *0.6))/4 * weightage
        for rec in self:
            fc_avg_scale = rec.section_avg_scale or 4 # or 5 is set as default in case nothing was provided
            if rec.administrative_supervisor_rating or rec.functional_supervisor_rating:

                ar = rec.administrative_supervisor_rating * 40
                f_rating = 60 if rec.administrative_supervisor_rating > 0 else 100
                fr = rec.functional_supervisor_rating * 60
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
        required=True
        )
    weightage = fields.Integer(
        string='Weight (Total 100%)', 
        required=True,
        default=20,
        readonly=True
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        required=True
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
    weighted_score = fields.Integer(
        string='Weighted (%) Score of specific KRA', 
        required=True,
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        required=True,
        help="Takes in the default scale",
        store=True,
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )
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
        'reviewer_rating')
    def compute_weighted_score(self):
        for rec in self:
            fc_avg_scale = rec.section_avg_scale or 5 # or 5 is set as default in case nothing was provided
            converted_fc_avg_scale = fc_avg_scale / 100 # i.e 35 / 100 = 0.3
            if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
                ar = rec.administrative_supervisor_rating * 0.3
                f_rating = 0.3 if rec.administrative_supervisor_rating > 0 else 0.6
                fr = rec.functional_supervisor_rating * f_rating
                rr = rec.reviewer_rating * 0.4
                ratings = (ar + fr + rr) / converted_fc_avg_scale
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
        required=True
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
        required=True
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
    
    weighted_score = fields.Integer(
        string='Weighted (%) Score of specific KRA', 
        compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        required=True,
        help="Takes in the default scale",
        store=True,
        )
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )
    
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
            converted_fc_avg_scale = fc_avg_scale / 100 # i.e 35 / 100 = 0.3
            if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
                ar = rec.administrative_supervisor_rating * 0.3
                f_rating = 0.3 if rec.administrative_supervisor_rating > 0 else 0.6
                fr = rec.functional_supervisor_rating * f_rating
                rr = rec.reviewer_rating * 0.4
                ratings = (ar + fr + rr) / converted_fc_avg_scale
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
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee"
        )
    approver_ids = fields.Many2many(
        'hr.employee', 
        string="Approvers",
        readonly=True
        )
    
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
        ('rating', 'Admin Supervisor/Functional Supervisor/Reviewer'),
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
                lc_section_weighted_score = rec.rec.pms_department_id.hr_category_id.lc_weighted_score 

                # rec.section_id.weighted_score
                # e.g 35 % * kra_final + 60% * lc_final + 15% * fc_final
                rec.overall_score = kra_section_weighted_score * rec.final_kra_score + \
                fc_section_weighted_score * rec.final_fc_score + \
                lc_section_weighted_score * rec.final_lc_score
            else:
                rec.overall_score = 0
        
    def check_kra_section_lines(self):
        # if the employee has administrative reviewer, 
        # system should validate to see if they have rated
        if self.employee_id.administrative_supervisor_id:
            aa_kra_line_not_rated = self.mapped('kra_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_id < 1)
            if aa_kra_line_not_rated:
                raise ValidationError("Please ensure all the administrative supervisors has rated above 0")
        # checks if employee is attached to any manager N/B manager is the functional suprv.
        if not (self.employee_id.department_id.parent_id or self.employee_id.parent_id):
            fc_kra_line_not_rated = self.mapped('kra_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1)
            if fc_kra_line_not_rated:
                raise ValidationError("Please ensure all the functional supervisors has rated above 0")
            
    def check_fc_lc_section_lines(self):
        # if the employee has administrative reviewer, 
        # system should validate to see if they have rated
        if self.employee_id.administrative_supervisor_id:
            aa_fc_line_not_rated = self.mapped('fc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_id < 1)
            if aa_fc_line_not_rated:
                raise ValidationError("Please ensure all the functional lines are rated above 0")
        # checks if employee is attached to any manager N/B manager is the functional suprv.
        if not (self.employee_id.department_id.parent_id or self.employee_id.parent_id):
            fc_kra_line_not_rated = self.mapped('fc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1)
            if fc_kra_line_not_rated:
                raise ValidationError(
                    "Please ensure all the functional lines are rated above 0"
                    )
        
        if self.employee_id.reviewer_id:
            aa_fc_line_not_rated = self.mapped('fc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1)
            if aa_fc_line_not_rated:
                raise ValidationError(
                    "Please ensure all the reviwer lines are rated above 0"
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
        department_manager = self.department_id.parent_id or self.employee_id.parent_id
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
            email_to = ','.join([hr_logins])
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
        self.env['pms.category'].action_notify(
            subject, 
            msg, 
            email_to, 
            email_cc)

    def button_submit(self):
        # send notification
        self.write({
                'state' 'rating'
            })
            
    def button_submit_rating(self): #'rating'
        self.check_kra_section_lines()
        self.check_fc_lc_section_lines()
        self.submit_mail_notification()
        self.write({
                'state' 'wating_approval'
            })
    
    def button_done(self):
        self.write({
                'state' 'done'
            })
        
    def button_withdraw(self):
        self.write({
                'state' 'withdraw'
            })
        
    def button_set_to_draft(self):
        self.write({
                'state' 'draft'
            })