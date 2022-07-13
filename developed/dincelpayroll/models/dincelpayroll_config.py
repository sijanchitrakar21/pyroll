# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from time import gmtime, strftime
from datetime import datetime, timedelta
from . import dincelpayroll_vars 
import math
import logging
_logger = logging.getLogger(__name__)

class DincelPayrollAccountSettings(models.Model):
	_inherit = 'dincelaccount.settings'
	
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	timesheet_app	= fields.Selection(dincelpayroll_vars.PAYSLIP_APP_OPTIONS, 'Timesheet app') 
	rounding_id 	= fields.Many2one('dincelpayroll.rounding', string='Rounding')
	api_publish 	= fields.Selection(dincelpayroll_vars.API_PUBLISH_OPTIONS, 'API Publish') 
	
	def get_config(self):
		#config =self.env['dincelpayroll.config']  
		config = self.search([], limit=1)
		return config
		
	def get_api_publish(self):
		config = self.get_config()
		if config:
			return config.api_publish	
		else:
			return None
			
	def get_timesheet_app(self):
		config = self.get_config()
		if config:
			return config.timesheet_app	
		else:
			return None
			
	def get_payfrequency(self):
		#config =self.env['dincelpayroll.config']  
		#config = self.search([], limit=1)
		config = self.get_config()
		if config.payfrequency_id:
			return config.payfrequency_id.id	
		else:
			return None
			
	def get_rounding(self):
		config = self.get_config()
		if config.rounding_id:
			return config.rounding_id	
		else:
			return None
'''			
class DincelPayrollConfig(models.Model):
	_name = 'dincelpayroll.config'
	_description	= "Payroll Config"
	name 			= fields.Char('Name')
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	timesheet_app	= fields.Selection(dincelpayroll_vars.PAYSLIP_APP_OPTIONS, 'Timesheet app') 
	rounding_id = fields.Many2one('dincelpayroll.rounding', string='Rounding')
	
	def get_config(self):
		#config =self.env['dincelpayroll.config']  
		config = self.search([], limit=1)
		return config
		
	def get_timesheet_app(self):
		config = self.get_config()
		if config:
			return config.timesheet_app	
		else:
			return None
			
	def get_payfrequency(self):
		#config =self.env['dincelpayroll.config']  
		#config = self.search([], limit=1)
		config = self.get_config()
		if config.payfrequency_id:
			return config.payfrequency_id.id	
		else:
			return None
			
	def get_rounding(self):
		config = self.get_config()
		if config.rounding_id:
			return config.rounding_id	
		else:
			return None
'''		
class DincelPayrollRounding(models.Model):
	_name = 'dincelpayroll.rounding'	
	_description	= "Payroll Rounding"
	name 			= fields.Char('Name')	
	trigger 		= fields.Float('Trigger (mins)')
	round_back 		= fields.Float('Round Back/Interval (mins)')
	
class DincelPayrollSequence(models.Model):
	_name = 'dincelpayroll.sequence'	
	_description	= "Payroll Sequence"
	name 			= fields.Char('Name')	
	code			= fields.Char('Code')
	date 			= fields.Date('Date')
	next_number		= fields.Integer('Next Number')
	
	def get_next_number_bydate(self, code):
		next_number=None
		#sql="select max(next_number) as next from dincelpayroll_sequence where code='%s'" % (code)
		#self.env.cr.execute(sql)	
		#rs2 = self.env.cr.dictfetchall()
		#for row in rs2:
		#	if row.get('next'):
		#		next_number = row.get('next')
		#items = self.env['hr.employee.attendance'].search([('employee_id', '=', employee.id),('dayofweek', '=', 0)], limit=1) #dayofweek=0=monday 
		today = datetime.today()
		items = self.search([('code', '=', code),('date', '=', today)], limit=1) #dayofweek=0=monday 
		for item in items:
			next_number=item.next_number
			vals={'next_number':next_number+1}
			item.write(vals)
		if not next_number:
			next_number=1
			vals={'name': code,'code': code,'date': today,'next_number':next_number+1}
			self.create(vals)
		return next_number		