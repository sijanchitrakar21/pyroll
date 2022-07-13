# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import logging
#import base64
#import csv
#from io import StringIO
from datetime import date, datetime, timedelta
import datetime as dt
#from datetime import date
#from datetime import datetime
#import datetime
import dateutil
from dateutil import parser
#import pyexcel as pe

_logger = logging.getLogger(__name__)

class PayrollGenerate(models.TransientModel):
	_name = 'hr.payroll.generate'
	_description = 'Payroll generate'

	individual = fields.Boolean("Individual", default=False) 
	group_id = fields.Many2one('hr.employee.group', string='Employee Group')	
	paydate = fields.Date('Pay Date')
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	employee_lines = fields.One2many('hr.employee.line','payroll_id', string='Employees')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	check_all = fields.Boolean("Check All", default=True)
	
	'''
	@api.multi
	def get_todate(self, code, dt):
		dt2=dt
		if dt:
			if code=="week":
				dt2
			elif code=="fortnight":
			elif code=="month":
		return dt2'''
		
 
		
	@api.onchange('check_all')
	def _onchange_check_all2(self):
		#if self.check_all:
		#if 'employee_lines' in vals:
		#    employee_lines = self.resolve_2many_commands('employee_lines', vals['employee_lines'])
		#else:
		employee_lines = self.employee_lines
		for line in employee_lines:	
			line['selected']= self.check_all
		return {'value': {'employee_lines': employee_lines}}
		
	@api.onchange('payfrequency_id')
	@api.onchange('date_to')
	def _onchange_payfrequency(self):
		if self.payfrequency_id and self.date_to:
			code=self.payfrequency_id.code 
			_reverse=True
			dt=self.env['hr.payslip.run'].calculate_end_date(code, self.date_to, _reverse)	
			values = {
				'date_from': dt,
			}
			return {'value':values} 
			
	@api.onchange('paydate')
	def _onchange_paydate(self):
		if self.paydate:
			values = {
				'date_to': self.paydate,
			}
			return {'value':values} 
		
	@api.onchange('group_id')
	def _onchange_group(self):
		ret=False
		_lines=[]
		if self.group_id:
			if self.group_id.code=="ALL":
				ids1 = self.env['hr.employee'].search([('active', '=', True)])
			else:
				ids1 = self.env['hr.employee'].search([('active', '=', True),('x_group_id', '=', self.group_id.id)])
				if self.group_id.code=="individual":
					ret=True
			for emp in ids1:
				_lines.append({'employee_id':emp.id,'selected':True,})
			
		values = {
			'employee_lines': _lines,
			'individual': ret,
			'check_all': True,
		}
		#_logger.error('_onchange_individual_onchange_individual values[ %s ][ %s ]',self.group_id, values)
		return {'value':values} 
	 
	@api.multi
	def button_payslip_create(self):
		var1=""
		str1=""
		count1=0
		payslip=None
		paydate=self.paydate
		date_from=self.date_from
		date_to=self.date_to
		date_to=parser.parse(date_to)
		date_from=parser.parse(date_from)
		_batch="%s-%s" % (date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"))
		#_number=_batch
		_number=self.env['ir.sequence'].next_by_code('payslip.ref')
		
		
		if self.individual and self.employee_id:
			#dt = date_from
			chequeno=_number.replace("SLIP/","")
			vals = {'date': paydate,
					'employee_id': self.employee_id.id,
					'x_payfrequency_id': self.payfrequency_id.id,
					'name':_number,#"Payslip %s - %s" % (self.date_from, self.date_to),
					'date_from': self.date_from,
					'date_to': self.date_to,
					'x_batch':_batch,
					'number':_number,
					'x_chequeno':chequeno,
					#'x_group_id':self.group_id.id,
				}
			if self.employee_id.x_group_id:
				vals['x_group_id']=self.employee_id.x_group_id.id
						
			payslip = self.env['hr.payslip'].create(vals)
			
			self._create_timesheet(payslip,  self.employee_id, date_from , date_to)
			
			count1+=1
					
			if payslip:
				self.env['hr.payslip'].calculate_summary(payslip.id)
		else:
			for row in self.employee_lines:
				 
				if row.selected: 
					vals = {'date': paydate,
							'employee_id': row.employee_id.id,
							'x_payfrequency_id': self.payfrequency_id.id,
							'name':"Payslip %s - %s" % (self.date_from, self.date_to),
							'date_from': self.date_from,
							'date_to': self.date_to,
							'x_batch':_batch,
							'number':_number,
							'x_group_id':self.group_id.id,
						}
						
								
					payslip = self.env['hr.payslip'].create(vals)
					self._create_timesheet(payslip,  row.employee_id, date_from , date_to)
					count1+=1
							
					if payslip:
						self.env['hr.payslip'].calculate_summary(payslip.id)
						
		if payslip:#count1>0:
			value = {
				'type': 'ir.actions.act_window',
				'name': _('Payslips'),
				'view_type': 'form',
				'view_mode': 'tree,form',
				'res_model': 'hr.payslip',
				'domain':[('number','=',_number)],
				'context':{},#{'search_default_partner_id': partner_id},
				'view_id': False,#view_id,
			}

			return value
			
	def _create_timesheet(self, payslip,  employee, date_from , date_to):
		dt = date_from
		amt_pc_loading=0
		loading_type=""
		group=None
		if employee.x_group_id:
			group=employee.x_group_id
			for line in group.category_ids:
				if line.code=="S-NSL":#summary night shift loading
					loading_type=line.subtype
					amt_pc_loading=line.pc_amt
				
		#if row.employee_id.x_pay_basis and row.employee_id.x_pay_basis=="H":#hourly pay basis 
		while dt <= date_to:
			_vals2 = {
				'name': dt.strftime("%a"),
				'date': dt,
				'employee_id':employee.id,
				'unit_amount': 0,
				'amount': 0,
				'ref': 0,
				'payslip_id':payslip.id
				}
			if group:
				
				for line in group.attendance_ids:
					if dt.strftime("%w") == line.dayofweek:#0/1/2/3
						if line.hour_from:
							_vals2['time_in'] 	= 	line.hour_from
						if line.hour_to:
							_vals2['hour_to'] 	= 	line.hour_to	
							
						_vals2['break_unpaid']	=	line.meal_unpaid
						_vals2['break_paid']	=	line.paid_meal
						_vals2['hrs_normal']	=	line.normal_pay
						_vals2['hrs_t15']		=	line.paid_t15
						_vals2['hrs_t20']		=	line.paid_t20
						
						if line.normal_pay > 0.0:
							if loading_type == "2":#night shift loading....
								_vals2['rate_loading']		=	amt_pc_loading
							if group.category_id:
								_vals2['category_id']=	group.category_id.id
						else:
							if group.nopay_id:
								_vals2['category_id']=	group.nopay_id.id
						#else:
							
						break
			#_logger.error('employee_linesemployee_lines _vals2[ %s ]attendance_ids[ %s ]',_vals2, group)			
			timesheet = self.env['hr.payslip.timesheet'].create(_vals2) #create the time data
			
			dt=dt+  timedelta(days = 1) #next day...
						
		return True			 
		#_logger.error('employee_linesemployee_lines count1count1[ %s ]paydate[ %s ]',count1, paydate)					
		#raise UserError(_("Warning if needed. [%s] [%s]count1[%s]" %  (count2, str1, count1)))
class PayrollEmployeeLine(models.TransientModel):
	_name = 'hr.employee.line'
	_description = 'Employee line'
	payroll_id = fields.Many2one('hr.payroll.generate', string='Payroll')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	selected = fields.Boolean("Select", default=True) 
	
	