# -*- coding: utf-8 -*-
{
	'name': 'Dincel Account',
	'version': '1.02',
	'website': 'https://www.dincel.com.au',
	'category': 'Payroll Account',
	'author':'Shukra Rai',
	'summary': 'Payroll Account',
	'description':'Dincel Payroll Account',
	'depends': ['account','account_fiscalyear'], #for referencing in many2one relationship
	'data': [
		'dincelaccount_menu.xml',
		'dincelaccount_views.xml',
		'res_config.xml',
		],
	'installable': True,
	'auto_install': False,
}
