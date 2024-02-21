from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError



class CompetencyReportLine(models.Model):
    _name = "competency.report.line"
    _description = "Competency reports"

    
    # show if report type is employee
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee", 
        required=True
        ) 
    competency_report_id = fields.Many2one(
        'competency.report',
        string="Competency Report", 
        required=True
        )
    self_rating = fields.Float(
        string="Self Rating", 
        readonly=True,
        store=True,
        )
    self_rating = fields.Float(
        string="Self Rating", 
        readonly=True,
        store=True,
        )
    senior_rating = fields.Float(
        string="Senior Rating", 
        readonly=True,
        store=True,
        )
    peer_rating = fields.Float(
        string="Peer Rating", 
        readonly=True,
        store=True,
        )
    junior_rating = fields.Float(
        string="Junior Rating", 
        readonly=True,
        store=True,
        )
    

class CompetencyReport(models.Model):
    _name = "competency.report"
    _description = "Competency reports"
    _rec_name = "hr_competency_template_id"

    report_type = fields.Selection([
        ('all', 'All Employee'),
        ('employee', 'All employees')
        ],
        string="Report type", 
        required=True,
        default='all'
        )
    
    # show if report type is employee
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee", 
        required=True
        )
    # required to filter the particular report template in questions 
    hr_competency_template_id = fields.Many2one(
        'hr.competency.config',
        string="Competency Period", 
        required=True
        )
    period_id = fields.Many2one(
    'pms.year',
    string="Period")

    hr_competency_report_line_ids = fields.One2many(
    'competency.report.line',
    'competency_report_id',
    string="Report ID")

    def generate_report(self):
        # ===============================
        if self.hr_competency_template_id and self.report_type:
            hr_competency_aggregation_ids = self.env['employee.aggregation'].sudo().search([
                ('period_id', '=', self.period_id.id)

                ])
            if hr_competency_aggregation_ids:
                for aggregation in hr_competency_aggregation_ids:
                    hr_competency_ids = aggregation.mapped('hr_competency_ids').filtered(
                        lambda s: s.rating_role == "senior"
                    )



        else:
            raise ValidationError('Please ensure that template and report type are rightly selected !!!')

 