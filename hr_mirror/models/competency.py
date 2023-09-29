from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class hrCompetencySectionLine(models.Model):
    _name = "hr.competency.attributes.line"
    _description="Competency section attribute line that users will fill in their rating"

    name = fields.Char(
        string="Name", 
        required=True)

    rate = fields.Float(
        string="Employee Rate",
        default=0
        )

    self_rating_term = fields.Selection([
        ('1', 'Rarely Demonstrated'),
        ('2', 'Sometimes Demonstrated'),
        ('3', 'Often Demonstrated'),
        ('4', 'Mostly Demonstrated'),
        ('5', 'Always Demonstrated'),
        ], string="Self Rating", default=""
        )
    appraiser_rating_term = fields.Selection([
        ('1', 'Rarely Demonstrated'),
        ('2', 'Sometimes Demonstrated'),
        ('3', 'Often Demonstrated'),
        ('4', 'Mostly Demonstrated'),
        ('5', 'Always Demonstrated'),
        ], string="Appraiser Rating", default=""
        ) 

    appraiser_rate = fields.Float(
        string="Appraiser Rate",
        default=0)

    percentage_rate = fields.Float(
        string="Percentage Score",
        compute="compute_percentage_score")

    hr_competency_section_line_id = fields.Many2one(
        "hr.competency.section.line",
        string="Competency line")
    
    is_reviewer = fields.Boolean(
        "Is reviewer?", 
        default=False,
        compute="determine_reviewer_user"
        )
    is_appraisee = fields.Boolean(
        "Is appraisee?", 
        default=False,
        compute="determine_appraisee_user"
        )
    
    @api.onchange('self_rating_term')
    def onchange_self_rating_term(self):
        if self.self_rating_term:
            self.rate = float(self.self_rating_term)
        else:
            self.rate = 0.00
        
    @api.onchange('appraiser_rating_term')
    def onchange_appraiser_rating_term(self):
        if self.appraiser_rating_term:
            self.appraiser_rate = float(self.appraiser_rating_term)
        else:
            self.appraiser_rate = 0.00
    
    # @api.onchange('appraiser_rate', 'rate')
    # def check_ratings(self):
    #     # status = self.hr_competency_section_line_id.hr_competency_id.state
    #     if self.rate > 0 and self.rate not in range(1, 6):
    #         self.rate = 0
    #         return {'warning': {
    #             'title': _("Warning"),
    #             'message': _("Self rating must be within the range of 1, 2, 3, 4, 5")
    #         }}  
        
    #     if self.appraiser_rate > 0 and self.appraiser_rate not in range(1, 6):
    #         self.appraiser_rate = 0
    #         return {'warning': {
    #             'title': _("Warning"),
    #             'message': _("Appraiser rating must be within the range of 1, 2, 3, 4, 5")
    #         }}
    
    @api.depends("appraiser_rate")
    def compute_percentage_score(self):
        for rec in self:
            # e.g total = rate / scale * number of rater (1)
            # total = total * 100
            if rec.appraiser_rate > 0:
                rate_result = rec.appraiser_rate / 5 * 1 # hardcorded the scale to 5
                rec.percentage_rate = rate_result * 100
            else:
                rec.percentage_rate = 0

    def determine_reviewer_user(self):
        for rec in self:
            rated_by = rec.hr_competency_section_line_id.hr_competency_id.rated_by
            if rated_by and rated_by.user_id.id == self.env.uid:
                rec.is_reviewer = True
            else:
                rec.is_reviewer = False
    
    def determine_appraisee_user(self):
        for rec in self:
            appraisee = rec.hr_competency_section_line_id.hr_competency_id.employee_id
            if appraisee and appraisee.user_id.id == self.env.uid:
                rec.is_appraisee = True
            else:
                rec.is_appraisee = False


class hrCompetencySectionLine(models.Model):
    _name = "hr.competency.section.line"
    _description="Competency section line  that users will fill in their rating"

    name = fields.Text(
        string="Name", 
        required=True)

    hr_competency_id = fields.Many2one(
        "hr.competency",
        string="Competency", 
        required=False)
    
    hr_employee_competency_id = fields.Many2one(
        "hr.employee.competency",
        string="Employee Competency") 

    average_total = fields.Float(
        string="Average total", 
        readonly=True, 
        compute="compute_average_total")
    
    percentage_average_total = fields.Float(
        string="Percentage Score", 
        readonly=True, 
        compute="compute_average_total")
     
    competency_attribute_line_ids = fields.One2many(
        "hr.competency.attributes.line",
        "hr_competency_section_line_id",
        string="Attributes",
        copy=False
    )

    @api.depends('competency_attribute_line_ids')
    def compute_average_total(self):
        # self.ensure_one() 
        '''for percentage score computation; 
        formula is total_percentage_score / lenght_of_attribute_lines e.g 80% + 40% / 4'''
        for rec in self:
            lenght_attribute_line = rec.competency_attribute_line_ids.ids
            if rec.competency_attribute_line_ids:
                total_rate = sum([rc.appraiser_rate for rc in rec.mapped('competency_attribute_line_ids')])
                rec.average_total = total_rate 

                percentage_average_total = sum([rc.percentage_rate for rc in rec.mapped('competency_attribute_line_ids')])
                rec.percentage_average_total = percentage_average_total / len(lenght_attribute_line)
            else:
                rec.average_total = 0
                rec.percentage_average_total = 0


class mirrorCompetency(models.Model):
    _name = "hr.competency"
    _description = "HR competency"
    _rec_name = "name"

    hr_competency_id = fields.Many2one(
        'hr.employee.competency',
        string="Employee competency"
        )

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
    rated_by = fields.Many2one(
        'hr.employee',
        string="Rated by",
        required=True
        )
    rating_role = fields.Selection([
        ('senior', 'Senior'),
        ('peers', 'Peers'),
        ('junior', 'Junior'),
        ], 
        string="Role", 
    )
    category_role_id = fields.Many2one(
        "category.role"
        )
    
    department_id = fields.Many2one(
        'hr.department',
        string="Department"
        )
    date_of_submission = fields.Datetime(
        string="Date of submission",
        )
    completion_date = fields.Datetime(
        string="Completion Date",
        )
    
    publish_date = fields.Datetime(
        string="Date of Publication",
        )
    hr_competency_config_id = fields.Many2one(
    'hr.competency.config',
    string="Competency config")

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
        'hr_competency_id',
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
    not_completed = fields.Boolean(
        "Rated?", 
        default=False,
        compute="check_if_all_rating_is_done"
        )
    
    is_reviewer = fields.Boolean(
        "Is reviewer?", 
        default=False,
        compute="determine_reviewer_user"
        )
    
    is_appraisee = fields.Boolean(
        "Is Appraisee?", 
        default=False,
        compute="determine_is_appraisee_user"
        )
    competency_overall_total = fields.Float(
        "Overall total?", 
        help='Average of the total sum of competency sverage score; EG. 100 + 30 + 10 / 3',
        compute="compute_competency_overall_total"
        )
    
    @api.depends('competency_ids')
    def compute_competency_overall_total(self):
        for rec in self:
            if rec.competency_ids:
                overall_total = sum(rec.competency_ids.mapped('percentage_average_total'))
                rec.competency_overall_total = overall_total / len(rec.competency_ids.ids)
            else:
                rec.competency_overall_total = False  

    def determine_reviewer_user(self):
        for rec in self:
            if rec.rated_by and rec.rated_by.user_id.id == self.env.uid:
                rec.is_reviewer = True
            else:
                rec.is_reviewer = False

    def determine_is_appraisee_user(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.user_id.id == self.env.uid:
                rec.is_appraisee = True
            else:
                rec.is_appraisee = False
    
    # def check_rating(self):
    #     is_rated = True
    #     if self.competency_ids:
    #         for rex in self.competency_ids:
    #             competency_attribute_ids = rex.mapped('competency_attribute_line_ids')
    #             not_rated = competency_attribute_ids.filtered(
    #                 lambda l: l.average_total <= 0
    #             )
    #             if not_rated:
    #                 is_rated = False
    #                 break
    #     return is_rated
        
    @api.depends('competency_ids')
    def check_if_all_rating_is_done(self):
        'determines if rating has been done'
        for rec in self:
            is_not_rated = False
            for comp in self.competency_ids:
                competency_attribute_ids = comp.mapped('competency_attribute_line_ids').filtered(
                    lambda l: not l.rate > 0
                )
                if competency_attribute_ids:
                    is_not_rated = True
                    break
            if is_not_rated:
                rec.not_completed = False
            else:
                rec.not_completed = True

    def validation_before_submission(self):
         
        lines = self.mapped('competency_ids').mapped('competency_attribute_line_ids')
        if self.state == "draft":
            if self.employee_id.user_id.id != self.env.uid:
                raise ValidationError("You are not responsible to submit this record")
            self_rating_below_zero = lines.filtered(
                lambda ln: ln.rate <= 0 or not ln.self_rating_term
            )
            if self_rating_below_zero:
                raise ValidationError("Please ensure all the line attributes self rating is above 0")
        elif self.state == "in_review":
            if self.rated_by.user_id.id != self.env.uid:
                raise ValidationError("You are not responsible to submit this record")
            self_rating_below_zero = lines.filtered(
                lambda ln: ln.appraiser_rate <= 0 or not ln.appraiser_rating_term
            )
            if self_rating_below_zero:
                raise ValidationError("Please ensure all the line attributes appraiser's rating are rated")
              
    # def validation_before_submission(self):
    #     if self.state == "draft":
    #         for cm in self.competency_ids:
    #             self_rating_below_zero = cm.mapped('competency_attribute_line_ids').filtered(
    #                 lambda ln: ln.rate <= 0
    #             )
    #             if self_rating_below_zero:
    #                 raise ValidationError("Please ensure all the line attributes self rating is above 0")
    #     elif self.state == "in_review":
    #         for cm in self.competency_ids:
    #             self_rating_below_zero = cm.mapped('competency_attribute_line_ids').filtered(
    #                 lambda ln: ln.appraiser_rate < 0
    #             )
    #             if self_rating_below_zero:
    #                 raise ValidationError("Please ensure all the line attributes self rating is above 0")
              
    def action_submit(self):
        # self.validation_before_submission()
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

    def generate_aggregate(self):
        existing_aggregation_id = self.env['employee.aggregation'].sudo().search([
            ('period_id', '=', self.period_id.id),
            ('hr_competency_config_id', '=', self.hr_competency_config_id.id)
        ])
        if existing_aggregation_id:
            existing_aggregation_id.hr_competency_ids = [(4, self.id)]
        
        else:
            self.env['employee.aggregation'].sudo().create({
            'name': f'360 Degrees for {self.employee_id.name}',
            'employee_id': self.employee_id.id,
            'period_id': self.period_id.id,
            'hr_competency_config_id': self.hr_competency_config_id.id,
            'department_id': self.employee_id.department_id.id,
            'hr_competency_ids': [(4, self.id)],
        })

    def action_done(self):
        self.validation_before_submission()
        self.generate_aggregate()
        self.write({
            'state': 'completed',
            'completion_date': fields.Date.today()
        })

    def action_sign(self):
        self.write({
            'state': 'signed'
        }) 

    def action_refuse(self):
        self.write({
            'state': 'draft'
        }) 
    def action_set_to_draft(self):
        self.write({
            'state': 'draft'
        }) 


class mirrorCompetencyConfig(models.Model):
    _name = "hr.competency.config"
    _description = "Competency Config"

    name = fields.Text(
        string="Name", 
        required=True
        )

    competency_ids = fields.Many2many(
        'hr.competency.section', 
        string="Attributes"
        )
    competency_reviewer_ids = fields.Many2many(
        'hr.competency.reviewer',
        'hr_reviewer_config_rel',
        'hr_reviewer_config_id',
        'hr_reviewer_id',
        string="Competency reviewers"
        )

    # lc_attribute_ids = fields.One2many(
    #     'hr.competency.attributes',
    #     string="Attributes"
    #     )
    period_id = fields.Many2one(
    'pms.year',
    string="Period")

    type_of_competency = fields.Selection([
        ('lc', 'Leadership Competency'),
        ('fc', 'Functional Competency'),
        ], string="Type", default="lc", required=True
        )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('publish', 'Publish'),
        ('unpublish', 'Unpublish'),
        ], 
        string="State", 
        default="draft"
    )

    # def generate_rating(self):
    #     """Loops through each reviewers linked employee records 
    #     and generates appraisee ratings for them
    #     """
    #     hr_competency = self.env['hr.competency'].sudo()
    #     for rev in self.competency_reviewer_ids:
    #         for app in rev.employee_ids:
    #             hr_competency.create({
    #                 'employee_id': rev.employee_id.id,
    #                 'name': f"({self.name}) {app.id}",
    #                 'rated_by': app.id,
    #                 'rating_role': rev.employee_id.rating_role,
    #                 'publish_date': fields.Date.today(),
    #                 'hr_competency_config_id': self.id,
    #                 'period_id': self.period_id.id,
    #                 'competency_ids': [(0, 0, {
    #                     'name': comp.name, 
    #                     'competency_attribute_line_ids': [(0, 0, {
    #                         'name': att.name,
    #                     }) for att in comp.lc_attribute_ids]
    #                 }) for comp in self.competency_ids],
    #             })

    def generate_employee_competency(self):
        """Loops through each raters linked employee records 
        and generates appraisee ratings for them
        """
        hr_employee_competency = self.env['hr.employee.competency'].sudo()
        for appr in self.competency_reviewer_ids:
            hr_employee_competency.create({
                'employee_id': appr.employee_id.id,
                'name': f"{self.name} - {appr.employee_id.name}",
                'rater_ids': appr.category_role_ids.ids,
                'publish_date': fields.Date.today(),
                'hr_competency_config_id': self.id,
                'period_id': self.period_id.id,
                'competency_ids': [(0, 0, {
                    'name': comp.name, 
                    'competency_attribute_line_ids': [(0, 0, {
                        'name': att.name,
                    }) for att in comp.lc_attribute_ids]
                }) for comp in self.competency_ids],
            })
            subject = '360-Degree Feedback: Self-Assessment'
            # msg = f"""Dear {appr.employee_id.name}, <br/><br/> 
            # I wish to notify you that a feedback form <br/>\
            # has been generated for you.<br/>\
            # <br/>Kindly login to rate yourself <br/>\
            # Yours Sincerely<br/>HR Department"""

            msg = f"""Dear {appr.employee_id.name}, <br/><br/> 
                I hope this message finds you well. As part of our ongoing\
                commitment to fostering professional growth and development,\
                we are initiating the 360-degree feedback process titled "{self.name}"\
                has been generated for you.<br/>\
                <br/>We kindly request you to take a moment and to complete your self-assessment by following the steps below: <br/>\
                <br/><ol>\
                <li>Visit the following link to access the system http://hrpms.myeedc.com:8069/web</li></li>\
                <br/><li>Log in using your credentials sent earlier</li>\
                <br/><li>Click 360 Feedback in the menu</li>\
                <br/><li>Click the "{self.name} - {appr.employee_id.name}" record and wait for it to open</li>\
                <br/><li>Click and edit and select each of the leadership categories to rate yourself</li>\
                </ol>\
                <br/>If you encounter any technical issues or have questions about the self-assessment process,\
                please don't hesitate to reach out to the HR team for assistance.\
                <br/> Thank you for your participation.\
                <br/><br/>Yours Sincerely<br/>HR Department<br/>EEDC Corporate Headquarters<br/>eedctalentmanagement@enugudisco.com"""

            email_cc = ''

            email_to = appr.employee_id.work_email
            self._send_mail(subject, msg, email_to, email_cc)

    # def validate_reviewers_role(self):
    #     count = 1
    #     for rec in self.competency_reviewer_ids:
    #         count =+ 1
    #         for emp in rec.employee_ids:
    #             if not emp.rating_role:
    #                 raise ValidationError(f"Employee by name {emp.name} under the appraisee {rec.employee_id.name}- at line {count}")

    def action_publish(self):
        # self.validate_reviewers_role()
        self.generate_employee_competency()
        self.state = "publish"

    def action_unpublish(self):
        appraisee_ids = self.env['hr.employee.competency'].search([
            ('hr_competency_config_id', '=', self.id)])
        if appraisee_ids:
            for rec in appraisee_ids:
                rec.active = False
        self.state = "unpublish"

    def action_cancel_publish(self):
        self.state = "draft"

    def _send_mail(self, subject, msg, email_to, email_cc):
        email_from = self.env.user.email
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


class hrCompetencySection(models.Model):
    _name = "hr.competency.section"

    name = fields.Text(
        string="Name", 
        required=True)
    
    lc_attribute_ids = fields.One2many(
        'hr.competency.section.attributes', 
        'hr_competency_id',
        string="Attributes"
        )
    
    type_of_competency = fields.Selection([
        ('lc', 'Leadership Competency'),
        ('fc', 'Functional Competency'),
        ], string="Type", default="lc",
        )
    

class hrCompetencySectionAttributes(models.Model):
    _name = "hr.competency.section.attributes"

    name = fields.Text(
        string="Name", 
        required=True) 
    hr_competency_id = fields.Many2one(
        "hr.competency.section",
        string="Name", 
        required=True) 
    



