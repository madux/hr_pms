##############################################################################
#    Copyright (C) 2022 MAACH SOFTWARE. All Rights Reserved


{
    'name': 'EEDC Migration Module',
    'version': '14.0.0',
    'author': "Maach media",
    'category': 'HR',
    'summary': '',
    'description': "",
    'depends': ['base'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/import_employee_view.xml',
        'views/config_view.xml',
        
    ],
    "sequence": 3,
    'installable': True,
    'application': True,
}
