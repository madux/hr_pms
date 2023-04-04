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


class HRUnit(models.Model):
    _name = "hr.work.unit"
    _description = "HR work unit"

    name = fields.Char(
        string="Name", 
        required=True
        )


class HRDistrict(models.Model):
    _name = "hr.district"
    _description = "HR district"

    name = fields.Char(
        string="Name", 
        required=True
        )

class HRLevel(models.Model):
    _name = "hr.level"
    _description = "HR level"

    name = fields.Char(
        string="Name", 
        required=True
        )
    
class HRUNIT(models.Model):
    _name = "hr.unit"
    _description = "HR Unit"

    name = fields.Char(
        string="Name", 
        required=True
        )
    
class HRgrade(models.Model):
    _name = "hr.grade"
    _description = "HR grade"

    name = fields.Char(
        string="Name", 
        required=True
        )

# class HrEmployeePublicInherit(models.Model):
#     _inherit = "hr.employee.public"
    
#     administrative_supervisor_id = fields.Many2one('hr.employee', string="Administrative Supervisor")
#     reviewer_id = fields.Many2one('hr.employee', string="Reviewer")
#     employment_date = fields.Date(string="Employement date")
#     level_id = fields.Many2one('hr.level', string="Level")
#     grade_id = fields.Many2one('hr.grade', string="Grade")
#     work_unit_id = fields.Many2one('hr.work.unit', string="Unit/SC/Workshop/Substation")
#     unit_id = fields.Many2one('hr.unit', string="Unit")
#     ps_district_id = fields.Many2one('hr.district', string="Employee District")
#     employee_number = fields.Char(
#         string="Staff Number", 
#         )
#     migrated_password = fields.Char(
#         string="migrated password", 
#         ) 
#     pms_number_appraisal = fields.Integer(string="Appraisal",)# compute="_compute_employees_component")
#     pms_number_queries = fields.Integer(string="Queries",)# compute="_compute_employees_component")
#     pms_number_commendation = fields.Integer(string="Commendation",)# compute="_compute_employees_component")
#     pms_number_warning = fields.Integer(string="Queries", )#compute="_compute_employees_component")
#     pms_number_absent = fields.Integer(string="Absent", )#compute="_compute_employees_component")
    

class HrEmployee(models.AbstractModel):
    _inherit = "hr.employee.base"

    # pms_appraisal_ids = fields.Many2many('usl.employee.appraisal', string="Appraisals", readonly=True)
    administrative_supervisor_id = fields.Many2one('hr.employee', string="Administrative Supervisor")
    reviewer_id = fields.Many2one('hr.employee', string="Reviewer")
    employment_date = fields.Date(string="Employement date")
    level_id = fields.Many2one('hr.level', string="Level")
    grade_id = fields.Many2one('hr.grade', string="Grade")
    work_unit_id = fields.Many2one('hr.work.unit', string="Unit/SC/Workshop/Substation")
    unit_id = fields.Many2one('hr.unit', string="Unit")
    ps_district_id = fields.Many2one('hr.district', string="Employee District")
    employee_number = fields.Char(
        string="Staff Number", 
        )
    migrated_password = fields.Char(
        string="migrated password", 
        )
    pms_number_appraisal = fields.Integer(string="Appraisal",)# compute="_compute_employees_component")
    pms_number_queries = fields.Integer(string="Queries",)# compute="_compute_employees_component")
    pms_number_commendation = fields.Integer(string="Commendation",)# compute="_compute_employees_component")
    pms_number_warning = fields.Integer(string="Queries", )#compute="_compute_employees_component")
    pms_number_absent = fields.Integer(string="Absent", )#compute="_compute_employees_component")
    
    # def _message_post(self, template):
    #     """Wrapper method for message_post_with_template

    #     Args:
    #         template (str): email template
    #     """
    #     if template:
    #         self.message_post_with_template(
    #             template.id, composition_mode='comment',
    #             model='hr.employee', res_id=self.id,
    #             email_layout_xmlid='mail.mail_notification_light',
    #         )

    def send_credential_notification(self):
        MAIL_TEMPLATE = self.env.ref(
        'hr_pms.mail_template_pms_notification', raise_if_not_found=False)
        # self.with_context(allow_write=True)._message_post(
        #     MAIL_TEMPLATE) 
        rec_ids = self.env.context.get('active_ids', [])
        for rec in rec_ids:
            record = self.env['hr.employee'].browse([rec])
            if record.work_email or record.private_email:
                email_to = record.work_email or record.private_email 
                ir_model_data = self.env['ir.model.data']
                template_id = ir_model_data.get_object_reference('hr_pms', 'mail_template_pms_notification')[1]         
                if template_id:
                    ctx = dict()
                    ctx.update({
                        'default_model': 'hr.employee',
                        'default_res_id': record.id,
                        'default_use_template': bool(template_id),
                        'default_template_id': template_id,
                        'default_composition_mode': 'comment',
                    })
                    template_rec = self.env['mail.template'].browse(template_id)
                    if email_to:
                        template_rec.write({'email_to': email_to})
                    template_rec.with_context(ctx).send_mail(record.id, True)
                # record.action_send_mail(
                #     'mail_template_pms_notification', 
                #     [record.work_email, record.private_email],
                #     )
    
    # def action_send_mail(self, with_template_id, email_items= None, email_from=None):
    #     '''Email_to = [lists of emails], Contexts = {Dictionary} '''
    #     email_to = (','.join([m for m in email_items])) if email_items else False
    #     ir_model_data = self.env['ir.model.data']
    #     template_id = ir_model_data.get_object_reference('hr_pms', 'mail_template_pms_notification')[1]         
    #     if template_id:
    #         ctx = dict()
    #         ctx.update({
    #             'default_model': 'hr.employee',
    #             'default_res_id': self.id,
    #             'default_use_template': bool(template_id),
    #             'default_template_id': template_id,
    #             'default_composition_mode': 'comment',
    #         })
    #         template_rec = self.env['mail.template'].browse(template_id)
    #         if email_to:
    #             template_rec.write({'email_to': email_to})
    #         template_rec.with_context(ctx).send_mail(self.id, True)

    # @api.depends('appraisal_ids')
    # def _compute_employees_component(self):
    #     for rec in self:
    #         appraisals = self.env['usl.employee.appraisal'].search([('employee_id', '=', rec.id)])
    #         appr = rec.appraisal_ids
    #         rec.number_appraisal = len(rec.appraisal_ids)
    #         rec.number_queries = sum([amt.number_queries for amt in rec.appraisal_ids])
    #         rec.number_warning = sum([amt.number_warning for amt in rec.appraisal_ids])
    #         rec.number_commendation = sum([amt.number_commendation for amt in rec.appraisal_ids])
    #         rec.number_absent = sum([amt.number_absent for amt in rec.appraisal_ids])

    def open_employee_appraisals(self):
        pass 
        # for rec in self:
        #     appraisals = self.env['usl.employee.appraisal'].search([('employee_id', '=', self.id)])
        #     emp_appraisal = [rec.id for rec in appraisals] if appraisals else []
        #     form_view_ref = self.env.ref('maach_hr_appraisal.usl_employee_appraisal_form_view', False)
        #     tree_view_ref = self.env.ref('maach_hr_appraisal.view_usl_employee_appraisal_tree', False)
        #     return {
        #         'domain': [('id', 'in', emp_appraisal)],
        #         'name': 'Employee Appraisal',
        #         'res_model': 'usl.employee.appraisal',
        #         'type': 'ir.actions.act_window',
        #         'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
        #         'target': 'current',
        #     }

    def stat_button_query(self):
        pass

    def stat_button_number_commendation(self):
        pass

    def stat_button_warning(self):
        pass

    def stat_button_absent(self):
        pass

    def stat_button_total_appraisal(self):
        pass
