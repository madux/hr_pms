##############################################################################
#    Copyright (C) 2021. All Rights Reserved
#    Maach / QIS Solutions

{
    'name': 'HR Performance Mirror Addons',
    'version': '13.0',
    'author': "Maduka Chris Sopulu",
    'summary': 'HR Performance Management to review superiors',
    'depends': ['hr_pms'],
    'description': "HR Performance Management to review superiors",
    "data": [
            'security/security_view.xml',
            'security/ir_rule.xml',
            'security/ir.model.access.csv',
            'views/hr_competency_view.xml',
            'views/hr_competency_config_view.xml',
            'views/linking_reviewer.xml',
            'views/aggregation_view.xml',
            'views/hr_employee_view.xml',
    ],
    'css': [],
    'js': [],
    # 'qweb': [
    #     'static/xml/dashboard.xml',
    # ],
    "active": False,
    'application': True,
    "sequence": 6,
    # "images": ['images/images.jpg'],
    "price": 60,
    "currency": 'EUR',
}
