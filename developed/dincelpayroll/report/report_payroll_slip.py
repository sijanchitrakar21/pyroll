# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
#import logging
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
import logging
_logger = logging.getLogger(__name__)
class ReportPayslipCommon(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payslip_common'
	
	def _get_lines(self, payslip):
		#= self.payslip_get_lines(payslip), summary 
		lines, summary = self.env['hr.payslip.manage'].payslip_get_lines(payslip)
		'''summary={'gross_amt':"${:,.2f}".format(round(payslip.x_gross_amt,2)),
				'tax_amt':"${:,.2f}".format(round(payslip.x_tax_amt,2)),
				'net_amt':"${:,.2f}".format(round(payslip.x_net_amt,2)),
				'super_amt':"${:,.2f}".format(round(payslip.x_super_amt,2)),
				'annual_leave':"{:.2f}".format(round(payslip.x_annual_leave,2)),
				'sick_leave':"{:.2f}".format(round(payslip.x_sick_leave,2)),
				'lsl_leave':"{:.2f}".format(round(payslip.x_lsl_leave,2)),
				'lsl_enable':payslip.x_lsl_enable,
				#'gross_payslip_amt':"{:.2f}".format(round(payslip.x_gross_payslip_amt,2)),
				} 
		lines	= []
		gross_payslip_amt=0.0
		for item in payslip.x_summary_ids:
			if item.category_id and item.category_id.print_type =="hide":
				continue
			values 					= {}
			values['name'] 			= item.name
			values['type'] 			= "Wages"
			if item.category_id and item.category_id.calc4gross:
				gross_payslip_amt+= float(item.sub_total)
			if item.tot_hrs or item.ytd_total: 
				if item.tot_hrs:
					values['net_hrs'] 	= "{:.2f}".format(round(item.net_hrs or 0.0,2))
					values['tot_hrs'] 	= "{:.2f}".format(round(item.tot_hrs,2))
					values['pay_rate'] 	= "${:,.4f}".format(round(item.pay_rate,4))
					values['sub_total'] 	= "${:,.4}".format(round(item.sub_total,4))
				else:
					values['tot_hrs'] 	= ""	
					values['pay_rate'] 	= ""	
					values['sub_total']	= ""	
					values['net_hrs']	= ""	
				if item.ytd_total:	
					values['ytd_total'] 	= "${:,.4}".format(item.ytd_total)
				else:
					values['ytd_total'] 	= ""	
					
				lines.append(values)	
			 
		summary['gross_payslip_amt']="${:,.2f}".format(round(gross_payslip_amt,2))'''	
		return lines, summary 
		
	def get_report_values_new(self, ids, _active_id, data):
		model 		= 'report.employee.payroll'
		docs 		= self.env[model].browse(_active_id)
		employee_id = data['form'].get('employee_id')
		#employee  	= data['form'].get('employee')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		payslip_id 	= data['form'].get('payslip_id')
		 
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		
		payslip	=self.env['hr.payslip'].browse(payslip_id)
		lines, summary = self._get_lines(payslip)
		
		employee=self.env['hr.employee'].browse(employee_id)
		if employee.job_id:
			job_position=employee.job_id.name
		else:
			job_position="Staff"
		pay_basis, leave_rate, other_rate, rate_base,salary_annual = self.env['hr.employee.rate'].get_employee_rates(employee_id, payslip.date)
		date	= datetime.strptime(payslip.date, "%Y-%m-%d").strftime("%d/%m/%Y")
		salary=""
		if rate_base and pay_basis:
			if pay_basis=="S":
				salary="$%s + Super" % "{:,}".format(round(rate_base))
			else:
				salary="$%s " % "{:,}".format(round(salary_annual,2)) #salary="$%s Hourly" % (rate_base)
		_logger.error("pay_basis[%s] leave_rate[%s] other_rate[%s] rate_base[%s] salary_annual[%s ] " % (pay_basis, leave_rate, other_rate, rate_base, salary_annual))		
		super=""		
		for line in employee.x_super_ids:
			super+="%s " % (line.name)
		_line2="%s" % (employee.x_suburb)
		if employee.x_state_id and employee.x_state_id.code:
			_line2+=" %s" % (employee.x_state_id.code)
		if employee.x_postcode:
			_line2+=" %s" % (employee.x_postcode)
		_line3=""	
		
		ytd_sick, ytd_annual, ytd_super, ytd_tax = self.env['hr.payslip'].get_values_ytd(payslip)	
		val= {
			'doc_ids': ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_till': date_till,#str(date_till).strftime("%d/%m/%Y"),
			'date_from': date_from,
			'date_from': date_from,
			'date': date,
			'job_position': job_position,
			'employee_id': employee_id,
			'employee': employee.name,
			'address_line1': employee.x_street,
			'address_line2': _line2,
			'address_line3': _line3,
			'payfrequency':payslip.x_payfrequency_id.name,
			'salary': salary,
			'lines': lines,
			'chequeno': payslip.x_chequeno,
			'super': super,
			'summary': summary,
			'ytd_sick': "{:.2f}".format(round(ytd_sick,2)),
			'ytd_annual': "{:.2f}".format(round(ytd_annual,2)),
			'ytd_super': "${:.2f}".format(round(ytd_super,2)),
			'ytd_tax': "${:.2f}".format(round(ytd_tax,2)),
		}
		#_logger.error('report_leavesummaryreport_leavesummary 222[ %s ]lines[ %s ]' %  (self.ids, lines))
		return val
		
class ReportPayrollPagePayslip(models.AbstractModel):
	_name = 'report.dincelpayroll.report_pagepayslip'
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		#if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
		#	raise UserError(_("Payslip report content is missing, this report cannot be printed."))
		if not data.get('form'):
			raise UserError(_("Payslip report content is missing, this report cannot be printed."))
		_ids=self.ids	
		_active_id=data['form'].get('active_id')#self.env.context.get('active_id')
		#_active_id2=self.env.context.get('active_id')
		#_logger.error('get_report_values _active_id[ %s ]_active_id2[ %s ]' %  (_active_id, _active_id2))
		return self.env['report.dincelpayroll.report_payslip_common'].get_report_values_new(_ids, _active_id, data)	
		'''
		model 		= 'report.employee.payroll'
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		#employee  	= data['form'].get('employee')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		payslip_id 	= data['form'].get('payslip_id')
		 
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		
		payslip	=self.env['hr.payslip'].browse(payslip_id)
		lines, summary = self._get_lines(payslip)
		
		employee=self.env['hr.employee'].browse(employee_id)
		if employee.job_id:
			job_position=employee.job_id.name
		else:
			job_position="Staff"
		pay_basis, leave_rate, other_rate, rate_base = self.env['hr.employee.rate'].get_employee_rates(employee_id, payslip.date)
		date	= datetime.strptime(payslip.date, "%Y-%m-%d").strftime("%d/%m/%Y")
		salary=""
		if rate_base and pay_basis:
			if pay_basis=="S":
				salary="$%s + Super" % "{:,}".format(round(rate_base))
			else:
				salary="$%s Hourly" % (rate_base)
		super=""		
		for line in employee.x_super_ids:
			super+="%s " % (line.name)
		_line2=employee.x_suburb
		if employee.x_state_id:
			_line2+=" " + employee.x_state_id.code
		_line2+=" " + employee.x_postcode		
		_line3=""	
		ytd_sick, ytd_annual, ytd_super, ytd_tax = self.env['hr.payslip'].get_values_ytd(payslip)	
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_till': date_till,#str(date_till).strftime("%d/%m/%Y"),
			'date_from': date_from,
			'date_from': date_from,
			'date': date,
			'job_position': job_position,
			'employee_id': employee_id,
			'employee': employee.name,
			'address_line1': employee.x_street,
			'address_line2': _line2,
			'address_line3': _line3,
			'payfrequency':payslip.x_payfrequency_id.name,
			'salary': salary,
			'lines': lines,
			'chequeno': payslip.x_chequeno,
			'super': super,
			'summary': summary,
			'ytd_sick': "{:.2f}".format(round(ytd_sick,2)),
			'ytd_annual': "{:.2f}".format(round(ytd_annual,2)),
			'ytd_super': "${:.2f}".format(round(ytd_super,2)),
			'ytd_tax': "${:.2f}".format(round(ytd_tax,2)),
		}
		#_logger.error('report_leavesummaryreport_leavesummary 222[ %s ]lines[ %s ]' %  (self.ids, lines))
		return val'''
	'''	
	def _get_lines(self, payslip):
		 
		
		 
		res	= []
		for item in payslip.x_summary_ids:
			values 					= {}
			values['name'] 			= item.name
			values['type'] 			= "Wages"
			if item.tot_hrs or item.ytd_total: 
				if item.tot_hrs:
					values['tot_hrs'] 	= "{:.2f}".format(round(item.tot_hrs,2))
					values['pay_rate'] 	= "${:,.2f}".format(round(item.pay_rate,2))
					values['sub_total'] 	= "${:,.2f}".format(round(item.sub_total,2))
				else:
					values['tot_hrs'] 	= ""	
					values['pay_rate'] 	= ""	
					values['sub_total']	= ""	
					
				if item.ytd_total:	
					values['ytd_total'] 	= "${:,.2f}".format(item.ytd_total)
				else:
					values['ytd_total'] 	= ""	
					
				res.append(values)	
			 
			
		return res, summary '''
'''		
class ReportPayrollPagePayslipHtml(models.AbstractModel):
	_name = 'report.dincelpayroll.report_pagepayslip_html'	 
	@api.model
	def get_report_values(self, docids, data=None):
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		_ids=self.ids	
		_active_id=self.env.context.get('active_id')
		return self.env['report.dincelpayroll.report_payslip_common'].get_report_values_new(_ids, _active_id, data)	
	
class ReportPayrollPagePayslipPdf(models.AbstractModel):
	_name = 'report.dincelpayroll.report_pagepayslip_pdf'	 
	_template = 'dincelpayroll.report_pagepayslip'
	@api.model
	def get_report_values(self, docids, data=None):
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		_ids=self.ids	
		_active_id=self.env.context.get('active_id')
		return self.env['report.dincelpayroll.report_payslip_common'].get_report_values_new(_ids, _active_id, data)	'''