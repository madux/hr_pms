from odoo import models, fields, api, _
from datetime import datetime, date 
from odoo.exceptions import ValidationError


class PMS_SectionLine(models.Model):
    _name = "pms.section.line"
    _description= "Section lines"

    name = fields.Char(
        string="Title", 
        required=True)
    description = fields.Char(
        string="KBA Description", 
        required=False)
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )

    section_id = fields.Many2one(
        'pms.section', 
        string="Section ID"
        )
      