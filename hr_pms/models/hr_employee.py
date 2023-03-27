from datetime import datetime, timedelta
import time
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import http
import logging
from lxml import etree
import xlrd

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


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # pms_appraisal_ids = fields.Many2many('usl.employee.appraisal', string="Appraisals", readonly=True)
    administrative_supervisor_id = fields.Many2one('hr.employee', string="Administrative Supervisor")
    reviewer_id = fields.Many2one('hr.employee', string="Reviewer")
    work_unit_id = fields.Many2one('hr.work.unit', string="Unit/SC/Workshop/Substation")
    ps_district_id = fields.Many2one('hr.district', string="Employee District")
    employee_number = fields.Char(
        string="Staff Number",
    )
    pms_number_appraisal = fields.Integer(string="Appraisal", )  # compute="_compute_employees_component")
    pms_number_queries = fields.Integer(string="Queries", )  # compute="_compute_employees_component")
    pms_number_commendation = fields.Integer(string="Commendation", )  # compute="_compute_employees_component")
    pms_number_warning = fields.Integer(string="Queries", )  # compute="_compute_employees_component")
    pms_number_absent = fields.Integer(string="Absent", )  # compute="_compute_employees_component")

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

    # def open_employee_appraisals(self):
    #     for rec in self:
    #         appraisals = self.env['usl.employee.appraisal'].search([('employee_id', '=', self.id)])
    #         emp_appraisal = [rec.id for rec in appraisals] if appraisals else []
    #         form_view_ref = self.env.ref('maach_hr_appraisal.usl_employee_appraisal_form_view', False)
    #         tree_view_ref = self.env.ref('maach_hr_appraisal.view_usl_employee_appraisal_tree', False)
    #         return {
    #             'domain': [('id', 'in', emp_appraisal)],
    #             'name': 'Employee Appraisal',
    #             'res_model': 'usl.employee.appraisal',
    #             'type': 'ir.actions.act_window',
    #             'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
    #             'target': 'current',
    #         }

    # def stat_button_query(self):
    #     pass

    # def stat_button_number_commendation(self):
    #     pass

    # def stat_button_warning(self):
    #     pass

    # def stat_button_absent(self):
    #     pass

    # def stat_button_total_appraisal(self):
    #     pass

    class EmployeeImport(models.Model):
        _name = 'employee.import'

        file = fields.Binary(string="Excel File", required=True)
        description = fields.Char(max_length="255", readonly=True)
        state = fields.Selection(
            selection=[
                ("new", "New"),
                ("loaded", "Loaded"),
                ("imported", "Imported"),
            ],
            string="Status",
            required=True,
            copy=False,
            default="new",
        )

        def action_import_employees(self):
            data = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))

            sheet = data.sheet_by_index(0)
            for row in range(1, sheet.nrows):
                employee_vals = {}
                employee_vals['employee_number'] = sheet.cell(row, 0).value
                employee_vals['name'] = sheet.cell(row, 1).value
                employee_vals['work_phone'] = sheet.cell(row, 2).value
                employee_vals['work_email'] = sheet.cell(row, 3).value

                try:
                    employee_vals['department_id'] = self.env[
                        'hr.department'
                    ].search([('name', '=', sheet.cell(row, 4).value)]).id
                except Exception:
                    print('Could not find department')

                try:
                    employee_vals['job_id'] = self.env[
                        'hr.job'
                    ].search([('name', '=', sheet.cell(row, 5).value)]).id
                except Exception:
                    print('Could not find job')

                try:
                    employee_vals['parent_id'] = self.env[
                        'hr.employee'
                    ].search([('employee_number', '=', int(sheet.cell(row, 6).value))]).id
                except Exception:
                    print('Could not find employee')

                # raise ValidationError(employee_vals['parent_id'])

                employee = self.env['hr.employee'].create(employee_vals)

                self.state = 'imported'

                self.description = "%s employees successfully imported" % row

            return {'type': 'ir.actions.act_window_close'}

        @api.onchange('file')
        def _onchange_garden(self):
            if self.file:
                self.state = 'loaded'
