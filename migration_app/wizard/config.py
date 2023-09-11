
from odoo import fields, models ,api, _ 


class ImportConfig(models.TransientModel):
    _name = 'hr.import_config'

    name = fields.Char(
        string="Name", 
        )
    email_to_exclude = fields.Text(
        string="Email to exclude", 
        placeholder="example1@gmail.com,example.com"
        )
    active = fields.Boolean(
        string="Active", 
        )
    
      