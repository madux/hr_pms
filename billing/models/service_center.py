from odoo import api, models, fields

class ResDistrict(models.Model):
    _name = "service.center"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    loc_address = fields.Char(required=True, string='Address')
    injection_id = fields.Many2one('injection.substation')
    oms = fields.Many2one('hr.employee', string='OMS')
    book_feeder_ids = fields.One2many('book.feeder', 'service_center_id', string='Books')
    district_id = fields.Many2one('res.district')