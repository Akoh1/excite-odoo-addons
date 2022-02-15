# -*- coding: utf-8 -*-
{
    'name': "Fhfl Sales Custom",

    'summary': """
        custom sales order implementation for fhfl""",

    'description': """
        custom sales order implementation for fhfl
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sales_team', 'account', 'stock',
                'product', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_order.xml',
        'views/account_invoice.xml',
        'views/report_invoice_templates.xml',
        'views/product.xml',
        'views/crm.xml',
        'views/res_config.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
