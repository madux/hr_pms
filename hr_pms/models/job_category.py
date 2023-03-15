from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import ValidationError
from odoo import http


class PMSJobCategory(models.Model):
    _name = "pms.category"
    _description= "The job category of based on job roles"
    _inherit = "mail.thread"

    name = fields.Char(
        string="Name", 
        placeholder="OFFICER - MGR", 
        required=True)
    sequence = fields.Char(
        string="Sequence")
        
    kra_weighted_score = fields.Integer(
        string='KRA Section Weight', 
        placeholder="eg. 35",
        required=True,
        )
    fc_weighted_score = fields.Integer(
        string='FC Section Weight', 
        placeholder="eg. 20",
        required=True,
        )
    lc_weighted_score = fields.Integer(
        string='LC Section Weight', 
        placeholder="eg. 40",
        required=True,
        )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancel', 'Cancel'),
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

    published_date = fields.Date(
        string="Published date", 
        readonly=True, 
        store=True)
    
    loaded_via_data = fields.Boolean(
        string="Loaded via data", 
        readonly=True, 
        default=False, 
        store=True)

    job_role_ids = fields.Many2many(
        'hr.job', 
        string="Job role"
        )
    section_ids = fields.Many2many(
        'pms.section',
        'pms_section_category_rel',
        'category_id',
        'section_id',
        string="Sections"
    )
    pms_department_ids = fields.Many2many(
        'pms.department', 
        'pms_department_category_rel', 
        'department_id', 
        'category_id',
        string="PMS Department ID")

    # active = fields.Date(
    #     string="Active",
    #     readonly=True,
    #     default=True,
    #     store=True)
    
    @api.constrains('job_role_ids')
    def _check_lines(self):
        if not self.loaded_via_data and not self.mapped('job_role_ids'):
            raise ValidationError('You must assign at least one job role')

    @api.onchange('pms_year_id')
    def _onchange_year_id(self):
        '''Gets the periodic date interval from the settings'''
        if self.pms_year_id:
            self.date_from = self.pms_year_id.date_from
            self.date_end = self.pms_year_id.date_end
        else:
            self.date_from = False
            self.date_end = False

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
                'body_html': msg
            }
        mail_id = self.env['mail.mail'].sudo().create(mail_data)
        self.env['mail.mail'].sudo().send(mail_id)
        self.message_post(body=msg)
    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/>. ".format(base_url)

    def send_mail_notification(self, pms_department_obj):
        subject = "Appraisal Notification"
        department_manager = pms_department_obj.department_id.parent_id
        if department_manager:
            email_to = department_manager.work_email
            email_cc = [] #[rec.work_email for rec in self.approver_ids]
            msg = """Dear {}, <br/>
            I wish to notify you that an appraisal template with description, {} \
            has been initialized. You may proceed with publishing it out \
            to staff under your department (Unit).<br/>\
            <br/>Kindly {} to review <br/>\
            Yours Faithfully<br/>{}<br/>HR Department ({})""".format(
                department_manager.name,
                self.name, self.employee_id.name,
                self.get_url(pms_department_obj.id, pms_department_obj._name),
                self.env.user.name,
                self.env.user.company_id.name,
                )
        self.action_notify(subject, msg, email_to, email_cc)

    def button_publish(self):
        # TODO Add publish button with security as PMS Officer,
        # Create record (pms.department) for each job role department
        # i.e if there are 4 job roles, it generates a record for each department
        # forwards the mail notification to the department managers
        if self.job_role_ids and self.section_ids:
            # filters set of departments to forward generate
            department_ids = set([depart.department_id.id for depart in self.job_role_ids])
            Pms_Department = self.env['pms.department']
            if department_ids:
                # create pms.department record
                for dep in department_ids:
                    department_id = self.env['hr.department'].browse([dep])
                    pms_department = Pms_Department.create({
                        'name': self.name,
                        'department_id': department_id.id,
                        'pms_year_id': self.pms_year_id.id,
                        'date_from': self.pms_year_id.date_from,
                        'date_end': self.pms_year_id.date_end,
                        'deadline': self.deadline,
                        'hr_category_id': self.id,
                        'section_line_ids': [(0, 0, {
                            'section_id': sec.id,
                            'name': sec.name,
                            'max_line_number': sec.max_line_number,
                            'type_of_section': sec.type_of_section,
                            'pms_category_id': self.id,
                            # 'weighted_score': sec.weighted_score,
                            'section_avg_scale': sec.section_avg_scale,
                            'section_line_ids': [(0, 0, {
                                'name': sec_line.name,
                                'section_id': sec_line.section_id.id,
                                'is_required': sec_line.is_required,
                            }) for sec_line in sec.section_line_ids]
                        }) for sec in self.section_ids],
                    })
                    # after generating the record, send notification email
                    self.write({
                        'pms_department_ids': [(4, pms_department.id)],
                        'published_date': fields.Date.today(),
                        'state': 'review'

                        })
                    self.send_mail_notification(pms_department)
            self.write({
                'state' 'published'
            })
        else:
            raise ValidationError('Please add sections and job roles')
    
    def _message_post(self, template):
        """Wrapper method for message_post_with_template
        Args:
            template (str): email template
        """
        if template:
            ir_model_data = self.env['ir.model.data']
            template_id = ir_model_data.get_object_reference('hr_pms', template)[1]
            self.message_post_with_template(
                template_id, composition_mode='comment',
                model='{}'.format(self._name), res_id=self.id,
                email_layout_xmlid='mail.mail_notification_light',
            )
     
    # TODO Add cancel button as with security PMS Officer,
    # Ensure all the appraisals sent to employees will be deactivated or cancelled

    def button_cancel(self):
        for rec in self.pms_department_ids:
            rec.state = "cancel"
        self.write({
                'state' 'cancel'
            })
        
    def button_set_to_draft(self):
        self.write({
                'state' 'draft'
            })