# -*- coding: utf-8 -*-
{
    'name': "Employee Onboarding Form",

    'summary': """
        This module handles the printing form for employee missing field""",

    'description': """
        This module handles the printing form for employee missing field
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_recruitment', 'web', 'mail',
                'hr_appraisal'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
