# -*- coding: utf-8 -*-
{
    'name': "Smart KPI",

    'summary': """
        Manages KPI Setup and appraisal workflow for FHFL""",

    'description': """
        This module manages KPI Setup and appraisal workflow. It allows the Managers to do 
        the scoring and recommendation for an Appraisee. This is for FHFL.
    """,

    'author': "Ifeoluwa",
    'website': "https://www.tunnox.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/smart_kpi_menu.xml',
        'views/smart_kpi_view.xml',
        'views/smart_kpi_factor.xml',
        'views/kpi_deadline_view.xml',
        'views/kpi_grade.xml',
        'views/smart_kpi_biz.xml',
        'views/kra_report.xml',
        'views/templates.xml',
        'data/email_data.xml',
        'data/sequence.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
