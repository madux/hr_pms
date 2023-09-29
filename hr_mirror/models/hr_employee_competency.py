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
                hr_competency.create({
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
                subject = f'Request for Your Feedback: 360-Degree Assessment for {self.name}'

            msg = f"""Dear {emp.name}, <br/><br/> 
                I hope this message finds you well. As part of our ongoing\
                commitment to fostering professional growth and development,\
                you have been selected to provide valuable feedback on the performance of {self.name} as part of our 360-degree feedback process.\
                <br/>Your input is highly valued and will contribute to our efforts to enhance leadership competencies within our organization.\ 
                <br/>To provide your feedback on {self.name}, please follow these steps: <br/>\
                <br/><ol>\
                <li>Visit the following link to access the system http://hrpms.myeedc.com:8069/web</li>\
                <br/><li>Log in using your credentials sent earlier</li>\
                <br/><li>Click 360 Feedback in the menu</li>\
                <br/><li>Click the "{self.name} - {self.employee_id.name}" record and wait for it to open</li>\
                <br/><li>Click edit and select and give your feedback on each of the leadership categories</li>\
                </ol>\
                <br/>If you encounter any technical issues or have questions about the self-assessment process,\
                please don't hesitate to reach out to the HR team for assistance.\
                <br/> Thank you for your participation.\
                <br/><br/>Yours Sincerely<br/>HR Department<br/>EEDC Corporate Headquarters<br/>eedctalentmanagement@enugudisco.com"""

            email_cc = self.employee_id.work_email

            email_to = emp.work_email
            self._send_mail(subject, msg, email_to, email_cc)
    
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

    def _send_mail(self, subject, msg, email_to, email_cc):
        email_from = 'eedctalentmanagement@enugudisco.com'
        mail_data = {
                'email_from': email_from,
                'subject': subject,
                'email_to': email_to,
                'reply_to': email_from,
                'email_cc': email_cc,
                'body_html': msg,
                'state': 'sent'
            }
        mail_id = self.env['mail.mail'].sudo().create(mail_data)
        self.env['mail.mail'].sudo().send(mail_id)

 