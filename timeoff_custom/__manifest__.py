# -*- coding: utf-8 -*-
{
    'name': "Timeoff Resume",

    'summary': """
        This module is to enable ability to resume before total timeoff""",

    'description': """
        This module is to enable ability to resume before total timeoff
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_holidays'],

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
