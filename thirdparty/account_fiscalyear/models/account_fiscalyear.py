# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
import pytz
from datetime import timedelta
from datetime import date
import datetime

	
class AccountFiscalYear(models.Model):
	_name = 'account.fiscalyear'
	_description="Fiscal year"
	
	@api.multi
	def _get_default_company(self):
		return self.env.user.company_id.id
	
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', size=6, required=True)
	date_start=fields.Date(string='Start date', required=True)
	date_stop=fields.Date(string='End date', required=True)
	period_ids=fields.One2many('account.period', 'fiscalyear_id', 'Periods')
	company_id=fields.Many2one('res.company', 'Company', default=_get_default_company)
	state=fields.Selection([
		('draft', 'Open'),
		('done', 'Closed'),], string='Status',default='draft', required=True)
	_order = "date_start, id"
	
	def get_au_date(self, dttime):
		_from_date 	= datetime.datetime.strptime(str(dttime),"%Y-%m-%d %H:%M:%S")
		time_zone	= 'Australia/Sydney'
		tz 			= pytz.timezone(time_zone)
		tzoffset 	= tz.utcoffset(_from_date)
		
		dt 	= str((_from_date + tzoffset).strftime("%Y-%m-%d"))
		return dt
		
	def get_au_datetime(self, dttime):
		_from_date 	= datetime.datetime.strptime(str(dttime),"%Y-%m-%d %H:%M:%S")
		time_zone	= 'Australia/Sydney'
		tz 			= pytz.timezone(time_zone)
		tzoffset 	= tz.utcoffset(_from_date)
		
		dt 	= str((_from_date + tzoffset).strftime("%Y-%m-%d %H:%M:%S"))
		return dt
		
	def get_gmt_datetime(self, dttime):
		_from_date 	= datetime.datetime.strptime(str(dttime),"%Y-%m-%d %H:%M:%S")
		time_zone	= 'Australia/Sydney'
		tz 			= pytz.timezone(time_zone)
		
		aware_d = tz.localize(_from_date, is_dst=None)
		dt=aware_d.astimezone(pytz.utc)
		return dt
		
class AccountPeriod(models.Model):
	_name = 'account.period'
	_description="Account period"
	name = fields.Char('Name')
	code = fields.Char('Code', size=12, required=True) 
	special=fields.Boolean('Opening/Closing Period',help="These periods can overlap.")
	date_start=fields.Date(string='Start date', required=True)
	date_stop=fields.Date(string='End date', required=True)
	fiscalyear_id=fields.Many2one('account.fiscalyear', string='Fiscal Year')
	state=fields.Selection([
		('draft', 'Open'),
		('done', 'Closed'),], string='Status',default='draft', required=True)

	_order = "date_start, special desc"

	@api.multi
	def button_close_period(self):
		return self.write({"state":"done"})
	@api.multi
	def button_open_period(self):
		return self.write({"state":"draft"})	
		