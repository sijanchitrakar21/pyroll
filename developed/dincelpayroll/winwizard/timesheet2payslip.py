# -*- coding: utf-8 -*-
#https://www.slideshare.net/TaiebKristou/odoo-icon-smart-buttons
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import logging
import base64
import csv
from odoo.addons.dincelpayroll.models import dincelpayroll_vars 
#from io import StringIO
#from datetime import date, datetime, timedelta
#import datetime as dt
from datetime import date
from datetime import datetime
from datetime import timedelta
import datetime
#from datetime import date
#from datetime import datetime
#import datetime
import dateutil
from dateutil import parser
#import pandas
import xlrd
import os
from odoo.tools.config import config
_logger = logging.getLogger(__name__)

 		
class Timesheet2Payslip(models.TransientModel):
	_name = 'hr.timesheet2payslip'
	_description = 'Timesheet 2 payslip'
	paydate = fields.Date('Pay Date')
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	lines = fields.One2many('hr.timesheet2payslip.line','timesheet_id', string='Employees')
	qty=fields.Integer("Qty test",default=lambda self: self._get_init_qty(),)
	
	def _get_init_qty(self):
		return 1
		
	@api.onchange('qty')
	def _onchange_qty(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids', []) or []
		_lines=[]
		paydate=None
		date_from=None
		date_to=None
		payfrequency_id=None
		
		for line in active_ids:
			copy	=self.env['hr.timesheet.import.copy'].browse(line)
			if not paydate:
				paydate=copy.date
			if not payfrequency_id:
				payfrequency_id=copy.payfrequency_id.id
			if not date_from:
				date_from=copy.date_from
			if not date_to:
				date_to=copy.date_to	
			_lines.append({'import_id':line,'employee_id':copy.employee_id.id,'emp_number':copy.employee_id.x_emp_number})
		value={'lines': _lines}
		if paydate:
			value['paydate']=paydate
		if payfrequency_id:
			value['payfrequency_id']=payfrequency_id
		if date_from:
			value['date_from']=date_from
		if date_to:
			value['date_to']=date_to	
		return {'value': value}
		
	
	@api.multi
	def button_ts2payslip_create(self):
		
		return self.import_timesheet_copy()
	
	def import_timesheet_copy(self):
		ids=[]
		var1		=""
		str1		=""
		count1		=0
		payslip		=None
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		
		#emp_arr		= []
		obj_payslip	= self.env['hr.payslip']
		obj_time	= self.env['hr.employee.timesheet']
		obj_leave	= self.env['hr.payslip.leave']
		user_id		= self.env.user.id
		
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		period_id 	= self.env['account.period'].finds(paydate)
		fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
		_config		= self.env['dincelaccount.settings'].load_default()
		
		for line in self.lines:
			count1+=1	
			payslip		= None
			employee	= line.employee_id
			employee_id	= employee.id
			vals = {'date': paydate,
					'employee_id': employee_id,
					'x_payfrequency_id': self.payfrequency_id.id,
					'date_from': self.date_from,
					'date_to': self.date_to,
					'x_is_timesheet':True,
				}
			if employee.x_group_id:
				vals['x_group_id'] =	employee.x_group_id.id
			if fiscal_id:
				vals['x_fiscal_id'] =	fiscal_id
			
			if _config:
				vals['x_clearing_account_id']	=	_config.payroll_clearing_code.id
			if line.import_id:
				vals['x_time_import_id']	=	line.import_id.id
			items 		= obj_payslip.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
			if len(items) > 0:
				for item in items:
					item.write(vals)
					payslip = item
			else:
				_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
				vals['name']=_number#"%s %s - %s" % (_number, self.date_from, self.date_to)
				vals['number']=_number
				vals['x_chequeno']=_number.replace("SLIP/","")
				payslip = self.env['hr.payslip'].create(vals)
			if payslip:
				self.env['hr.timesheet.import.copy'].update_payslip_from_ts(payslip, line.import_id)
				ids.append(payslip.id)
				
				
				
				'''
				#---------------------------------
				#timesheet------------------------
				#---------------------------------
				for item in line.import_id.line_ids:
					_vals={
						'employee_id': employee_id,
						'category_id': item.category_id.id,
						'hrs': item.hrs,
						'hrs_net': item.hrs_net,
						'xfactor': item.xfactor,
						'date': item.date,
						'name': item.name,
						'payslip_id': payslip.id,
						'reversed':False,
						}
					lineitems 	= obj_time.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',item.category_id.id),('date','=',item.date)])	
					if len(lineitems)>0:
						for item in lineitems:
							item.write(_vals)
					else:
						obj_time.create(_vals)
				#---------------------------------
				#leaves---------------------------
				#---------------------------------	
				for item in line.import_id.leave_ids:
					_vals={
						'employee_id': employee_id,
						'category_id': item.category_id.id,
						'tot_hrs': item.tot_hrs,
						'date': item.date,
						'date_from':item.date_from,
						'date_to':item.date_to,
						'holiday_id': item.holiday_id.id,
						'payslip_id': payslip.id,
						'reversed':False,
						}
					lineitems 	= obj_leave.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',item.category_id.id), ('date','=',item.date), ('holiday_id','=',item.holiday_id.id)])	
					if len(lineitems)>0:
						for item in lineitems:
							item.write(_vals)
					else:
						obj_leave.create(_vals)	 
				#---------------------------------------
				self.env['hr.payslip'].calculate_payslip(payslip)	
				ids.append(payslip.id)
				
				#---------------------------------------
				#line.write({"state":'done'})
				line.import_id.write({"state":'done'})
				#---------------------------------------'''
				
		 
		value = {
			'type': 'ir.actions.act_window',
			'name': _('Payslips'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.payslip',
			'domain':[('id','in',ids)],
			'context':{},#{'search_default_partner_id': partner_id},
			'view_id': False,#view_id,
		}

		return value
		
	def _create_timesheet(self, payslip,  employee, date_from , date_to):
		dt 				= date_from
		amt_pc_loading	= 0
		loading_type	= ""
		group			= None
		obj_time		= self.env['hr.employee.timesheet']		
		
		while dt <= date_to:
			
			_vals={
				'employee_id':employee.id,
				'xfactor':1,
				'date':dt,
				'name': dt.strftime("%a"),
				'payslip_id': payslip.id,
				}
			#_found=False	
			if employee.x_group_id:
				for line in employee.x_group_id.attendance_ids:
					if (int(line.dayofweek)-dt.weekday())==0:
						_vals['hrs']		=	line.normal_pay
						_vals['hrs_net']	=	line.normal_pay
						if line.category_id:
							_vals['category_id']=	line.category_id.id
						break	
			
			obj_time.create(_vals)
			dt=dt+  timedelta(days = 1) #next day...	
		return True	
	 	 
		
class Timesheet2PayslipLine(models.TransientModel):
	_name = 'hr.timesheet2payslip.line'
	_description = 'Employee line'
	timesheet_id = fields.Many2one('hr.timesheet2payslip', string='Payroll')
	import_id = fields.Many2one('hr.timesheet.import.copy', string='Timesheet')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	emp_number = fields.Char(related='employee_id.x_emp_number')
	
	
	