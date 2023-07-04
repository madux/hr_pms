from odoo import models, fields, api

class InjectionSubstation(models.Model):
    _name = 'injection.substation'

    name = fields.Char(required=True, string='Injection Substation')
    address = fields.Char(required=True)
    code = fields.Char(required=True, string='Substation_code')
    district_ids =  fields.One2many('res.district', 'injection_id', string='Districts')
    feeder_ids = fields.One2many('feeder.feeder', 'injection_id', string='Feeders')