from odoo import models, fields, api, _
from datetiime import datetime, date 
from odoo.exceptions import ValidationError


class PmsSection(models.Model):
    _name = "pms.section"
    _order = "create_date desc"
    _description = "PMS section"

    """A configuration is made on the section config side. 
    I.e create a section, assign the sections to a specific 
    job category. e.g SNR MGT, MID MGT, JR MGT"""

    name = fields.Char(
        string="Section Name", 
        required=True)

    max_line_number = fields.Float(
        string="Maximum Number of Input"
        )
    
     
    type_of_section = fields.Selection([
        ('KRA', 'KRA'),
        ('LC', 'Leadership Competence'),
        ('FC', 'Functional Competence'),
        ], string="Type of Section", 
        default = "", 
        readonly=False,
        required=False,
        )
    pms_category_id = fields.Many2one(
        'pms.category',
        string="Category"
    ) 
    section_avg_scale = fields.Integer(
        string='Section Scale', 
        required=True,
        help="Used to set default scale",
        store=True,
        )
    input_weightage = fields.Integer(
        string='Weightage (20%)', 
        placeholder="eg. 20",
        default=1,
        help="Used to set default weight for appraisee",
        store=True,
        )
    section_line_ids = fields.One2many(
        "pms.section.line",
        "section_id",
        string="Section Lines"
    )
    # consider removing or make invisible N/B not to be used
    weighted_score = fields.Integer(
        string='Section Weighted', 
        placeholder="eg. 35",
        required=False,
        )
    
    @api.constrains('job_roles')
    def _check_lines(self):
        """Checks if no section line is added and max line is less than 1"""
        if not self.mapped('section_line_ids') and self.max_line_number < 1:
            raise ValidationError(
                'You must provide the lines or set the maximum number to above 0'
                )
        if self.weighted_score < 1:
            raise ValidationError(
                """Section weight must be set above 0%"""                )

    