# -*- coding: utf-8 -*-
{
    'name': "Appraisal Custom",

    'summary': """
        Custom module for Appraisal module""",

    'description': """
        Custom module for Appraisal module
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_appraisal'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/views.xml',
        'views/templates.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
