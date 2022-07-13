# -*- coding: utf-8 -*-
{
	'name': 'Dincel Payroll Web',
	'version': '1.00',
	'website': 'https://www.odoo.com/page/community-builder',
	'category': 'Website',
	'author':'Shukra Rai',
	'summary': 'Dincel Payroll Web',
	'description':'Dincel Payroll Web',
	'depends': ['website'], #for referencing in many2one relationship #'account', 'hr', 'project', 'sale_timesheet', 'hr_timesheet', 'analytic', 'account_fiscalyear', 'hr_holidays
	'data': [
		'dincelweb_menu.xml',
		'dincelweb_views.xml',
		'dincelweb_templates.xml',
		'security/ir.model.access.csv',
		'security/staff_security.xml',
		],
	'installable': True,
	'auto_install': False,
}
