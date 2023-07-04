from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bill_ids = fields.One2many('feeder.customer.details', 'customer_id', string="Bills")
    book_id = fields.Many2one('book.feeder', domain="[('transformer_id','=',transformer_id)]")
    feeder_id = fields.Many2one('feeder.feeder', compute='_compute_feeder_id', inverse='_inverse_book_id_transformer')
    transformer_id = fields.Many2one('feeder.transformer',compute='_compute_transformer_id', inverse='_inverse_book_id', domain="[('feeder_id','=',feeder_id)]")
    marketer = fields.Many2one(related='book_id.marketer_id')
    service_center_id = fields.Many2one(related='book_id.service_center_id')
    customer_class_id = fields.Many2one('customer.class')
    band = fields.Char()
    customer_account = fields.Char()
    old_account_no = fields.Char()
    juice_location_id = fields.Char()

    @api.depends('book_id')
    def _compute_transformer_id(self):
        for partner in self:
            if partner.book_id:
                partner.transformer_id = partner.book_id.transformer_id

    def _inverse_book_id(self):
        for partner in self:
            self.book_id = None

    @api.depends('transformer_id', 'book_id')
    def _compute_feeder_id(self):
        for partner in self:
            if partner.transformer_id or partner.book_id.transformer_id:
                partner.feeder_id = partner.transformer_id.feeder_id or partner.book_id.transformer_id.feeder_id

    def _inverse_book_id_transformer(self):
        for partner in self:
            self.book_id = None
            self.transformer_id = None

class ResDistrict(models.Model):
    _name = 'res.district'

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    loc_state = fields.Char(required=True, string='State')
    book_ids = fields.One2many('book.feeder', 'district_id')
    feeder_ids = fields.One2many('feeder.feeder', 'district_id')
    service_center_ids = fields.One2many('service.center', 'district_id')
    injection_id = fields.Many2one('injection.substation')


class CustomerClass(models.Model):
    _name = 'customer.class'

    name = fields.Char(required=True)