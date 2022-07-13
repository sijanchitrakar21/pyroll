from odoo import models, fields, api, _
from datetime import datetime, timedelta
import datetime as dt
import time
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class DincelAccountPayrollSettings(models.Model):
	_name = "dincelaccount.settings"
	_description = "Payroll Account Settings"
	name = fields.Char('Name')
	payroll_clearing_code = fields.Many2one('account.account', string='Clearing/Payment Account')	
	payroll_liability_id = fields.Many2one('account.account', string='Default Payroll Liability Account')	
	wage_expense_id = fields.Many2one('account.account', string='Wages Expense Account')	
	super_liability_id = fields.Many2one('account.account', string='Super Liability Account')	
	super_expense_id = fields.Many2one('account.account', string='Super Expense Account')	
	leave_personal_id = fields.Many2one('account.account', string='Personal Leave')	
	leave_annual_id = fields.Many2one('account.account', string='Annual Leave')	
	tax_account_id = fields.Many2one('account.account', string='PAYG Tax/Liability Account')	
	pay_bank_id = fields.Many2one('res.bank', string='Default Payment Bank')	
	pay_descr = fields.Char('Pay Description')
	lsl_rule_ids = fields.One2many('dincelaccount.lsl.rule', 'settings_id', 'LSL Rules', auto_join=True)	
	odoo_tmp_folder= fields.Char('Odoo Temp Folder')
	scan_ts_file= fields.Char('Timesheet Scan File', help="Default filename is ta.dat at /var/tmp-odoo/timesheet/ta.dat")
	
	@api.multi
	def unlink(self):
		if self.id:
			raise UserError(_('You cannot delete this due to system requirement issue.'))
		return super(DincelAccountPayrollSettings, self).unlink()
		
	def load_default(self):
		items		= self.search([], limit=1) 
		for _obj in items:
			return _obj
		return False
		
	def get_scan_ts_file(self):
		_obj		= self.load_default()
		if _obj:
			return _obj.odoo_tmp_folder + "" + _obj.scan_ts_file
		else:	
			return "/var/tmp-odoo/timesheet/ta.dat"	
		
	def get_odoo_tmp_folder(self):
		_obj		= self.load_default()
		if _obj:
			return _obj.odoo_tmp_folder
		return "/var/tmp/tmp-odoo"	
		
	def is_time_format(self, input):
		try:
			time.strptime(input, '%H:%M')
			return True
		except ValueError:
			return False
		
class DincelAccountLSLRule(models.Model):
	_name = "dincelaccount.lsl.rule"
	_description = "Payroll Long Service Leave"
	min_years = fields.Float('Min Years')
	settings_id = fields.Many2one('dincelaccount.settings', string='Account Settings')	
	state_id = fields.Many2one('res.country.state', string='State')
	