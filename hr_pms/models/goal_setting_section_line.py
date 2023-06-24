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
        string='KRA Description',
        size=300
        )
    weightage = fields.Integer(
        string='Weight(Total 100%)', 
        )
    target = fields.Char(
        string='Target', 
        size=24
        )
    # target_uom = fields.Many2one(
    #     'pms.uom',
    #     string="Goal Setting Section"
    # )
    target_uom = fields.Many2one(
        'pms.uom',
        string="Goal Setting Section"
    )
    acceptance_status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ], string="Acceptance status", default = "Yes", readonly=False)
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
        if self.weightage > 0 and self.weightage not in range (5, 26):
            self.weightage = 0
            raise UserError('Weightage must be within the range of 5 to 25')
        
    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['hyr_draft']):
            raise ValidationError(_('You cannot delete a KRA section once submitted Click the Ok and then discard button to go back'))
        return super(GoalSettingSectionLine, self).unlink()