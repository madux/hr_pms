from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    bill_ids = fields.One2many('feeder.customer.details', 'customer_ids')
