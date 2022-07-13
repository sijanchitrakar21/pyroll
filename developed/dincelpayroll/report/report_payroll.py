# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import os
import logging
import base64
import csv
from io import StringIO
from datetime import date, datetime, timedelta
import datetime as dt
#from datetime import date
#from datetime import datetime
#import datetime
import dateutil
from dateutil import parser
#import pyexcel as pe
'''
	#---------------------------------------------------------------------
	all payroll reports below..............
	#---------------------------------------------------------------------
	Activity Summary:		'actsummary'
	Activity Details:		'actdetails'
	Employment Details:		'empdetails'
	Payroll advice:			'payadvice'
	Timesheets: 			'emptimesheet'
	Unprossessed Timesheets:'pendingtimesheet'
	Standard Pay Details:	'stdpaydtl'
	Accruals:				'super_accurals'
	Super Summary			'super_summary'
	Super Contribution(ATO)	'super_ato'
	Forcast Accruals:		'forecastaccurals'
	Summary:				'entitlesumm'
	Details:				'entitledetails'
	Payroll Tax Report:			'payrolltax'
	Payroll Tax Payment:		'payrolltaxpay'
	PAYG Witholding Tax:		'paygtax'
	Payment Summary Report:		'yearend'
	ATO EMPDUPE Media File:		'atomedia'
	Preview EMPDUPE Media File:	'atopreview'
	Costing Reports:			'costing'
	Payroll Summary:			'paysummary'
	Payroll Register Summary:	'payregistersummary'
	Payroll Entries:			'payentry'
	Allowances:					'payallowance'
	Deductions:					'paydeduction'
	Termination Pay Details:	'payterminate'
	Salary Sacrifice:			'salsacrifice'
	Hours Worked: 				'hrsworked'
	Employee Annivesary dates:	'annidates'
	Payrun Journals:			'payrunjurn'
	Leave liablity Journals:	'leaveliabjurn'
	Payroll Tax Journals: 		'taxjurn'
	#---------------------------------------------------------------------
'''
_logger = logging.getLogger(__name__)

class PayrollReport(models.TransientModel):
	_name = 'hr.payroll.report'
	_description = 'Payroll Report'
	date_till 		= fields.Date('Date To', default=lambda self: self._context.get('date', fields.Date.context_today(self)))
	date_from		= fields.Date('Date From', default=lambda self: self._context.get('date', fields.Date.context_today(self)))
	reportcode 		= fields.Char('Report')
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	employee_lines  = fields.One2many('hr.report.employee.line','report_id', string='Employees')
	check_all = fields.Boolean("Check All", default=True)
	individual = fields.Boolean("Individual", default=False) 
	archived = fields.Boolean("Archived Employee", default=False) 
	group_id = fields.Many2one('hr.employee.group', string='Employee Group')	
	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
	group_ids = fields.Many2many('hr.employee.group', 'payroll_report_group_rel', 'report_id', 'group_id', string='Groups')
	
	@api.onchange('group_ids')
	def _onchange_group_ids(self):
		emp_obj	=self.env['hr.employee']
		_lines	=[]
		id_list	=[]
		ids1	=[]
		
		if self.archived:
			_active=False
		else:
			_active=True
		all_user=False	
		for grp in self.group_ids:
			if grp.code=="ALL":	
				all_user=True
				ids1 = self.env['hr.employee'].search([('active', '=', _active)],order='x_last_name asc, x_first_name asc')
				for emp in ids1:
					_lines.append({'employee_id':emp.id,'selected':True,})
		if not all_user:
			for grp in self.group_ids:
				ids1 = emp_obj.search([('x_group_id', '=', grp.id),('active', '=', _active)],order='x_last_name asc, x_first_name asc')
				for emp in ids1:
					_lines.append({'employee_id':emp.id,'selected':True,})
				
		if len(self.employee_lines) > 0:
			self.employee_lines = [(5,)]	
			
		values = {
			'employee_lines': _lines,
		}
		
		if len(id_list)>0:
			domain  = {'employee_id': [('id','in', (id_list))]}
		else:
			domain	= {}
		#_logger.error('_onchange_archived_onchange_archived values[ %s ][ %s ]' % (domain, _active))
		return {'domain': domain,'value':values}	
		
		
	@api.onchange('archived')
	def _onchange_archived(self):
		_lines	=[]
		id_list	=[]
		ids1	=[]
		if self.archived:
			_active	= False
			ids1 	= self.env['hr.employee'].search([('active', '=', _active)],order='x_last_name asc, x_first_name asc') #[('x_current', '=', True),
		else:
			_active	= True
		if self.group_id:
			
			if self.group_id.code=="ALL":
				ids1 = self.env['hr.employee'].search([('active', '=', _active)],order='x_last_name asc, x_first_name asc') #[('x_current', '=', True),
			else:
				ids1 = self.env['hr.employee'].search([('x_group_id', '=', self.group_id.id),('active', '=', _active)],order='x_last_name asc, x_first_name asc')
				
		for emp in ids1:
			_lines.append({'employee_id':emp.id, 'selected':True,})
			#id_list.append(emp.id)
			#else:
			
			
		ids2 = self.env['hr.employee'].search([('active', '=', _active)],order='x_last_name asc, x_first_name asc')
		for emp in ids2:
			id_list.append(emp.id)
		if len(self.employee_lines) > 0:
			self.employee_lines = [(5,)]	
		values = {
			'employee_lines': _lines,
		}
		if len(id_list)>0:
			domain  = {'employee_id': [('id','in', (id_list))]}
		else:
			domain={}
		#_logger.error('_onchange_archived_onchange_archived values[ %s ][ %s ]' % (domain, _active))
		return {'domain': domain,'value':values}
		
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
	
	@api.onchange('group_id')
	def _onchange_group(self):
		#ret=False
		_lines=[]
		if self.archived:
			_active=False
		else:
			_active=True
		if self.group_id:
			if self.group_id.code == "ALL":
				ids1 = self.env['hr.employee'].search([('active', '=', _active)], order='x_last_name asc, x_first_name asc') #[('x_current', '=', True),
			else:
				ids1 = self.env['hr.employee'].search([('x_group_id', '=', self.group_id.id),('active', '=', _active)], order='x_last_name asc, x_first_name asc')
				#('x_current', '=', True),
				#if self.group_id.code=="individual":
				#	ret=True
			for emp in ids1:
				_lines.append({'employee_id': emp.id, 'selected':True,})
				
		if len(self.employee_lines) > 0:
			self.employee_lines = [(5,)]	
			
		values = {
			'employee_lines': _lines,
			#'individual': ret,
			'check_all': True,
		}
		#_logger.error('_onchange_individual_onchange_individual values[ %s ][ %s ]',self.group_id, values)
		return {'value':values} 
		
	def _build_comparison_context(self, data):
		result = {}
		return result
		
	def _print_report_root(self, data):
		raise NotImplementedError()
		
	def get_csv_paysuper_ato(self, empids):
		date_from, date_till = self.date_from, self.date_till
		csv="""Surname, First name, Date of birth (dd/mm/yyyy), Contribution payment start date (dd/mm/yyyy), Contribution payment end date (dd/mm/yyyy),Super guarantee ,
			,Personal , Salary sacrifice , Employer additional , Spouse , Award/Productivity , Total (optional) ,\n"""
		lines, summary = self.env['hr.payroll.report'].get_paysuper_summary_lines(date_from, date_till, empids)
		for item in lines:
		
			emp_surname		=item['emp_surname']
			emp_fname		=item['emp_fname']
			emp_dob			=item['emp_dob']
			date_start		=item['date_start']
			date_end		=item['date_end']
			super_amt		=item['super_amt']
			personal_amt	=item['personal_amt']
			sacrifice_amt	=item['sacrifice_amt']
			employer_amt	=item['employer_amt']
			spouse_amt		=item['spouse_amt']
			award_amt		=item['award_amt']
			csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (emp_name, emp_no, super_fund, super_member_no, "SGC Superannuation", super_amt)
			for item2 in item['super_list']:
				super_text	=item2['super_text']
				super_amt	=item2['super_amt']
				csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (emp_name, emp_no, super_fund, super_member_no, super_text, super_amt)
				
		tot_super_amt=summary['tot_super_amt']
		csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % ("","", "", "", "TOTAL", tot_super_amt)	
		
		return csv
		
	def get_csv_paysuper_summary(self, empids):
		date_from, date_till = self.date_from, self.date_till
		csv="employee, gross_amt, deduct_amt, tax_amt, net_amt, expense_amt,\n"
		lines, summary = self.env['hr.payroll.report'].get_paysuper_summary_lines(date_from, date_till, empids)
		for item in lines:
		
			emp_name		=item['emp_name']
			emp_no			=item['emp_no']
			super_fund		=item['super_fund']
			super_member_no	=item['super_member_no']
			super_amt		=item['super_amt']
			
			csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (emp_name, emp_no, super_fund, super_member_no, "SGC Superannuation", super_amt)
			for item2 in item['super_list']:
				super_text	=item2['super_text']
				super_amt	=item2['super_amt']
				csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (emp_name, emp_no, super_fund, super_member_no, super_text, super_amt)
				
		tot_super_amt=summary['tot_super_amt']
		csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % ("","", "", "", "TOTAL", tot_super_amt)	
		
		return csv
		
	def get_csv_payregistersummary(self, empids):
		date_from, date_till = self.date_from, self.date_till
		csv="employee, gross_amt, deduct_amt, tax_amt, net_amt, expense_amt,\n"
		lines, summary = self.env['hr.payroll.report'].get_payregistersummary_lines(date_from, date_till, empids)
		for item in lines:
			#item={}
			emp_name		=item['emp_name']
			gross_amt		=item['gross_amt']
			deduct_amt		=item['deduct_amt']
			tax_amt			=item['tax_amt']
			net_amt			=item['net_amt']
			expense_amt		=item['expense_amt']
			csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (emp_name, gross_amt, deduct_amt, tax_amt, net_amt, expense_amt)
		tot_gross_amt		=summary['gross_amt'] or 0.0
		tot_deduct_amt		=summary['deduct_amt'] or 0.0
		tot_tax_amt			=summary['tax_amt'] or 0.0
		tot_net_amt			=summary['net_amt'] or 0.0
		tot_expense_amt		=summary['expense_amt'] or 0.0
		csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % ("TOTAL",tot_gross_amt, tot_deduct_amt, tot_tax_amt, tot_net_amt, tot_expense_amt)	
		return csv
		
	def get_csv_paysummary(self, empids):
		
		csv="id, first name, last name, emp no, date, payslip ref, gross amt,gross payslip_amt, tax amt, net amt,  super amt, leave_annual, leave personal, lsl, ytd_personal, ytd_annual, ytd_lsl, is_timesheet,\n"
		
		#@_logger.error('get_csv_paysummaryget_csv_paysummary individual[ %s ]empids[ %s ]',self.individual, empids)
					
		lines = self.get_paysummary_lines(self.date_from, self.date_till, empids)
		
		#_logger.error('get_csv_paysummaryget_csv_paysummary222 [ %s ][ %s ]lines[ %s ]' % (self.reportcode,self.individual, lines))
		for item in lines:
			#item={}
			emp_name	=item['emp_name']
			first_name	=item['first_name']
			last_name	=item['last_name']
			date		=item['date']
			emp_no		=item['emp_no']
			payslip_ref	=item['payslip_ref']
			gross_amt	=item['gross_amt']
			tax_amt		=item['tax_amt']
			net_amt		=item['net_amt']
			super_amt	=item['super_amt']
			leave_annual	=item['leave_annual']
			leave_personal	=item['leave_personal']
			leave_lsl	=item['leave_lsl']
			payslip_id		=item['payslip_id']
			ytd_personal	=item['ytd_personal']
			ytd_annual		=item['ytd_annual']
			ytd_lsl			=item['ytd_lsl']
			is_timesheet	=item['is_timesheet']
			gross_payslip_amt	=item['gross_payslip_amt']
			
			csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (payslip_id, first_name,last_name, emp_no, date, payslip_ref, gross_amt,gross_payslip_amt, tax_amt, net_amt,  super_amt, leave_annual, leave_personal,leave_lsl,ytd_personal,ytd_annual,ytd_lsl,is_timesheet)
			
		return csv
		
		
	def get_csv_payentry(self, empids):
		csv="id, name, emp no, date, payslip ref, gross amt, tax amt, net amt,  super amt, leave_annual, leave personal, ytd_personal, ytd_annual, ytd_lsl, is_timesheet,\n"
		
		has_detail=True
					
		lines = self.get_paysummary_lines(self.date_from, self.date_till, empids, has_detail)
		
		for item in lines:
		
			payslip_id	=item['payslip_id']
			emp_name	=item['emp_name']
			date		=item['date']
			emp_no		=item['emp_no']
			payslip_ref	=item['payslip_ref']
			gross_amt	=item['gross_amt']
			tax_amt		=item['tax_amt']
			net_amt		=item['net_amt']
			super_amt	=item['super_amt']
			leave_annual	=item['leave_annual']
			leave_personal	=item['leave_personal']
			
			ytd_personal	=item['ytd_personal']
			ytd_annual		=item['ytd_annual']
			ytd_lsl			=item['ytd_lsl']
			is_timesheet	=item['is_timesheet']
		
			
			csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (payslip_id, emp_name, emp_no, date, payslip_ref, gross_amt, tax_amt, net_amt,  super_amt, leave_annual, leave_personal,ytd_personal,ytd_annual,ytd_lsl,is_timesheet)
			#lines2	=item['summary_line']
			for item2 in item['summary_line']:
				#emp_name		=item['emp_name']
				date			=""
				#emp_no			=item['emp_no']
				payslip_ref		=item2['catname']
				gross_amt		=item2['sub_total']
				tax_amt			=""
				net_amt			=""
				super_amt		=""
				leave_annual	=""
				leave_personal	=""
				#payslip_id		=""
				ytd_personal	=""
				ytd_annual		=""
				ytd_lsl			=""
				is_timesheet	=""
				
				csv += "\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (payslip_id, emp_name, emp_no, date, payslip_ref, gross_amt, tax_amt, net_amt,  super_amt, leave_annual, leave_personal, ytd_personal, ytd_annual,ytd_lsl, is_timesheet)
		return csv
	
	def get_csv_open_balance(self,empids,date_from, date_till):
		
		csv=""
		sub_headers	=self.get_balance_headers()
		csv+="open balance till[%s]" % (date_till)
		csv+="\n"	
		csv+="id, emp name, emp no, gross ytd, net amt, payg ytd, super ytd, sick/personal leave, leave annual, ytd_lsl, total,"
		for item in sub_headers:
			csv+="\"%s-%s\"," % (item['id'],item['name'])
		csv+="\n"	
		
		#_logger.error('get_csv_open_balance111 csv[ %s ][ %s ]lines[ %s ]' % (csv,date_from, date_till))
		
		lines = self.get_balance_lines(date_from, date_till, empids, sub_headers)
		
		for item in lines:
			
			id		=item['id']
			#date	=item['date']
			name	=item['name']
			number	=item['number']
			
			gross_ytd		=item['gross_ytd']
			net_ytd	=item['net_ytd']
			payg_ytd	=item['payg_ytd']
			super_ytd	=item['super_ytd']
			sick_leave	=item['sick_leave']
			annual_leave=item['annual_leave']
			lsl_leave	=item['lsl_leave']
			
			total	=item['total']
			csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"," % (id,  name, number, gross_ytd, net_ytd, payg_ytd, super_ytd, sick_leave, annual_leave, lsl_leave, total)
			for line in item['items']:
				qty=line['qty']
				csv+="\"%s\"," % (qty)
			csv+="\n"	
				
		return csv 
		
	@api.multi 
	def csv_export_external_app(self):
		ts_app=self.env['dincelaccount.settings'].get_timesheet_app()
		#_logger.error("csv_export_external_app curr=[%s]" % (ts_app))
		csv=""
		empids=[]
		if self.individual and self.employee_id:
			empids.append(self.employee_id.id)
		else:
			for emp in self.employee_lines:
				if emp.selected:
					empids.append(emp.employee_id.id)
					
		if self.reportcode == "entitledetails":
			csv = self.env['report.employee.leavebalance'].exp_leave_balance_all(ts_app, empids, self.date_till)		
		else:
			csv =""
		temp_path	="/var/tmp/odoo/payroll/"#+fname	
		fname		="%s" % (self.reportcode)
		if ts_app and self.reportcode=="entitledetails":
			#fname+="_%s" % (ts_app)
			fname="leavebalance"
		fname+=".csv"	
		_path		=temp_path+fname	
		#with open(_path, "w+") as _file:
		#	_file.write("%s" % csv) 
		'''os.makedirs(os.path.dirname(save_as), exist_ok=True)
		with open(save_as, 'a') as the_file:
			the_file.write(csv)

		w  write mode
		r  read mode
		a  append mode

		w+  create file if it doesn't exist and open it in write mode
		r+  create file if it doesn't exist and open it in read mode
		a+  create file if it doesn't exist and open it in append mode

		'''
		#return {
		#		'name': 'CSV Report',
		#		'res_model': 'ir.actions.act_url',
		#		'type' : 'ir.actions.act_url',
		#		'url': '/web/binary/download_file?model=account.invoice&field=datas&id=%s&path=%s&filename=%s' % (-1, temp_path, fname),
		#		'context': {}}	
		model, idid, title="report.employee.payroll", -1, "CSV File"	
		self.env['dincel.utils'].write_file(temp_path, fname,  csv)
	
		return self.env['dincel.utils'].download_file(model, idid, title, temp_path, fname)
	
	@api.multi
	def csv_payroll_report(self):
		csv=""
		empids=[]
		if self.individual and self.employee_id:
			empids.append(self.employee_id.id)
		else:
			for emp in self.employee_lines:
				if emp.selected:
					empids.append(emp.employee_id.id)
		
		#_logger.error('csv_payroll_reportcsv_payroll_report [ %s ][ %s ]empids[ %s ]' % (self.reportcode,self.individual, empids))			
		
		if self.reportcode=="entitlesumm":	
			
			csv="empno,employee,entitlement,opening balance,hrs accrued, hrs taken,available hrs,value,\n"
			
			if self.individual:
				
				emp		=self.employee_id 
				name	=emp.name
				empno	=emp.x_emp_number
				lines =self.env['report.dincelpayroll.report_leavesummary']._get_lines(emp.id, self.date_from, self.date_till)
				for item in lines:
					
					entitle	=item['name']
					openbal	=item['hrs_open']
					accrued	=item['hrs_accrued']
					taken	=item['hrs_taken']
					available	=item['hrs_balance']
					value		=item['hrs_value']
					csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\", \n" % (empno,name,entitle,openbal,accrued,taken,available,value)
					
			else:
				#emplines=[]
				for line in self.employee_lines:
					if line.selected:
						emp=line.employee_id
						 
						#model 		= 'report.employee.leavebalance'
						#lines =self.env['report.dincelpayroll.report_leavesummary']._get_lines(emp.id, self.date_from, self.date_till)
						#for empid in empids:
						#obj1=self.env['hr.employee'].browse(empid)
						lines =self.env['report.employee.leavebalance'].get_leave_summary_lines(emp.id, self.date_from, self.date_till)
					
						#val= {'employee':obj1.name,
						#		'lines':lines}
						#e#mplines.append(val) 	
						name	=emp.name
						empno	=emp.x_emp_number
						
						entitle,openbal,accrued,taken,available,value="","","","","",""
						
						csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\", \n" % (empno,name,entitle,openbal,accrued,taken,available,value)
						for item in lines:
							
							entitle	=item['name']
							openbal	=item['hrs_open']
							accrued	=item['hrs_accrued']
							taken	=item['hrs_taken']
							available	=item['hrs_balance']
							value		=item['hrs_value']
							csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\", \n" % (empno,name,entitle,openbal,accrued,taken,available,value)
							
						name	=""
						empno	=""
						entitle,openbal,accrued,taken,available,value="","","","","",""
						csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\", \n" % (empno,name,entitle,openbal,accrued,taken,available,value)	
				csv+=""	
				
		elif self.reportcode=="entitledetails":
			csv= self.env['report.employee.leavebalance'].get_csv_leave_lines_all(empids, self.date_from, self.date_till)
			'''
			csv+="empno, employee, ref, date,  annual accrued, annual taken, personal accrued, personal taken, parent taken,long service accrued, long service taken,\n"
			emp		=self.employee_id 
			name	=emp.name
			empno	=emp.x_emp_number
			lines, summary 	= self.env['report.dincelpayroll.report_leavedetails']._get_lines(emp.id, self.date_from, self.date_till)
			
			for item in lines:
				ref				=item['name']
				date			=item['date']
				leave_annual_a	=item['leave_annual_a']
				leave_annual_t	=item['leave_annual_t']
				leave_sick_a	=item['leave_sick_a']
				leave_sick_t	=item['leave_sick_t']
				leave_parent_a	=item['leave_parent_a']
				leave_parent_t	=item['leave_parent_t']
				leave_lsl_a		=item['leave_lsl_a']
				leave_lsl_t		=item['leave_lsl_t']
				
				csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (empno, name, ref, date, leave_annual_a, leave_annual_t, leave_sick_a, leave_sick_t,  leave_parent_t, leave_lsl_a, leave_lsl_t)
			
			ref="BALANCE"
			date=""
	
			csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (empno, name, ref, date, "", summary['annual_net'], "", summary['sick_net'],  summary['parent_net'], "", summary['lsl_net'])'''
		elif self.reportcode=="payentry":#or paydetails
			csv+=self.get_csv_payentry(empids)
		elif self.reportcode=="paysummary":
			csv+=self.get_csv_paysummary(empids)
		elif self.reportcode=="payregistersummary":
			csv+=self.get_csv_payregistersummary(empids)	
		elif self.reportcode=="super_summary":
			csv+=self.get_csv_paysuper_summary(empids)	
		elif self.reportcode=="super_ato":	
			csv+=self.get_csv_paysuper_ato(empids)	
		elif self.reportcode=="opening_balance":
			csv+=self.get_csv_open_balance(empids,self.date_from, self.date_till)
		elif self.reportcode=="empdetails":
			csv+=self.env['hr.employee.report'].get_csv_employee_details(empids, self.date_till)
		elif self.reportcode=="payslip":
			csv+=""
		else:
			csv+=""
		temp_path=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/payroll/"	
		#temp_path	="/var/tmp/odoo/payroll/"#+fname	
		fname		="%s.csv" % (self.reportcode)
		_path		=temp_path+fname	
		#with open(_path, "w+") as _file:
		#	_file.write("%s" % csv) 
		'''os.makedirs(os.path.dirname(save_as), exist_ok=True)
		with open(save_as, 'a') as the_file:
			the_file.write(csv)

		w  write mode
		r  read mode
		a  append mode

		w+  create file if it doesn't exist and open it in write mode
		r+  create file if it doesn't exist and open it in read mode
		a+  create file if it doesn't exist and open it in append mode

		'''
		#return {
		#		'name': 'CSV Report',
		#		'res_model': 'ir.actions.act_url',
		#		'type' : 'ir.actions.act_url',
		#		'url': '/web/binary/download_file?model=account.invoice&field=datas&id=%s&path=%s&filename=%s' % (-1,temp_path,fname),
		#		'context': {}}	
		model, idid, title="report.employee.payroll", -1, "CSV File"	
		self.env['dincel.utils'].write_file(temp_path, fname,  csv)
	
		return self.env['dincel.utils'].download_file(model, idid, title, temp_path, fname)
	
	@api.multi
	def check_payroll_report(self):

		res 			= {}
		
		data 			= {}
		data['ids'] 	= self.env.context.get('active_ids', [])
		#if self.reportcode=="paygtax":
		#	model 			= 'report.employee.payroll'
		#else:
		model 			= 'report.employee.leavebalance'
		data['model'] 	= model
		data['form'] 	= self.read(['date_till','date_from', 'employee_id', 'company_id','group_id','employee_lines','individual','archived'])[0]
		
		empids=[]
		if not self.individual:
			for emp in self.employee_lines:
				if emp.selected:
					empids.append(emp.employee_id.id)
			#if not self.individual:
			data['form']['empids'] = empids		
		if self.reportcode=="entitlesumm":
			if self.individual:
				res = self._print_report_entitlesumm(data)
			else:
				res = self._print_report_entitlesumm_all(data)#data['form']['empids'] = empids
				#res = self.env.ref('dincelpayroll.action_report_leavesummary_all').report_action(self, data=data, config=False)	
		elif self.reportcode=="entitledetails":
			if self.individual:
				res = self._print_report_entitledetails(data)
			else:
				res = self._print_report_entitledetails_all(data)
		elif self.reportcode=="payslip":
			res = self._print_report_payslip(data)
		elif self.reportcode=="payslip_pdf":
			res = self._print_report_payslip_pdf(data)
		elif self.reportcode=="paygtax":
			data['model'] 	= 'report.employee.payroll'#'report.employee.payroll'
			res = self._print_report_payg(data)
		elif self.reportcode=="payentry":
			#report_payroll_entries_document
			data['model'] 	= 'report.employee.payroll'
			res = self._print_report_payentry(data)
		elif self.reportcode=="paysummary":
			data['model'] 	= 'report.employee.payroll'
			#report_payroll_entries_document
			#_logger.error('_print_report_paysummary individual[ %s ]empids[ %s ]',self.individual, empids)
			res = self._print_report_paysummary(data)
		elif self.reportcode=="payregistersummary":
			data['model'] 	= 'report.employee.payroll'	
			res = self._print_report_payregistersummary(data)
		elif self.reportcode=="super_summary":
			data['model'] 	= 'report.employee.payroll'	
			res = self._print_report_paysuper_summary(data)
		elif self.reportcode=="opening_balance":
			data['model'] 	= 'report.employee.payroll'
			res = self._print_report_opening_balance(data)
		elif self.reportcode=="empdetails":
			data['model'] 	= 'report.employee.payroll'
			return self.env.ref('dincelpayroll.action_employee_details').report_action(self, data=data, config=False)	
		elif self.reportcode=="yearend":
			data['model'] 	= 'report.employee.payroll'
			return self.env.ref('dincelpayroll.action_payg_summary_annual').report_action(self, data=data, config=False)	
		else:
			res = self._print_report(data)
		return res
	
	def _print_report(self, data):
		return self.env.ref('dincelpayroll.action_report_defaultpage').report_action(self, data=data, config=False)	
		
	def _print_report_payentry(self, data):
		return self.env.ref('dincelpayroll.action_report_payentry').report_action(self, data=data, config=False)

	def _print_report_opening_balance(self, data):
		return self.env.ref('dincelpayroll.action_report_opening_balance').report_action(self, data=data, config=False)
		
	def _print_report_paysummary(self, data):
		return self.env.ref('dincelpayroll.action_report_paysummary').report_action(self, data=data, config=False)
		
	def _print_report_paysuper_summary(self, data):
		return self.env.ref('dincelpayroll.action_report_paysuper_summary').report_action(self, data=data, config=False)		
		
	def _print_report_payregistersummary(self, data):
		return self.env.ref('dincelpayroll.action_report_payregistersummary').report_action(self, data=data, config=False)	
		
	def _print_report_entitlesumm(self, data):
		return self.env.ref('dincelpayroll.action_report_leavesummary').report_action(self, data=data, config=False)	
	
	def _print_report_entitlesumm_all(self, data):
		return self.env.ref('dincelpayroll.action_report_leavesummary_all').report_action(self, data=data, config=False)		
	
	def _print_report_entitledetails(self, data):
		return self.env.ref('dincelpayroll.action_report_leavedetails').report_action(self, data=data, config=False)	
	
	def _print_report_entitledetails_all(self, data):
		return self.env.ref('dincelpayroll.action_report_leavedetails').report_action(self, data=data, config=False)	
		
	def _print_report_payslip(self, data):#not in use...16/10/18 //replaced by action_report_payslip_all
		return self.env.ref('dincelpayroll.action_report_pagepayslip').report_action(self, data=data, config=False)	
		
	def _print_report_payslip_pdf(self, data):#not in use...16/10/18
		return self.env.ref('dincelpayroll.action_report_pagepayslip_pdf').report_action(self, data=data, config=False)	
		
	def _print_report_payg(self, data):
		return self.env.ref('dincelpayroll.action_report_payg_summary').report_action(self, data=data, config=False)	
	
	def get_payslip_gross_calculated(self, payslip_id):
		gross_amt=0.0
		sql="select sum(d.sub_total)  "
		sql += " from hr_payslip p,hr_payslip_summary d,hr_pay_category c   "
		sql += " where d.payslip_id=p.id and c.calc4gross='t' "
		sql += " and c.id=d.category_id "
		sql += " and p.id='%s'" % (payslip_id)
		self._cr.execute(sql)
		
		rows1 = self._cr.dictfetchall()
		#_logger.error('get_payslip_gross_calculated [ %s ] [ %s ]  ' % (sql, rows1))
		for row in rows1:
			if row['sum']:
				gross_amt  += float(row['sum'])
		return gross_amt	
		
	def get_payslip_detail(self, payslip_id):
		res 	= []
		sql="select d.tot_hrs,d.pay_rate,d.sub_total,c.name as catname  "
		sql += " from hr_payslip p,hr_payslip_summary d,hr_pay_category c   "
		sql += " where d.payslip_id=p.id"
		sql += " and c.id=d.category_id "
		sql += " and p.id='%s'" % (payslip_id)
		self._cr.execute(sql)
		rows1 = self._cr.dictfetchall()
		for row in rows1:
			catname	  =row['catname']	
			tot_hrs   =row['tot_hrs']	
			pay_rate  =row['pay_rate']	
			sub_total =row['sub_total']	
			val={'catname':catname, 'tot_hrs':tot_hrs, 'pay_rate':pay_rate, 'sub_total':sub_total}
			res.append(val)
		return res	
		
	def get_paysuper_summary_lines(self, date_from, date_till, empids, has_detail=False):
		summary	= {}
		res 	= []	
		tot_super_amt	= 0.0
		sql="select e.id,e.name,e.x_first_name,e.x_last_name,e.x_emp_number from hr_employee e where e.id in(%s) order by e.x_last_name,e.x_first_name" % (str(empids).strip('[]'))
		#_logger.error("get_payregistersummary_linesget_payregistersummary_lines[%s]" % (sql))
		self._cr.execute(sql)
		rows = self._cr.dictfetchall()
		for row in rows:
			#emp_name	=row['name']	
			emp_no			= row['x_emp_number']	
			employee_id 	= row['id']	
			first_name		= row['x_first_name'] or ''
			last_name		= row['x_last_name'] or ''
			super_member_no	= ""
			super_fund		= ""
			if last_name or last_name:
				emp_name	= "%s, %s" % (last_name, first_name)
			else:
				emp_name	= row['name'] or ''

			sql  = "SELECT s.name,s.memberno "
			sql += " FROM hr_employee_super s  "
			sql += " WHERE s.active='t' and s.employee_id='%s' " % (employee_id)
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			for row1 in rows1:
				super_fund		= row1['name']	
				super_member_no	= row1['memberno']	

			gross_amt		= 0.0
			tax_amt			= 0.0
			net_amt			= 0.0
			super_amt		= 0.0
			super_total		= 0.0
			super_list 	= []	
			
			sql  = "SELECT p.id, p.date, p.name as payslip_ref, p.employee_id, p.x_fiscal_id, p.x_is_timesheet,  "
			sql += " p.x_gross_amt, p.x_tax_amt, p.x_net_amt, p.x_super_amt, p.x_annual_leave, p.x_sick_leave, p.x_lsl_leave "
			sql += " FROM hr_payslip p  "
			sql += " WHERE p.date between '%s' and '%s' and p.employee_id='%s' " % (date_from, date_till, employee_id)
			#_logger.error("get_payregistersummary_linesget_payregistersummary_lines222 sqlsqlsql[%s]" % (sql))
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			
			for row1 in rows1:
			
				payslip_id	=row1['id']	
				fiscal_id	=row1['x_fiscal_id']

				gross_amt	+=float(row1['x_gross_amt'])
				tax_amt		+=float(row1['x_tax_amt'])
				net_amt		+=float(row1['x_net_amt'])
				super_amt	+=float(row1['x_super_amt'])
				super_total +=float(row1['x_super_amt'])
				
				sql="""select c.name,c.super_type,sum(s.sub_total) as tot from hr_payslip_summary s, hr_pay_category c where 
						s.category_id=c.id and c.category='super' and s.payslip_id='%s' group by c.name,c.super_type """ % (payslip_id)
				self._cr.execute(sql)
				rows2 = self._cr.dictfetchall()
				for row2 in rows2:		
					if row2['tot']:
						super_amt2	= abs(float(row2['tot']))
						super_amt2  = round(super_amt2, 2)
						super_text	= row2['name']
						super_type	= row2['super_type']
						val2 = {'super_text': super_text,'super_type': super_type,'super_amt': super_amt2,}
						super_list.append(val2) 
						super_total +=super_amt2
				#tot_gross_amt +=	gross_amt	
				#tot_tax_amt +=	tax_amt	
				#tot_net_amt +=	net_amt	
				tot_super_amt +=super_amt	
				
				
				#val_ytd=self.env['hr.payslip'].get_all_ytd_values(payslip_id, date, employee_id, fiscal_id, skip_current)	
				
			val = {'emp_name': emp_name,
				  'first_name': first_name,
				  'last_name': last_name,
				  'emp_no': emp_no,
				  'super_fund': super_fund,
				  'super_member_no': super_member_no,
				  'gross_amt': gross_amt,
				  'tax_amt': tax_amt,
				  'net_amt': net_amt,
				  'super_amt': super_amt,
				  'super_list': super_list,
				  'super_total': super_total, #super_total
				}
				
				
			res.append(val) 	
			
		summary = {'tot_super_amt': tot_super_amt,	}
		#_logger.error("get_payregistersummary_linesget_payregistersummary_lines22resres[%s]" % (res))			
		return res, summary	
		
	def get_payregistersummary_lines(self, date_from, date_till, empids, has_detail=False):
		summary	= {}
		res 	= []		
		tot_gross_amt	=0.0
		tot_tax_amt		=0.0
		tot_net_amt		=0.0
		#tot_super_amt	=0.0
		tot_deduct_amt	=0.0
		tot_expense_amt	=0.0
		#tot_added_amt	=0.0
	  
		sql="select e.id,e.name,e.x_first_name,e.x_last_name,e.x_emp_number from hr_employee e where e.id in(%s) order by e.x_last_name,e.x_first_name" % (str(empids).strip('[]'))
		#_logger.error("get_payregistersummary_linesget_payregistersummary_lines[%s]" % (sql))
		self._cr.execute(sql)
		rows = self._cr.dictfetchall()
		for row in rows:
			#emp_name	=row['name']	
			emp_no			= row['x_emp_number']	
			employee_id 	= row['id']	
			first_name		= row['x_first_name'] or ''
			last_name		= row['x_last_name'] or ''
			if last_name or last_name:
				emp_name		= "%s, %s" % (last_name, first_name)
			else:
				emp_name	=row['name'] or ''
			gross_amt		= 0.0
			tax_amt			= 0.0
			net_amt			= 0.0
			#super_amt		= 0.0

			expense_amt		= 0.0
			deduct_amt		= 0.0
			#added_amt		= 0.0
				
			sql  = "SELECT p.id,p.date,p.name as payslip_ref,p.employee_id,p.x_fiscal_id,p.x_is_timesheet,  "
			sql += "p.x_gross_amt, p.x_tax_amt, p.x_net_amt, p.x_super_amt,p.x_annual_leave,p.x_sick_leave,p.x_lsl_leave "
			sql += " FROM hr_payslip p  "
			sql += " WHERE p.date between '%s' and '%s' and p.employee_id='%s' " % (date_from, date_till, employee_id)
		
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			
			for row1 in rows1:
			
				payslip_id	=row1['id']	
				fiscal_id	=row1['x_fiscal_id']

				gross_amt	+=float(row1['x_gross_amt'])
				tax_amt		+=float(row1['x_tax_amt'])
				net_amt		+=float(row1['x_net_amt'])
				expense_amt	+=float(row1['x_super_amt'])
			
				#expense_amt	=0
				#deduct_amt	=0
				#added_amt	=0
				sql="""select sum(s.sub_total) as tot from hr_payslip_summary s, hr_pay_category c where 
						s.category_id=c.id and c.category='deduction' and s.payslip_id='%s' """ % (payslip_id)
				self._cr.execute(sql)
				rows2 = self._cr.dictfetchall()
				for row2 in rows2:		
					if row2['tot']:
						deduct_amt	+=abs(float(row2['tot']))
				
				tot_gross_amt +=	gross_amt	
				tot_tax_amt +=	tax_amt	
				tot_net_amt +=	net_amt	
				tot_expense_amt +=	expense_amt	
				tot_deduct_amt +=	deduct_amt	
				
				#val_ytd=self.env['hr.payslip'].get_all_ytd_values(payslip_id, date, employee_id, fiscal_id, skip_current)	
			val = {'emp_name': emp_name,
				  'first_name': first_name,
				  'last_name': last_name,
				  'emp_no': emp_no,
				  'gross_amt': gross_amt,
				  'tax_amt': tax_amt,
				  'net_amt': net_amt,
				  'expense_amt':expense_amt,
				  'deduct_amt': deduct_amt,
				}
				
				
			res.append(val) 
			
		summary = {'gross_amt': tot_gross_amt,
				  'tax_amt': tot_tax_amt,
				  'net_amt': tot_net_amt,
				  'deduct_amt': tot_deduct_amt,
				  'expense_amt':tot_expense_amt,
				}
		return res, summary	
	
	
	def get_paysummary_lines(self, date_from, date_till, empids, has_detail=False):
		
		res 	= []
	
		#cr 		= self.env.cr
		#sql="select e.id,e.name,e.x_first_name,e.x_last_name,e.x_emp_number from hr_employee e where e.id in(%s) order by e.x_last_name,e.x_first_name" % (str(empids).strip('[]'))
		#for empid in empids:
		#emp	 = self.env['hr.employee'].browse(empid)
		sql  = "SELECT p.id,e.name,e.x_emp_number,e.x_lsl_leave as lsl_enable,p.date,p.name as payslip_ref,p.employee_id,p.x_fiscal_id,p.x_is_timesheet,  "
		sql += " e.x_first_name,e.x_last_name,p.x_gross_amt, p.x_tax_amt, p.x_net_amt, p.x_super_amt,p.x_annual_leave,p.x_sick_leave,p.x_lsl_leave "
		sql += " FROM hr_payslip p, hr_employee e "
		sql += " WHERE p.employee_id=e.id and p.date between '%s' and '%s' and p.employee_id in(%s) " % (date_from, date_till, str(empids).strip('[]'))
		sql += " order by e.x_last_name, e.x_first_name"
		#_logger.error('get_paysummary_lines sql[ %s ] date_from[ %s ]' % (sql, date_from))
		self._cr.execute(sql)
		rows1 = self._cr.dictfetchall()
		#if len(rows1)>0:
		for row in rows1:
			emp_name	=row['name']	
			employee_id =row['employee_id']	
			payslip_id	=row['id']	
			fiscal_id	=row['x_fiscal_id']
			emp_no		=row['x_emp_number']	
			payslip_ref	=row['payslip_ref']
			date		=row['date']
			gross_amt	=row['x_gross_amt']
			tax_amt		=row['x_tax_amt']
			net_amt		=row['x_net_amt']
			super_amt	=row['x_super_amt']
			is_timesheet=row['x_is_timesheet']
			leave_annual	=row['x_annual_leave']
			leave_personal	=row['x_sick_leave']
			
			first_name		=row['x_first_name']
			last_name		=row['x_last_name']
			
			if last_name or last_name:
				emp_name		= "%s, %s" % (last_name, first_name)
			else:
				emp_name	=row['name'] or ''
				
			lsl_enable		=row['lsl_enable']
			if lsl_enable:
				leave_lsl	=row['x_lsl_leave']
			else:
				leave_lsl	=0.0
			leave_annual=round(float(leave_annual),4)
			leave_personal=round(float(leave_personal),4)
			leave_lsl=round(float(leave_lsl),4)
			skip_current=True
			val_ytd=self.env['hr.payslip'].get_all_ytd_values(payslip_id, date, employee_id, fiscal_id, skip_current)	
			val= {'emp_name': emp_name,
				  'first_name': first_name,
				  'last_name': last_name,
				  'payslip_id': payslip_id,
				  'emp_no': emp_no,
				  'date': date,
				  'payslip_ref': payslip_ref,
				  'gross_amt': gross_amt,
				  'tax_amt': tax_amt,
				  'net_amt': net_amt,
				  'super_amt': super_amt,
				  'leave_annual': leave_annual,
				  'leave_personal': leave_personal,
				  'leave_lsl': leave_lsl,
				  'ytd_personal': val_ytd['sick_leave'],
				  'ytd_annual': val_ytd['annual_leave'],
				  'ytd_lsl': val_ytd['lsl_leave'],
				  'is_timesheet': is_timesheet,
				  'has_detail': has_detail,
				  'gross_payslip_amt':self.get_payslip_gross_calculated(payslip_id)
				}
			if has_detail:
				val['summary_line']=self.get_payslip_detail(payslip_id)
			#else:
			#	val['summary_line']=[]
			res.append(val) 
		
		return res	
	
	def get_balance_headers(self):
		sub_headers=[]
		index=0
		sql="select * from hr_pay_category where category in ('deduction','allowance') and is_summary='f' order by category,name"
		self._cr.execute(sql)
		rows1 = self._cr.dictfetchall()
		for row in rows1:
			name =row['name']	
			id   =row['id']	
			val={'name':name, 'id':id,'index':index,'qty':0}
			sub_headers.append(val)
			index+=1
		sub_headers.sort(key=lambda item:item['index'])	
		return sub_headers
	
	def get_item_balances(self, emp_id, sub_headers, date, fiscal_id):
		items=[]
		for item in sub_headers:
			#qty=0.0
			qty=self.env['hr.payslip'].get_ytd_bycategory(emp_id, item['id'], date, fiscal_id)
			'''sql="select a.* from hr_payslip_ytd a,hr_pay_category b where a.category_id=b.id and b.category in ('deduction','allowance') and b.is_summary='f' "
			sql+=" and a.employee_id='%s' and a.ytd_category='item' and a.category_id='%s' and a.date_ytd<='%s'" %(emp_id, item['id'], dt)
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			for row in rows1:
				if ['qty']:
					qty =+float(row['qty'])'''
			val={'id':item['id'],'index':item['index'],'qty':qty}
			items.append(val)
		items.sort(key=lambda item:item['index'])	
		
		return items	
		
			
	def get_balance_lines(self, date_from, date_till, empids, sub_headers):
			
		res 	= []
		fiscal_id 	= self.env['account.fiscalyear'].finds(date_till)
		#cr 		= self.env.cr
		for empid in empids:
			sql="select e.* from hr_employee e where e.id='%s'" % (empid)
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			for row in rows1:
				name 			=row['name']	
				number 			=row['x_emp_number']
				gross_ytd		=0
				net_ytd			=0
				payg_ytd		=0
				super_ytd		=0
				sick_leave		=0
				annual_leave	=0
				parent_leave	=0
				lsl_leave		=0
				total			=0
				payslip_id		=None
				ytd_items		=self.env['hr.payslip'].get_all_ytd_values(payslip_id, date_till, empid, fiscal_id)
				gross_ytd		=ytd_items['gross_amt']
				payg_ytd		=ytd_items['tax_amt']
				super_ytd		=ytd_items['super_amt']
				annual_leave	=ytd_items['annual_leave']
				sick_leave		=ytd_items['sick_leave']
				lsl_leave		=ytd_items['lsl_leave']
				net_ytd			=ytd_items['net_amt']
				'''ytd_leaves	= self.env['report.employee.leavebalance'].get_leave_ytd(empid, date_till)
				for item in ytd_leaves:
					balance =float(item['balance'])
					if item['code']=="annual":
						annual_leave+=balance
					elif item['code']=="personal":
						sick_leave+=balance
					elif item['code']=="parental":
						parent_leave+=balance
					elif item['code']=="longservice":
						lsl_leave+=balance'''
				total	=sick_leave+annual_leave+lsl_leave	
				items	=self.get_item_balances(empid, sub_headers, date_till, fiscal_id)
				val={'name':name, 'id':empid,'number':number,
					'gross_ytd':	round(gross_ytd,4),
					'net_ytd':	round(net_ytd,4),
					'payg_ytd':	round(payg_ytd,4),
					'super_ytd':	round(super_ytd,4),
					'sick_leave':	round(sick_leave,4),
					'annual_leave':	round(annual_leave,4),
					'lsl_leave':	round(lsl_leave,4),
					'total':	round(total,4),
					'items':	items,
					}
				res.append(val)
		return res
		
class ReportEmployeeLine(models.TransientModel):
	_name = 'hr.report.employee.line'
	_description = 'Report Employee line'
	report_id = fields.Many2one('hr.payroll.report', string='Report')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	selected = fields.Boolean("Select", default=True) 
	job_id = fields.Many2one('hr.job', related='employee_id.job_id')
	group_id = fields.Many2one('hr.employee.group', related='employee_id.x_group_id')
	emp_number = fields.Char(related='employee_id.x_emp_number')
	first_name = fields.Char(related='employee_id.x_first_name', store=True)
	last_name = fields.Char(related='employee_id.x_last_name', store=True)	
	
	
class PayrollReportDefaultpage(models.AbstractModel):
	_name = 'report.dincelpayroll.report_defaultpage'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model = 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till = data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from=datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till=datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'employee': employee_id,
			'report_title': "",
			}
		
		return val
		
		
class PayrollReportPaygSummary(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payg_summary'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model = 'report.employee.payroll'#self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till = data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from=datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till=datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'employee': employee_id,
			'report_title': "",
			}
		
		return val		
		
		
		
class PayrollReportPayslipSummary(models.AbstractModel):
	_name = 'report.dincelpayroll.report_paysummary'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		#employee_id= data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			#empids	= data['form'].get('empids')
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
		#_logger.error('get_report_values222 individual[ %s ] empids[ %s ]' % (individual, empids))	
		lines = self.env['hr.payroll.report'].get_paysummary_lines(date_from, date_till, empids)
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'lines': lines,
			'report_title': "Payroll Summary",
			}
		
		return val	
		
	
class PayrollReportPaysRegisterSummary(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payregistersummary'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		#employee_id= data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			#empids	= data['form'].get('empids')
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
		
		lines, summary = self.env['hr.payroll.report'].get_payregistersummary_lines(date_from, date_till, empids)
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'lines': lines,
			'summary': summary,
			'report_title': "Pay Register Summary",
			}
		
		return val	
				
class PayrollReportPaySuperSummary(models.AbstractModel):
	_name = 'report.dincelpayroll.report_paysuper_summary'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		#employee_id= data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
		
		lines, summary = self.env['hr.payroll.report'].get_paysuper_summary_lines(date_from, date_till, empids)
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'lines': lines,
			'summary': summary,
			'report_title': "Pay Super Summary",
			}
		
		return val	
						
class PayrollReportPayslipEntry(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payentry'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model = 'report.employee.payroll'#self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		#employee_id = data['form'].get('employee_id')
		date_till = data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		
		individual	= data['form'].get('individual')
		if individual:
			#empids	= data['form'].get('empids')
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
		#_logger.error('get_report_values222 individual[ %s ] empids[ %s ]' % (individual, empids))	
		has_detail=True
		lines = self.env['hr.payroll.report'].get_paysummary_lines(date_from, date_till, empids, has_detail)
		
		date_from	=datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	=datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'lines': lines,
			'report_title': "Payroll Summary",
			}
		return val	
		
		
class PayrollReportOpeningBalance(models.AbstractModel):
	_name = 'report.dincelpayroll.report_opening_balance'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		#employee_id= data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
		
		#lines = self.env['hr.payroll.report'].get_paysummary_lines(date_from, date_till, empids)
		
		sub_headers	= self.env['hr.payroll.report'].get_balance_headers()
		
		lines		= self.env['hr.payroll.report'].get_balance_lines(date_from, date_till, empids, sub_headers)
		
		#_logger.error('report_opening_balance sql[ %s ]sub_headers[ %s ]' % (sql, sub_headers))
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'sub_headers': sub_headers,
			'lines': lines,
			'report_title': "Payroll Opening Balance",
			}
		
		return val	

		