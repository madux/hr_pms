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
        )
    
    appraisee_weightage = fields.Float(
        string='Weight (Total 100%)',
        )
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    self_rating = fields.Integer(
        string='Self Rating', 
        )
        
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        )
    reviewer_rating = fields.Integer(
        string='Reviewer Ratings',
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
        ], string="Status", default = "draft", readonly=True, related="hyr_kra_section_id.state")
    
    weighted_score = fields.Float(
        string='Weighted (%) Score of specific KRA', 
        store=True,
        compute="compute_weighted_score"
        )
    
    @api.onchange(
        'self_rating', 
        'functional_supervisor_rating', 
        'administrative_supervisor_rating',
        'reviewer_rating')
    def onchange_rating(self):
        if self.state == 'hyr_functional_rating':
            if self.hyr_kra_section_id.employee_id.parent_id and self.env.user.id != self.hyr_kra_section_id.employee_id.parent_id.user_id.id:
                self.functional_supervisor_rating = 0
                raise UserError(
                """Ops ! You are not entitled to add a rating\n because you are not the employee's functional manager"""
                )
        if self.state == 'hyr_admin_rating':
            if self.hyr_kra_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.hyr_kra_section_id.employee_id.administrative_supervisor_id.user_id.id:
                self.administrative_supervisor_rating = 0
                raise UserError(
                """Ops ! You are not entitled to add a rating \n because you are not the employee's administrative supervisor"""
                )
        # if self.state == 'reviewer_rating':
        #     if self.hyr_kra_section_id.employee_id.reviewer_id and self.env.user.id != self.hyr_kra_section_id.employee_id.reviewer_id.user_id.id:
        #         self.reviewer_rating = 0
        #         raise UserError("Ops ! You are not entitled to add a rating because you are not the employee's reviewer")
            
        # if self.self_rating > self.section_avg_scale:
        #     self.self_rating = 1
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Self rating Scale should be in the range of 1 - {}'.format(self.section_avg_scale)
        #         }
        #     return {'warning': message}
        # if self.functional_supervisor_rating > self.section_avg_scale:
        #     self.functional_supervisor_rating = 1
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Functional supervisor rating Scale should be in the range of 1 - {}'.format(self.section_avg_scale)
        #         }
        #     return {'warning': message}
        
        # if self.administrative_supervisor_rating > self.section_avg_scale:
        #     self.administrative_supervisor_rating = 1
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Administrative supervisor rating Scale should be in the range of 1 - {}'.format(self.section_avg_scale)
        #         }
        #     return {'warning': message}
    
        # if self.reviewer_rating > self.section_avg_scale:
        #     self.reviewer_rating = 1
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': "Reviewer's rating Scale should be in the range of 1 - {}".format(self.section_avg_scale)
        #         }
        #     return {'warning': message}

    @api.onchange('weightage',)
    def onchange_weightage(self):
        if self.weightage > 0 and self.weightage not in range (5, 26):
            self.weightage = 0
            raise UserError('Weightage must be within the range of 5 to 25')
    
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
     
    # @api.depends(
    #     'weightage',
    #     'administrative_supervisor_rating',
    #     'functional_supervisor_rating',
    #     'reviewer_rating')
    # def compute_weighted_score(self):
    #     # =(((admin_rating*40 )+(functional_rating *60))/4) * (weightage /100)
    #     for rec in self:
    #         fc_avg_scale = rec.section_avg_scale or 4 # or 5 is set as default in case nothing was provided
    #         if rec.administrative_supervisor_rating or rec.functional_supervisor_rating or rec.reviewer_rating:
    #             ar = rec.administrative_supervisor_rating * 30 if rec.administrative_supervisor_rating > 0 else 0
    #             # f_rating = 30 if rec.administrative_supervisor_rating > 0 else 60
    #             f_rating = get_fa_rating(
    #                 rec.functional_supervisor_rating, 
    #                 rec.administrative_supervisor_rating, 
    #                 rec.reviewer_rating)
    #             fr = rec.functional_supervisor_rating * f_rating
    #             rr = rec.reviewer_rating * 40
    #             ratings = (ar + fr + rr) / fc_avg_scale
    #             rec.weighted_score = ratings * (rec.weightage / 100)
    #         else:
    #             rec.weighted_score = 0

    def unlink(self):
        for delete in self.filtered(lambda delete: delete.state not in ['hyr_draft']):
            raise ValidationError(_('You cannot delete a KRA section once submitted Click the Ok and then discard button to go back'))
        return super(HYR_KRA_SectionLine, self).unlink()