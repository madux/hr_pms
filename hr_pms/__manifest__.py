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
            'data/mail_data.xml',
            'views/hr_pms_config_view.xml',
            'views/hr_category_view.xml',
            'views/pms_department_view.xml',
            'views/section_view.xml',
            'wizards/post_normalisation_views.xml',
            'wizards/goal_setting_upload_views.xml',
            'views/appraisee_view.xml',
            'views/employee_inherit_view.xml',
            'views/hr_level_category.xml',
            # 'views/hr_employee_public_inherited.xml',
            'views/pms_instruction_view.xml',
            'views/section_line_view.xml',
            'views/assessment_config.xml',
            'views/pms_yr_view.xml',
            'wizards/appraisal_return_view.xml',
            'static/xml/dashboard_action.xml',
            # 'views/employees_import_view.xml',
            'report/pms_appraisal_templates.xml',
            # 'report/pms_appraisal_reports.xml',


    ],
    'css': [],
    'js': [],
    'qweb': [
        'static/xml/dashboard.xml',
    ],
    "active": False,
    'application': True,
    "sequence": 6,
    # "images": ['images/images.jpg'],
    "price": 60,
    "currency": 'EUR',
}
