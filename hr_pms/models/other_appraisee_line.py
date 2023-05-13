from datetime import datetime, timedelta
import time
import base64
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import logging
from lxml import etree
_logger = logging.getLogger(__name__)


class Training_SectionLine(models.Model):
    _name = "training.section.line"
    _description= "training appraisal Section lines"

    training_section_id = fields.Many2one(
        'pms.appraisee',
        string="Appraisal"
    )

    name = fields.Char(
        string='Training Description',
        )
    comments = fields.Text(
        string='Comments', 
        
        )
    requester_id = fields.Many2one(
        'res.users',
        string='Requested by', 
        default=lambda self: self.env.uid,
        )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True, related="training_section_id.state")
    

class currentAssessmentSectionLine(models.Model):
    _name = "current.assessment.section.line"
    _description= "Assessment appraisal Section lines"

    current_assessment_section_id = fields.Many2one(
        'pms.appraisee',
        string="Appraisal"
    )

    name = fields.Char(
        string='name', 
        )
    desc = fields.Char(
        string='Description', 
        )
    weightage = fields.Float(
        string='Weight (Total 100%)'
        )
    
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        )
    reviewer_rating = fields.Integer(
        string='Reviewer Ratings',
        ) 
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True)
    # , related="current_assessment_section_id.state")
    
    weighted_score = fields.Float(
        string='Weighted (%) Score', 
        store=True,
        # compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale',
        help="Takes in the default scale",
        default=5
        )
    assessment_type = fields.Selection([
        ('Ordinary', 'Ordinary'),
        ('Diligent', 'Diligent'),
        ('Fantastic', 'Fantastic'),
        ('Superb', 'Superb'),
        ], string="Choose", default = "", readonly=False)
    
    @api.onchange('assessment_type')
    def onchange_assessment_type(self):
        self.validate_rating()
        if self.assessment_type == 'Ordinary':
            rating = 1
        elif self.assessment_type == 'Diligent':
            rating = 2
        elif self.assessment_type == 'Fantastic':
            rating = 3
        elif self.assessment_type == 'Superb':
            rating = 4 
        else:
            rating = 0
        self.administrative_supervisor_rating = rating
        self.functional_supervisor_rating = rating
        self.reviewer_rating = rating
    
    # @api.depends(
    #     'administrative_supervisor_rating',
    #     'functional_supervisor_rating',
    #     'reviewer_rating')
    # def compute_weighted_score(self):
    #     for rec in self:
    #         fc_avg_scale = 4 # or 5 is set as default in case nothing was provided
    #         if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
    #             ar = rec.administrative_supervisor_rating * 30
    #             f_rating = 30 if rec.administrative_supervisor_rating > 0 else 60
    #             fr = rec.functional_supervisor_rating * f_rating
    #             rr = rec.reviewer_rating * 40
    #             ratings = (ar + fr + rr) / fc_avg_scale
    #             rec.weighted_score = ratings
    #         else:
    #             rec.weighted_score = 0
    
    # @api.onchange(
    #     'functional_supervisor_rating', 
    #     'administrative_supervisor_rating',
    #     'reviewer_rating'
    #     )
    def validate_rating(self):
        if self.state == 'functional_rating':
            if self.current_assessment_section_id.employee_id.parent_id and self.env.user.id != self.current_assessment_section_id.employee_id.parent_id.user_id.id:
                self.assessment_type = ""
                self.functional_supervisor_rating = False
                # return {
                #     'title': 'User Validation Issue',
                #     'message': "Ops ! You are not entitled to add a rating because you are not the employee's functional manager"
                # }
                raise UserError("Wrong Access !! You are not entitled to add a rating because you are not the employee's functional manager")
        if self.state == 'admin_rating':
            if self.current_assessment_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.current_assessment_section_id.employee_id.administrative_supervisor_id.user_id.id:
                self.assessment_type = ""
                self.administrative_supervisor_rating = False
                # return {
                #     'title': 'User Validation Issue',
                #     'message': "Ops ! You are not entitled to add a rating because you are not the employee's administrative supervisor"
                # }
                raise UserError("Access Error !!! You are not entitled to add a rating because you are not the employee's administrative supervisor")
        if self.state == 'reviewer_rating':
            if self.current_assessment_section_id.employee_id.reviewer_id and self.env.user.id != self.current_assessment_section_id.employee_id.reviewer_id.user_id.id:
                self.assessment_type = ""
                self.reviewer_rating = False
                # return {
                #     'title': 'Security Rule',
                #     'message': """Ops ! You are not entitled to add a rating because you are not the employee's reviewer"""
                # }
                raise UserError("Access Error !!!You are not entitled to add a rating because you are not the employee's reviewer")
            
        # if self.functional_supervisor_rating > 5:
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Functional supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     self.functional_supervisor_rating = False
        #     return {'warning': message}
        # if self.administrative_supervisor_rating > 5:
        #     self.administrative_supervisor_rating = False
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     return {'warning': message}
        # if self.reviewer_rating > 5:
        #     self.reviewer_rating = False
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     return {'warning': message}
    
    
class PotentialSectionLine(models.Model):
    _name = "potential.assessment.section.line"
    _description= "potential appraisal Section lines"

    potential_section_id = fields.Many2one(
        'pms.appraisee',
        string="potential assessment Appraisal"
    )

    name = fields.Char(
        string='Description', 
        )
    desc = fields.Char(
        string='Description', 
        )
    weightage = fields.Float(
        string='Weight (Total 100%)', 
        )
    administrative_supervisor_rating = fields.Integer(
        string='AA Rating', 
        )
    functional_supervisor_rating = fields.Integer(
        string='FA Rating', 
        )
    reviewer_rating = fields.Integer(
        string='Reviewer Ratings',
        ) 
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", default = "draft", readonly=True)
    # , related="potential_section_id.state")
    
    weighted_score = fields.Float(
        string='Weighted (%) Score', 
        store=True,
        # compute="compute_weighted_score"
        )
    section_avg_scale = fields.Integer(
        string='Section Scale',
        help="Takes in the default scale",
        default=5
        )
    assessment_type = fields.Selection([
        ('Low Potential', 'Low Potential'),
        ('Medium Potential', 'Medium Potential'),
        ('High Potential', 'High Potential'),
        ('Ready to go', 'Ready to go'),
        ], string="Choose", default = "", readonly=False)
    
    @api.onchange('assessment_type')
    def onchange_assessment_type(self):
        self.validate_rating()
        if self.assessment_type == 'Low Potential':
            rating = 1
        elif self.assessment_type == 'Medium Potential':
            rating = 2
        elif self.assessment_type == 'High Potential':
            rating = 3
        elif self.assessment_type == 'Ready to go':
            rating = 4 
        else:
            rating = 0
        self.administrative_supervisor_rating = rating
        self.functional_supervisor_rating = rating
        self.reviewer_rating = rating
    
    # @api.depends(
    #     'administrative_supervisor_rating',
    #     'functional_supervisor_rating',
    #     'reviewer_rating')
    # def compute_weighted_score(self):
    #     for rec in self:
    #         fc_avg_scale = 4 # or 5 is set as default in case nothing was provided
    #         if rec.reviewer_rating or rec.administrative_supervisor_rating or rec.functional_supervisor_rating:
    #             ar = rec.administrative_supervisor_rating * 30
    #             f_rating = 30 if rec.administrative_supervisor_rating > 0 else 60
    #             fr = rec.functional_supervisor_rating * f_rating
    #             rr = rec.reviewer_rating * 40
    #             ratings = (ar + fr + rr) / fc_avg_scale
    #             rec.weighted_score = ratings
    #         else:
    #             rec.weighted_score = 0

    # @api.onchange(
    #     'functional_supervisor_rating', 
    #     'administrative_supervisor_rating',
    #     'reviewer_rating'
    #     )
    def validate_rating(self): # potential
        if self.state == 'functional_rating':
            if self.potential_section_id.employee_id.parent_id and self.env.user.id != self.potential_section_id.employee_id.parent_id.user_id.id:
                self.assessment_type = ""
                self.functional_supervisor_rating = False
                # return {
                #     'title': 'User Validation Issue',
                #     'message': "Ops ! You are not entitled to add a rating because you are not the employee's functional manager"
                # }
                raise UserError("Ops ! You are not entitled to add a rating because you are not the employee's functional manager")
        if self.state == 'admin_rating':
            if self.potential_section_id.employee_id.administrative_supervisor_id and self.env.user.id != self.potential_section_id.employee_id.administrative_supervisor_id.user_id.id:
                self.assessment_type = ""
                self.administrative_supervisor_rating = False
                # return {
                #     'title': 'User Validation Issue',
                #     'message': "Ops ! You are not entitled to add a rating because you are not the employee's administrative supervisor"
                # }
                raise UserError("Ops ! You are not entitled to add a rating because you are not the employee's administrative supervisor")
        if self.state == 'reviewer_rating':
            if self.potential_section_id.employee_id.reviewer_id and self.env.user.id != self.potential_section_id.employee_id.reviewer_id.user_id.id:
                self.assessment_type = False
                self.reviewer_rating = False
                # return {
                #     'title': 'Security Rule',
                #     'message': """Ops ! You are not entitled to add a rating because you are not the employee's reviewer"""
                # }
                raise UserError("""Access Error !!! You are not entitled to add a rating because you are not the employee's reviewer""")
            
        # if self.functional_supervisor_rating > 5:
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Functional supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     self.functional_supervisor_rating = False
        #     return {'warning': message}
        # if self.administrative_supervisor_rating > 5:
        #     self.administrative_supervisor_rating = False
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     return {'warning': message}
        # if self.reviewer_rating > 5:
        #     self.reviewer_rating = False
        #     message = {
        #             'title': 'Invalid Scale',
        #             'message': 'Administrative supervisor rating Scale should be in the range of 1 - 5'
        #         }
        #     return {'warning': message}
        

class QualityCheckSectionLine(models.Model):
    _name = "qualitycheck.section.line"
    _description= "Quality checks & due diligence to be done by the HR Team"

    qualitycheck_section_id = fields.Many2one(
        'pms.appraisee',
        string="QC Appraisal"
    )

    date_of_observation = fields.Date(
        string='Date of Observation / Check', 
        )
    observation_comment = fields.Text(
        string='Observation / Comments', 
        )
    action_required = fields.Char(
        string='Action Required', 
        )
    date_of_closed_observation = fields.Date(
        string='Closed Observation', 
        )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('admin_rating', 'Admin Supervisor'),
        ('functional_rating', 'Functional Supervisor'),
        ('reviewer_rating', 'Reviewer'),
        ('wating_approval', 'HR to Approve'),
        ('done', 'Done'),
        ('withdraw', 'Withdrawn'),
        ], string="Status", 
        default = "draft", 
        readonly=True, 
        related="qualitycheck_section_id.state"
        )
    