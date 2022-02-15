# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Nigeria - IFRS Accounting',
    'version': '1.1',
    'category': 'Localization/Account Charts',
    'description': """
This is the base module to manage the accounting chart for Nigeria.
==============================================================================

* Chart of Accounts.
 
    """,
    'author': 'erpSOFTapp',
    'depends': [
        'account',
	'account_accountant',
		'base'
        
    ],
    'data': [

 	'data/account_chart_template.xml',
	'data/account.account.template.csv',
	'data/account.chart.template.csv',
	
 	  'data/res.country.state.csv',
	 
       
	
    ],
    'test': [
    
    ],
    'demo': [
        
    ],
    'installable': True,
    'website': 'https://www.erpsoftapp.com',
}
