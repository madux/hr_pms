from odoo import api, models, fields

class MeterDetails(models.Model):
    _name = 'meter.details'

    meter_no = fields.Char(required=True)
    meter_type = fields.Many2one('meter.type')
    meter_make = fields.Many2one('meter.make')
    communications = fields.Selection(
        selection=[
            ('sts','STS'),
            ('amr','AMR'),
            ('bybot', 'ByBot'),
            ('dlms','DLMS'),
            ('elma_otv','Elmar_otv'),
            ('etelem', 'Etelem'),
            ('jps_axis','JPS_Axis'),
            ('mas', 'MAS'),
            ('multispeak','MultiSpeak'),
            ('multispeak_mlp', 'MultiSpeak_MLP'),
            ('nes', 'NES'),
            ('nh', 'NH'),
            ('openway', 'OpenWay'),
            ('none', 'None')
        ]
    )
    tarrif_index = fields.Integer(string='STS TI: Tariff Index')
    factor = fields.Integer()
    units = fields.Selection(
        selection =[
            ('kwh', 'kWh'),
            ('btu', 'Btu'),
            ('kl', 'kL'),
            ('kw', 'kW')
        ]
    )
    customer = fields.Many2one('res.partner')
    meter_capacity = fields.Float()
    no_of_digits = fields.Integer()
    sgc = fields.Char(string='STS SGC')
    stskm = fields.Integer(string='STS KRN Key Revision')
    phases = fields.Integer()
    disconnect = fields.Boolean(default=False, string='Disconnected?')


class MeterDetails(models.Model):
    _name = 'meter.type'

    name = fields.Char(required=True)

class MeterMake(models.Model):
    _name = 'meter.make'

    name = fields.Char(required=True)