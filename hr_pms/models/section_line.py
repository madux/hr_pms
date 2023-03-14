from odoo import models, fields, api, _
from datetiime import datetime, date 
from odoo.exceptions import ValidationError


class PMS_SectionLine(models.Model):
    _name = "pms.section.line"
    _description= "Section lines"

    name = fields.Char(
        string="Description", 
        required=True)
    is_required = fields.Boolean(
        string="Is required", 
        default=False
        )

    section_id = fields.Many2many(
        'pms.section', 
        string="Section ID"
        )
      