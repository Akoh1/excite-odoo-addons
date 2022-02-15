# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mail Enterprise',
    'category': 'Productivity/Discuss',
    'depends': ['mail'],
    'description': """
Bridge module for mail and enterprise
=====================================

Display a preview of the last chatter attachment in the form view for large
screen devices.
""",
    'data': [
        'views/mail_enterprise_templates.xml',
    ],
    'qweb': [
        'static/src/bugfix/bugfix.xml',
        'static/src/xml/mail_enterprise.xml',
    ],
    'auto_install': True,
    'license': 'OEEL-1',
}
