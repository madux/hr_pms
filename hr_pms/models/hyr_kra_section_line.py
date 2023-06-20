from datetime import datetime, timedelta
import time
import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from lxml import etree

_logger = logging.getLogger(__name__)

class HYR_KRA_SectionLine(models.Model):
    _name = "hyr.kra.section.line"
    _description= "HRY Employee appraisee KRA Section lines"
     
    hyr_kra_section_id = fields.Many2one(
        'pms.appraisee',
        string="HYR KRA Section"
    )

    name = fields.Char(
        string='Description',
        size=300
        )
    weightage = fields.Float(
        string='FA Weight (Total 100%)', 
        )
    
    reverse_weightage = fields.Float(
        string='Reverse Weightage (Total 100%)', 
        store=True
        )
    
    appraisee_weightage = fields.Float(
        string='Weight (Total 100%)',
        )
    is_functional_manager = fields.Boolean(
        string="is functional manager", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_administrative_supervisor = fields.Boolean(
        string="is administrative supervisor", 
        default=False,
        compute="compute_user_rating_role"
        )
    is_reviewer = fields.Boolean(
        string="is Reviewer", 
        default=False,
        compute="compute_user_rating_role"
        )
    state = fields.Selection([
        ('hyr_draft', 'Half Year Review'),
        ('hyr_admin_rating', 'Admin Supervisor(HYR)'),
        ('hyr_functional_rating', 'Functional Appraiser(HYR)'),
        ('draft', 'Start Full Year Review'),
        ('admin_rating', 'Administrative Appraiser'),
        ('functional_rating', 'Functional Appraiser'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Completed'),
        ('signed', 'Signed Off'),
        ('withdraw', 'Withdrawn'), 
        ], string="Status", readonly=True, related="hyr_kra_section_id.state")
    hyr_fa_rating = fields.Selection([
        ('none', ''),
        ('poor_average', 'Poor Average'),
        ('good_average', 'Good Average'),
        ('excellent', 'Excellent'),
        ], string="FA Review", default = "", readonly=False)
    hyr_aa_rating = fields.Selection([
        ('none', ''),
        ('poor_average', 'Poor Average'),
        ('good_average', 'Good Average'),
        ('excellent', 'Excellent'),
        ], string="AA Review", default = "", readonly=False)
    
    weighted_score = fields.Float(
        string='Weighted (%) Score of specific KRA', 
        store=True,
        compute="compute_weighted_score"
        )
    
    @api.onchange(
        'hyr_rating', 
        )
    def onchange_rating(self):
        if self.state == 'hyr_functional_rating':
            if self.hyr_kra_section_id.employee_id.parent_id and self.env.user.id != self.hyr_kra_section_id.employee_id.parent_id.user_id.id:
                self.hyr_rating = ""
                raise UserError(
                """Ops ! You are not entitled to add a rating\n because you are not the employee's functional manager"""
                )
        if self.state == 'hyr_admin_rating':
            if self.hyr_kra_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.hyr_kra_section_id.employee_id.administrative_supervisor_id.user_id.id:
                self.hyr_rating = ""
                raise UserError(
                """Ops ! You are not entitled to add a rating \n because you are not the employee's administrative supervisor"""
                )

    @api.onchange('weightage')
    def onchange_weightage(self):
        if self.weightage > 0 and self.weightage not in range (5, 26):
            self.weightage = 0
            raise UserError('Weightage must be within the range of 5 to 25')
        self.reverse_weightage = self.weightage
    
    @api.onchange('appraisee_weightage',)
    def onchange_appraisee_weightage(self):
        if self.appraisee_weightage > 0 and self.appraisee_weightage not in range (5, 26):
            self.appraisee_weightage = 0
            raise UserError('Appraisee Weightage must be within the range of 5 to 25')
             
    @api.depends('hyr_kra_section_id')
    def compute_user_rating_role(self):
        """
        Used to determine if the current user
        is a functional/department mmanager,
        administrative supervisor or reviewer
        """
        current_user = self.env.uid 
        if self.hyr_kra_section_id:
            self.is_functional_manager = True if current_user == self.hyr_kra_section_id.employee_id.parent_id.user_id.id else False
            self.is_administrative_supervisor = True if current_user == self.hyr_kra_section_id.employee_id.administrative_supervisor_id.user_id.id else False
            self.is_reviewer = True if current_user == self.hyr_kra_section_id.employee_id.reviewer_id.user_id.id else False
        else:
            self.is_functional_manager,self.is_administrative_supervisor,self.is_reviewer = False, False, False

    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['hyr_draft']):
            raise ValidationError(_('You cannot delete a KRA section once submitted Click the Ok and then discard button to go back'))
        return super(HYR_KRA_SectionLine, self).unlink()