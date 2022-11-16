# -*- coding: utf-8 -*-
{
    'name': "Fhfl Sales Custom",

    'summary': """
        custom sales order implementation for fhfl""",

    'description': """
        custom sales order implementation for fhfl
    """,

    'author': "Samuel Akoh <ojima.asm@gmail.com>",
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '14.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sales_team', 'account', 'stock',
                'product', 'crm', 'project', 'sale_crm', 'purchase',
                'account_asset'],

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
        'views/lms.xml',
        'views/help_own.xml',
        'views/crm_sale.xml',
        'views/report_sale_installment.xml',
        'views/account_asset.xml',
        # 'views/purchase.xml',
        'data/create_sequence_number_in_odoo.xml',
        'data/cron.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
