# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from time import gmtime, strftime
from datetime import datetime, timedelta
import datetime as dt
from dateutil import parser
from dateutil.relativedelta import relativedelta
from . import dincelpayroll_vars 
from odoo.exceptions import UserError
#import datetime
import re
import time #for time:time
from PyPDF2 import PdfFileWriter, PdfFileReader
#from dateutil import parser
import base64
import io
import os.path
from odoo.http import request
import subprocess
from subprocess import Popen, PIPE, STDOUT
import logging
_logger = logging.getLogger(__name__)
'''
PAY_FREQUENCY_OPTIONS=[
			('week', 'Weekly'),
			('fortnight', 'Fortnightly'),
			('month', 'Monthly'),
			]	
			
PAY_CATEGORY_OPTIONS=[
		('allowance', 'Allowance'),
		('deduction', 'Deduction'),
		('wage', 'Wage'),
		('entitle', 'Entitlements'),
		('leave', 'Leaves'),
		('tax', 'TAX'),
		('super', 'Super'),
		] 
'''
#-----------------------------------------------------------------------------------------------------------
#https://www.ato.gov.au/Rates/Schedule-1---Statement-of-formulas-for-calculating-amounts-to-be-withheld/
#-----------------------------------------------------------------------------------------------------------		
#_inherit = ['mail.thread']
class DincelPayslipEmployee(models.Model):
	_name = 'hr.payslip'
	_inherit = ['hr.payslip', 'mail.thread']	
	#_inherit = ['mail.thread']	
	#x_date = fields.Date(string='Date', default=datetime.today())
	date = fields.Date('Payment Date',) #see in module "hr_payroll_account "
	x_batch = fields.Char('Batch')
	x_chequeno= fields.Char('Cheque No')
	x_type = fields.Selection(dincelpayroll_vars.PAY_FREQUENCY_OPTIONS, string='Payment Type') 
	x_payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	x_timesheet_ids = fields.One2many('hr.payslip.timesheet','payslip_id', string='Timesheet Summary', copy=True, auto_join=True)
	x_timesheet_ids2 = fields.One2many('hr.employee.timesheet', 'payslip_id', 'Timesheet Lines', copy=True, auto_join=True)	
	x_summary_ids = fields.One2many('hr.payslip.summary','payslip_id', string='Pay Summary')
	x_ytd_ids = fields.One2many('hr.payslip.ytd','payslip_id', string='YTD Summary')
	x_payment_ids = fields.One2many('hr.payslip.payline','payslip_id', string='Other Payments')
	#x_group_id = fields.Many2one('hr.employee.group', string='Employee Group')	
	x_super_amt = fields.Float("Super Accrued")	
	x_annual_leave = fields.Float("Accrued Annual Leave (hrs) - This pay", digits=(10, 3))	
	x_sick_leave = fields.Float("Accrued Personal Leave (hrs) - This pay", digits=(10, 3))	
	x_lsl_leave = fields.Float("Accrued Long Service Leave Accrued (hrs) - This pay", digits=(10, 3))	
	x_tax_amt = fields.Float("Tax amount")	
	x_gross_amt = fields.Float("Gross Taxable amount")	
	#x_taxable_amt = fields.Float("Taxable amount")	
	#x_gross_taxable = fields.Float("Gross Taxable")	
	x_net_amt = fields.Float("Net amount")	
	x_lsl_enable = fields.Boolean("Long Service Enabled", compute='_lsl_enabled')
	x_printed = fields.Boolean("Printed")
	x_emailed = fields.Boolean("Emailed")
	x_email_que = fields.Boolean("Email Queue")
	x_clearing_account_id= fields.Many2one('account.account', string='Clearing Account')	
	x_journal_ids = fields.One2many('account.move', 'x_payslip_id', string='Journals')
	x_leave_ids = fields.One2many('hr.payslip.leave', 'payslip_id', string='Leaves')
	x_fiscal_id = fields.Many2one('account.fiscalyear', string='Fiscal year')
	x_gross_ytd	= fields.Float(string="YTD Gross  Paid $", compute='_compute_ytd') 
	x_tax_ytd	= fields.Float(string="YTD Tax Deducted $", compute='_compute_ytd') 
	x_net_ytd	= fields.Float(string="YTD Net", compute='_compute_ytd') 
	x_super_ytd	= fields.Float(string="YTD Super Paid $", compute='_compute_ytd') 
	x_annual_ytd	= fields.Float(string="Accrued Annual Leave (hrs)", compute='_compute_ytd') 
	x_personal_ytd	= fields.Float(string="Accrued Personal Leave (hrs)", compute='_compute_ytd') 
	x_lsl_ytd	= fields.Float(string="Accrued YTD Longservice Leave (hrs)", compute='_compute_ytd') 
	x_xls_dcs = fields.Boolean('DCS Excel?')
	x_is_timesheet= fields.Boolean('Timesheet Exists', default=False)
	x_pdf_exists = fields.Boolean(string="Pdf exists",compute='_pdf_payslip_exists')
	x_job_id = fields.Many2one('hr.job', related='employee_id.job_id')
	x_group_id = fields.Many2one('hr.employee.group', related='employee_id.x_group_id')
	#x_gross_pay_hours	= fields.Float(string='Payperiod hours', compute="_gross_pay_hours")
	x_emp_number = fields.Char(related='employee_id.x_emp_number')
	x_payslip_deli = fields.Selection(related='employee_id.x_payslip_deli')
	x_email_pay = fields.Char(related='employee_id.x_email_pay')
	x_first_name = fields.Char(related='employee_id.x_first_name', store=True)
	x_last_name = fields.Char(related='employee_id.x_last_name', store=True)
	x_emp_name = fields.Char(related='employee_id.name', store=True)
	x_emp_status = fields.Selection(related='employee_id.x_emp_status')
	x_gross_payslip_amt	= fields.Float(string='Calculated Gross (payslip)')#, compute="_gross_payslip_amt")
	x_hours_variance = fields.Boolean("Hour Variance", default=False)
	x_authorise_variance = fields.Boolean("Authorise Hour Variance", default=False, track_visibility='onchange')
	x_termination_pay = fields.Boolean("Termination Pay", default=False)
	x_worked_hrs	= fields.Float(string='Calculated work hrs')
	x_offset_hrs	= fields.Float("Offset Hours")
	x_origin_id= fields.Many2one('hr.payslip', string='Origin Payslip')
	x_time_import_id= fields.Many2one('hr.timesheet.import.copy', string='Timesheet')
	#x_batch = fields.Char('Batch')
	state = fields.Selection([
		('draft', 'Draft'),
		('verify', 'Waiting'),
		('confirm', 'Confirmed'),
		('done', 'Done'),
		('reversed', 'Reversed'),
		('cancel', 'Rejected'),
	], string='Status', index=True, readonly=True, copy=False, default='draft', track_visibility='onchange')
	_order = 'date desc, x_last_name asc, x_first_name asc'
	
	#x_gross_payslip_amt	= fields.Float(string='Calculated Gross (payslip)', compute="_gross_payslip_amt")
	'''
	@api.depends('x_gross_amt', 'x_summary_ids')
	def _gross_payslip_amt(self):
		gross_amt=0.0
		for line in self.x_summary_ids:
			if line.category_id and line.category_id.calc4gross:
				gross_amt+= float(line.sub_total)
		self.x_gross_payslip_amt=gross_amt'''

		
	def _pdf_payslip_exists(self):
		for record in self:
			_path, _file, _exists=self.get_pdf_fileinfo(record)
			self.x_pdf_exists = _exists
			
	def _compute_ytd(self):
		for record in self:
			val				=self._get_all_ytd(record)
			_gross_ytd		=val['gross_amt']
			_tax_ytd		=val['tax_amt']
			_super_ytd		=val['super_amt']
			_annual_ytd		=val['annual_leave']
			_personal_ytd	=val['sick_leave']
			_lsl_ytd		=val['lsl_leave']
			_net_ytd		=val['net_amt']
			record.x_gross_ytd		= round(_gross_ytd,2)
			record.x_tax_ytd		= round(_tax_ytd,2)
			record.x_super_ytd		= round(_super_ytd,2)
			record.x_annual_ytd		= round(_annual_ytd,2)
			record.x_personal_ytd	= round(_personal_ytd,2)
			record.x_lsl_ytd		= round(_lsl_ytd,2)
			record.x_net_ytd		= round(_net_ytd,2)
			
	def _lsl_enabled(self):
		for record in self:
			#lsl_enable = self.employee_id.x_lsl_leave
			if record.employee_id:
				record.x_lsl_enable=record.employee_id.x_lsl_leave
			
 
				
	def get_employee_base_rate(self, employee, dt,payfreq_code=""):
		#if employee.x_pay_basis and employee.x_pay_basis=="S":#Salary 
		#rate_base 		=self.get_hourly_rate(employee.x_salary, payfreq, employee.x_payperiod_hr)
		#pay_basis, leave_rate, other_rate, salary_rate
		pay_basis, leave_rate, other_rate, rate_base, salary_annual = self.env['hr.employee.rate'].get_employee_rates(employee.id, dt)
		weekly_hrs	= 38.0
		if employee.x_group_id:
			daily_hrs= employee.x_group_id.daily_net_hrs
			days_week= employee.x_group_id.week_work_days
			if not daily_hrs:
				daily_hrs=7.6
			if not days_week:
				days_week=5	
			weekly_hrs =	days_week*daily_hrs
			
				
		if pay_basis == "S":
			_salary 	= float(rate_base)
			week_amt 	= round((_salary/52.0),4)
			rate_base 	= round((week_amt/weekly_hrs),4)#round((rate_base / (employee.x_work_hrs*52)),4)
			leave_rate=other_rate=rate_base
		#else:
		#	_salary 	= float(rate_base)*float(weekly_hrs)*52
		#pay_period_amt	= self.get_pay_period_amt(_salary, payfreq_code)
		#else:
		#if not rate_base:#just in case
		#	rate_base		= employee.timesheet_cost
		#	leave_rate 		= other_rate =rate_base
		return rate_base, leave_rate, other_rate, salary_annual
		
	def get_value_data(self, payslip):
		#----------------------------------------------
		employee	=payslip.employee_id
		#rate_other	=employee.x_other_rate
		gross_amt	=0.0
		tax_amt		=0.0
		round_precise=4
		obj_emp=self.env['hr.employee']
		#---------------------------------------------- 
		annual_accrud	=0.0
		lsl_accrud		=0.0
		sick_accrud		=0.0
		#>> x_code [breavement, nopay, compensation, communit, parental,annual, personal, longservice]
		#>> hardcoded...in order to automati or link with timesheets/payslip summary table/s...
		_payperiod_annual,_fortnight_hrs = obj_emp.get_leave_fortnight_hrs(employee.id, type="annual")
		_payperiod_personal,_fortnight_hrs = obj_emp.get_leave_fortnight_hrs(employee.id, type="personal")
		_payperiod_lsl,_fortnight_hrs = obj_emp.get_leave_fortnight_hrs(employee.id, type="longservice")
		#annual_entitle	=self.env['hr.employee'].get_leave_entitlement_daily(employee.id, type="annual")
		#sick_entitle	=self.env['hr.employee'].get_leave_entitlement_daily(employee.id, type="personal")
		#lsl_entitle		=self.env['hr.employee'].get_leave_entitlement_daily(employee.id, type="longservice") #type="lsl"
		
		annual_entitle=_payperiod_annual
		sick_entitle=_payperiod_personal
		lsl_entitle=_payperiod_lsl
		#daily_hrs		=employee.x_daily_hrs
		#annual_entitle	=round((float(annual_entitle)*float(daily_hrs)),4)
		#sick_entitle	=round((float(sick_entitle)*float(daily_hrs)),4)
		#lsl_entitle		=round((float(lsl_entitle)*float(daily_hrs)),4)
		#----------------------------------------------
		payfreq_code 		= payslip.x_payfrequency_id.code 
		pay_period_amt 	= 0.0
		rate_base, leave_rate, other_rate, salary_annual = self.get_employee_base_rate(employee, payslip.date, payfreq_code)
		'''
		if employee.x_pay_basis and employee.x_pay_basis=="S":#Salary 
			#rate_base 		=self.get_hourly_rate(employee.x_salary, payfreq, employee.x_payperiod_hr)
			pay_basis, leave_rate, other_rate, rate_base = self.env['hr.employee.rate'].get_employee_rates(employee.id, payslip.date)
			if not employee.x_work_hrs: #weekly hours
				weekly_hrs	=40.0
			else:
				weekly_hrs	=float(employee.x_work_hrs)
					
			if pay_basis=="S":
				_salary 	= float(rate_base)
				week_amt 	= round((_salary/52.0),4)
				rate_base 	= round((week_amt/weekly_hrs),4)#round((rate_base / (employee.x_work_hrs*52)),4)
				
			else:
				_salary 	= float(rate_base)*float(weekly_hrs)*52
			pay_period_amt	= self.get_pay_period_amt(_salary, payfreq)
		else:
			rate_base		= employee.timesheet_cost
		'''
		# ----------------------------------------------
		tot_hrs				= 0.0
		ot15_net			= 0.0
		ot20_net			= 0.0
		annual_net			= 0.0
		personal_net		= 0.0
		paidbreak_net		= 0.0
		partday_net			= 0.0
		loadingshift_net	= 0.0
		loadingleave_net	= 0.0
		
		leaveday_ids = []
		for line in payslip.x_leave_ids:
			for day in line.day_ids:
				exists=False
				for item in leaveday_ids:
					if item['id'] == day.id:
						exists=True
						break
				if exists==False:		
					vals1={'id':day.id,'holiday_status_id':line.holiday_id.holiday_status_id.id}
					leaveday_ids.append(vals1)
		tot_worked_hrs=0.0			
		for line in payslip.x_timesheet_ids:
			tot_hrs		+=line.hrs_normal
			ot15_net	+=line.hrs_t15
			ot20_net	+=line.hrs_t20
			annual_net	+=line.leave_annual
			personal_net+=line.leave_sick
			paidbreak_net	+=line.break_paid
			partday_net		+=line.leave_part
			
			
			'''if line.category_id.accrued:
				#accrued leave 
				if line.hrs_normal > 0.0 and line.hrs_normal >= daily_hrs:
					sick_accrud		+=	sick_entitle
					annual_accrud	+=	annual_entitle
					lsl_accrud		+=	lsl_entitle
				elif line.hrs_normal > 0.0 and line.hrs_normal<=daily_hrs:
					#part day leave
					sick_accrud		+=	(sick_entitle*(line.hrs_normal/daily_hrs))
					annual_accrud	+=	(annual_entitle*(line.hrs_normal/daily_hrs))
					lsl_accrud		+=	(lsl_entitle*(line.hrs_normal/daily_hrs))
				else:#other leave/annual leave etc..#todo test and verify later...[25/06]
					sick_accrud		+=	sick_entitle
					annual_accrud	+=	annual_entitle
					lsl_accrud		+=	lsl_entitle 
			if line.hrs_loading>0.0:
				if line.category_id.code=="AL":#see below ==> [def _onchange_paycategory(self)]
					loadingleave_net+=line.hrs_loading
				else:
					loadingshift_net+=line.hrs_loading
			'''		
		'''summary = self.get_summary(payslip, employee, rate_base)
		gross_amt			=summary['gross_amt']
		tot_sick_leaves		=summary['tot_sick_leaves']
		tot_lsl_leaves		=summary['tot_lsl_leaves']
		tot_parent_leaves	=summary['tot_parent_leaves']
		tot_loading_hrs		=summary['tot_loading_hrs']
		tot_hrs		=summary['tot_hrs']
		sick_net	=summary['sick_net']
		annual_net	=summary['annual_net']
		lsl_net		=summary['lsl_net'] 
	  
		if pay_period_amt>0.0:
			gross_amt=pay_period_amt
		'''	
		#----------------------------------------------------------------------------------------------------
		#Other payments....
		#for line in payslip.x_payment_ids:
		#	_amt=line.sub_total
		#	gross_amt+=round(_amt,4)
		#Other payments tab...........
		#----------------------------------------------------------------------------------------------------	
		tot_worked_hrs=tot_hrs+ot15_net+ot20_net+annual_net+personal_net
		_amt		=	tot_hrs*rate_base
		gross_amt	=	round(_amt,4)	
		#if pay_period_amt>0.0:
		#	gross_amt=pay_period_amt
		
		val_ret={
			'gross_amt':round(gross_amt,round_precise),
			#'tax_amt':round(tax_amt,4),
			#'net_amt':round(net_amt,4),
			#'super_amt':round(super_amt,round_precise),
			'annual_accrud':round(annual_accrud,round_precise),
			'lsl_accrud':round(lsl_accrud,round_precise),
			'sick_accrud':round(sick_accrud,round_precise),
			'loadingleave_net':round(loadingleave_net,round_precise),
			'loadingshift_net':round(loadingshift_net,round_precise),
			'partday_net':round(partday_net,round_precise),
			'paidbreak_net':round(paidbreak_net,round_precise),
			'personal_net':round(personal_net,round_precise),
			'annual_net':round(annual_net,round_precise),
			'ot20_net':round(ot20_net,round_precise),
			'ot15_net':round(ot15_net,round_precise),
			'tot_hrs':round(tot_hrs,round_precise),
			'rate_base':round(rate_base,round_precise),
			'leaveday_ids':leaveday_ids,
		}
		#_logger.error('val_retval_ret[ %s ]' %  (val_ret))
		return val_ret
		
	def sql_odoo_update(self, sql_update, obj, hrs, rate, ytd):
		#if hrs!=0.0:	
		#	_sub_total  = float(hrs) * float(rate)
		#	_sub_total=round(_sub_total,2)
		#	#ytd+=_sub_total
		if sql_update:
			#sql="update hr_payslip_summary set tot_hrs='%s',pay_rate='%s',ytd_total='%s' where id='%s'" % (hrs, rate, ytd, obj.id)
			sql="update hr_payslip_summary set tot_hrs='%s',ytd_total='%s' where id='%s'" % (hrs, ytd, obj.id)
			self.env.cr.execute(sql)
		else:
			val1={
				'tot_hrs':hrs,
				#'pay_rate':rate,
				'ytd_total':ytd,
				}
			obj.update(val1)
			#_logger.error('sql_odoo_updatesql_odoo_update[ %s ][ %s ]' %  (obj, val1))	
			
	def get_ytd_bycategory(self, employee_id, category_id, date, fiscal_id):
		ytd_total	=0.0
		
		sql	="""select sum(s.tot_hrs*s.pay_rate) as ytd_total 
				from hr_payslip_summary s,hr_payslip p where 
				s.payslip_id=p.id and p.date<='%s' and p.employee_id='%s' and s.category_id='%s'
				""" % (date, employee_id, category_id)
		if fiscal_id:
			sql	+=" and p.x_fiscal_id='%s'" % (fiscal_id)
		
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('ytd_total'):
				ytd_total  += float(row.get('ytd_total'))
			
		sql="""select s.ytd_total 
				from hr_payslip_ytd s  
				where 
				s.employee_id='%s' and s.category_id='%s' and s.date_ytd <='%s'
				""" % (employee_id, category_id, date)
		if fiscal_id:
			sql+=" and s.fiscal_id='%s'" % (fiscal_id)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('ytd_total'):
				ytd_total  += float(row.get('ytd_total'))
			
		return ytd_total
		
	def get_summary_ytd(self, payslip, category_id, skip_current=False):
		ytd_total=0.0
		if category_id:
			sql="""select s.category_id,sum(s.tot_hrs*s.pay_rate) as ytd_total 
					from hr_payslip_summary s,hr_payslip p where 
					s.payslip_id=p.id and p.date<='%s' and p.employee_id='%s' and s.category_id='%s'
					""" % (payslip.date, payslip.employee_id.id, category_id)
			if payslip.x_fiscal_id:
				sql+=" and p.x_fiscal_id='%s'" % (payslip.x_fiscal_id.id)
			if skip_current:
				sql+=" and (s.payslip_id<>'%s') " % (payslip.id)
			sql+=" group by s.category_id" 
			
			self.env.cr.execute(sql)	
			rs2 = self.env.cr.dictfetchall()
			for row in rs2:
				#category_id= row.get('category_id')
				if row.get('ytd_total'):
					ytd_total  += float(row.get('ytd_total'))
			#_logger.error('get_summary_ytdget_summary_ytd11[ %s ][ %s ]' %  (rs2, sql))	
			sql="""select s.ytd_total 
					from hr_payslip_ytd s  
					where 
					s.employee_id='%s' and s.category_id='%s' 
					""" % (payslip.employee_id.id, category_id)
			if payslip.x_fiscal_id:
				sql+=" and s.fiscal_id='%s'" % (payslip.x_fiscal_id.id)
			self.env.cr.execute(sql)	
			rs2 = self.env.cr.dictfetchall()
			
			for row in rs2:
				#category_id= row.get('category_id')
				if row.get('ytd_total'):
					ytd_total  += float(row.get('ytd_total'))
			#_logger.error('get_summary_ytdget_summary_ytd 22[ %s ][ %s ]' %  (ytd_total, sql))		
		return ytd_total
		
	def get_ytd_archive(self, fiscal_id, employee_id, code=""):
		return self._get_ytd_archive(fiscal_id, employee_id, code)
		
	def _get_ytd_archive(self, fiscal_id, employee_id, code=""):
		net=0
		sql="select sum(qty) as net from hr_payslip_ytd where fiscal_id='%s' and employee_id='%s' and ytd_category='%s' " % (fiscal_id, employee_id, code)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('net'):
				try:
					net=float(row.get('net'))
				except:
					net=0
					pass
				return net
		return 0
	
	def get_all_ytd_values(self, payslip_id, date, employee_id, fiscal_id, skip_current=False):
		val={'gross_amt':0,'tax_amt':0,'net_amt':0,'super_amt':0,'annual_leave':0,'lsl_leave':0,'sick_leave':0.0}
		 
		sql="""select sum(p.x_gross_amt) as gross_amt, sum(p.x_tax_amt) as tax_amt, sum(p.x_net_amt) as net_amt,
				sum(p.x_super_amt) as super_amt, sum(p.x_annual_leave) as annual_leave, sum(p.x_lsl_leave) as lsl_leave,
				sum(p.x_sick_leave) as sick_leave
				from hr_payslip p where 
				p.date<='%s' and p.employee_id='%s' """ % (date, employee_id)
		if skip_current and payslip_id:
			sql+=" and p.id!='%s'" % (payslip_id)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('gross_amt'):
				val['gross_amt']  = float(row.get('gross_amt'))
			if row.get('tax_amt'):
				val['tax_amt']  = float(row.get('tax_amt'))
			if row.get('net_amt'):
				val['net_amt']  = float(row.get('net_amt'))
			if row.get('super_amt'):
				val['super_amt']  = float(row.get('super_amt'))
			if row.get('annual_leave'):
				val['annual_leave']  = float(row.get('annual_leave'))
			if row.get('lsl_leave'):
				val['lsl_leave']  = float(row.get('lsl_leave'))
			if row.get('sick_leave'):
				val['sick_leave']  = float(row.get('sick_leave'))
		if fiscal_id:
			val['gross_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="gross")
			val['tax_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="tax")
			val['net_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="net")
			val['super_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="super")
			val['annual_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="annual")
			val['sick_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="personal")
			val['lsl_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="longservice")
		return val
		
	def _get_all_ytd(self, payslip, skip_current=False):
		if payslip.x_fiscal_id:
			fiscal_id=payslip.x_fiscal_id.id
		else:
			fiscal_id=None
		val=self.get_all_ytd_values(payslip.id, payslip.date, payslip.employee_id.id, fiscal_id, skip_current)	
		'''val={'gross_amt':0,'tax_amt':0,'net_amt':0,'super_amt':0,'annual_leave':0,'lsl_leave':0,'sick_leave':0.0}
		 
		sql="""select sum(p.x_gross_amt) as gross_amt, sum(p.x_tax_amt) as tax_amt, sum(p.x_net_amt) as net_amt,
				sum(p.x_super_amt) as super_amt, sum(p.x_annual_leave) as annual_leave, sum(p.x_lsl_leave) as lsl_leave,
				sum(p.x_sick_leave) as sick_leave
				from hr_payslip p where 
				p.date<='%s' and p.employee_id='%s' """ % (payslip.date, payslip.employee_id.id)
		if skip_current:
			sql+=" and p.id!='%s'" % (payslip.id)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('gross_amt'):
				val['gross_amt']  = float(row.get('gross_amt'))
			if row.get('tax_amt'):
				val['tax_amt']  = float(row.get('tax_amt'))
			if row.get('net_amt'):
				val['net_amt']  = float(row.get('net_amt'))
			if row.get('super_amt'):
				val['super_amt']  = float(row.get('super_amt'))
			if row.get('annual_leave'):
				val['annual_leave']  = float(row.get('annual_leave'))
			if row.get('lsl_leave'):
				val['lsl_leave']  = float(row.get('lsl_leave'))
			if row.get('sick_leave'):
				val['sick_leave']  = float(row.get('sick_leave'))
		if payslip.x_fiscal_id:
			fiscal_id=payslip.x_fiscal_id.id
			employee_id=payslip.employee_id.id
			
			val['gross_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="gross")
			val['tax_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="tax")
			val['net_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="net")
			val['super_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="super")
			val['annual_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="annual")
			val['sick_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="personal")
			val['lsl_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="longservice")'''
		return val
		
	def get_values_ytd(self, payslip):
		val=self._get_all_ytd(payslip)
		ytd_sick=val['sick_leave']
		ytd_annual=val['annual_leave']
		ytd_super=val['super_amt']
		ytd_tax=val['tax_amt']
		'''
		ytd_sick, ytd_annual, ytd_super, ytd_tax =0.0, 0.0, 0.0, 0.0
		 
		sql="""select p.x_sick_leave as ytd_sick,p.x_annual_leave as ytd_annual,p.x_super_amt as ytd_super,p.x_tax_amt as ytd_tax   
				from hr_payslip p where 
				p.date<='%s' and p.employee_id='%s' """ % (payslip.date, payslip.employee_id.id)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		for row in rs2:
			if row.get('ytd_sick'):
				ytd_sick  = float(row.get('ytd_sick'))
			if row.get('ytd_annual'):
				ytd_annual  = float(row.get('ytd_annual'))
			if row.get('ytd_super'):
				ytd_super  = float(row.get('ytd_super'))
			if row.get('ytd_tax'):
				ytd_tax  = float(row.get('ytd_tax'))	'''
		return ytd_sick, ytd_annual, ytd_super, ytd_tax
		
	def _update_value_ytd_item(self, payslip, _code, _net, _ytd, _index, sql_update=False): 	
		obj		=	self.env['hr.payslip.ytd']
		item	= 	None
		payslip_id=payslip.id
		employee_id=payslip.employee_id.id
		if payslip_id and _code:
			sql		=	"select id from hr_payslip_ytd where payslip_id='%s' and ytd_category='%s'" % (payslip_id, _code)
			self.env.cr.execute(sql)	
			rs2 	= self.env.cr.dictfetchall()
			for row in rs2:
				if row.get('id'):
					item=obj.browse(row.get('id'))
	
		#if item:
		#	sql="update hr_payslip_ytd set sub_total='%s',ytd_total='%s' where id='%s'" % (item.id)
		#else:
		#	sql="insert into hr_payslip_ytd"
	 
		vals={'qty':_net,'sub_total':_net,'ytd_total':_ytd,'sequence':_index,'date_ytd':payslip.date,'employee_id':employee_id}
		if payslip.x_fiscal_id:
			vals['fiscal_id']=payslip.x_fiscal_id.id
		if item:
			if sql_update:
				sql="update hr_payslip_ytd set qty='%s',sub_total='%s',ytd_total='%s',sequence='%s' " % (_net,_net, _ytd, _index )
				if payslip.x_fiscal_id:
					sql+=",fiscal_id='%s'" % (payslip.x_fiscal_id.id)
				sql+=" where id='%s'" % (item.id)	
				self.env.cr.execute(sql)
			else:
				item.write(vals)
		else:
			vals['payslip_id']	=payslip_id
			vals['ytd_category']=_code
			vals['employee_id']	=employee_id
			#vals['date']=payslip.date
			#if payslip.x_fiscal_id:
			#	vals['fiscal_id']=payslip.x_fiscal_id.id
			obj.create(vals) 
				
	def _update_value_ytd(self,payslip,gross_amt, tax_amt, net_amt, vals_accrud, sql_update=False):
	
		vals_ytd 		= self._get_all_ytd(payslip)
		
		annual_accrud	= vals_accrud['annual_accrud']
		lsl_accrud		= vals_accrud['lsl_accrud']
		sick_accrud		= vals_accrud['sick_accrud']
		
		_id			=payslip.id
		
		ytd_gross	=vals_ytd['gross_amt']
		ytd_tax		=vals_ytd['tax_amt']
		ytd_net		=vals_ytd['net_amt']
		ytd_super	=vals_ytd['super_amt']
		ytd_annual	=vals_ytd['annual_leave']
		ytd_sick	=vals_ytd['sick_leave']
		ytd_lsl		=vals_ytd['lsl_leave']
		
		_net,_ytd,_code,_index=gross_amt, ytd_gross, "gross", 0
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=tax_amt, ytd_tax, "tax", 1
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=net_amt,ytd_net, "net",2
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=sick_accrud,ytd_super, "super",3
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=sick_accrud,ytd_sick, "personal",4
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=annual_accrud,ytd_annual, "annual",5
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		_net,_ytd,_code,_index=lsl_accrud,ytd_lsl, "longservice",6
		self._update_value_ytd_item(payslip, _code, _net, _ytd, _index,sql_update)
		
		
	def update_value_summary(self, payslip, sql_update=False):
		'''
		vals=self.get_value_data(payslip)
		#_logger.error('update_value_summary vals[ %s ][ %s ]' %  (self.id, vals))	
		#gross_amt	=vals['gross_amt']
		#tax_amt		=vals['tax_amt']
		#net_amt		=vals['net_amt']
		#super_amt	=vals['super_amt']
		annual_accrud=vals['annual_accrud']
		lsl_accrud	=vals['lsl_accrud']
		sick_accrud	=vals['sick_accrud']
		loadingleave_net=vals['loadingleave_net']
		loadingshift_net=vals['loadingshift_net']
		partday_net	=vals['partday_net'],
		paidbreak_net=vals['paidbreak_net']
		personal_net	=vals['personal_net']
		annual_net	=vals['annual_net']
		ot20_net	=vals['ot20_net']
		ot15_net	=vals['ot15_net']
		tot_hrs		=vals['tot_hrs']
		rate_base	=vals['rate_base']
		leaveday_ids		=vals['leaveday_ids']
		employee=payslip.employee_id
		salary_annual=None
		#_logger.error('leaveday_idsleaveday_ids[ %s ]annual_net[ %s ]personal_net[ %s ]' %  (leaveday_ids, annual_net, personal_net))
		gross_amt=0.0
		for line in payslip.x_summary_ids:
			gross_amt+=line.sub_total
			if line.category_id:
				_ytd = self.get_summary_ytd(payslip, line.category_id.id)
				tot_hrs=line.tot_hrs
				self.sql_odoo_update(sql_update, line, tot_hrs, rate_base, _ytd)
			 
		gross_amt=round(gross_amt,2)
		if gross_amt==0.0:
			tax_amt=net_amt=super_amt=0.0
		else:
			payfreq = payslip.x_payfrequency_id.code 
			
			tax_amt, super_amt, super_pc = self.env['dincelpayroll.scale'].get_tax_amount_final(employee, payfreq, gross_amt, salary_annual)
			
			net_amt		= round((gross_amt-tax_amt),2)
			
		if sql_update:
			sql="""update hr_payslip set 
					x_gross_amt='%s',
					x_tax_amt='%s',
					x_net_amt='%s',
					x_super_amt='%s',
					x_annual_leave='%s',
					x_lsl_leave='%s',
					x_sick_leave='%s' 
				where 
					id='%s' 
				""" % (gross_amt, tax_amt, net_amt, super_amt, annual_accrud, lsl_accrud, sick_accrud, payslip.id)
			self.env.cr.execute(sql)
			
			leave_any=False
			hrs_normal=7.6 
			items = self.env['hr.employee.attendance'].search([('employee_id', '=', employee.id),('dayofweek', '=', 0)], limit=1) #dayofweek=0=monday 
			for item in items:
				hrs_normal=item.normal_pay
			for leaveday in leaveday_ids:
				if leaveday:
					holiday_status_id=leaveday['holiday_status_id']
					if holiday_status_id:
						items = self.env['hr.pay.category'].search([('holiday_status_id', '=', holiday_status_id)], limit=1)
						for item in items:
							leave_annual=0.0
							leave_sick=0.0
							if item.holiday_status_id:
								if item.holiday_status_id.x_code=="annual":
									leave_annual=hrs_normal
								elif item.holiday_status_id.x_code=="personal":
									leave_sick=hrs_normal	
							sql="""update hr_payslip_timesheet set category_id='%s',hrs_normal='0',leave_annual='%s',leave_sick='%s'
									where id='%s'""" % (item.id, leave_annual, leave_sick, leaveday['id'])
							self.env.cr.execute(sql)
							leave_any=True
			
		else:
			val1={
				'x_gross_amt':gross_amt,
				'x_tax_amt':tax_amt,
				'x_net_amt':net_amt,
				'x_super_amt':super_amt,
				'x_annual_leave':annual_accrud,
				'x_lsl_leave':lsl_accrud,
				'x_sick_leave':sick_accrud,
				}
				
			for line in payslip.x_timesheet_ids:
				for leaveday in leaveday_ids:
					if leaveday:
						if leaveday['id']==line.id:
							holiday_status_id=leaveday['holiday_status_id']
							if holiday_status_id:
								items = self.env['hr.pay.category'].search([('holiday_status_id', '=', holiday_status_id)], limit=1)
								for item in items:
									line.update({'category_id':item.id})
			payslip.update(	val1 )
		
		self._update_value_ytd(payslip,gross_amt, tax_amt, net_amt, vals, sql_update)
		'''
		return
		
	@api.onchange('x_timesheet_ids')
	def _summary_calculate(self):
		'''for payslip in self:
			#self.get_leave_summary(payslip) #, payslip.employee_id
			self.update_value_summary(payslip) #not in use.....13/12/2018'''
		return	
	

	def update_dcs_timesheet(self, payslip):	
		for line in payslip.x_timesheet_ids:
			#if line.is_summary:
			line.write({'category_id':False,
						'hrs_t15':0.0,
						'hrs_t20':0.0,
						'loading_night':0.0,
						'loading_noon':0.0,
						'leave_annual':0.0,
						'leave_sick':0.0,
						'leave_unpaid':0.0,
						'leave_part':0.0,
						'hrs_normal':0.0,
						}) #reset tot hrs
		for item in payslip.x_timesheet_ids2:
			#if item.date:
			dt=parser.parse(item.date)
			vals_sheet={'date':item.date,
					'name': dt.strftime("%a"),
					'payslip_id':payslip.id,
					#'payslip_id':payslip.id,
					#'hrs_normal':item.hrs_net,
					}
			if item.hrs_net:
				_qty=float(item.hrs_net)
			else:
				_qty=0.0
			if item.category_id.is_dcstime:		
				vals_sheet['category_id']=item.category_id.id
			_found=False	
				
			if item.category_id.code=="OT15":	
				vals_sheet['hrs_t15']=_qty
				_found=True
			elif item.category_id.code=="OT20":	
				vals_sheet['hrs_t20']=_qty	
				_found=True
			elif item.category_id.code=="loading-night":	
				vals_sheet['loading_night']=_qty
				_found=True
			elif item.category_id.code=="loading-noon":	
				vals_sheet['loading_noon']=_qty		
				_found=True
			elif item.category_id.code=="leave-annual":
				vals_sheet['leave_annual']=_qty	
				_found=True
			elif item.category_id.code in["leave-personal","leave-sick"]:
				vals_sheet['leave_sick']=_qty	
				_found=True
			elif item.category_id.code in["leave-unpaid","part-unpaid"]:
				vals_sheet['leave_unpaid']=_qty	
				_found=True
			elif item.category_id.code in["part-paid"]:
				vals_sheet['leave_part']=_qty	
				_found=True
			elif item.category_id.code in["paid-br"]:
				vals_sheet['break_paid']=_qty		
				_found=True
			#else:
			if item.category_id.is_dcstime and _found==False:		
				vals_sheet['hrs_normal']=_qty		
				
			_objFound		=False
			for item1 in payslip.x_timesheet_ids:
				if item1.date==item.date:
					#if item1.category_id.id==item.category_id.id:
					##_found=True
					_objFound=item1
					break
			if _objFound:
				_objFound.write(vals_sheet)
			else:	
				timesheet = self.env['hr.payslip.timesheet'].create(vals_sheet) 		
	#@api.onchange('x_timesheet_ids.category_id')
	'''def _leaves_calculate(self):
		#"""
		#Compute the total leaves of payslip
		#"""
		#_logger.error('_leaves_calculate_leaves_calculate[ %s ]payslippayslip[ %s ]' %  (self.ids, payslip))
		for payslip in self:
			self.get_leave_summary(payslip)
			
			#amount_untaxed = amount_tax = 0.0
			#for line in payslip.x_timesheet_ids:
			#	amount_untaxed += line.price_subtotal
			#	amount_tax += line.price_tax
			#payslip.update({
			#	'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
			#	'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
			#	'amount_total': amount_untaxed + amount_tax,
			#})'''
			
	@api.onchange('x_type')
	def _onchange_payfrequency(self):
		if self.date_from:
			dt_end=self.env['hr.payslip.run'].calculate_end_date(self.x_type, self.date_from)	
			if dt_end:
				self.update({'date_to':dt_end})
				
	@api.onchange('date_from')
	def _onchange_from_date(self):
		dt_end=self.env['hr.payslip.run'].calculate_end_date(self.x_type, self.date_from)	
		if dt_end:
			self.update({'date_to':dt_end})	
			
	def _add_update_payslip_otherline(self,payslip, qty, rate_base, paytype):
		_found=False
		summary=None
		vals_summary={}
		items = self.env['hr.pay.category'].search([('pay_type', '=', paytype)], limit=1)
		for item in items:
			_qty=qty
			for line in payslip.x_summary_ids:
				if line.category_id and line.category_id.id==item.id:
					_found=True
					_qty+=line.tot_hrs
					summary=line
			vals_summary = {'category_id': item.id,'name':item.name}
			#if item.category:
			#	vals_summary['pay_header']=item.category
			if item.expense_account_id:
				vals_summary['account_id']=item.expense_account_id.id
			if payslip.employee_id.x_coststate_id:
				vals_summary['cost_state_id']=payslip.employee_id.x_coststate_id.id
			if payslip.employee_id.x_costcentre_id:	
				vals_summary['costcentre_id']=payslip.employee_id.x_costcentre_id.id
		
			vals_summary['tot_hrs']=float(_qty)
			if float(abs(_qty))>0.0:
				vals_summary['pay_rate']=float(abs(rate_base))
			else:
				vals_summary['pay_rate']=0.0
			if payslip.x_fiscal_id:
				vals_summary['fiscal_id']=payslip.x_fiscal_id.id
			if _found==False:
				vals_summary['payslip_id']=payslip.id
				summary = self.env['hr.payslip.summary'].create(vals_summary)	
			else:
				summary.write(vals_summary)	
		#	return 	summary	
		#_logger.error("_add_update_payslip_line["+str(summary)+"]vals_summary["+str(vals_summary)+"]items["+str(items)+"]")		
		return 	summary	
		
	def _add_update_payslip_line(self,payslip, item, rate_base):
		_found=False
		summary=None
		if item.hrs_normal:
			_qty=item.hrs_normal
			for line in payslip.x_summary_ids:
				if line.category_id and line.category_id.id==item.category_id.id:
					_found=True
					_qty+=line.tot_hrs
					summary=line
			vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name}
			#if item.category:
			#	vals_summary['pay_header']=item.category
			if item.account_id:
				vals_summary['account_id']=item.account_id.id
			if payslip.employee_id.x_coststate_id:
				vals_summary['cost_state_id']=payslip.employee_id.x_coststate_id.id
			if payslip.employee_id.x_costcentre_id:	
				vals_summary['costcentre_id']=payslip.employee_id.x_costcentre_id.id
		
			vals_summary['tot_hrs']=float(_qty)
			vals_summary['pay_rate']=float(abs(rate_base))
			
				
			if _found==False:
				vals_summary['payslip_id']=payslip.id
				summary = self.env['hr.payslip.summary'].create(vals_summary)	
			else:
				summary.write(vals_summary)	
		#_logger.error("_add_update_payslip_line["+str(summary)+"]["+str(vals_summary)+"]["+str(summary)+"]")		
		return 	summary
	
	def calculate_payslip(self, payslip):
		
		if payslip.x_xls_dcs:
			for line in payslip.x_summary_ids:
				if line.is_summary:
					line.write({'tot_hrs':0}) #reset tot hrs
			qty_loading1=0
			qty_loading2=0
			qty_leave_unpaid=0
			qty_leave_part=0
			qty_break_paid=0
			qty_leave_personal=0
			qty_leave_annual=0
			qty_ot20=0
			qty_ot15=0
			
		
			employee=payslip.employee_id
			payfreq_code 		= payslip.x_payfrequency_id.code 
			rate_base, leave_rate, other_rate, salary_annual = self.get_employee_base_rate(employee, payslip.date, payfreq_code)
			for line in payslip.x_timesheet_ids:
				if line.category_id:
					self._add_update_payslip_line(payslip, line, rate_base)
				if line.hrs_t15:
					qty_ot15+=line.hrs_t15
				if line.hrs_t20:
					qty_ot20+=line.hrs_t20
				if line.break_paid:
					qty_break_paid+=line.break_paid
				if line.leave_annual:
					qty_leave_annual+=line.leave_annual
				if line.leave_sick:
					qty_leave_personal+=line.leave_sick
				if line.leave_unpaid:
					qty_leave_unpaid+=line.leave_unpaid
				if line.leave_part:
					qty_leave_part+=line.leave_part
				if line.loading_noon:
					qty_loading1+=line.loading_noon	
				if line.loading_night:
					qty_loading2+=line.loading_night	
			_rate= round(float(rate_base) * 1.5,2)		
			self._add_update_payslip_otherline(payslip, qty_ot15, _rate, "ot15")
			_rate= round(float(rate_base) * 2.0,2)		
			self._add_update_payslip_otherline(payslip, qty_ot20, _rate, "ot20")
			self._add_update_payslip_otherline(payslip, qty_leave_annual, rate_base, "leave_annual")
			self._add_update_payslip_otherline(payslip, qty_leave_personal, rate_base, "leave_personal")
			self._add_update_payslip_otherline(payslip, qty_leave_part, rate_base, "leave_partday")
			self._add_update_payslip_otherline(payslip, qty_break_paid, rate_base, "paid_break")
			self._add_update_payslip_otherline(payslip, qty_loading2, rate_base, "loading_night")
			self._add_update_payslip_otherline(payslip, qty_loading1, rate_base, "loading_noon")
			
			self.calculate_summary(payslip.id)
		else:
			self.calculate_summary_new(payslip)
	


	
	#-----------------------------------------------------------------------------------------------------------------------
	#-----------------------------------------------------------------------------------------------------------------------
	#-----------------------------------------------------------------------------------------------------------------------
	#	by new timesheet template....according as import from people key [30/10/18]
	#-----------------------------------------------------------------------------------------------------------------------
	#-----------------------------------------------------------------------------------------------------------------------
	#-----------------------------------------------------------------------------------------------------------------------
	def calculate_summary_new(self, payslip):
		sql_update	= False
		gross_amt	= tax_amt=net_amt=super_amt=deduct_amt_posttax=0.0
		obj_emp		= self.env['hr.employee']
		
		for line in payslip.x_summary_ids:
			if line.is_summary:
				line.write({'tot_hrs':0}) #reset tot hrs
		
		employee	 = payslip.employee_id
		payfreq_code = payslip.x_payfrequency_id.code 
		
		rate_base, leave_rate, other_rate,salary_annual = self.get_employee_base_rate(employee, payslip.date, payfreq_code)
		rate_base	= round(rate_base, 2)	#as per payslip is 2 digits
		leave_rate	= round(leave_rate, 2)	#as per payslip is 2 digits
		other_rate	= round(other_rate, 2)	#as per payslip is 2 digits
		
		#_logger.error("calculate_summary_new rate_base[%s], leave_rate[%s], other_rate[%s],salary_annual[%s]" % (rate_base, leave_rate, other_rate,salary_annual)) 
		annual_accrud	=0.0
		lsl_accrud		=0.0
		sick_accrud		=0.0
		super_pc		=9.5
		_default_work_hrs=38.0
		_payperiod_annual=0.0
		_payperiod_personal=0.0
		_payperiod_lsl=0.0
		tax_amt_deduction=0.0
		
		#>> x_code [breavement, nopay, compensation, communit, parental,annual, personal, longservice]
		#>> hardcoded...in order to automatic or link with timesheets/payslip summary table/s...
		arr_leaves=obj_emp.get_leave_hrs_arr(employee) #, payperiod="fortnight", pay_basis="S"
		for item in arr_leaves:
			_default_work_hrs=float(item['work_hrs'])
			if item['type']=="annual":
				_payperiod_annual=float(item['accured'])
			elif item['type']=="personal":
				_payperiod_personal=float(item['accured'])
			elif item['type']=="longservice":
				_payperiod_lsl=float(item['accured'])

		daily_hrs		=7.6
		if employee.x_group_id:
			daily_hrs=employee.x_group_id.normal_hrs
		#workdays=""#eg mon:tue:thu:fri=[1][2][3][4]
		workdays_arr=[]
		week_arr=dincelpayroll_vars.WEEK_DAY_OPTIONS_ARR	
		for item in employee.x_group_id.attendance_ids:
			if item.normal_pay and float(item.normal_pay)>0.0:
				workdays_arr.append(week_arr[int(item.dayofweek)])
			else:
				if item.category_id and item.category_id.pay_type in ["base"]: #just in case of extra hours,,,need to add this for super calculate
					workdays_arr.append(week_arr[int(item.dayofweek)])
		tot_worked_hrs	=0.0
		tot_leave_hrs	=0.0
		loading_hrs_ex	=0.0
		_leave_ids		=[]
		is_time_half_pay=employee.x_group_id.is_time_half_pay or False
		is_break_pay	=employee.x_group_id.is_break_pay or False
		if payslip.x_time_import_id:
			#ts_item=payslip.x_time_import_id
			loading_hrs_ex = self.env['hr.timesheet.import.copy'].get_loading_expt_hours(payslip.x_time_import_id, employee)
		#check leave rates and applies
		for leaveitem in payslip.x_leave_ids:
			if not leaveitem.category_id:
				continue

			_qty		=	leaveitem.tot_hrs
			if _qty > 0: 
				if _qty >= leaveitem.holiday_id.x_total_hrs:
					sql="update hr_holidays set x_redeem='full' where id='%s'" % (leaveitem.holiday_id.id)
				else:
					sql="update hr_holidays set x_redeem='part' where id='%s'" % (leaveitem.holiday_id.id)
			else:
				sql="update hr_holidays set x_redeem='none' where id='%s'" % (leaveitem.holiday_id.id)

			self.env.cr.execute(sql)
			
			summary		= 	None
			amt_type	=	leaveitem.category_id.amt_type
			
			rate_found	=False
			xfactor		=1.0
			rate=rate_base
			if leaveitem.holiday_status_id:
				if leaveitem.holiday_status_id.x_code in ["annual","personal","partday","longservice"]:
					rate=leave_rate
					rate_found=True
			if rate_found==False and leaveitem.category_id.holiday_status_id:
				if leaveitem.category_id.holiday_status_id.x_code in ["annual","personal","partday","longservice"]:
					rate		=leave_rate
					rate_found	=True
			if not rate_found:
				if amt_type:
					if amt_type=="times" and xfactor>0:
						rate=rate_base*xfactor
						#rate=round(rate,2)
					elif xfactor==0:
						rate=0
			if amt_type and amt_type=="zero":	#no pay or part -unpaid
				rate=0
			else:
				tot_leave_hrs	+=float(_qty)	
			
			#_amt_current=rate*_qty	
			for line in payslip.x_summary_ids:
				if line.category_id and (line.category_id.id==leaveitem.category_id.id):
					#_found=True
					_qty+=line.tot_hrs
					if line.is_manual:
						rate=line.pay_rate
						
					summary=line
					
			_amt_current=rate*_qty			
			vals_summary = {'category_id': leaveitem.category_id.id,'name':leaveitem.category_id.name,'sequence':leaveitem.category_id.sequence}

			if leaveitem.category_id.expense_account_id:
				vals_summary['account_id']=leaveitem.category_id.expense_account_id.id
			if payslip.employee_id.x_coststate_id:
				vals_summary['cost_state_id']=payslip.employee_id.x_coststate_id.id
			if payslip.employee_id.x_costcentre_id:	
				vals_summary['costcentre_id']=payslip.employee_id.x_costcentre_id.id
			
			vals_summary['is_summary']	=True
			vals_summary['tot_hrs']		=float(_qty)
			vals_summary['pay_rate']	=float(abs(rate))
			skip_current=True
			_ytd 		= self.get_summary_ytd(payslip, leaveitem.category_id.id, skip_current)
			vals_summary['ytd_total']=float(_ytd)+_amt_current	
			if summary:
				summary.write(vals_summary)	
			else:
				vals_summary['payslip_id']	=payslip.id
				summary = self.env['hr.payslip.summary'].create(vals_summary)	
			 
			if leaveitem.category_id.id not in _leave_ids:	
				_leave_ids.append(leaveitem.category_id.id)	
				
		tot_worked_hrs	+=float(tot_leave_hrs)	 #assume leave is always inside the work days
		#check for summary of timesheet...	
		for item in payslip.x_timesheet_ids2:
			if not item.category_id:
				continue
			if item.category_id.amt_type=="zero":
				continue #skip zero and unpaid
			_qty		=	item.hrs#_net
			xfactor		=	item.xfactor
			rate		=	rate_base
			summary		= 	None
			amt_type	=	item.category_id.amt_type
			factor_type =	item.category_id.factor_type
			_leave_found= 	False
			 
			if item.category_id.id in _leave_ids:	
				_leave_found = True
			if not _leave_found:	#ignore the same leave if repeaded in timesheeet....todo confirm with semra/raj later...
				if amt_type and amt_type=="zero":	#no pay or part -unpaid
					tot_worked_hrs+=0.0
					rate=0.0
				else:
					#if payslip.x_is_timesheet:		#regardless take this calculation...just in case some employee are in timesheet...
					if item.category_id.pay_type and item.category_id.pay_type in ["loading_leave","loading_night","loading_noon"]:
						skip_workhr=True
					else:	
						dt = parser.parse(item.date)
						dayname=dt.strftime('%a')
						if dayname in workdays_arr:
							if item.category_id.pay_type=="OT15":
								if is_time_half_pay:#only if enabled eg. tools afternoon vs production d/n
									tot_worked_hrs+=float(_qty)
							elif item.category_id.pay_type=="paid_break":
								if is_break_pay:	#only if enabled eg. tools afternoon vs production d/n
									tot_worked_hrs+=float(_qty)
							else:
								tot_worked_hrs+=float(_qty)
			
				#rate_found	=False
				if item.category_id.holiday_status_id:
					if item.category_id.holiday_status_id.x_code in ["annual","personal","partday","longservice"]:
						rate		=leave_rate
						#rate_found	=True
				'''		
				if not rate_found and amt_type:
					if amt_type=="times" and xfactor>0:
						rate		=rate_base*xfactor
						#rate=round(rate,2)
					elif xfactor==0:
						rate	=0
				'''	
				#_amt_current	=rate*_qty	
				
				for line in payslip.x_summary_ids:
					if line.category_id and (line.category_id.id==item.category_id.id):
						_qty+=line.tot_hrs
						if line.is_manual:
							rate=line.pay_rate
						summary=line
				_amt_current	=rate*_qty			
				vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name}
			
				if item.category_id.expense_account_id:
					vals_summary['account_id']=item.category_id.expense_account_id.id
				if payslip.employee_id.x_coststate_id:
					vals_summary['cost_state_id']=payslip.employee_id.x_coststate_id.id
				if payslip.employee_id.x_costcentre_id:	
					vals_summary['costcentre_id']=payslip.employee_id.x_costcentre_id.id
				vals_summary['is_summary']=True
				vals_summary['xfactor']=float(xfactor)
				vals_summary['factor_type']=factor_type
				vals_summary['tot_hrs']=float(_qty)
				vals_summary['pay_rate']=float(abs(rate))
				
				skip_current=True
				_ytd = self.get_summary_ytd(payslip, item.category_id.id, skip_current)
				vals_summary['ytd_total']=float(_ytd)+_amt_current	
				if summary:
					summary.write(vals_summary)	
				else:
					vals_summary['payslip_id']=payslip.id
					summary = self.env['hr.payslip.summary'].create(vals_summary)	
				
		
		#calculate accurals, leaves,
		if tot_worked_hrs >= _default_work_hrs:
			annual_accrud	=_payperiod_annual
			sick_accrud		=_payperiod_personal
			lsl_accrud		=_payperiod_lsl
			
		else:
			annual_accrud	=_payperiod_annual*tot_worked_hrs/_default_work_hrs
			sick_accrud		=_payperiod_personal*tot_worked_hrs/_default_work_hrs
			lsl_accrud		=_payperiod_lsl*tot_worked_hrs/_default_work_hrs
		offset_hrs=tot_worked_hrs - _default_work_hrs	
		if abs(offset_hrs) >0.0:
			hour_variance=True
		else:
			hour_variance=False
			
		
		
		#---------------------------------------------------------------------------------------			
		#----------------ADD special pay ------------- or loading ------------------------------			
		#---------------------------------------------------------------------------------------
		for special_pay in employee.x_group_id.specialpay_ids:
			if special_pay.type=="loading":
				loading_pay=None
				loading_hrs=0.0
				rate=rate_base
				for line in payslip.x_summary_ids:
					if line.category_id and (line.category_id.id==special_pay.parent_id.id):
						loading_pay=special_pay.category_id 
						loading_hrs=line.tot_hrs
						if special_pay.parent_id.holiday_status_id:
							if special_pay.parent_id.holiday_status_id.x_code in ["annual"]:
								rate=leave_rate
				
				if loading_pay:
					summary		= 	None
					vals_summary = {'category_id': loading_pay.id,'name':loading_pay.name}
					vals_summary['tot_hrs']			=float(loading_hrs)-float(loading_hrs_ex)
					vals_summary['xfactor']		=float(loading_pay.factor_default)
					vals_summary['factor_type']	=loading_pay.factor_type
					vals_summary['pay_rate']	=rate
					#vals_summary['pay_rate']	=rate_base
					#vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2) copy

					vals_summary['employee_id']		=employee.id
					for line in payslip.x_summary_ids:
						if line.category_id and (line.category_id.id==loading_pay.id):
							summary=line

					if summary:
						summary.write(vals_summary)	
					else:
						vals_summary['payslip_id']	=payslip.id
						summary = self.env['hr.payslip.summary'].create(vals_summary)	
		#loading ...etc	from the employee group level
		'''
		for item2 in employee.x_group_id.category_ids:
			_found_auto_parent=False
			_auto_attach_id	=False
			_objFound		=False
			for item1 in payslip.x_summary_ids:
				if item1.category_id.id==item2.id:
					#_found=True
					_objFound=item1
					break
			vals_summary = {'category_id': item2.id,'name':item2.name,'payslip_id':payslip.id}
			if item2.category:
				vals_summary['pay_header']=item2.category
			if item2.expense_account_id:
				vals_summary['account_id']=item2.expense_account_id.id

			#	vals_summary['cost_state_id']=item2.cost_state_id.id
			if item2.pc_amt:	

				if item2.auto_category_id:
					_auto_attach_id=item2.auto_category_id#.id or False
				_base_hrs=1.0
				_rate=item2.pc_amt
				
				if _auto_attach_id:
					_qty=0.0
					for item3 in payslip.x_summary_ids:
						if item3.category_id.id==_auto_attach_id.id:
							_qty+=float(item3.tot_hrs)
							_rate=item3.pay_rate
							_found_auto_parent=True #todo later...
				else: 
					_qty=1.0
				if item2.amt_type=="pc":			
					_rate=float(_rate)*float(item2.pc_amt)*0.01
				if item2.pc_amt < 0.0:
					_qty=-1.0 * float(_qty)
				if abs(_qty)>0.0:
		
					vals_summary['pay_rate']=float(abs(_rate))
					vals_summary['tot_hrs']=float(_qty)	
		
					if _objFound:
						_objFound.write(vals_summary)
					else:	
						
						summary = self.env['hr.payslip.summary'].create(vals_summary) '''
		#---------------------------------------------------------------------------	
		#loading ...etc	from the employee level
		items_entitlements = self.env['hr.payroll.entitlement'].search([('employee_id', '=', employee.id)])
		
		
		for item2 in items_entitlements:
			_found_auto_parent	=False
			_auto_attach_id		=False
			_objFound			=False
			for item1 in payslip.x_summary_ids:
				if item1.category_id.id==item2.category_id.id:
					#_found=True
					_objFound=item1
					break
			vals_summary = {'category_id': item2.category_id.id,'name':item2.category_id.name,'payslip_id':payslip.id}
			if item2.category:
				vals_summary['pay_header']=item2.category
			if item2.account_id:
				vals_summary['account_id']=item2.account_id.id
			if item2.cost_state_id:
				vals_summary['cost_state_id']=item2.cost_state_id.id
			if item2.amount:	
				#_qty=1
				#if item2.amount < 0.0:
				#	_qty=-1
				#vals_summary['tot_hrs']=float(_qty)
				if item2.category_id.auto_category_id:
					_auto_attach_id=item2.category_id.auto_category_id#.id or False
				_base_hrs=1.0
				_rate=item2.amount
				
				if _auto_attach_id:
					_qty=0.0
					for item3 in payslip.x_summary_ids:
						if item3.category_id.id==_auto_attach_id.id:
							_qty+=float(item3.tot_hrs)
							_rate=item3.pay_rate
							_found_auto_parent=True #todo later...
				else: 
					#if _qty==0.0:
					_qty=1.0
				if item2.amt_type=="pc":			
					_rate=float(_rate)*float(item2.amount)*0.01
				if item2.amount < 0.0:
					_qty=-1.0 * float(_qty)
				if abs(_qty)>0.0:
					#_logger.error("entitlemententitlement222["+str(_qty)+"]["+str(item2.category_id.id)+"]["+str(item2.category_id.name)+"]")		
					vals_summary['pay_rate']=float(abs(_rate))
					vals_summary['tot_hrs']=float(_qty)	
					#if item2.category_id.is_directpay == False:
					#	vals_summary['sub_total']=float(_qty)*float(abs(_rate))				
					#if _found_auto_parent:
					if _objFound:
						_objFound.write(vals_summary)
					else:	
						
						#_amt_current=float(abs(item.amount))*float(_qty)	
						#skip_current=True
						#_ytd = self.get_summary_ytd(payslip, item.category_id.id, skip_current)
						#vals_summary['ytd_total']=float(_ytd)+_amt_current	
						#gross_amt+=_amt_current
						#vals_summary['sub_total']=round((item.amount*_qty),2)
						summary = self.env['hr.payslip.summary'].create(vals_summary) 
		#---------------------------------------------------------------------------
		amt_suparable=0.0 #eg some allowances are suparable.............eg alex rosovic
		gross_payslip_amt=0.0
		#---------------------------------------------------------------------------
		for item2 in payslip.x_summary_ids:
			skip_current= True
			_ytd 		= self.get_summary_ytd(payslip, item2.category_id.id, skip_current)
			_qty		= float(item2.tot_hrs)
			_pay_rate	= float(item2.pay_rate)
			#_pay_rate	= round(_pay_rate, 2)
			if item2.category_id.is_directpay == False:
				if item2.factor_type == "rate":
					#_pay_rate	=float(item2.pay_rate)*float(item2.xfactor)
					_pay_rate	= float(_pay_rate)*float(item2.xfactor)
					#_pay_rate	= round(_pay_rate, 2)
				else:
					_qty		=float(item2.tot_hrs)*float(item2.xfactor)
				#_amt_current	=float(_pay_rate)*float(_qty)#*float(item2.xfactor)
				_amt_current	=round(_pay_rate,4)*round(_qty,4)#*float(item2.xfactor)
				#vals_total['sub_total']=_amt_current
			else:
				#_amt_current=_pay_rate#float(item2.sub_total)
				_amt_current	=round(_pay_rate,4)*round(_qty,4)
			if item2.category_id.is_tax:
				tax_amt_deduction+=_amt_current
			else:	
				if item2.category_id.tax_type and item2.category_id.tax_type=="post":
					deduct_amt_posttax+=_amt_current	
				else:
					gross_amt+=_amt_current	
			if item2.category_id.category and item2.category_id.category =="allowance":
				if item2.category_id.super:
					amt_suparable+=_amt_current #superable allowance (eg alex rosovic)
					
			_ytd_total	=float(_ytd)+_amt_current	
			#,'tot_hrs':item2.tot_hrs,'pay_rate':item2.pay_rate
			vals_total={'ytd_total':_ytd_total,'sub_total':_amt_current, 'net_hrs':_qty,'net_rate':round(_pay_rate, 2)} #background calc is 4 digits but display is 2 digits
			#vals_total['ytd_total']=_amt_current
			#_logger.error("entitlemententitlement items2items2[%s][%s]" % (items2,vals_total))
			#gross_amt=0.0
			
			if item2.category_id and item2.category_id.calc4gross: #eg salary sacrifice/super are  calc4gross=FALSE
				gross_payslip_amt += float(_amt_current)# float(item2.sub_total)
				
			#@self.x_gross_payslip_amt=gross_amt
			item2.write(vals_total)	
			#_logger.error("calculate_summary_ratevals_item2item2["+str(vals_total)+"]")	
		gross_amt=round(gross_amt,2)
		if gross_amt==0.0:
			tax_amt=net_amt=super_amt=gross_payslip_amt=0.0
		else:
			payfreq = payslip.x_payfrequency_id.code 
			#week_earned_amt			= self.env['hr.payslip.run'].get_weekly_pay(payfreq_code, gross_amt)		
			#week_earned_amt 		= round(week_earned_amt,2)			
			#tax_weekly, super_pc	= self.env['dincelpayroll.scale'].calculate_tax_amt(employee, week_earned_amt)		
			#tax_weekly 				= round(tax_weekly,2)
			#tax_amt1				= round(float(self.env['hr.payslip.run'].get_payslip_tax(payfreq_code, tax_weekly)),2)
			#tax_amt 		= round(tax_amt1+0.5)
			#tax_amt 		= round(tax_amt1)
			#_logger.error("get_weekly_payget_weekly_pay["+str(tax_amt1)+"]["+str(tax_amt)+"]["+str(tax_weekly)+"]["+str(tax_amt)+"]")	
			tax_amt, super_amt, super_pc =self.env['dincelpayroll.scale'].get_tax_amount_final(employee, payfreq, gross_amt, salary_annual)
			if gross_amt<0.0:#reverse payslip
				tax_amt=float(tax_amt)*(-1.0)
			tax_amt+=tax_amt_deduction	
			net_amt		= round((gross_amt-tax_amt+deduct_amt_posttax),2)
			#super_amt	= round((gross_amt*super_pc*0.01),2)	
			if not leave_rate:
				leave_rate=0.0
			if not super_pc:
				super_pc=9.5
			if employee.x_emp_status=="casual":
				#super_amt	= round((gross_amt*super_pc*0.01),2)	
				amt_suparable+=gross_amt
			else:	
				amt_suparable+=(tot_worked_hrs*leave_rate)
				#@@super_amt	= round(((tot_worked_hrs*leave_rate)*super_pc*0.01),2)	
			super_amt= round((amt_suparable*super_pc*0.01),2)
			
		#----------------------------------------------
		
		vals_accrud={}	
		if employee.x_emp_status=="casual":
			annual_accrud=lsl_accrud=sick_accrud=0.0
		vals_accrud['annual_accrud']=annual_accrud
		vals_accrud['lsl_accrud']	=lsl_accrud
		vals_accrud['sick_accrud']	=sick_accrud
		#annual_accrud	= vals_accrud['annual_accrud']
		#lsl_accrud		= vals_accrud['lsl_accrud']
		#sick_accrud		= vals_accrud['sick_accrud']	
		self._update_value_ytd(payslip,gross_amt, tax_amt, net_amt, vals_accrud, sql_update)
		sql_update=True
		if sql_update:
			sql="""update hr_payslip set 
					x_gross_payslip_amt='%s',
					x_gross_amt='%s',
					x_tax_amt='%s',
					x_net_amt='%s',
					x_super_amt='%s',
					x_annual_leave='%s',
					x_lsl_leave='%s',
					x_sick_leave='%s', 
					x_worked_hrs='%s',
					x_offset_hrs='%s',
					x_hours_variance='%s' 
				where 
					id='%s' 
				""" % (gross_payslip_amt, gross_amt, tax_amt, net_amt, super_amt, annual_accrud, lsl_accrud, sick_accrud, tot_worked_hrs, offset_hrs, hour_variance, payslip.id)
			self.env.cr.execute(sql)
			
			
		else:
			val1={
				'x_gross_payslip_amt': gross_payslip_amt,
				'x_gross_amt': gross_amt,
				'x_tax_amt': tax_amt,
				'x_net_amt': net_amt,
				'x_super_amt': super_amt,
				'x_annual_leave': annual_accrud,
				'x_lsl_leave': lsl_accrud,
				'x_sick_leave': sick_accrud,
				'x_hours_variance': hour_variance,
				'x_worked_hrs': tot_worked_hrs,
				'x_offset_hrs': offset_hrs,
				}
			
			payslip.update(	val1 )
		
		self.update_dcs_timesheet(payslip)
		
		return True
	
	def update_update_leave_ts(self, payslip):
		obj_time	= self.env['hr.employee.timesheet']
		normal_hrs=payslip.x_group_id.normal_hrs or 7.6
		normal_category=(payslip.x_group_id.category_id and payslip.x_group_id.category_id.id) or False
		
		for ts in payslip.x_timesheet_ids2:
			if ts.category_id.holiday_status_id and ts.category_id.holiday_status_id.id:
				ts.unlink()
				
		for leave in payslip.x_leave_ids:
			leave_id=leave.category_id.id
			tot_hrs=leave.tot_hrs
			hrs_taken=0
			date_from1 	= self.env['account.account'].get_au_date(leave.date_from)
			#date_from2 	= self.env['account.account'].utc_to_local(leave.date_from)
			date_to1 	= self.env['account.account'].get_au_date(leave.date_to)
			#_logger.error("button_update_leave_ts date_from["+str(leave.date_from)+"]date_from1["+str(date_from1)+"]["+str(tot_hrs)+"]")	
			date_from=parser.parse(date_from1)
			date_to=parser.parse(date_to1)
			for ts in payslip.x_timesheet_ids2:
				ds_date=parser.parse(ts.date)
				if ts.category_id.id == leave_id:
					if ds_date >=date_from and ds_date<=date_to:
						hrs_taken+=ts.hrs
			balance=tot_hrs-hrs_taken
			if balance>0.0:
				dt		= date_from#parser.parse(date_from)
				#dt=leave.date_from
				xfactor=1
				while balance>0.0:
					name 	= "%s" %  (dt.strftime("%a"))
					if balance>normal_hrs:
						leave_hrs=normal_hrs
					else:
						leave_hrs=balance
					_vals={
						'employee_id': payslip.employee_id.id,
						'category_id': leave_id,
						'hrs': leave_hrs,			#item.hrs, #making negative for reverse
						'hrs_net': leave_hrs,	#item.hrs_net, #making negative for reverse
						'xfactor': xfactor,
						'date': dt,
						'name': name,
						'payslip_id': payslip.id,
						'reversed':False,
						}
					obj_time.create(_vals)	
					balance=balance-leave_hrs
					dt	=	dt + timedelta(days=1) #next day loop...
		if normal_category:
			for ts in payslip.x_timesheet_ids2:
				if ts.category_id.id == normal_category:
					ds_date=parser.parse(ts.date)
					leave_taken=0.0
					for ts2 in payslip.x_timesheet_ids2:
						ds_date2=parser.parse(ts2.date)
						if ds_date2==ds_date:
							if ts2.category_id.holiday_status_id and ts2.category_id.holiday_status_id.id: 
								leave_taken+=float(ts2.hrs)
					balance=normal_hrs-float(leave_taken)
					if balance>=0.0:
						net_hrs=float(ts.xfactor)*balance
						ts.write({'hrs':balance,'net_hrs':net_hrs})
						
		return True
		
	@api.multi
	def button_update_leave_ts(self):
		
		payslip 	= self.browse(self.id)	
		
		self.update_update_leave_ts(payslip)			
		return
		
	@api.multi
	def button_clear_emailque(self):
		#for payslip in self:
		self.update({'x_email_que':False})		
		
	@api.multi
	def button_calculate_payslip(self):
		for payslip in self:
			self.calculate_payslip(payslip)
			#dt_import 	= dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			#impname 	= self.env['account.account'].get_au_datetime(dt_import)
			#payslip.x_chequeno=impname
	@api.multi
	def button_leave_balance(self):
		dt=datetime.today()
		ctx = self._context.copy()
		#model = 'account.invoice'
		ctx.update({'default_employee_id':self.employee_id.id, 
					'default_date_till':self.date, 
					'default_date_from':self.date, 
					'default_reportcode':'entitlesumm'})
		return {
			'name': _('Entitle Summary'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.payroll.report',
			#'views': [(view.id, 'form')],
			#'view_id': view.id,
			'target': 'new',
			#'res_id':self.id,
			'context': ctx,
		}
		#return True
		
	@api.multi
	def button_mark_as_draft(self):
		self.update({'state':'draft'})		
	
	@api.multi
	def button_generate_ato_test(self):
		payslip = self.env['hr.payslip'].browse(self.id)	
		self.env['dincelpayroll.ato'].create_payevent_xml(payslip)
		
	def generate_aba_file(self, payslips):
		_err=None
		config		= self.env['dincelaccount.settings'].load_default()
		_obank		= self.env['hr.employee.bank']#self.pool.get('res.partner.bank')
		_aba		= self.env['dincelaccount.aba']
		 
		bank_id=1
		journal_id  = 1						#_obj.journal_id.id
		description = config.pay_descr		#""#_obj.comment#''.join(e for e in string if e.isalnum())
		description = description[:12]
		d_description= 'PAYMENT DATA'		#''.join(e for e in description if e.isalnum())
		transactions=[]
		
		
		_bank=config.pay_bank_id#_obank.browse(cr, uid, bank_id, context=context)
		if _bank:
			d_bsb			=_bank.x_bsb
			d_accountNumber	=_bank.x_account_no
			d_bankName		=_bank.bic
			d_remitter		=_bank.x_owner_name
			d_userName		=_bank.x_owner_name
			d_directEntryUserId=_bank.x_bank_userid
			
			
			'''bsb="123-564"
			accountNumber="112233449"
			bankName="CBA"
			userName="DINCEL const"
			remitter="DINCEL"
			directEntryUserId="123456"
			description="DINCEL BDFD"
			'''
			
			for line in payslips:
				#invoice_id =line.invoice_id.id
				#partner_id = line.invoice_id.partner_id.id
				#partner_id = line.invoice_id.partner_id.id
				#_logger.error("x_payline_idsx_payline_ids["+str(invoice_id)+"]["+str(line.invoice_id.reference)+"]")
				#_logger.error("generate_aba_testgenerate_alineamountline.amount ["+str(line.amount)+"]")
				net_amt		= int(round(line.x_net_amt,2)*100)	#to CENTS
				employee	= line.employee_id
				reference	= description#line.ref_aba
				#_ac=_objac.browse(cr, uid, invoice_id, context=context)
				#if line.invoice_id.reference:
				#	reference=line.invoice_id.reference
				#else:
				#	reference=None
				#if not reference:# or reference=="":
				#	reference=line.invoice_id.number
				#	            team_stage_ids = self.env['crm.stage'].search(['|', ('team_id', '=', merged_data['team_id']), ('team_id', '=', False)], order='sequence')
				banks = _obank.search([('employee_id', '=', employee.id)], order='sequence')
				balance=0
				for bank in banks:
					_id1		= bank.id
					type		= bank.type
					bsb			= bank.bsb
					accountNumber=bank.account_number
					bankName	= bank.name
					remitter	= ''
					userName	= bank.name
					#directEntryUserId=_bank.x_bank_userid
					indicator=""
					taxWithholding=""
					transactionCode=_aba.EXTERNALLY_INITIATED_CREDIT
					
				
					'''
					accountName="CBA"
					bsb="111-444"
					amount="12500"
					indicator=""
					
					reference="RefText11"
					remitter="Shukra Rai"
					taxWithholding=""'''
					
					if type=="full":
						amount=net_amt
					else:
						if type=="part":
							salary_amt=bank.part_salary_amt
							salary_amt=int(round(salary_amt,2)*100)
							amount=salary_amt
							balance=net_amt-salary_amt
						else:#type ==balance
							amount=balance
					vals = {
							'accountName':userName,
							'accountNumber':accountNumber,
							'bsb':bsb,
							'amount':amount,
							'indicator':indicator,
							'transactionCode':transactionCode,
							'reference':reference,
							'remitter':remitter,
							'taxWithholding':taxWithholding,
							}
					if float(amount)> 0:
						transactions.append(vals)
					else:
						_logger.info("payslip.button_manage generate_aba_file negative amount[%s] found in transaction...vals[%s]" % (amount, vals))	
					#transactions.append(vals)		
			#_logger.error("generate_aba_testgenerate_aba_test1["+str(transactions)+"]")
			if not _err:
				_aba._init(d_bsb, d_accountNumber, d_bankName, d_userName, d_remitter, d_directEntryUserId, d_description)
				#_logger.error("generate_aba_testgenerate_aba_test1[%s %s]" % (datetime.today(), datetime.today()))
				_aba.payDate=datetime.today()#_obj.date
				_str = _aba.generate_aba(transactions)
				dttime1 = str(datetime.today())[:10]
				_idid = dttime1.replace("-", "")
				#datetime.strptime(dttime1, "%Y%m%d")#"%s" % (datetime.strptime(dt.datetime.now(), "%Y%m%d"))
				fname="Pay_%s.aba" % (_idid)
			 
				save_path=config.odoo_tmp_folder+"/aba"#"/var/tmp-odoo/aba/"
				temp_path=save_path+"/"+fname
				 
				#f=open(temp_path,'w')
				#f.write(_str)
				#f.close()
				self.env['dincel.utils'].write_file(save_path, fname,  _str)
				model, idid, title ="dincelaccount.aba", str(_idid), "Aba File"
				return self.env['dincel.utils'].download_file(model, idid, title, save_path, fname)
				'''
				return {
					'name': 'Aba File',
					'res_model': 'ir.actions.act_url',
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (str(_idid),save_path,fname),
					'context': {}}	'''		
	
	
		
	@api.multi
	def button_generate_aba(self):
		
		payslip = self.env['hr.payslip'].browse(self.id)	
		payslips=[]
		payslips.append(payslip)
		
		
		'''
		transactions=[]
		_aba =self.env['dincelaccount.aba']  
		_config	=self.env['dincelaccount.settings'].load_default()
		
		_err=None
		 
		
		#_idid=self.id
		#_obj=_obj.browse(cr, uid, _idid, context=context)
		if _config.pay_bank_id:
			emp=self.employee_id
			
			_bank=_config.pay_bank_id
			
			
			d_description	= 'PAYMENT DATA'
			d_bsb			=_bank.x_bsb
			d_accountNumber =_bank.x_account_no
			d_bankName		=_bank.bic
			d_remitter		=_bank.x_owner_name
			d_userName		=_bank.x_owner_name
			d_directEntryUserId=_bank.x_bank_userid
				
			
			 
			 
			 
			amount_total	=round(self.x_net_amt,2)	 
			amount_cents	=int(amount_total*100)	#to CENTS
			#partner_id	= line.supplier_id.id
			reference	= emp.x_pay_text#line.ref_aba
			
			paid_net=0.0
			for bank in emp.x_bank_ids: 
				bsb				=bank.bsb
				accountNumber	=bank.account_number
				bankName		=bank.bank_name
				remitter		=bank.name
				userName		=bank.name
				#directEntryUserId=_bank.x_bank_userid
				indicator		=""
				taxWithholding	=""
				transactionCode	=_aba.EXTERNALLY_INITIATED_CREDIT
				if paid_net<amount_total:
					if bank.type=="balance":#FULL Salary	
						amt_net=amount_total-paid_net
					elif bank.type=="part":
						pc_amt = round(float(bank.part_salary_amt),2)
						if bank.part_type=="amt": #or pc 
							if pc_amt>amount_total:
								amt_net=amount_total
							else:
								amt_net=pc_amt
						else:#pc
							amt_net=pc_amt*amount_total*0.01
					else:
						amt_net=amount_total
						
					amount_cents	=int(amt_net*100)
					paid_net+=amt_net	
					 
					vals = {
						'accountName':userName,
						'accountNumber':accountNumber,
						'bsb':bsb,
						'amount':amount_cents,
						'indicator':indicator,
						'transactionCode':transactionCode,
						'reference':reference,
						'remitter':remitter,
						'taxWithholding':taxWithholding,
						}
						
					transactions.append(vals)	
			#_logger.error("generate_aba_testgenerate_aba_test1["+str(transactions)+"]")
			if not _err:
				_aba._init(d_bsb, d_accountNumber, d_bankName, d_userName, d_remitter, d_directEntryUserId, d_description)
				_aba.payDate=self.date
				_str=_aba.generate_aba(transactions)
				
				fname="pay_"+str(self.number)+".aba"
				
				#save_path="/var/tmp/odoo/aba/"
				save_path	=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/aba/"
				temp_path=save_path+fname
				
				
				f=open(temp_path,'w')
				f.write(_str)
				f.close()
				
				#sql="update account_voucher set x_aba_downloaded='t' where id='%s' " % (_idid)
				#cr.execute(sql)
				
				return {
					'name': 'Aba File',
					'res_model': 'ir.actions.act_url',
					'type' : 'ir.actions.act_url',
					'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (self.id,save_path,fname),
					'context': {}}	'''	
		return self.generate_aba_file(payslips)
		
	def post_leave_journal(self, payslip):
		annual_accrud	=payslip.x_annual_leave
		lsl_accrud		=payslip.x_lsl_leave
		sick_accrud		=payslip.x_sick_leave
		'''
		'x_annual_leave':annual_accrud,
				'x_lsl_leave':lsl_accrud,
				'x_sick_leave':sick_accrud,
				
		vals	=self.get_value_data(payslip)
		
		annual_accrud	=vals['annual_accrud']
		lsl_accrud		=vals['lsl_accrud']
		sick_accrud		=vals['sick_accrud']
		 
		personal_taken	=vals['personal_net']
		annual_taken	=vals['annual_net']'''
		lsl_taken		=0.0 
		parental_taken	=0.0
		personal_taken	=0.0
		annual_taken	=0.0
		for line in payslip.x_summary_ids:
			#_stype	=line.category_id.summary_type
			_stype=None
		
			holidays = self.env['hr.holidays.status'].search([('x_category_id','=',line.category_id.id)], limit=1)
			for day in holidays:
				_stype=day.x_code
			#_logger.error("x_summary_idsx_summary_ids["+str(holidays)+"]["+str(_stype)+"]["+str(line.category_id.name)+"]")	
			if not _stype:	
				if line.category_id.holiday_status_id:
					_stype=line.category_id.holiday_status_id.x_code
			#_logger.error("x_summary_idsx_summary_ids_stype["+str(_stype)+"]["+str(_stype)+"]["+str(line.category_id.name)+"]")	
			if _stype:
				if _stype=="parental":
					parental_taken	+=line.tot_hrs
				elif _stype=="longservice":
					lsl_taken		+=line.tot_hrs
				elif _stype=="personal":
					personal_taken		+=line.tot_hrs
				elif _stype=="annual":
					annual_taken		+=line.tot_hrs			
		id1=self.env['hr.payslip.leave.balance'].create_balance("annual", payslip, annual_accrud, annual_taken)	
		id1=self.env['hr.payslip.leave.balance'].create_balance("personal", payslip, sick_accrud, personal_taken)			
		id1=self.env['hr.payslip.leave.balance'].create_balance("longservice", payslip, lsl_accrud, lsl_taken)
		id1=self.env['hr.payslip.leave.balance'].create_balance("parental", payslip, 0.0, parental_taken)
		
	@api.multi
	def button_validate_pay(self):
		#ret = self.calculate_summary(self.id, True	)
		#if ret:
		payslip 	= self.browse(self.id)	
		self.post_leave_journal(payslip)
		move_id=self.env['dincelaccount.journal'].payslip2journals(payslip.id)
		if move_id:
			payslip.write({'state':'done'})			
	
	@api.multi
	def button_update_leavebalance(self):
		#ret = self.calculate_summary(self.id, True	)
		#if ret:
		payslip 	= self.browse(self.id)	
		self.post_leave_journal(payslip)

		
	@api.multi
	def button_payslip_wizard(self):
		#view = self.env.ref('dincelpayroll.wizard.payroll.generate.form')
		dt=datetime.today()
		vals={'paydate':dt,'date_to':dt}
		wiz = self.env['hr.payroll.generate'].create(vals)
		return {
			'name': _('Create payslip'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.payroll.generate',
			#'views': [(view.id, 'form')],
			#'view_id': view.id,
			'target': 'new',
			'res_id':wiz.id,
			'context': self.env.context,
		}
		
	def save_payslippdf_byid(self, id):
		payslip 	= self.browse(id)#@line.payslip_id
		return self.save_pdf_file_byobj(payslip)
		
	def save_pdf_file_byobj(self, payslip):
		
	
		#_logger.error("save_payslippdf_byidsave_payslippd111	["+str(id)+"]["+str(self)+"]")	
		'''payslip 	= self.browse(id)	
		ids	= [id]
		data 			= {}
		data['ids'] 	= ids
		model 			= 'report.employee.payroll'
		data['model'] 	= model			
		data['form'] 	= {'date':payslip.date,
			'date_till':	payslip.date_to,
			'date_from':	payslip.date_from, 
			'payslip_id':	payslip.id, 
			'employee_id':	payslip.employee_id.id, 
			'employee':		payslip.employee_id.name, 
			'active_id':	payslip.id, 
			'company_id':	payslip.company_id.id
			}'''
			
		#@base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		
		#-----------method 1.html --------------------------------
		
		payslips=[]	
		
		employee=payslip.employee_id
		val=self.env['hr.payslip.manage'].get_payslip_prevew_data(payslip, employee)
		payslips.append(val)
		
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		data 			= {}
		data['ids'] 	= [payslip.id]
		#active_id 		= self.env.context.get('active_id')
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] 	= {'payslips':payslips,'active_id':payslip.id} #, 'time':time
		
		#-----------method 1.html --------------------------------
		#report		=self.env.ref('dincelpayroll.action_report_payslip_all').report_action(self, data=data, config=False)
		report	= self.env.ref('dincelpayroll.action_report_payslip_all')
		body1 	= report.with_context(self.env.context).render_qweb_html(None, data=data)[0]
		
		#report	= self.env.ref('dincelpayroll.action_report_pagepayslip')
		#body1 	= report.with_context(self.env.context).render_qweb_html(None, data=data)[0]
		#pdf = report.with_context(self.env.context).render_qweb_pdf(None, data=data)[0]
		#.render_qweb_pdf(docids, data=data)[0]
		#pdf1 = base64.b64encode(pdf)
				
		html 	= body1.decode('utf-8')
		html 	= html.replace('href="/', 'href="%s/' % base_url)
		html 	= html.replace('src="/', 'src="%s/' % base_url)
		
		_rootpath, _file_pdf, _exists	= self.get_pdf_fileinfo(payslip)
		_file_html = _file_pdf.replace(".pdf",".html")
		
		_path		= _rootpath + "/" + _file_html 
		with open(_path, "w+") as _file:
			_file.write("%s" % html) 
		_path1		= _rootpath + "/" + _file_html 
		with open(_path1, "w+") as _file:
			_file.write("%s" % html) 
		temp_path 	= _rootpath + "/" +  _file_pdf.replace(".pdf",".pdf")
		#_logger.error("save_payslippdf_byidsave_payslippdf_byid		["+str(id)+"]["+str(_path)+"]["+str(temp_path)+"]")	
		process		= subprocess.Popen(["wkhtmltopdf", _path, temp_path], stdin=PIPE, stdout=PIPE)
		out, err 	= process.communicate()
		return process.returncode, out, err, temp_path
		
	def generate_payslip_pdf(self):
		returncode, out, err, temp_path = self.save_payslippdf_byid(self.id)
		return returncode, out, err, temp_path
		
		
	def generate_payslip_pdf_bak(self):
		data 			= {}
		data['ids'] 	= self.ids
		model 			= 'report.employee.payroll'
		data['model'] 	= model			
		data['form'] 	= {'date':self.date,
			'date_till':	self.date_to,
			'date_from':	self.date_from, 
			'payslip_id':	self.id, 
			'employee_id':	self.employee_id.id, 
			'employee':		self.employee_id.name, 
			'active_id':	self.id, 
			'company_id':	self.company_id.id
			}
			
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		payslip 	= self.browse(self.id)#@line.payslip_id
		
		#-----------method 1.html --------------------------------
		report	= self.env.ref('dincelpayroll.action_report_pagepayslip')
		body1 	= report.with_context(self.env.context).render_qweb_html(None, data=data)[0]
		html 	= body1.decode('utf-8')
		html 	= html.replace('href="/', 'href="%s/' % base_url)
		html 	= html.replace('src="/', 'src="%s/' % base_url)
		
		_rootpath, _file_pdf, _exists= self.get_pdf_fileinfo(payslip)
		_file_html = _file_pdf.replace(".pdf",".html")
		#_rootpath  	= "/var/tmp/odoo/payslips/"
		#_file_html	= "PAY_%s.html" %  (self.number)
		#_file_pdf	= "PAY_%s.pdf" %  (self.number)
		_path		= _rootpath + "/" + _file_html #@ "/var/log/odoo/PAY_%s.html"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % html) 
			
		temp_path 	= _rootpath + "/" + _file_pdf
		process		= subprocess.Popen(["wkhtmltopdf", _path, temp_path],stdin=PIPE,stdout=PIPE)
		out, err 	= process.communicate()
		 
		'''
		pdf_content 	= report.with_context(self.env.context).render_qweb_pdf(None, data=data)[0]	
		pdf_content_stream = io.BytesIO(pdf_content)
		buffer=pdf_content_stream
		_data=base64.encodestring(buffer.getvalue())
		
		_path		= _rootpath + "payslip2_%s.pdf" %  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % _data) 
		
		ir_attachement_obj=self.env['ir.attachment']
		attachment_vals = {
			'name': _file_pdf,
			'datas': _data,
			'datas_fname': _file_pdf,
			'res_model': 'hr.payslip',
			'res_id': self.id,
		}
		
		ir_id = ir_attachement_obj.create(attachment_vals) 
		'''	
		return process.returncode, out, err, temp_path
		
	@api.multi	
	def button_payslip_pdf_new(self):
		self.generate_payslip_pdf()
		return True
		
	def get_pdf_fileinfo(self, payslip):
		#_path  	= "/var/tmp/odoo/payslips"
		_path	=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payslips/"
		_fname	= "PAY_%s.pdf" %  (re.sub('\W+','', payslip.number ))#self.number)
		#_fname	= re.sub('\W+','', _fname )
		##[Matches any non-alphanumeric character; this is equivalent to the class [^a-zA-Z0-9_] ]
		temp_path 	= _path +"/"+ _fname
		if os.path.isfile(temp_path):
			_exists=True
		else:
			_exists=False
		return _path, _fname, _exists
		
	@api.multi 
	def button_download_payslip_pdf(self):
		#save_path  	= "/var/tmp/odoo/payslips/"
		#_file_html	= "PAY_%s.html" %  (self.number)
		#fname	= "PAY_%s.pdf" %  (self.number)
		payslip 	= self.browse(self.id)
		save_path, fname, _exists = self.get_pdf_fileinfo(payslip)
		
		#temp_path 	= save_path +"/"+ fname
		if not _exists:# temp_path.exists():
			raise UserError(_("Warning! no file to download."))
		#save_path,fname
		#'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (self.id,save_path,fname),
		return {
				'name': 'Payslip File',
				'res_model': 'ir.actions.act_url',
				'type' : 'ir.actions.act_url',
				'url': '/web/binary/download_file?model=hr.payslip&field=datas&id=%s&path=%s&filename=%s' % (self.id, save_path, fname),
				'context': {}}
				
	@api.multi	
	def button_payslip_pdf_newBak(self): #, cr, uid, ids, context=None
		#active_id = self.env.context.get('active_id')
		'''data 			= {}
		data['ids'] 	= self.ids
		model 			= 'report.employee.payroll'
		data['model'] 	= model			
		data['form'] 	= {'date':self.date,
			'date_till':	self.date_to,
			'date_from':	self.date_from, 
			'payslip_id':	self.id, 
			'employee_id':	self.employee_id.id, 
			'employee':		self.employee_id.name, 
			'active_id':	self.id, 
			'company_id':	self.company_id.id
			}'''
		payslips=[]	
		payslip=self#@line.payslip_id
		employee=self.employee_id
		val=self.get_payslip_prevew_data(payslip, employee)
		payslips.append(val)
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		data 			= {}
		data['ids'] 	= self.ids
		active_id 		= self.env.context.get('active_id')
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] 	= {'payslips':payslips,'active_id':self.id, 'time':time}
		
		#-----------method 1.html --------------------------------
		report		=self.env.ref('dincelpayroll.action_report_payslip_all').report_action(self, data=data, config=False)
		#report		= self.env.ref('dincelpayroll.action_report_pagepayslip')
		body1 		= report.with_context(self.env.context).render_qweb_html(None, data=data)[0]
		html 		= body1.decode('utf-8')
		html 		= html.replace('href="/', 'href="%s/' % base_url)
		html 		= html.replace('src="/', 'src="%s/' % base_url)
		_rootpath=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payslips/"
		#_rootpath 	= "/var/tmp/odoo/payslips/"
		_file_html	= "PAY_%s.html" %  (self.number)
		_file_pdf	= "PAY_%s.pdf" %  (self.number)
		_path		= _rootpath + _file_html #@ "/var/log/odoo/payslip_%s.html"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % html) 
		temp_path 	= _rootpath + _file_pdf
		process		= subprocess.Popen(["wkhtmltopdf", _path, temp_path],stdin=PIPE,stdout=PIPE)
		out, err 	= process.communicate()	
		#-----------------------------------------------------------
		'''_logger.error('config_parameterconfig_parameter self.id[ %s ]base_url[ %s ]',self.id, base_url)
		#-----------method 2.html --------------------------------	
		_ids		= self.ids 
		_active_id	= self.id 
		values 		= self.env['report.dincelpayroll.report_payslip_common'].get_report_values_new(_ids, _active_id, data)	
		body2 		= self.env['ir.ui.view'].render_template("dincelpayroll.report_pagepayslip", values)	
		html 		= body2.decode('utf-8')
		_path		= "/var/tmp/odoo/payslip_%s.pdf"%  (self.number)
		_path		= "/var/log/odoo/payslip_%s.html"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % html) 
		#-----------------------------------------------------------	
		'''
		
		
		'''
		body = body2

		header = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
		header = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=header))

		pdf= self.env['ir.actions.report']._run_wkhtmltopdf(
			[body],
			header=header,
			landscape=True,
			specific_paperformat_args={'data-report-margin-top': 10, 'data-report-header-spacing': 10}
		)
		_path		= "/var/log/odoo/payslip_%s.pdf"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % pdf) 
			
		pdf2 	= report.with_context(self.env.context).render_qweb_pdf(None, data=data)[0]	
		pdf = base64.b64encode(pdf2)
		#pdf= base64.decodestring(pdf2)
		_path		= "/var/log/odoo/payslip2_%s.pdf"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % pdf) 
		pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf2))]
		#abc1= request.make_response(pdf2, headers=pdfhttpheaders)
		#_path		= "/var/log/odoo/payslip3_%s.pdf"%  (self.number)
		#with open(_path, "w+") as _file:
		#	_file.write("%s" % abc1) 
		'''
		return True
		
	@api.multi	
	def button_payslip_pdf_new2(self): #, cr, uid, ids, context=None
		
		payslips	=[]	
		payslip		=self#@line.payslip_id
		employee	=self.employee_id

		val=self.env['hr.payslip.manage'].get_payslip_prevew_data(payslip, employee)
		payslips.append(val)
		base_url 		= self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		data 			= {}
		data['ids'] 	= self.ids
		
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] 	= {'payslips':payslips,'active_id':self.id, 'time':time}

		report	= self.env.ref('dincelpayroll.action_report_payslip_all')

		pdf 	= report.with_context(self.env.context).render_qweb_pdf(None, data=data)[0]
		_file_name	= "PAY_%s" %  (re.sub('\W+','', payslip.number ))
		items = self.env['ir.attachment'].search([('name', '=', _file_name),('res_id', '=', payslip.id),('res_model', '=', 'hr.payslip')]) 
		for item in items:
			item.unlink()
			
		self.env['ir.attachment'].create({
			'name': "" +(_file_name),
			'type': 'binary', 
			'res_id':payslip.id,
			'res_model':'hr.payslip',
			'datas':base64.b64encode(pdf),
			'mimetype': 'application/x-pdf',
			'datas_fname':"" +(_file_name)+".pdf"
			})
		
		
		return True
		
	def get_pdf_new(self, body):
		#lines = self.with_context(print_mode=True).get_pdf_lines(line_data)
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		rcontext = {
			'mode': 'print',
			'base_url': base_url,
		}

		#body = self.env['ir.ui.view'].render_template(
		#	"stock.report_stock_inventory_print",
		#	values=dict(rcontext, lines=lines, report=self, context=self),
		#)

		header = self.env['ir.actions.report'].render_template("web.internal_layout", values=rcontext)
		header = self.env['ir.actions.report'].render_template("web.minimal_layout", values=dict(rcontext, subst=True, body=header))
		#_logger.error('get_pdf_newget_pdf_new headerheader[ %s ]bodiesbodies[ %s ]' %  (body,rcontext))
		return self.env['ir.actions.report']._run_wkhtmltopdf(body.encode())		
		
	@api.multi
	def button_payslip_pdf1(self):
		data 			= {}
		data['ids'] 	= self.ids
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] 	= {'date':self.date,
			'date_till':self.date_to,
			'date_from':self.date_from, 
			'payslip_id':self.id, 
			'employee_id':self.employee_id.id, 
			'employee':self.employee_id.name, 
			'active_id':self.id, 
			'company_id':self.company_id.id}
		pdf= self.env.ref('dincelpayroll.action_report_pagepayslip_pdf').report_action(self, data=data, config=False)
		_fname	= "PAY_%s.pdf" %  (re.sub('\W+','', self.number ))#self.number)
		_path	=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payslips/%s" % (_fname)
		#_path="/var/log/odoo/payslip_%s.pdf"%  (self.number)
		with open(_path, "w+") as _file:
			_file.write("%s" % pdf) 
		
		return pdf	
	@api.multi
	def button_payroll_slip(self):
		res 			= {}
		
		data 			= {}
		data['ids'] 	= self.ids
		active_id 		= self.env.context.get('active_id')
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] 	= {'date':self.date,
			'date_till':self.date_to,
			'date_from':self.date_from, 
			'payslip_id':self.id, 
			'employee_id':self.employee_id.id, 
			'employee':self.employee_id.name,
			'active_id':self.id, 			
			'company_id':self.company_id.id}
		#_logger.error('button_payroll_slip data [ %s ] ' %  (data)) 
		return self.env.ref('dincelpayroll.action_report_pagepayslip').report_action(self, data=data, config=False)	
		'''dt=datetime.today()
		ctx = self._context.copy()
		#model = 'account.invoice'
		ctx.update({'default_employee_id':self.employee_id.id, 
					'default_date_till':self.date, 
					'default_date_from':self.date, 
					'default_reportcode':'payslip'})
		return {
			'name': _('Payslip'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.payroll.report',
			#'views': [(view.id, 'form')],
			#'view_id': view.id,
			'target': 'new',
			#'res_id':self.id,
			'context': ctx,
		}'''
		
	@api.model
	def create(self, vals):
		record = super(DincelPayslipEmployee, self).create(vals)	
		#self.init_summarytable(record.id)
		'''if vals.get('employee_id'):
			employee_id=vals.get('employee_id')
			#	' ' 'employee = self.env['hr.employee'].browse(employee_id)
			if employee.x_group_id:
				for line in employee.x_group_id.summary_ids:
					vals_summary = {'sequence':line.sequence,'category_id': line.category_id.id,'name':line.name,'payslip_id':record.id}
					summary = self.env['hr.payslip.summary'].create(vals_summary)'''
		return record
		
	# return super(AccountAccount, self).write(vals)	
	def init_summarytable(self, id):
		'''items = self.env['hr.pay.category'].search([('is_summary', '=', True)])
		for item in items:
			vals_summary = {'category_id': item.id,'name':item.name,'payslip_id':id}
			if item.expense_account_id:
				vals_summary['account_id']=item.expense_account_id.id
			if item.category:
				vals_summary['pay_header']=item.category
			summary = self.env['hr.payslip.summary'].create(vals_summary)
			#_logger.debug('_init_summarytableinit_summarytable[ %s ]' %  (vals_summary))'''
		payslip = self.env['hr.payslip'].browse(id)	
		self.calculate_payslip(payslip)
		#self.calculate_summary(id)
		'''
		employee_id =  payslip.employee_id.id
		items2 = self.env['hr.payroll.entitlement'].search([('employee_id', '=', employee_id)])
		for item in items2:
			_found=False
			#for item1 in items:
			#	if item1.id==item.category_id.id:
			#		_found=True
			#		break
			if _found==False:		
				vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name,'payslip_id':id}
				if item.category:
					vals_summary['pay_header']=item.category
				if item.account_id:
					vals_summary['account_id']=item.account_id.id
				if item.cost_state_id:
					vals_summary['cost_state_id']=item.cost_state_id.id
				if item.amount:	
					_qty=1
					if item.amount < 0.0:
						_qty=-1
					vals_summary['tot_hrs']=float(_qty)
					vals_summary['pay_rate']=float(abs(item.amount))
					#vals_summary['sub_total']=round((item.amount*_qty),2)
				summary = self.env['hr.payslip.summary'].create(vals_summary) '''
		return True
		
	@api.multi
	def write(self, values):
		#ctx = dict(self._context or {})
		
		record = super(DincelPayslipEmployee, self).write(values)#, self.with_context(ctx)).write(values)
		#sql_update=True
		#self.calculate_summary(self.id, sql_update)
		#self.calculate_summary(self.id)
		#self.calculate_summary(self.id, True	)
		return record
		
	@api.multi
	def unlink(self):
		for record in self:
			#if location.unavailable:
			#if self.x_time_import_id:
			record.x_time_import_id.update({'payslip_ref':'','state':'draft'})
			#return super(DincelPayslipEmployee, self).unlink() 
			#return record.unlink() 
		return super(DincelPayslipEmployee, self).unlink() 	
	@api.multi
	def button_calculate_summary(self):
		#self.init_summarytable(self.id)
		'''account = self.env['dincelaccount.settings'].search([], limit=1)
		_logger.error('button_calculate_summary self.id[ %s ][ %s ]',self.id, account)
		if account.payroll_clearing_code:
			vals={}
			vals['x_clearing_account_id']=account.payroll_clearing_code.id
		'''	
		'''empids = self.env['hr.employee'].search([])
		for emp in empids:
			if not emp.x_emp_number:
				_number		=self.env['ir.sequence'].next_by_code('employee.no')
				#_logger.error('button_calculate_summary employeeemployeeno summary creating one for id[ %s ] _number[ %s ]',emp.id, _number)
				if _number:
					emp.write({'x_emp_number':_number})'''
				
		if len(self.x_summary_ids) == 0:
			self.init_summarytable( self.id )
			#_logger.error('button_calculate_summary no summary creating one for id[ %s ] name[ %s ]',self.id, self.name)
		return self.calculate_summary(self.id, True	)
	
	def get_hourly_ratexx(self, annual_salary, payfreq, payperiod_hr):
		payperiod_hr=float(payperiod_hr)
		year_hour=1.0
		#pay_period_amt=annual_salary
		if payfreq=="month":#month
			year_hour=12.0*payperiod_hr
			#pay_period_amt=annual_salary/12.0
		elif payfreq=="week":#week
			year_hour=payperiod_hr*52.0
			#pay_period_amt=annual_salary/52.0
		elif payfreq=="fortnight":#fortnight
			year_hour=payperiod_hr*26.0
			#pay_period_amt=annual_salary/26.0
		_rate=	float(annual_salary)/float(year_hour)
		return _rate#, pay_period_amt
		
	def get_pay_period_amt(self, annual_salary, payfreq):
		
		pay_period_amt=annual_salary
		if payfreq=="month":#month
			pay_period_amt=annual_salary/12.0
		elif payfreq=="week":#week
			pay_period_amt=annual_salary/52.0
		elif payfreq=="fortnight":#fortnight
			pay_period_amt=annual_salary/26.0
		
		return pay_period_amt
		
	def calculate_summary(self,_id, sql_update=False):	
		payslip 	= self.browse(_id)
		#employee	= payslip.employee_id
		#self.get_leave_summary(payslip)
		#if payslip.x_xls_dcs:
		#	self.update_value_summary(payslip, sql_update)
		#else:	
		self.calculate_summary_new(payslip)
		
	@api.multi
	def button_reset_timesheet(self):
		#payslip 	= self.browse(self.id)
		for line in self.x_timesheet_ids:
			dt=parser.parse(line.date)
			for defitem in self.employee_id.x_attendance_ids:
				if (int(defitem.dayofweek)-dt.weekday())==0:
					vals1={"category_id":defitem.category_id.id,
						"hrs_normal":defitem.normal_pay,
						"hrs_t15":defitem.paid_t15,
						"hrs_t20":defitem.paid_t20,
						"break_paid":defitem.paid_meal,
						"break_unpaid":defitem.meal_unpaid,
						"leave_annual":0.0,
						"leave_sick":0.0,
						"leave_unpaid":0.0,
						"leave_part":0.0,
						"rate_loading":0.0,
						"hrs_loading":0.0,
						}
					#_logger.error('button_reset_timesheetbutton_reset_timesheet vals1[ %s ]id[ %s ]' %  (vals1, line.id))
					line.update(vals1)
					break
		return True
		
	

class PayrollPayslipYTD(models.Model):
	_name = 'hr.payslip.ytd'
	_description = 'Payslip YTD'	
	_order = 'sequence'	
	payslip_id 	 = fields.Many2one('hr.payslip', string='Payslip')
	ytd_category = fields.Selection(dincelpayroll_vars.YTD_CATEGORY_OPTIONS, string='Category')
	sequence 	= fields.Integer("Sequence")
	ytd_total	= fields.Float(string='YTD')
	sub_total	= fields.Float(string='This Pay (Subtotal)')
	qty	= fields.Float(string='Hrs/Qty')
	debit	= fields.Float(string='Debit')
	credit	= fields.Float(string='Credit')
	employee_id = fields.Many2one("hr.employee", string="Employee", ondelete='cascade')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	date_ytd 	= fields.Date('Date Ytd')
	ref 		= fields.Char('Ref')
	fiscal_id = fields.Many2one('account.fiscalyear', string='Fiscal year')
	
class PayrollTimesheetSummary(models.Model):
	_name = 'hr.payslip.summary'
	_description = 'Payslip summary'	
	_order = 'sequence, name'	
	name 		= fields.Char('Title')
	payslip_id 	= fields.Many2one('hr.payslip', string='Payslip')
	tot_hrs		= fields.Float(string='Hours')
	pay_rate	= fields.Float(string='Rate', digits=(12, 4))
	sub_total	= fields.Float(string='This Pay (Subtotal)') #, compute="_sub_total",store=True
	pay_header = fields.Selection(dincelpayroll_vars.PAY_CATEGORY_OPTIONS, string='Header')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )
	super	= fields.Boolean(related='category_id.super')
	taxable	= fields.Boolean(related='category_id.taxable')
	is_directpay= fields.Boolean(related='category_id.is_directpay')
	account_id 	= fields.Many2one('account.account', string='GL Code', domain=[('active','=',True)])
	sequence 	= fields.Integer("Sequence")
	ytd_total	= fields.Float(string='YTD')
	is_summary	= fields.Boolean(string='Auto Sum?', default=False)
	is_manual	= fields.Boolean(string='Manual', default=False)
	tax_id = fields.Many2one("account.tax", string='Tax')
	cost_state_id = fields.Many2one("res.country.state", string='Cost State')
	costcentre_id = fields.Many2one("hr.cost.centre", string='Cost Centre')
	fiscal_id = fields.Many2one('account.fiscalyear', string='Fiscal year')
	factor_type = fields.Selection(dincelpayroll_vars.TS_FACTOR_TYPE_OPTIONS, 'Factor Type',  default='hrs') 
	xfactor		= fields.Float(string='Factor', default=1.0, digits=(8, 4))
	net_hrs		= fields.Float(string='Net Hours')
	net_rate	= fields.Float(string='Net Rate', digits=(12, 4))
	
	@api.onchange('pay_rate')
	def _onchange_pay_rate(self):
		vals={'is_manual': True}
		return {'value':vals}
		
	@api.onchange('pay_header')
	def _onchange_pay_header(self):
		if self.pay_header:
			domain={'category_id': [('category','=',self.pay_header)]}
			return {'domain':domain}
			
	@api.onchange('category_id')
	def _onchange_category_id(self):
		if self.category_id:
			vals={'name': self.category_id.name	}
			#if self.category_id.tax_id:
			#	vals['tax_id']=self.category_id.tax_id.id
			if self.category_id.expense_account_id:
				vals['account_id']=self.category_id.expense_account_id.id	
		else:		
			vals={'name': ''}
		return {'value':vals}
			
	@api.onchange('tot_hrs','pay_rate','category_id')
	def _sub_total(self):
		for record in self:
			if self.category_id.is_directpay == False:
				_result=(record.tot_hrs * record.pay_rate)  + 0.0009
				#_result=round(_result,2)
				#_result_result=round(_result,2)
				record.sub_total= round(_result,2)
			else:	
				record.sub_total=record.net_rate
		#17 x [(23.69	x 1.5)=35.535]	= 604.095 rounding issue....eg >>this became >604.09 (if no + 0.005)
		#check Brett empid 625 [pay period ending 6/nov/18]
		
	
class PayrollPaymentLine(models.Model):
	_name = 'hr.payslip.payline'
	_description = 'Other payments'
	payslip_id 	= fields.Many2one('hr.payslip', string='Payslip')
	hrs_qty	= fields.Float(string='Qty / Hours')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )
	unit_price	= fields.Float(string='Unit Price')
	sub_total	= fields.Float(string='Subtotal')#, compute="_sub_total"
	
	@api.depends('hrs_qty','unit_price')
	def _sub_total(self):
		for record in self:
			record.sub_total=record.hrs_qty * record.unit_price
			
class PayrollEmployeeTimesheet(models.Model):
	_name = 'hr.employee.timesheet'
	_description = 'Employee timesheet line'	
	name 		 = fields.Char('Day')
	sequence	 = fields.Integer('Sequence')
	employee_id  = fields.Many2one('hr.employee', string='Employee')
	category_id  = fields.Many2one('hr.pay.category', string='Pay Category') 
	date 		 = fields.Date('Date')
	hrs			 = fields.Float(string='Hours')
	xfactor		 = fields.Float(string='Hrs x Factor', default=1.0, digits=(8, 4))
	hrs_net		 = fields.Float(string='Net Hours')
	batch_id 	 = fields.Many2one('hr.timesheet.batch', string='Timesheet Import Batch',ondelete='cascade',)
	payslip_id 	 = fields.Many2one('hr.payslip', string='Timesheet Payslip',ondelete='cascade',)
	accrued_leave = fields.Boolean(related='category_id.accrued')
	reversed 	= fields.Boolean('Reversed', default=False)
	factor_type = fields.Selection(dincelpayroll_vars.TS_FACTOR_TYPE_OPTIONS, 'Factor Type',  default='hrs') 
	#dayofweek 	 = fields.Selection(dincelpayroll_vars.WEEK_DAY_OPTIONS)
	
	@api.onchange('hrs')
	def onchange_hrs(self):
		#values = {
		#	'hrs_net': self.hrs,
		#}
		#return {'value':values} 
		self.update({'hrs_net':self.hrs})	
		
	@api.onchange('date')
	def onchange_date(self):
		#_logger.error('_onchange_payfrequency:, payfrequency_id[ %s ] date_from[ %s ]' % (self.payfrequency_id, self.date_from))
		if self.date:
			dt=parser.parse(str(self.date))
			name = "%s" %  (dt.strftime("%a"))
			#name = "%s" %  (self.date.strftime("%a"))
			values = {
				'name': name,
			}
			return {'value':values} 
			
	#@api.depends('qty', 'xfactor')
	#def _compute_total(self):
	#	for record in self:
	#		record.net_hrs = record.qty * record.xfactor
	#		
class PayrollTimesheetLine(models.Model):
	_name = 'hr.payslip.timesheet'
	_description = 'Payslip timesheet line'
	name 		= fields.Char('Day')
	payslip_id 	= fields.Many2one('hr.payslip', string='Payslip')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' ) #, domain=[('type','=', 0)],
	date 		= fields.Date('Date')
	time_in		= fields.Float(string='Time In') #, compute="_compute_time"
	time_out	= fields.Float(string='Time Out') #, compute="_compute_time"
	tot_hrs		= fields.Float(string='Total Hours', compute='_compute_total')
	break_unpaid= fields.Float(string='Unpaid Break',default="0.0")
	break_paid	= fields.Float(string='Paid Break',default="0.0")
	hrs_normal	= fields.Float(string='Normal Hours',default="0.0")
	hrs_t15		= fields.Float(string='OT 1.5',default="0.0")
	rate_t15	= fields.Float(string='Rate 1.5',default="1.5")
	hrs_t20		= fields.Float(string='OT 2.0',default="0.0")
	rate_t20	= fields.Float(string='Rate 2.0',default="2.0")
	account_id 	= fields.Many2one('account.account', string='GL Account')
	project_id 	= fields.Many2one('project.project', string='Project')
	hrs_loading	= fields.Float(string='Loading / Allowance', compute='_compute_loading')
	rate_loading= fields.Float(string='% Loading',default="0.0") #0.15 for 15%, and 0.30 for 30% loading
	loading_noon	= fields.Float(string='Afternoon Shift Ldg @15%',default="0.0")
	loading_night	= fields.Float(string='Night Shift Ldg @30%',default="0.0")
	leave_annual= fields.Float(string='Annual Leave',default="0.0")
	leave_sick	= fields.Float(string='Sick Leave',default="0.0")
	leave_unpaid= fields.Float(string='Unpaid Leave',default="0.0")
	leave_part	= fields.Float(string='Part Day Leave',default="0.0")
	is_weekend	= fields.Boolean(string='Is Weekend', compute='_is_weekend')
	is_over_hours= fields.Boolean(string='Is Over Hrs', compute='_is_over_hours')
	tot_worked_hrs	= fields.Float(string="Tot. Worked Hrs", compute='_compute_total' ) #, store=True
	
	@api.multi
	@api.depends('name', 'date')
	def name_get(self):
		result = []
		for account in self:
			name = account.name + ' ' + account.date
			result.append((account.id, name))
		return result 
		
	@api.depends('name')
	def _is_weekend(self):
		for record in self:
			if record.name in ["Saturday","Sunday"]:
				record.is_weekend= True
			else:	
				record.is_weekend= False
			
	@api.depends('tot_hrs')
	def _is_over_hours(self):
		for record in self:
			if record.tot_hrs>12.00:
				record.is_over_hours= True
			else:	
				record.is_over_hours= False
				
	@api.onchange('category_id','employee_id')
	def _onchange_paycategory(self):
		if self.category_id and self.employee_id:
			if self.employee_id.x_group_id:
				amt=self.employee_id.x_group_id.normal_hrs
			else:
				amt=self.category_id.pc_amt 
			code=self.category_id.code
			vals={}
			if code=="leave-annual": #annual leave 
				vals['hrs_normal']	="0"	
				vals['leave_annual']=amt
				vals['leave_sick']	="0"
				vals['rate_loading']="0"
				sql="""select e.amount from hr_payroll_entitlement e,hr_pay_category c where e.category_id=c.id and c.summary_type='loadingleave' 
						and e.employee_id='%s'""" % (self.employee_id.id)
				self.env.cr.execute(sql)
				#_logger.error('_onchangecategory_id_onchangecavalsvals[ %s ]' %  (sql))
				rs = self.env.cr.dictfetchall()
				for row in rs:
					vals['rate_loading']= row.get('amount')
					
			elif code=="leave-personal": #Sick leave 
				vals['hrs_normal']	="0"	
				vals['leave_annual']="0"
				vals['leave_sick']	=amt
				vals['rate_loading']="0"
			else:#elif code in ["NS","DS"]: #@night shift/day shift
				vals['hrs_normal']	=amt
				vals['leave_annual']=0
				vals['leave_sick']	="0"	
				vals['rate_loading']="0"
				if code in ["night-shift","noon-shift"]:
					sql="""select e.amount from hr_payroll_entitlement e,hr_pay_category c where e.category_id=c.id and c.summary_type='loadingshift' 
							and e.employee_id='%s'""" % (self.employee_id.id)
					self.env.cr.execute(sql)
					#_logger.error('_onchangecategory_id_onchangecasqlsql[ %s ]' %  (sql))
					rs = self.env.cr.dictfetchall()
					for row in rs:
						vals['rate_loading']= row.get('amount')
			#_logger.error('_onchange_paycategory_onchange_paycategory sqlsqlsql[ %s ]' %  (vals))
			return {'value':vals} 	
		#else:
		#	_logger.error('_onchangecategory_id_onchangecategory_id[ %s ]employee_id[ %s ]' %  (self.category_id, self.employee_id))
			
	@api.depends('hrs_normal','rate_loading')
	def _compute_loading(self):
		for record in self:
			#if record.leave_sick>0.0:
			#	record.hrs_loading=record.leave_sick * 0.01  * record.rate_loading
			#el
			if record.leave_annual>0.0:
				record.hrs_loading=record.leave_annual * 0.01  * record.rate_loading
			else:
				record.hrs_loading=record.hrs_normal * 0.01  * record.rate_loading
			
	@api.depends('break_unpaid', 'break_paid','hrs_normal','hrs_t15','hrs_t20','leave_annual','leave_sick','leave_unpaid','leave_part')
	def _compute_total(self):
		for record in self:
			#record.tot_hrs = record.break_unpaid + record.break_paid + record.hrs_normal + record.hrs_t15 + record.hrs_t20 + record.leave_annual + record.leave_sick+ record.leave_unpaid + record.leave_part
			record.tot_worked_hrs = record.break_paid + record.hrs_normal + record.hrs_t15 + record.hrs_t20 + record.leave_annual + record.leave_sick+ record.leave_unpaid + record.leave_part
			record.tot_hrs =record.tot_worked_hrs+record.break_unpaid
	'''		
	#@api.depends('break_paid','hrs_normal','hrs_t15','hrs_t20','leave_annual','leave_sick','leave_unpaid','leave_part')
	@api.onchange('break_paid')
	@api.onchange('hrs_normal')
	@api.onchange('hrs_t15')
	@api.onchange('hrs_t20')
	@api.onchange('leave_annual')
	@api.onchange('leave_sick')
	@api.onchange('leave_unpaid')
	@api.onchange('leave_part')
	def _onchange_hours(self): #_compute_total(self):
		#for record in self:
		tot = record.break_paid + record.hrs_normal + record.hrs_t15 + record.hrs_t20 + record.leave_annual + record.leave_sick+ record.leave_unpaid + record.leave_part
		vals={'tot_worked_hrs':tot}
		#_logger.error('_compute_subtotal_compute_subtotal sqlsqlsql[ %s ]' %  (vals))
		return {'value':vals} 	'''
		
class DincelPayrollEmployeePayslipRun(models.Model):
	_inherit = 'hr.payslip.run'			
	x_date = fields.Date(string='Date', default=datetime.today())
	x_type = fields.Selection(dincelpayroll_vars.PAY_FREQUENCY_OPTIONS, string='Payment Frequency')
			
	@api.onchange('date_start')
	def _onchange_from_date(self):
		
		#_logger.error('_onchange_from_date_onchange_from_date[ %s ]x_type[ %s ][ %s ]',self.date_start, self.x_type, "1")
		dt_end=self.calculate_end_date(self.x_type, self.date_start)	
		if dt_end:
			self.update({'date_end':dt_end})
		#return super(DincelPayrollEmployee, self).on_date_start_change()
	def get_payslip_tax(self, _type, week_tax_amt):
		tax_amt=week_tax_amt
		if _type=="week":
			tax_amt=week_tax_amt
		elif _type=="fortnight":
			tax_amt=week_tax_amt*2
		elif _type=="month":
			tax_amt=week_tax_amt*52/12
		elif _type=="year":
			tax_amt=week_tax_amt*52
		else:
			tax_amt=week_tax_amt
		return tax_amt
		
	def get_weekly_pay(self, _type, _amt):
		week_amt=_amt
		if _type=="week":
			week_amt=_amt
		elif _type=="fortnight":
			week_amt=_amt/2.0
		elif _type=="month":
			week_amt=_amt*12.0/52.0
		elif _type=="year":
			week_amt=_amt/52.0
		else:
			week_amt=_amt
		return week_amt
		
	def calculate_end_date(self, _type, _dt, _reverse = False):
		dt_end=_dt
		try:
			if _type and _dt:
				if _type=="week":
					if _reverse:
						dt_end  =  parser.parse(_dt) -  timedelta(weeks = 1) +  timedelta(days = 1)
					else:
						dt_end  =  parser.parse(_dt) +  timedelta(weeks = 1) -  timedelta(days = 1)
				elif _type=="fortnight":
					if _reverse:
						dt_end  =  parser.parse(_dt) -  timedelta(weeks = 2) +  timedelta(days = 1)
					else:
						dt_end  =  parser.parse(_dt) +  timedelta(weeks = 2) -  timedelta(days = 1)
				elif _type=="month":
					if _reverse:
						dt_end  =  parser.parse(_dt) - relativedelta(months=1)  +  timedelta(days = 1)#+  timedelta(months = 1)
					else:
						dt_end  =  parser.parse(_dt) + relativedelta(months=1)  -  timedelta(days = 1)#+  timedelta(months = 1)
		except:
			pass
		#_logger.error('calculate_end_date calculate_end_date[ %s ][ %s ][ %s ]' % (dt_end, _type, _dt))
		return dt_end
		
	@api.onchange('x_type')
	def _onchange_payfrequency(self):
		#_logger.error('_onchange_payfrequency date_start111[ %s ]x_type[ %s ]',self.date_start, self.x_type)
		if self.date_start:
			'''_type=self.x_type
			dt_end=False
			if _type=="week":
				dt_end  =  parser.parse(self.date_start) +  timedelta(weeks = 1)
			elif _type=="fortnight":
				dt_end  =  parser.parse(self.date_start) +  timedelta(weeks = 2)
			elif _type=="month":
				dt_end  =  parser.parse(self.date_start) + relativedelta(months=1) #+  timedelta(months = 1)'''
			dt_end=self.calculate_end_date(self.x_type, self.date_start)	
			if dt_end:
				self.update({'date_end':dt_end})
		#_logger.error('_onchange_payfrequency date_start222[ %s ]x_type[ %s ]',self.date_start, self.x_type)		
		#self.update(values)	
class DincelPayrollLeave(models.Model):
	_name="hr.payslip.leave"
	payslip_id 		= fields.Many2one('hr.payslip', string='Payslip')
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	holiday_id 		= fields.Many2one('hr.holidays', string='Leave')
	date_from 		= fields.Datetime(string='Date From')		
	date_to 		= fields.Datetime(string='Date To')		
	tot_hrs 		= fields.Float("Hours", store=True, readonly=True, compute='_compute_leaves_hrs',)	
	days 			= fields.Float("Days")	
	day_ids 		= fields.Many2many('hr.payslip.timesheet', 'hr_payslip_leave_rel', 'payslip_id', 'leave_id', string='Days Excelx')
	day_ids2 		= fields.Many2many('hr.employee.timesheet', 'hr_payslip_leave_rel2', 'payslip_id', 'leave_id', string='Days Timesheet')
	category_id 	= fields.Many2one('hr.pay.category', 
			string='Leave Category') #, 
			#domain=[('active','=',True),('is_summary', '=', False),('holiday_status_id', '!=', None)] 
			
	date 			= fields.Date(string='Date')
	#holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type')
	holiday_status_id = fields.Many2one('hr.holidays.status', related='holiday_id.holiday_status_id')
	reversed 		= fields.Boolean('Reversed', default=False)
	leave_days  	= fields.One2many('hr.payslip.leave.day','payslip_leave_id', string='Leave Days')
	balance_hrs		= fields.Float("Balance Hours")	
	
	@api.depends('leave_days.hours')
	def _compute_leaves_hrs(self):
		tot_hrs=0
		try:
			if len(self.leave_days)>0:
				tot_hrs = sum(line.hours for line in self.leave_days)
		except:
			pass
		self.tot_hrs = tot_hrs	
			
	@api.onchange('date_from', 'date_to')
	def _onchange_dates(self):
		pay_from	= self.payslip_id.date_from
		pay_to		= self.payslip_id.date_to
		if pay_from and pay_to:
			pay_from	= parser.parse(pay_from)
			pay_to		= parser.parse(pay_to)
			date_from 	= self.date_from
			date_to 	= self.date_to
			if date_to and date_from:
				date_from	= parser.parse(date_from)
				date_to		= parser.parse(date_to)
			
				#_logger.error('pay_from=%s date_from=%s  date_to=%s pay_to=%s ' % (pay_from, date_from, date_to, pay_to))
				#if pay_from>date_from or date_to>pay_to:
				#	raise UserError(_("Warning! invalid from or to date found!!"))
		
	@api.onchange('day_ids')
	def _onchange_day_ids(self):
		return
		'''if self.day_ids:
			 for item in self.day_ids:
				#_logger.error('_onchange_day_ids holiday_id[ %s ] item[ %s ]category_id[ %s ]',self.holiday_id, item,item.category_id)		
				item.update({'category_id':2})
				for item2 in self.payslip_id.x_timesheet_ids:
					if item2.id==item.id:
						item2.update({'category_id':2})
						#_logger.error('_onchange_day_ids holiday_id[ %s ] item2 category_id [ %s ]category_id[ %s ]',self.holiday_id, item2.category_id,item.category_id)
						break 
			#timesheet_ids = []
			 
			_ids=[]
			for item2 in self.payslip_id.x_timesheet_ids:
				_found=False
				for item in self.day_ids:
					if item2.id==item.id:
						#item2.update({'category_id':2})
						item2.write({'category_id':2})
						if item2.id not in _ids:
							_ids.append(item2.id)
						_found=True
			for item2 in self.payslip_id.x_timesheet_ids:			
				if item2.id not in _ids:
					if item2.category_id and item2.category_id.id==2:
						item2.write({'category_id':1}) 
						
				#timesheet_ids.append(item2)	
				#_ids.append(item2.id)
			#for x in timesheet_ids:
			#	_logger.error('timesheet_idstimesheet_ids id[ %s ] item[ %s ]category_id[ %s ]', x.id, x, x.category_id)
			#self.payslip_id.write({'x_timesheet_ids': [(6, 0, [x.id for x in timesheet_ids])]})
			#self.payslip_id.write({'x_timesheet_ids': [(6, 0, list(_ids))]})'''	
	
	@api.onchange('holiday_id')
	def _onchange_holiday_id(self):
		if self.holiday_id:
			vals={'date_from': self.holiday_id.date_from, 'date_to': self.holiday_id.date_to	}
			'''hrs_normal=7.6
			sql="select sum(tot_hrs) from hr_payslip_leave where holiday_id='%s'" % (self.holiday_id.id)
			if self.employee_id:
				#hrs_normal=7.6
				for item in self.employee_id.x_attendance_ids:
					if item.dayofweek=="1":#monday..for example
						hrs_normal=item.normal_pay
						break
					
			self.env.cr.execute(sql) 
			rows = self.env.cr.fetchall()
			tot_hrs=self.holiday_id.x_total_hrs
			for row in rows:
				if row[0]:
					tot_hrs-=float(row[0])
			if tot_hrs>0.0 and 	hrs_normal>0.0:	
				vals['days']=round((tot_hrs/hrs_normal),2)	
			vals['tot_hrs']=tot_hrs		'''
			if self.holiday_id.holiday_status_id and self.holiday_id.holiday_status_id.x_category_id:
				vals['category_id']=self.holiday_id.holiday_status_id.x_category_id.id or None
					
			vals['balance_hrs']	= self.holiday_id.x_balance_hrs
			vals['date']	= self.holiday_id.date_from
			
			pay_from	= self.payslip_id.date_from
			pay_to		= self.payslip_id.date_to
			
			if pay_from and pay_to:
				if len(self.leave_days):
					self.leave_days=[(5,)] #delete or clear 
				pay_from	= parser.parse(pay_from)
				pay_to		= parser.parse(pay_to)
				#if pay_from<pay_to: assumed already 
				items=[]
				dt=pay_from
				while (dt<=pay_to):
					name 	= "%s %s" %  (dt.strftime("%a"), dt.strftime("%d/%m"))
					item = {
						'is_leave': False,
						'date': dt,
						'hours': 0,
						'name': name,
						'payslip_leave_id': self.id,#self.holiday_id.id,
						}
					items.append(item)
					dt	=	dt + timedelta(days=1) #next day loop...
				#return {'value':{'leave_days':items}}	
				vals['leave_days']=items
			return {'value':vals}
			
	@api.multi
	def write(self, values):
		#for item in self.day_ids:
		#	_logger.error('hr_payslip_leavewritewrite holiday_id[ %s ] item[ %s ]',self.holiday_id, item)		
		return super(DincelPayrollLeave, self).write(values)
	
	@api.multi
	def unlink(self):
		for item in self.day_ids:
			dt=parser.parse(item.date)
			for defitem in self.employee_id.x_attendance_ids:
				if (int(defitem.dayofweek)-dt.weekday())==0:
					if defitem.category_id:
						sql="""update hr_payslip_timesheet set category_id='%s',hrs_normal='%s',leave_annual='0',leave_sick='0'
								where id='%s'""" % (defitem.category_id.id, defitem.normal_pay, item.id)
						self.env.cr.execute(sql)
					break
		if self.holiday_id:
			sql="select 1 from hr_payslip_leave where holiday_id='%s' and id!='%s'" % (self.holiday_id.id, self.id)
			self.env.cr.execute(sql)
			rs = self.env.cr.fetchall()
			if len(rs) == 0:
				sql="update hr_holidays set x_redeem='none' where id='%s'" % (self.holiday_id.id)
			else:
				sql="update hr_holidays set x_redeem='part' where id='%s'" % (self.holiday_id.id)
			self.env.cr.execute(sql)	
		return super(DincelPayrollLeave, self).unlink() 
		
class DincelPayrollLeaveDay(models.Model):
	_name="hr.payslip.leave.day"
	payslip_leave_id 		= fields.Many2one('hr.payslip.leave', string='Payslip Leave')	
	name	= fields.Char('Name')
	date	= fields.Date('Date')
	is_leave= fields.Boolean('Leave')
	hours	= fields.Float('Hours')
	
	@api.onchange('is_leave')
	def _onchange_is_leave(self):
		val={}
		hrs_normal=7.6
		if self.payslip_leave_id.employee_id.x_group_id:
			hrs_normal=self.payslip_leave_id.employee_id.x_group_id.normal_hrs
		if self.is_leave:
			val['hours']=hrs_normal
		else:	
			val['hours']=0
		
		for line in self.payslip_leave_id.payslip_id.x_timesheet_ids2:
			#_logger.error("_onchange_is_leave_onchange_is_leave dt[%s] self[%s] hrs_normal[%s]" % (line.date, self.date, hrs_normal))
			if line.date == self.date:
				if self.is_leave:
					#val_hrs={'hrs':0,'hrs_net':0}
					hrs=0
				else:
					#val_hrs={'hrs':hrs_normal,'hrs_net':hrs_normal}
					hrs=hrs_normal
				#line.write(val_hrs)
				sql="update hr_employee_timesheet set hrs='%s',hrs_net='%s' where id='%s'" % (hrs, hrs, line.id)
				self.env.cr.execute(sql)
		return {'value':val}
		
			
class PayslipEmailQueue(models.Model):
	_name = 'hr.email.queue'
	_description = 'Email queue'
	payslip_id 		= fields.Many2one('hr.payslip', string='Payslip')	
	employee_id 	= fields.Many2one('hr.employee', string='Employee')	
	dt_added	= fields.Datetime('Date')
	dt_sent	= fields.Datetime('Sent Date')
	state	= fields.Selection([
			('queue', 'Queue'),
			('sent', 'Sent')
			], 'State',  default='queue') 
			
			