##############################################################################
#    Copyright (C) 2021. All Rights Reserved
#    Maach / QIS Solutions

{
    'name': 'HR Performance Management',
    'version': '13.0',
    'author': "Maduka Chris Sopulu / QIS Solution",
    'summary': 'HR Performance Management: To enable users generate PMS for employees',
    'depends': ['base','hr'],
    'description': "HR Performance Management",
    "data": [
            'security/security_view.xml',
            'security/ir_rule.xml',
            'security/ir.model.access.csv',
            'data/data.xml',
            'views/hr_pms_config_view.xml',
            'views/hr_category_view.xml',
            'views/pms_department_view.xml',
            'views/section_view.xml',
            'views/appraisee_view.xml',
            'views/employee_inherit_view.xml',
            'views/employee_import_view.xml'
    ],
    'css': [],
    'js': [],
    'qweb': [],
    "active": False,
    'application': True,
    "sequence": 6,
    "images": ['images/images.jpg'],
    "price": 60,
    "currency": 'EUR',
}
