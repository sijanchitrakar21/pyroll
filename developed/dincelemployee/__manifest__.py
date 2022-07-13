# -*- coding: utf-8 -*-
{
	'name': 'Dincel Employee',
	'version': '1.01',
	'website': 'https://www.dincel.com.au',
	'category': 'Employee',
	'author':'Shukra Rai',
	'summary': 'Employee portal, leave, payslips, etc',
	'description':'Employee portal, leave, payslips, etc',
	'depends': ['account','hr', 'analytic','account_fiscalyear'], #for referencing in many2one relationship
	'data': [
		'employee_views.xml',
		'menu_items.xml',
	],
	'installable': True,
	'auto_install': False,
}
