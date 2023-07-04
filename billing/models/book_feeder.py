from odoo import api, models, fields

class BookFeeder(models.Model):
    _name = "book.feeder"

    name = fields.Char(required=True, string='Book Name')
    code = fields.Char(required=True, string='Book Code')
    # loc_address = fields.Char(required=True, string='Address')
    marketer_id = fields.Many2one('marketer', string='Marketer')
    transformer_id = fields.Many2one('feeder.transformer')
    service_center_id = fields.Many2one('service.center')
    district_id = fields.Many2one('res.district')
    customer_ids = fields.One2many('res.partner', 'book_id')