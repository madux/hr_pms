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



class PMS_Appraisee(models.Model):
    _name = "pms.appraisee"
    _description= "Employee appraisee"
    _inherit = "mail.thread"

    name = fields.Char(
        string="Description Name", 
        required=True
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
            
    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee"
        )
    employee_number = fields.Char( 
        string="Staff ID",
        related="employee_id.employee_number"
        )
    job_title = fields.Char( 
        string="Job title",
        related="employee_id.job_title"
        )
    work_unit_id = fields.Many2one(
        'hr.work.unit',
        string="Job title",
        related="employee_id.work_unit_id"
        )
    job_id = fields.Many2one(
        'hr.job',
        string="Function", 
        related="employee_id.job_id"
        )
    ps_district_id = fields.Many2one(
        'hr.district',
        string="District", 
        related="employee_id.ps_district_id"
        )
    department_id = fields.Many2one(
        'hr.department', 
        string="Department ID"
        )
    reviewer_id = fields.Many2one(
        'hr.employee', 
        string="Reviewer",
        related="employee_id.reviewer_id"
        )
    administrative_supervisor_id = fields.Many2one(
        'hr.employee', 
        string="Administrative Supervisor",
        related="employee_id.administrative_supervisor_id"
        )
    manager_id = fields.Many2one(
        'hr.employee', 
        string="Functional Manager",
        related="employee_id.parent_id"
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
        ('fully_agreed', 'Fully Agreed'),
        ('largely_agreed', 'Largely Agreed'),
        ('partially_agreed', 'Partially Agreed'),
        ('largely_disagreed', 'Largely Disagreed'),
        ('totally_disagreed', 'Totally Disagreed'),
        ], string="Perception on PMS", default = "none")
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
    training_section_line_ids = fields.One2many(
        "training.section.line",
        "training_section_id",
        string="Training section"
    )
    current_assessment_section_line_ids = fields.One2many(
        "current.assessment.section.line",
        "current_assessment_section_id",
        string="Assessment section",
        # default=lambda self: self._get_current_assessment_lines()
    )

    potential_assessment_section_line_ids = fields.One2many(
        'potential.assessment.section.line',
        'potential_section_id',
        string="potential assessment Appraisal"
    )
    qualitycheck_section_line_ids = fields.One2many(
        "qualitycheck.section.line",
        "qualitycheck_section_id",
        string="Quality check section"
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
    def _get_default_instructions(self):
        ins = self.env.ref('hr_pms.pms_instruction_1').description
        return ins
    
    instruction_html = fields.Text(
        string='Instructions', 
        store=True,
        default=lambda self: self._get_default_instructions(),
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
    
    reviewer_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Reviewer Unit", 
        related="employee_id.reviewer_id.work_unit_id"
        )
    
    # @api.depends()
    # def compute_reviewer_details(self):
    #     reviewer_work_unit=self.employee_id.reviewer_id.hr_work_unit.name
    #     self.reviewer_work_unit = reviewer_work_unit

    #     reviewer_job_id =self.employee_id.reviewer_id.job_id.name
    #     self.reviewer_work_unit = reviewer_job_id

    #     reviewer_job_id =self.employee_id.reviewer_id.job_id.name
    #     self.reviewer_work_unit = reviewer_job_id

    reviewer_job_title = fields.Char(
        string="Reviewer Designation", 
        related="employee_id.reviewer_id.job_title"
        )
    reviewer_job_id = fields.Many2one(
        'hr.job',
        string="Reviewer Function",
        related="employee_id.reviewer_id.job_id" 
        )
    reviewer_district = fields.Many2one(
        'hr.district',
        string="Reviewer District", 
        related="employee_id.reviewer_id.ps_district_id"
        )
    reviewer_department = fields.Many2one(
        'hr.department',
        string="Reviewer department", 
        related="employee_id.reviewer_id.department_id"
        )
    reviewer_employee_number = fields.Char(
        string="Reviewer Employee Number", 
        related="employee_id.reviewer_id.employee_number"
        )
    
    manager_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Manager Unit", 
        related="employee_id.parent_id.work_unit_id"
        )
    manager_job_title = fields.Char(
        string="Manager Designation", 
        related="employee_id.parent_id.job_title"
        )
    manager_job_id = fields.Many2one(
        'hr.job',
        string="Manager Function", 
        related="employee_id.parent_id.job_id"
        )
    manager_district = fields.Many2one(
        'hr.district',
        string="Manager District", 
        related="employee_id.parent_id.ps_district_id"
        )
    
    manager_department = fields.Many2one(
        'hr.department',
        string="Manager department", 
        related="employee_id.parent_id.department_id"
        )
    manager_employee_number = fields.Char(
        string="Manager Employee Number", 
        related="employee_id.parent_id.employee_number"
        )
    supervisor_work_unit = fields.Many2one(
        'hr.work.unit',
        string="Supervisor Unit", 
        related="employee_id.administrative_supervisor_id.work_unit_id"
        )
    supervisor_job_title = fields.Char(
        string="Supervisor Designation", 
        related="employee_id.administrative_supervisor_id.job_title"
        )
    supervisor_job_id = fields.Many2one(
        'hr.job',
        string="Supervisor Function", 
        related="employee_id.administrative_supervisor_id.job_id"
        )
    supervisor_department = fields.Many2one(
        'hr.department',
        string="Supervisor Dept", 
        related="employee_id.administrative_supervisor_id.department_id"
        )
    supervisor_district = fields.Many2one(
        'hr.district',
        string="Supervisor District", 
        related="employee_id.administrative_supervisor_id.ps_district_id"
        )
    supervisor_employee_number = fields.Char(
        string="Supervisor Employee Number", 
        related="employee_id.administrative_supervisor_id.employee_number"
        )
    
    @api.depends('pms_department_id')
    def get_kra_section_scale(self):
        if self.pms_department_id:
            kra_scale = self.pms_department_id.sudo().mapped('section_line_ids').filtered(
                    lambda res: res.type_of_section == "KRA")
            scale = kra_scale[0].section_avg_scale if kra_scale else 4
            self.dummy_kra_section_scale = scale 
        else:
            self.dummy_kra_section_scale = 4
      
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
                    "Ops! Please ensure all administrative supervisor's rating on KRA section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('kra_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating on KRA section is at least 1"
                ) 
            
    def check_fc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating on functional competency section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating on functional competency line is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('fc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager rating's on functional competency line is at least rated 1"
                ) 
            
    def check_lc_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at leadership competency is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating at leadership competency is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('lc_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating at leadership competency is at least 1"
                ) 
    
    def check_current_assessment_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at current assessment section is at least 1"
                )
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating at current assessment section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating at current assessment section is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('current_assessment_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating at current assessment section is at least 1"
                ) 
            
    def check_potential_assessment_section_lines(self):
        if self.state == "admin_rating":
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating on potential assessment section is at least 1"
                )
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.administrative_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all administrative supervisor's rating on potential assessment section is at least 1"
                )
        elif self.state == "functional_rating":
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.functional_supervisor_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all functional manager's rating on potential assessment section is at least 1"
                )

        elif self.state == "reviewer_rating":
            if self.mapped('potential_assessment_section_line_ids').filtered(
                lambda line: line.reviewer_rating < 1):
                raise ValidationError(
                    "Ops! Please ensure all reviewer's rating on potential assessment section is at least 1"
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

    def validate_weightage(self):
        sum_weightage = sum([weight.weightage for weight in self.mapped('kra_section_line_ids')])
        if sum_weightage != 100:
            raise ValidationError('Please ensure the sum of KRA weight by Appraisee is equal to 100 %')
        
    def button_submit(self):
        # send notification
        self.validate_weightage()
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
        self.check_current_assessment_section_lines()
        self.check_potential_assessment_section_lines()
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
        self.check_current_assessment_section_lines()
        self.check_potential_assessment_section_lines()
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
        self.check_current_assessment_section_lines()
        self.check_potential_assessment_section_lines()
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