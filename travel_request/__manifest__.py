# -*- coding: utf-8 -*-
{
    'name': "Travel Request Custom",

    'summary': """
        To enable Travel Request functionality""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Samuel Akoh <ojima.asm@gmail.com>",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'fhfl_sales_custom'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
