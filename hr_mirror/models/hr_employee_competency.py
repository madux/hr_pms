from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class EmployeeCompetency(models.Model):
    _name = "hr.employee.competency"
    _description = "HR Employee competency"
    _rec_name = "name"

    """this is to help employees recieve their appraisal for self rating: once submited 
    it will generate duplicate records for the reviewers"""

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
        string="Ratee", 
        required=True
        )
    rater_ids = fields.Many2many(
        'hr.competency.role',
        'raters_employee_competency_role_rel',
        'rater_employee_competency_role_id',
        'competency_employee_role_id',
        string="Rater IDs",
        required=True
        )
    
    rater_review_ids = fields.One2many(
        'hr.competency',
        'hr_competency_id',
        string="Competency",
        )
    
    department_id = fields.Many2one(
        'hr.department',
        string="Department"
        )
    date_of_submission = fields.Datetime(
        string="Date of submission",
        )
    publish_date = fields.Datetime(
        string="Date of Publication",
        )
    hr_competency_config_id = fields.Many2one(
    'hr.competency.config',
    string="Competency config")

    competency_id = fields.Many2one(
    'hr.competency',
    string="Competency ID")

    period_id = fields.Many2one(
    'pms.year',
    string="Period")

    administrative_supervisor_id = fields.Many2one(
        'hr.employee',
        string="Administrative Supervisor"
        )
    manager_id = fields.Many2one(
        'hr.employee',
        string="Manager"
        )
    active = fields.Boolean(
        string="Active",
        default=True
        )
    reviewer_id = fields.Many2one(
        'hr.employee',
        string="Reviewer"
        )
    competency_ids = fields.One2many(
        'hr.competency.section.line',
        'hr_employee_competency_id',
        string="Competency Section"
        )
    type_of_competency = fields.Selection([
        ('lc', 'Leadership Competency'),
        ('fc', 'Functional Competency'),
        ], string="Type", default="lc", required=True
        )
    perception = fields.Selection([
        ('agreed', 'Agreed'),
        ('disagreed', 'Disagreed'),
        ], string="Perception", default=""
        )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'Waiting for Review'),
        ('completed', 'Completed'),
        ('signed', 'Signed'),
        ('refused', 'Refused'),
        ], string="State", default="draft"
        )
    
    # competency_overall_total = fields.Float(
    #     "Overall total?", 
    #     help='Average of the total sum of competency sverage score; EG. 100 + 30 + 10 / 3',
    #     compute="compute_competency_overall_total"
    #     )
    
 
    def validation_before_submission(self):
        lines = self.mapped('competency_ids').mapped('competency_attribute_line_ids')
        if self.state == "draft":
            if self.employee_id.user_id.id != self.env.uid:
                raise ValidationError("You are not responsible to submit this record")
            self_rating_below_zero = lines.filtered(
                lambda ln: ln.rate <= 0 or not ln.self_rating_term
            )
            if self_rating_below_zero:
                raise ValidationError("Please ensure all the line attributes must be rated")
         
    def generate_raters_records(self):
        """Loops through each reviewers linked employee records 
        and generates appraisee ratings for them
        """
        hr_competency = self.env['hr.competency'].sudo()
        for rater in self.rater_ids:
            for emp in rater.employee_ids:
                new_hr_competency = hr_competency.create({
                    'employee_id': self.employee_id.id,
                    'name': f"({self.name}) - {self.employee_id.name}",
                    'rated_by': emp.id,
                    'category_role_id': rater.category_role_id.id,
                    'hr_competency_id': self.id,
                    'state': 'in_review',
                    'date_of_submission': fields.Date.today(),
                    'hr_competency_config_id': self.hr_competency_config_id.id,
                    'period_id': self.period_id.id,
                    'competency_ids': [(0, 0, {
                        'name': comp.name, 
                        'competency_attribute_line_ids': [(0, 0, {
                            'name': att.name,
                            'rate': att.rate,
                            'self_rating_term': att.self_rating_term,
                        }) for att in comp.competency_attribute_line_ids]
                    }) for comp in self.competency_ids],
                })
                self._send_mail_to(new_hr_competency)
    
    def action_submit(self):
        self.validation_before_submission()
        self.generate_raters_records()
        self.write({
            'state': 'in_review'
        })

    def validate_return(self):
        if self.employee_id.user_id.id != self.env.uid:
            raise ValidationError("You are not responsible to return this record")

    def action_withdraw(self):
        self.validate_return()
        self.write({
            'state': 'draft'
        })

    def _send_mail_to(self, record):
        template_id = self.env.ref(
        'hr_mirror.mail_template_mirror_raters_notification', raise_if_not_found=False)
        if template_id:
                ctx = dict({
                    'default_model': 'hr.competency',
                    'default_res_id': record.id,
                    'default_use_template': bool(template_id.id),
                    'default_template_id': template_id.id,
                    'default_composition_mode': 'comment',
                })
                template_id.with_context(ctx).send_mail(record.id, False)
 