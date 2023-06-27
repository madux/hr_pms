##############################################################################
#    Copyright (C) 2021. All Rights Reserved
#    Enugu Electricity Distribution Company

{
    'name': 'Billing System',
    'version': '14.0',
    'author': "Maduka Chris Sopulu, Paul Ugwu",
    'summary': 'Billing System: To enable the the generation  of bills for individuals',
    'depends': ['base'],
    'description': "Billing System",
    "data": [
            'security\security_view.xml',
            #'security/ir_rule.xml',
            'security\ir.model.access.csv',
            #'data/data.xml',
            'views/res_partner_views.xml',
            # 'views/feeder_views.xml',

    ],
    'application': True,
    "sequence": 6,
}
