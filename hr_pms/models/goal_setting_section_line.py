from datetime import datetime, timedelta
import time
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from lxml import etree

_logger = logging.getLogger(__name__)


class GoalSettingSectionLine(models.Model):
    _name = "goal.setting.section.line"
    _description= "Goal setting section line"
     
    goal_setting_section_id = fields.Many2one(
        'pms.appraisee',
        string="Goal Setting Section"
    )
    name = fields.Char(
        string='KRA',
        size=300
        )
    weightage = fields.Integer(
        string='Weightage', 
        )
    
    pms_uom = fields.Selection([
        ('Desc', 'Desc'),
        ('Naira', 'Naira'),
        ('Percentage', 'Percentage(s)'),
        ('Day', 'Day(s)'),
        ('Week', 'Week(s)'),
        ('Month', 'Month(s)'),
        ('Others', 'Others'),
        ], string="Unit of Measure", default = "")
    target = fields.Char(
        string='Target', 
        size=15
        )       
    acceptance_status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ], string="Acceptance", default = "yes", readonly=False)
    fa_comment = fields.Text(
        string='Comment(s)', 
        )
    state = fields.Selection([
        ('goal_setting_draft', 'Goal Settings'),
        ('hyr_draft', 'Draft'),
        ('hyr_admin_rating', 'Admin Supervisor'),
        ('hyr_functional_rating', 'Functional Supervisor'),
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", readonly=True, related="goal_setting_section_id.state")
    
    @api.onchange('weightage')
    def onchange_weightage(self):
        if self.weightage > 0 and self.weightage not in range (0, 26):
            self.weightage = 0
            raise UserError('Weightage must be within the range of 1 to 25')
        
    @api.onchange('pms_uom')
    def onchange_pms_uom(self):
        self.ensure_one()
        if self.pms_uom:
            self.target = False

    @api.onchange('target')
    def onchange_target(self):
        self.ensure_one()
        if self.target:
            if self.pms_uom in ['Naira', 'Day', 'Month', 'week', 'Percentage']:
                value = self.target.replace(',', '')
                value_uom = value
                if self.pms_uom in ['Naira']:
                    try:
                        value_uom = float(value_uom) if '.' in value_uom else int(value_uom) 
                        value_uom = "₦ {:0,.2f}".format(float(value_uom))
                    except Exception as e:
                        raise ValidationError("Wrong value provided for Naira Unit of measure")
                if self.pms_uom == 'Percentage':
                    try:
                        value_uom = f"{float(value_uom)} %" if '.' in value_uom else f"{int(value_uom)} %" 
                    except Exception as e:
                        value_uom = value 
                        # raise ValidationError("Wroskss")
                self.target = value_uom

    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['goal_setting_draft']):
            raise ValidationError(_('You cannot delete a KRA section once submitted Click the Ok and then discard button to go back'))
        return super(GoalSettingSectionLine, self).unlink()