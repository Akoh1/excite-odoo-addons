# -*- coding: utf-8 -*-
{
    'name': "Employee Salary Grade",

    'summary': """
        This module is to add salary grade for employee and custom fields""",

    'description': """
        This module is to add salary grade for employee and custom fields
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr_work_entry_contract', 'hr_contract'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
