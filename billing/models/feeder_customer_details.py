from odoo import models, fields, api


class FeederCustomerDetails(models.Model):
    _name = 'feeder.customer.details'

    transformer_id = fields.Many2one('feeder.transformer')
    feeder_id = fields.Many2one('feeder.feeder')
    reading_id = fields.Many2one('feeder.reading')
    x_invoice = fields.Integer(string="Invoice ID")
    user_class_id = fields.Many2one('feeder.class', string='Class')
    #user_tarrif = fields.Many2one('feeder.extension', string='New tarrif')
    tarrif_name =  fields.Char()
    tarrif_rate = fields.Integer()
    customer_ids = fields.Many2one('customer.billing.details')
    prev_balance = fields.Float()
    last_payment = fields.Float()
    net_arreas = fields.Float()
    prev_read = fields.Float()
    current_read = fields.Float()
    number_class = fields.Integer()
    e_month = fields.Selection( 
        selection=[
            ('Jan', 'January'),
            ('feb', 'February'),
            ('Mar', 'March'),
            ('apr', 'April'),
            ('may', 'May'),
            ('jun', 'June'),
            ('Jul', 'July'),
            ('aug', 'August'),
            ('sep', 'September'),
            ('oct', 'October'),
            ('nov', 'November'),
            ('dec', 'December'), 
        ],
        string='Month',
    )
    e_year = fields.Integer(string='Year')
    consumed = fields.Float(string='Consumed(KWH)')
    adjustment = fields.Float()
    discount = fields.Float()
    amount = fields.Float()
    e_type = fields.Selection(
        selection=[
            ('public_dss', 'Public DSS'),
            ('dt_meter_reading', 'DT Meter Reading'),
            ('md_meter_reading', 'MD Meter Reading'),
            ('md_measured_bulk_reading', 'MD_Measured_Bulk_Reading'),
            ('metered_bulk_reading', 'Metered Bulk Reading'),
        ],
        string='Type',
    )
    vat = fields.Float()
    month_due = fields.Float()
    total_due = fields.Float()


    class FeederTransformer(models.Model):
        _name = 'feeder.transformer'

    
    class FeederFeeder(models.Model):
        _name = 'feeder.feeder'

    
    class FeederReading(models.Model):
        _name = 'feeder.reading'

    class FeederClass(models.Model):
        _name = 'feeder.class'