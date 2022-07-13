from odoo import models, fields, api
from datetime import datetime, timedelta
import datetime as dt
#from datetime import datetime
#import datetime
from odoo.exceptions import UserError
from dateutil import parser
import logging
import csv
import os 
from . import dincelpayroll_vars 
_logger = logging.getLogger(__name__)
# class openacademy(models.Model):
#     _name = 'openacademy.openacademy'

#     name = fields.Char()
'''
decoration-bf - shows the line in BOLD 
decoration-it - shows the line in ITALICS 
decoration-danger - shows the line in LIGHT RED 
decoration-info - shows the line in LIGHT BLUE 
decoration-muted - shows the line in LIGHT GRAY 
decoration-primary - shows the line in LIGHT PURPLE 
decoration-success - shows the line in LIGHT GREEN 
decoration-warning - shows the line in LIGHT BROWN
'''
class PayrollHrSuperFund(models.Model):
	_name = 'hr.super.fund'
	_description = 'Superfund Company'		
	name 	= fields.Char("Account Name")
	active 			= fields.Boolean("Active", default=True) 
	
class PayrollHrEmployeeSuper(models.Model):
	_name = 'hr.employee.super'
	_description = 'Employee Superfund'		
	name 	= fields.Char("Account Name")
	usi 	= fields.Char("USI")
	abn 	= fields.Char("ABN")
	memberno 	= fields.Char("Membership")
	employer_membership 	= fields.Char("Employer Membership")
	phone 	= fields.Char("Phone")
	website 	= fields.Char("Website")
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	super_fund_id 	= fields.Many2one('hr.super.fund', string='Superfund')
	active 			= fields.Boolean("Active", default=True) 
	
class PayrollHrCostCentre(models.Model):
	_name = 'hr.cost.centre'
	_description = 'Cost Centre'			
	name 	= fields.Char("Name")	
	code 	= fields.Char("Code")	
	
class PayrollHrEmployeeBank(models.Model):
	_name = 'hr.employee.bank'
	_description = 'Employee Bank'			
	name 	= fields.Char("Account Name")
	bsb 	= fields.Char("BSB")
	bank_name 	= fields.Char("Bank Name")
	account_number 	= fields.Char("Account Number")
	sequence	= fields.Integer("Sequence", default=True)
	part_salary_amt	= fields.Float("Part Salary Amount")
	part_type	= fields.Selection([
			('amt', 'Amount'),
			('pc', 'Percentage')
			], 'Contribution',  default='amt') 
	active 			= fields.Boolean("Active", default=True) 
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	type	= fields.Selection([
			('full', 'Full Salary'),
			('part', 'Part Salary'),
			('balance', 'Balance'),
			], 'Contribution Type',  default='full') 

class PayrollHrEmployeeRate(models.Model):
	_name = 'hr.employee.rate'
	_order = 'date_from desc'
	pay_basis = fields.Selection([
			('S', 'Salary'),
			('H', 'Hourly'),
			], string='Pay Basis') 
	leave_rate = fields.Float("Leave Rate", digits=(10, 5))	
	other_rate = fields.Float("Other Rate", digits=(10, 5))	
	employee_id = fields.Many2one('hr.employee', string='Employee')
	salary_rate = fields.Float('Rate / Annual Salary', digits=(10, 5))	
	salary_annual = fields.Float('Annual Salary')
	#salary_annual = fields.Float('Annual Salary')
	super_amount = fields.Float('Super Per Payperiod')		
	date_from = fields.Date(string='Date From')
	date_till = fields.Date(string='Date To')
	job_id = fields.Many2one('hr.job', 'Job Position')
	comments 	= fields.Char("Comments")
	
	@api.onchange('pay_basis','salary_rate')
	def _onchange_dayofweek(self):
		for record in self:
			#emp_id=self.employee_id.id
			#group_id=self.employee_id.x_group_id.id
			#pay_basis=self.pay_basis
			#_rate=self.salary_rate
			#leave_rate,super_amount,salary=self.calc_salary(emp_id,group_id,pay_basis,_rate)
			#vals={'salary_annual':salary,'leave_rate':leave_rate,'super_amount':super_amount}
			#return {'value':vals}
			if record.pay_basis=="year":
				vals={'salary_annual':record.salary_rate}
				return {'value':vals}
			else:
				if record.employee_id.x_group_id:
					emp_id		=record.employee_id.id
					group_id	=record.employee_id.x_group_id.id
					tax_scale_id=record.employee_id.x_tax_scale_id.id
					_rate		=record.salary_rate
					leave_rate, super_amount, salary = self.calc_salary(emp_id,group_id,record.pay_basis,_rate, tax_scale_id)
					#_factor=record.employee_id.x_group_id.factor_hr_rate
					#if _factor:
					#_rate=float(record.salary_rate)*float(_factor)
					vals={'leave_rate':leave_rate}
					#if super_amount:
					vals['super_amount']=super_amount
					#if salary:
					vals['salary_annual']=salary	
					return {'value':vals}
			return {}
			
				
	#todo if rqd get other value of [pay_period="fortnight"] eg "weekly" etc//not in use...
	def calc_salary(self, emp_id, group_id, pay_basis, _rate, tax_scale_id, pay_period="fortnight"):
		leave_rate, super_amount, salary=0.0,0.0,0.0
		#employee	=self.env['hr.employee'].browse(emp_id)
		group		=self.env['hr.employee.group'].browse(group_id)
		_super_pc=9.5
		if pay_basis=="S":
			salary=_rate
		else:
			salary=0.0
			leave_rate=_rate
			super_amount=0.0
			if group.factor_hr_rate:
				_factor=group.factor_hr_rate
				_days_hrs = group.daily_net_hrs #11.5 for factory 
				_work_days = group.week_work_days	#4 for factory 
					
				leave_rate=float(_rate)*float(_factor)
				salary=leave_rate*float(_days_hrs)*float(_work_days)*52
				
				'''
				#_logger.error('calc_salarycalc_salary[ %s ][ %s ][ %s ][ %s ]' % (tax_scale_id,_factor,_days_hrs,_work_days))
				if tax_scale_id:
					
					_super_pc=self.env['dincelpayroll.scale'].get_super_pc(tax_scale_id)
					salary=leave_rate*float(_days_hrs)*float(_work_days)*52
					super_amount=float(_super_pc)*0.01*salary/26.0 #, pay_period="fortnight"
					#if group.factor_annual_type=="factor":'''
		if tax_scale_id:
			_super_pc=self.env['dincelpayroll.scale'].get_super_pc(tax_scale_id)			#	salary=leave_rate*float(group.factor_annual_salary)
		super_amount=float(_super_pc)*0.01*salary/26.0 #, pay_period="fortnight"		
		return leave_rate, super_amount, salary
	
	#---------------------------------------------------------------------------------------------------------
	#this is being saved in employee card....
	#---recalculate the "factor_hr_rate" will make sure it always gets the right value in runtime
	#---------------------------------------------------------------------------------------------------------	
	def get_employee_rates(self, employee_id, dt = None):
		#pay_basis, leave_rate, other_rate, salary_rate =None, None, None, None
		pay_basis, leave_rate, other_rate, salary_rate,salary_annual ='S', 0, 0, 0, 0
		if not dt:
			dt=datetime.today()
			dt=dt.strftime("%Y-%m-%d")
		if employee_id and dt:
			factor_hr_rate=1.0
			sql="select g.factor_hr_rate from hr_employee_group g,hr_employee e where g.id=e.x_group_id and e.id='%s'" % (employee_id)
			self.env.cr.execute(sql)
			rs = self.env.cr.dictfetchall()
			for row in rs:
				factor_hr_rate 	= row.get('factor_hr_rate') or 1.0
				
			sql="select r.* from hr_employee_rate r where r.employee_id='%s' and ('%s' between r.date_from  and r.date_till)" % (employee_id, dt)
			#_logger.error('get_employee_ratesget_employee_rates[ %s ]',sql)
			self.env.cr.execute(sql)
			rs = self.env.cr.dictfetchall()
			for row in rs:
				leave_rate 			= row.get('leave_rate')
				other_rate 			= row.get('other_rate')
				salary_rate 		= row.get('salary_rate')
				pay_basis 			= row.get('pay_basis')
				salary_annual		= row.get('salary_annual')
			if not salary_rate:
				sql="select r.* from hr_employee_rate r where r.employee_id='%s' and r.date_from<='%s' and r.date_till is null" % (employee_id, dt)
				#_logger.error('get_employee_ratesget_employee_rates[ %s ]',sql)
				self.env.cr.execute(sql)
				rs = self.env.cr.dictfetchall()
				for row in rs:
					leave_rate 		= row.get('leave_rate')
					other_rate 		= row.get('other_rate')
					salary_rate 	= row.get('salary_rate')
					pay_basis 		= row.get('pay_basis')
					salary_annual	= row.get('salary_annual')
		if not leave_rate:
			leave_rate=0.0
		else:
			if factor_hr_rate:
				leave_rate = float(factor_hr_rate) * float(salary_rate)
		if not other_rate:
			other_rate=0.0
		if not salary_rate:
			salary_rate=0.0
		if not salary_annual:
			salary_annual=0.0
		try:
			leave_rate=float(leave_rate)
			other_rate=float(other_rate)
			salary_rate=float(salary_rate)
			salary_annual=float(salary_annual)
		except:
			pass
		return pay_basis, leave_rate, other_rate, salary_rate, salary_annual
		
class PayrollHrLeaveBalance(models.Model):
	_name = 'hr.payslip.leave.balance'
	date = fields.Date(string='Date') 
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	accrud_in = fields.Float("Accrud")
	taken_out = fields.Float("Taken")
	name = fields.Char("Description")
	payslip_id 	= fields.Many2one('hr.payslip', string='Payslip')
	holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type')
	#ref_no = fields.Char("Reference")
	type = fields.Selection([
			('annual', 'Annual'),
			('longservice', 'Long Service Leave'),
			('personal', 'Personal Leave'),
			('parental', 'Parental Leave'),
			], string='Leave')
			
	def create_balance(self, type, payslip, _in, _out):
		if abs(_in) > 0.0 or abs(_out) > 0.0:
			_status_id=None
			#items = self.env['hr.payslip.leave.balance'].search([('payslip_id', '=', payslip.id),('type','=',type)])
			holidays = self.env['hr.holidays.status'].search([('x_code','=',type)], limit=1)
			for day in holidays:
				_status_id=day.id
			if _status_id:
				_in		= round(float(_in), 4)
				_out	= round(float(_out), 4)
				
				items = self.env['hr.payslip.leave.balance'].search([('payslip_id', '=', payslip.id),('holiday_status_id','=',_status_id)])
				if items:
					for item in items:
						item.update({'accrud_in': _in, 'taken_out': _out})
				else:
					vals={'date':payslip.date,
						'employee_id':payslip.employee_id.id,
						'type':type,
						'accrud_in':_in,
						'taken_out':_out,
						'payslip_id':payslip.id,
						'holiday_status_id':_status_id,
						'name':payslip.number}
					return self.env['hr.payslip.leave.balance'].create(vals)
			else:
				_logger.error("create_balanceerror_ leave code not found _in[%s]_out[%s]type[%s]" % (_in,_out,type))	
				return -1	
		return None
		
class PayrollHrEmployeeLeave(models.Model):
	_name = 'hr.employee.leave'
	pay_basis = fields.Selection([
			('year', 'Yearly'),
			('once', 'Once'),
			], string='Pay Basis')
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	entitlement 	= fields.Float("Entitlement", digits=(8, 4))	
	hours 	= fields.Float("Entitle Hours ", digits=(8, 4))	
	uom_code = fields.Selection(dincelpayroll_vars.HR_UOM_OPTIONS, string='UOM Code', default='day')
	uom_id = fields.Many2one("hr.uom", string="UOM")
	holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type')
	type = fields.Selection([
			('annual', 'Annual'),
			('longservice', 'Long Service Leave'),
			('personal', 'Personal Leave'),
			('parental', 'Parental Leave'),
			], string='Leave')
	accural_hourly	= fields.Float(string="Hourly Accural", compute='_compute_hourly', digits=(6, 4)) 
	accural_daily	= fields.Float(string="Daily Accural", compute='_compute_daily', digits=(6, 4)) 
	notes = fields.Char('Notes')
	
	@api.onchange('holiday_status_id','hours')
	def _onchange_hours(self):
		for record in self:
			vals={}
			#vals={'x_work_hrs':week_hrs,'x_daily_hrs':day_hrs}
			#record.write(vals) 
			return {'value':vals}
			
	def _compute_hourly(self):
		for record in self:
			_amt=0.0
			if record.employee_id and record.pay_basis=="S":
				a=float(record.employee_id.x_work_hrs)
				a2=float(record.employee_id.x_work_days)
				if a2>0 and a>0:
					a3=float(a/a2)
					b=float(record.entitlement)
					d= float(b / (a*52.0))
					_amt=round(d,4)
				#_logger.error('_compute_hourly a[ %s ], b[ %s ], d[ %s ]_amt[ %s ]',a, b, d, _amt)	
			record.accural_hourly =_amt
			
	def _compute_daily(self):
		for record in self:
			_amt=0.0
			if record.employee_id and record.pay_basis=="S":
				a=float(record.employee_id.x_work_hrs)
				a2=float(record.employee_id.x_work_days)
				if a2>0 and a>0:
					a3=float(a/a2)
					b=float(record.entitlement)
					d= float(b / (a*52))
					_amt=d*a3
					_amt=round(_amt,4)
			record.accural_daily =_amt
			
class DincelHrEmployee(models.Model):
	_inherit = 'hr.employee'			
	x_recordid = fields.Char('MyOB Record ID',size=18)
	x_bank_ids = fields.One2many('hr.employee.bank','employee_id', string='Bank Details')
	x_pay_text = fields.Char('Pay Statement Text',size=18)
	x_super_ids = fields.One2many('hr.employee.super','employee_id', string='Super Details')
	x_leave_ids = fields.One2many('hr.employee.leave','employee_id', string='Leave Details')
	x_rate_ids = fields.One2many('hr.employee.rate','employee_id', string='Rate Details')
	x_tax_scale_id = fields.Many2one('dincelpayroll.tax.scale', string='Tax Scale')	
	x_group_id = fields.Many2one('hr.employee.group', string='Employee Group')	
	x_other_rate = fields.Float("Other Rate")	
	x_work_hrs = fields.Float("Working Hrs (weekly)")	
	x_daily_hrs = fields.Float("Working Hrs (daily)")	
	x_work_days = fields.Integer("Working Days (weekly)")	
	x_pay_basis = fields.Selection([
			('H', 'Hourly'),
			('S', 'Salary'),
			], string='Pay Basis')
	x_leave_rate = fields.Float("Leave Rate")	
	x_first_name = fields.Char('First Name')
	x_mid_name = fields.Char('Middle Name')
	x_last_name = fields.Char('Last Name')
	x_other_name = fields.Char('Other Name')
	x_prev_fname = fields.Char('Previous First Name')
	x_prev_midname = fields.Char('Previous Middle Name')
	x_prev_lname = fields.Char('Previous Last Name')
	x_display_name	= fields.Char(string="Full Name", compute='_display_name') 
	x_street = fields.Char('Street')
	x_suburb = fields.Char('Suburb')
	x_postcode = fields.Char('Postcode')
	x_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
	x_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
	x_date_start = fields.Date('Start Date')
	x_date_stop = fields.Date('Termination Date')
	x_basis  = fields.Selection([
			('individual', 'Individual'),
			('hire', 'Labour Hire'),
			('other', 'Other'),
			], string='Employment Basis')
	x_abn = fields.Char('ABN')		
	x_category  = fields.Selection([
			('permanent', 'Permanent'),
			('temp', 'Temporary'),
			], string='Employment Category') 
	x_emp_status  = fields.Selection([
			('full', 'Full Time'),
			('part', 'Part Time'),
			('casual', 'Casual'),
			('other', 'Other'),
			], string='Employment Status') 		
	x_payslip_deli  = fields.Selection(dincelpayroll_vars.PAYSLIP_DELIVERY_OPTIONS, string='Payslip Delivery') 		
	x_payslip_create_type  = fields.Selection(dincelpayroll_vars.PAYSLIP_CREATE_OPTIONS, string='Payslip Creation') 		
	x_email = fields.Char('Email')		
	x_email_pay = fields.Char('Payslip Email')
	x_mobile = fields.Char('Mobile')	
	x_tfn = fields.Char('TFN')	
	x_tfn_excode= fields.Char('TFN Exception Code')	
	x_kin_name = fields.Char('Next of Kin Name')	
	x_kin_phone = fields.Char('Next of Kin Contact')	
	x_salary = fields.Float('Annual Salary')
	x_payperiod_hr = fields.Float('Hrs in Payperiod')
	x_payfrequency_id = fields.Many2one("hr.payroll.payfrequency", string="Pay Frequency")
	x_expense_id = fields.Many2one('account.account', string='GL Expense Account')
	x_super_id = fields.Many2one('account.account', string='GL Super Account')
	x_general_exmpt = fields.Boolean('General Exception')
	x_au_resident = fields.Boolean('Australian Resident', default=True)
	x_leave_loading = fields.Boolean('Apply Leave Loading')
	x_help_debt = fields.Boolean('HECS-HELP Debt')
	x_sfss_debt = fields.Boolean('SFSS Debt')
	x_medicare_vary = fields.Boolean('Medicare Variation')
	x_senior_offset = fields.Boolean('Senior Offset Claimed')
	x_zone_special = fields.Boolean('Zone, Dependent or Special Rebates Claimed')	
	x_salary_rate	= fields.Float(string="Salary / Rate", compute='_get_salary_rate', digits=(12, 2)) 
	x_lsl_leave = fields.Boolean('Long Service Leave?')
	x_entitlement_ids = fields.One2many('hr.payroll.entitlement','employee_id', string='Entitlements', copy=True, auto_join=True)
	x_coststate_id = fields.Many2one("res.country.state", string='Cost State')
	x_costcentre_id = fields.Many2one("hr.cost.centre", string='Cost Centre')
	x_workhrs_ids = fields.One2many('hr.employee.workhrs','employee_id', string='Work Hours NA', copy=True, auto_join=True)
	x_attendance_ids = fields.One2many('hr.employee.attendance','employee_id', string='Work/Attedance Hours', copy=True, auto_join=True)
	x_current = fields.Boolean('Current Employee', default=True)
	x_emp_number = fields.Char('Employee No')	
	x_emp_type  = fields.Selection([
			('factory', 'Factory Staff'),
			('office', 'Office/Other Staff'),
			], string='Employee Type',help="Factory emp number starts with 5###, & Others with 1###", required=True) 
	x_skip_ts_import = fields.Boolean('Skip Timesheet Import', default=False)
	x_payslip_enable = fields.Boolean('Payslip Create Enabled?', default=True)
	x_super_user= fields.Boolean(string="Super User", compute='_is_super_user1')
	
	#@api.depends('x_super_user')
	def _is_super_user1(self):
		super_user = False	
		results = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
		for item in results:
			if item.has_group('base.group_super_user'):
				super_user = True
			else:
				super_user = False	
		#_logger.error("super_usersuper_user["+str(super_user)+"]["+str(self._uid)+"]results["+str(results)+"]")
		#return super_user
		self.x_super_user = super_user		
		
	@api.model
	def create(self, vals):
		if vals.get('x_emp_type') and vals.get('x_emp_type') =="office":
			_number		=self.env['ir.sequence'].next_by_code('employee.no')
		else:
			_number		=self.env['ir.sequence'].next_by_code('employee.no.factory')
		vals['x_emp_number'] = _number
		record = super(DincelHrEmployee, self).create(vals)	
		
		return record
		
	def _display_name(self):
		for record in self:
			_display_name=""
			if record.x_first_name:
				_display_name = record.x_first_name
			if record.x_mid_name:
				_display_name="%s %s" % (_display_name, record.x_mid_name)
			if record.x_last_name:
				_display_name="%s %s" % (_display_name, record.x_last_name)	
			record.x_display_name=_display_name
			
	@api.multi
	def button_import_entitlements(self):
		employee_id=self.id
		#items = self.env['hr.pay.category'].search([('is_summary', '=', True)])
		items2 = self.env['hr.payroll.entitlement'].search([('employee_id', '=', employee_id)])
		if self.x_group_id:
			items = self.x_group_id.category_ids
			for item in items:
				_found=False
				for item2 in items2:
					if item.id==item2.category_id.id:
						_found=True
						break
				if _found==False:
					vals = {'category_id': item.id,'description':item.name,'employee_id':employee_id}
					#if item.expense_account_id:
					#	vals_summary['account_id']=item.expense_account_id.id
					if item.payable_account_id:
						vals['account_id']=item.payable_account_id.id
					if item.category:
						vals['category']=item.category
					if self.x_coststate_id:	
						vals['cost_state_id']=self.x_coststate_id.id
					if self.x_costcentre_id:
						vals['costcentre_id']=self.x_costcentre_id.id
					#items2.write(.append((0, 0, vals_summary))
					#_logger.error('button_import_summary[ %s ]' %  (vals_summary))
					self.write({'x_entitlement_ids':[(0,0,vals)]})
	
	@api.multi
	def button_emp_leave_balance(self):
		dt=datetime.today()
		'''ctx = self._context.copy()
		#model = 'account.invoice'
		ctx.update({'default_employee_id':self.employee_id.id, 
					'default_date_till':self.date, 
					'default_date_from':self.date, 
					'default_reportcode':'entitlesumm'})'''
		#res 			= {}
		empids=[]
		data 			= {}
		employee_lines	= {}
		data['ids'] 	= []#self.env.context.get('active_ids', [])
		empids.append(self.id)
		employee_lines['employee_id']=self.id
		#if self.reportcode=="paygtax":
		#	model 			= 'report.employee.payroll'
		#else:
		model 			= 'report.employee.leavebalance'
		data['model'] 	= model
		data['form'] 	= {'date_till':dt, 'date_from':dt, 'employee_id': self.id, 'individual': True, 'employee_lines':employee_lines, 'archived':False} 
		data['form']['empids'] = empids	
		self.env.ref('dincelpayroll.action_report_leavesummary').report_action(self, data=data, config=False)	
		#return True
		
	@api.multi
	def button_import_summary(self):
		employee_id=self.id
		#items = self.env['hr.pay.category'].search([('is_summary', '=', True)])
		items2 = self.env['hr.payroll.entitlement'].search([('employee_id', '=', employee_id)])
		if self.x_group_id:
			items = self.x_group_id.summary_ids
			for item in items:
				_found=False
				for item2 in items2:
					if item.id==item2.category_id.id:
						_found=True
						break
				if _found==False:
					vals_summary = {'category_id': item.id,'description':item.name,'employee_id':employee_id}
					#if item.expense_account_id:
					#	vals_summary['account_id']=item.expense_account_id.id
					if item.payable_account_id:
						vals_summary['account_id']=item.payable_account_id.id
					if item.category:
						vals_summary['category']=item.category
					if self.x_coststate_id:	
						vals_summary['cost_state_id']=self.x_coststate_id.id
					if self.x_costcentre_id:
						vals_summary['costcentre_id']=self.x_costcentre_id.id
					#items2.write(.append((0, 0, vals_summary))
					#_logger.error('button_import_summary[ %s ]' %  (vals_summary))
					self.write({'x_entitlement_ids':[(0,0,vals_summary)]})
	
	@api.multi
	def button_import_attendance(self):
		employee_id=self.id
		
		items2 = self.env['hr.employee.attendance'].search([('employee_id', '=', employee_id)])
		
		if self.x_group_id:
		
			for item in self.x_group_id.attendance_ids:
				_found=False
				for item2 in items2:
					if item.dayofweek==item2.dayofweek:
						_found=True
						break
				if _found==False:
					vals = {'dayofweek': item.dayofweek,'name':item.name,'hour_from':item.hour_from,'hour_to':item.hour_to}
					if item.category_id:
						vals['category_id']=item.category_id.id
					if item.normal_pay:
						vals['normal_pay']=item.normal_pay	
					if item.meal_unpaid:
						vals['meal_unpaid']=item.meal_unpaid
					if item.paid_meal:
						vals['paid_meal']=item.paid_meal
					if item.paid_t15:
						vals['paid_t15']=item.paid_t15
					if item.paid_t20:
						vals['paid_t20']=item.paid_t20			
					self.write({'x_attendance_ids':[(0,0,vals)]})
					
	@api.multi
	def button_import_leaves(self):
		employee_id=self.id
		test_imp_id=1 #admin employee//from /employee/user [Administrator]
		items2 = self.env['hr.employee.leave'].search([('employee_id', '=', employee_id)])
		#sql="select employee_id from hr_employee_leave limit 1"
		#self.env.cr.execute(sql)
		#rs = self.env.cr.dictfetchall()
		#for row in rs:
		if employee_id and test_imp_id:
			#test_imp_id= row.get('employee_id')
			items = self.env['hr.employee.leave'].search([('employee_id', '=', test_imp_id)])
			
			for item in items:
				_found=False
				for item2 in items2:
					if item.type==item2.type:
						_found=True
						break
				if _found==False:
					vals_summary = {'entitlement': item.entitlement,'type':item.type,'pay_basis':item.pay_basis}
					if item.uom_code:
						vals_summary['uom_code']=item.uom_code
					if item.holiday_status_id:
						vals_summary['holiday_status_id']=item.holiday_status_id.id	
					if item.accural_hourly:
						vals_summary['accural_hourly']=item.accural_hourly
					if item.accural_daily:
						vals_summary['accural_daily']=item.accural_daily
					 
					self.write({'x_leave_ids':[(0,0,vals_summary)]})
	
	def get_leave_hrs_arr(self, employee, payperiod="fortnight", pay_basis="S"):
		hrs_arr=[]
		if not employee:
			return hrs_arr
		_payperiod_annual, _default_work_hrs 	= self._leave_fortnight_hrs(employee, "annual", payperiod, pay_basis)
		_payperiod_personal, _default_work_hrs 	= self._leave_fortnight_hrs(employee, "personal", payperiod, pay_basis)
		_payperiod_lsl, _default_work_hrs 		= self._leave_fortnight_hrs(employee, "longservice", payperiod, pay_basis)
		
		item={"accured":_payperiod_annual,"type":"annual","work_hrs":_default_work_hrs}
		hrs_arr.append(item)
		
		item={"accured":_payperiod_personal,"type":"personal","work_hrs":_default_work_hrs}
		hrs_arr.append(item)
		
		item={"accured":_payperiod_lsl,"type":"longservice","work_hrs":_default_work_hrs}
		hrs_arr.append(item)
		return 	hrs_arr
		
	def _leave_fortnight_hrs(self, employee, type, payperiod="fortnight", pay_basis="S"):
		if not employee:
			return 0.0, 0.0 
		daily_hrs	= float(employee.x_work_hrs)
		week_days	= float(employee.x_work_days)
		
		if not week_days or week_days==0.0:	
			week_days = 5.0
			
		entitlement	= 0.0
		
		if employee.x_group_id:
			daily_hrs	= float(employee.x_group_id.daily_net_hrs) #11.5
			week_days	= float(employee.x_group_id.week_work_days) #4days
			for line in employee.x_group_id.leave_ids:
				if line.holiday_status_id.x_code==type:
					entitlement = float(line.quantity)
					#pay_basis	= row.get('pay_basis')
					uom_code	= line.uom_code
					if uom_code == "week":
						entitlement = entitlement * week_days #4*4=16
					break
		
		#pay_basis=""
		#>> x_code [breavement, nopay, compensation, communit, parental,annual, personal, longservice]
		#>> hardcoded...in order to automati or link with timesheets/payslip summary table/s...
		sql="select a.* from hr_employee_leave a,hr_holidays_status b where a.holiday_status_id=b.id and a.employee_id='%s' and b.x_code='%s'" % (employee.id, type)
		self.env.cr.execute(sql)
		rs = self.env.cr.dictfetchall()
		if len(rs) > 0:
			for row in rs:
				entitlement = float(row.get('entitlement'))
				#pay_basis	= row.get('pay_basis')
				uom_code	= row.get('uom_code')
				if uom_code=="week":
					entitlement=entitlement*week_days
	
		_entitlement_hrs, _total_work_hrs= self._compute_leaves_hrs(entitlement, daily_hrs, week_days,payperiod,pay_basis)		
		#_logger.error("get_leave_entitlements_hrspatype[%s]payperiod[%s]entitlement[%s]daily_hrs[%s]week_days[%s]" % (type,payperiod,entitlement, daily_hrs, week_days))
		return _entitlement_hrs, _total_work_hrs	
	def get_leave_fortnight_hrs(self, emp_id, type, payperiod="fortnight", pay_basis="S"):
		if not emp_id:
			return 0.0, 0.0 
			
		#_daily, _weekly, _payperiod, _fortnight_hrs = 0.0, 0.0, 0.0, 0.0
		
		employee 	= self.env['hr.employee'].browse(emp_id)
		return self._leave_fortnight_hrs(employee, type, payperiod, pay_basis)
	
	def _compute_leaves_hrs(self, entitlement_days, daily_hrs, week_days,payperiod="fortnight",pay_basis="S"):	
		_entitlement_hrs		= float(entitlement_days)*float(daily_hrs) #cause entitlement is in terms of hours
		_weekly_hrs				= float(daily_hrs)*float(week_days)
		_year_work_hrs			= _weekly_hrs*52.0
		_fortnight_hrs			= _weekly_hrs*2.0
		_month_hrs				= _year_work_hrs/12.0
		if not _weekly_hrs:
			return 0,0
			
		_entitlement_fortnight	= _entitlement_hrs*_fortnight_hrs/_year_work_hrs
		_entitlement_weekly		= _entitlement_fortnight/2.0
		_entitlement_month		= _entitlement_hrs/_month_hrs
		
		if payperiod == "day":# for week
			_entitlement_daily	= _entitlement_weekly/float(week_days)
			_entitlement_hrs	= _entitlement_daily
			_total_work_hrs		= daily_hrs
		elif  payperiod == "week":
			_total_work_hrs		= _weekly_hrs
			_entitlement_hrs	= _entitlement_weekly
		elif  payperiod == "fortnight":
			_entitlement_hrs	= _entitlement_fortnight
			_total_work_hrs		= _fortnight_hrs
		elif  payperiod == "month":
			_fortnight_hrs		= _entitlement_month
			_total_work_hrs		= _month_hrs
		else: #year
			_year_work_hrs		= _weekly_hrs*52.0
			_total_work_hrs		= _year_work_hrs
			
		return _entitlement_hrs, _total_work_hrs
		
	def _compute_daily_leave(self, entitlement, daily_hrs, week_days,pay_basis="S"):			
		a=daily_hrs#float(record.employee_id.x_work_hrs)
		a2=week_days#float(record.employee_id.x_work_days)
		#_amt=0.0
		if daily_hrs > 0.0 and week_days > 0.0 and entitlement > 0.0:
			a3	= float(a/a2) #daily hours
			b	= float(entitlement) #yearly entitlement
			d	= float(b / (a*52))
			_amt= d*a3
			_amt= round(_amt,4)
		return _amt	
		
	def _get_salary_rate(self):
		for record in self:
			pay_basis, leave_rate, other_rate, salary_rate,salary_annual = self.env['hr.employee.rate'].get_employee_rates(record.id)
			record.x_salary_rate=salary_rate
	
	def _get_weekly_hours(self,  payfreq, pay_hr):
		_type=payfreq
		if _type=="week":
			week_hr=pay_hr
		elif _type=="fortnight":
			week_hr=pay_hr/2
		elif _type=="month":
			week_hr=pay_hr*12/52
		elif _type=="year":
			week_hr=pay_hr/52
		else:
			week_hr=_amt
		return week_hr
		
	def _get_weekly_vars(self,payfrequency, payperiod_hr, work_days):
		week_hrs=0
		day_hrs=0
		if payfrequency and payperiod_hr and work_days:
			week_hrs=self._get_weekly_hours(payfrequency.code, payperiod_hr)
			day_hrs=float(week_hrs)/float(work_days)
			day_hrs=round(day_hrs,2)
		return week_hrs, day_hrs
	
	def _calculate_salary(self, emp_id, _group_id, _rate):
		_salary=0.0
		return _salary
		
	@api.onchange('x_group_id','timesheet_cost')
	def _onchange_group_id(self):
		for record in self:
			if record.x_pay_basis=="S":
				_salary=record.timesheet_cost
			else:
				_salary=self._calculate_salary(record.id, record.x_group_id, record.timesheet_cost )
			vals={'x_salary':_salary}
			return {'value':vals}
			
	@api.onchange('x_payfrequency_id','x_payperiod_hr','x_work_days')
	def _onchange_payperiod(self):
		for record in self:
			week_hrs,day_hrs=self._get_weekly_vars(record.x_payfrequency_id, record.x_payperiod_hr, record.x_work_days)
			vals={'x_work_hrs':week_hrs,'x_daily_hrs':day_hrs}
			#record.write(vals) 
			return {'value':vals}
		
	#x_record_ref = fields.Char('Record Ref')	
	@api.onchange('x_first_name','x_mid_name','x_last_name')
	def _onchange_name(self):
		for record in self:
			_name=""
			if record.x_first_name:
				_name = record.x_first_name
			if record.x_mid_name:
				_name += " %s" % (record.x_mid_name)
			if record.x_last_name:
				_name += " %s" % (record.x_last_name)	
			return {'value':{'name':_name}}
			
	def get_default_rate(self, empid):
		
		#pay_basis, leave_rate, other_rate, rate_base,salary_annual = self.env['hr.employee.rate'].get_employee_rates(empid, _date)
		#payfreq_code 		= payslip.x_payfrequency_id.code 
		#pay_period_amt 	= 0.0
		employee = self.env['hr.employee'].browse(empid)
		_date	 = datetime.today()
		rate_base, leave_rate, other_rate, salary_annual = self.env['hr.payslip'].get_employee_base_rate(employee, _date)
		'''
		employee = self.env['hr.employee'].browse(empid)
		#_logger.error('get_default_rate employee[ %s ]empid[ %s ]' %  (employee, empid))
		rate_base=0
		if employee:
			if employee.timesheet_cost:
				rate_base=employee.timesheet_cost
			if employee.x_pay_basis:#Salary 
				if employee.x_pay_basis == "S":
					_date=datetime.today()
					pay_basis, leave_rate, other_rate, rate_base,salary_annual = self.env['hr.employee.rate'].get_employee_rates(empid, _date)
					if not employee.x_work_hrs: #weekly hours
						weekly_hrs	=40.0
					else:
						weekly_hrs	=float(employee.x_work_hrs)
							
					if pay_basis=="year":
						_salary 	= float(rate_base)
						week_amt 	= round((_salary/52.0),4)
						rate_base 	= round((week_amt/weekly_hrs),4)#round((rate_base / (employee.x_work_hrs*52)),4)
						
				#else:
				#	_salary 	= float(rate_base)*float(weekly_hrs)*52
			#pay_period_amt	= self.get_pay_period_amt(_salary, payfreq)
		#else:
		#	rate_base		=employee.timesheet_cost'''
		return rate_base

class DincelLogRecord(models.Model):
	_name = "hr.log.record"	
	name 		= fields.Char("Name")	
	date 		= fields.Date('Date')
	empnumber 	= fields.Char("Number")
	fname 		= fields.Char("First Name")
	lname		= fields.Char("Last Name")
	paytype		= fields.Char("Pay Type")
	hrs			= fields.Char("Hrs")
	comments	= fields.Char("Comments")

#14/02/2020,14:14:27,1444837427,Staff Entry,OUT_ENTRY,50328,1
class DincelTimesheetScan(models.Model):
	_name = "hr.timesheet.scan"	
	name 		= fields.Char("Name")	
	date 		= fields.Date('Date')
	time 		= fields.Char("Time")
	in_out		= fields.Char("In/Out")
	employee_no	= fields.Char("Employee No")
	finger_no	= fields.Integer("Finger No", size=1)
	
	def import_scan_ts(self, ts_app):
		#Default filename is ta.dat at /var/tmp-odoo/timesheet/ta.dat
		file_path	= self.env['dincelaccount.settings'].get_scan_ts_file() #+ "/timesheet/ta.dat"
		#for line in copy.summary_ids:
		count1	= 0
		file_found=False	
		if (os.path.exists(file_path)):
			#raise UserError(("Error! No new file found to import.\n\n%s\n" % (file_path)))
			file_found=True
			start_import= False
			name		= ""
			sql			= "select id,name from hr_timesheet_scan order by id desc limit 1"
			self._cr.execute(sql)
			rows1 		= self._cr.fetchall()
			if len(rows1) > 0:
				recordid= rows1[0][0]
				name	= rows1[0][1]
			else:
				start_import	=True
				
			count1	= 0
			#start_import	=True
			try:	
			#if file_found:
				with open(file_path) as f:
					reader 	= csv.reader(f)#csv.reader(f, delimiter="\t")
					d 		= list(reader)
					
					for item in d:
						count1	+= 1
						transid		= item[2]
						if start_import:
							date		= item[0]
							time		= item[1]
							in_out		= item[4]
							employee_no	= item[5]
							finger_no	= item[6]
							#sql="update hr_timesheet_scan set in_out='%s' where name='%s'" % (in_out, transid)
							#self._cr.execute(sql)
							vals = {'date':date,'time': time,'name':transid,'in_out':in_out,'employee_no': employee_no,'finger_no':finger_no}
							'''items 		= self.env['hr.timesheet.scan'].search([('employee_no','=',employee_no),('name','=',transid)])	
							if len(items)>0:
								for item in items:
									item.write(vals)
							else:	'''	
							self.env['hr.timesheet.scan'].create(vals)
						else:
							if transid == name:
								start_import = True
				#file_path	= self.env['dincelaccount.settings'].get_scan_ts_file()	
				newname="%s_%s" %(file_path, dt.datetime.now().strftime("%Y%m%d"))
				os.rename(file_path, newname) 
			except ValueError as ex:
				_logger.error('DincelTimesheetScan.import_scan_ts() err ex [ %s ] name[ %s ] count1[ %s ] ' % (ex, name, count1))
				pass  
			
		#_logger.error("import_scan_ts [%s] count1[%s]" % (file_path, count1))
		return True
		
		
class DincelTimesheetImportCopy(models.Model):
	_name = "hr.timesheet.import.copy"	
	_description = 'Timesheet Import'	
	_inherit = ['mail.thread']	
	name 		= fields.Char("Reference")	
	date 		= fields.Date('Date Import')
	date_from 	= fields.Date('Date From')
	date_to 	= fields.Date('Date To')
	day_ids 	= fields.One2many('hr.timesheet.import.copydays', 'timesheet_id', 'Days')
	line_ids 	= fields.One2many('hr.timesheet.import.copyline', 'timesheet_id', 'Timesheet Lines')
	summary_ids = fields.One2many('hr.timesheet.import.copysummary', 'timesheet_id', 'Summary Lines')
	leave_ids 	= fields.One2many('hr.timesheet.import.leaveline', 'timesheet_id', 'Leave Lines')
	user_id		= fields.Many2one('res.users','Created By')
	employee_id = fields.Many2one("hr.employee", string="Employee")
	payfrequency_id = fields.Many2one("hr.payroll.payfrequency", string="Pay Frequency")
	state = fields.Selection(dincelpayroll_vars.IMPORT_COPY_STATE_OPTIONS, string='State', default='draft', track_visibility='onchange') 
	x_first_name = fields.Char(related='employee_id.x_first_name', store=True)
	x_last_name = fields.Char(related='employee_id.x_last_name', store=True)
	x_group_id = fields.Many2one('hr.employee.group', related='employee_id.x_group_id', store=True)
	x_emp_number = fields.Char(related='employee_id.x_emp_number')
	hours_variance= fields.Boolean("Hour Variance", default=False)
	authorise_variance = fields.Boolean("Authorise Hour Variance", default=False, track_visibility='onchange')
	total_hrs	= fields.Float("Total Hours w/o Loading")
	offset_hrs	= fields.Float("Unbalanced Hrs")
	payslip_ref	= fields.Char("Payslip Ref") 
	auto_calc_lock = fields.Boolean(string='Auto calc lock', default=False)
	_order = 'date desc, x_last_name asc, x_first_name asc'
	
	@api.multi
	def write(self, values):
		record = super(DincelTimesheetImportCopy, self).write(values)#, self.with_context(ctx)).write(values)
		copy 	= self.browse(self.id)
		self.calculate_summary_new(copy)
		return record
		
	@api.multi	
	def button_confirm_timesheet(self):
		if self.state=="draft":
			self.write({'state':"confirm"})
			
	@api.multi	
	def button_draft_timesheet(self):
		if self.state=="confirm":
			self.write({'state':"draft"})	
			
	@api.multi
	def button_date_inout_fix(self):
		ctx = self._context.copy()
		#model = 'account.invoice'
		#from odoo.tools.translate import _
		ctx.update({'default_employee_id':self.employee_id.id, 
					'default_date_to':self.date_to, 
					'default_date_from':self.date_from, 
					'default_date':self.date, 
					'default_import_id':self.id})
		return {
			'name': "Day in/out",
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hr.timesheet.manage',
			#'views': [(view.id, 'form')],
			#'view_id': view.id,
			'target': 'new',
			#'res_id':self.id,
			'context': ctx,
		}
		#return True
		
	@api.multi
	def button_date_range(self):
		'''date_from	=	parser.parse(self.date_from)
		date_to		=	parser.parse(self.date_to)
		copydays 	=   self.env['hr.timesheet.import.copydays']
		dt			=	date_from
		scan_ids 	=	[] #so that same date not processed twice
		while (dt <= date_to):
			#name 		= 	"%s" %  (dt.strftime("%A"))
			emp_id		=	self.employee_id.id
			next_day_out=	self.employee_id.x_group_id.next_day_out
			employee_no	=	self.employee_id.x_emp_number
			hrs_in		=	self.employee_id.x_group_id.hrs_in or "8:30"
			hrs_out		=	self.employee_id.x_group_id.hrs_out or "17:00"
			_vals={
				'employee_id':emp_id,
				'timesheet_id':self.id,
				'name':name,
				'date':dt
				}
			
			#sql="select * from hr_timesheet_scan where employee_no='%s' and date='%s' "	 % ()
			lines=copydays.search([('timesheet_id','=',self.id),('date','=',dt)])	
			if len(lines)>0:
				for line in lines:
					line.write(_vals)
					copydays_id=line.id
					scan_ids = self.day_details_update_insert(emp_id, employee_no, dt, copydays_id, next_day_out, hrs_in, hrs_out, scan_ids)
			else:
				new=copydays.create(_vals)
				copydays_id=new.id
				scan_ids = self.day_details_update_insert(emp_id, employee_no, dt, copydays_id, next_day_out, hrs_in, hrs_out, scan_ids)
			dt	=	dt + timedelta(days=1) #next day loop...	'''
		dtfrom, dtto, employee = self.date_from, self.date_to, self.employee_id
		self.add_date_range_timesheet(self.id, dtfrom, dtto, employee)
		self.init_ts_after_import(self)
		#self.update_paid_hours(self)
		
		return True
		
	def init_ts_after_import(self, ts):
		self.update_rounding_hours(ts)
		self.update_paid_hours(ts)
		self.update_pay_hours_calculation(ts)
		
	def update_paid_hours(self, ts):
		#employee	=	ts.employee_id
		#employee_no	=	employee.x_emp_number
		#emp_id		=	employee.id
		is_miss_hours=False
		#reset first....in/out
		for line in ts.day_ids:
			_val={'actual_from':'','actual_to':''}
			line.write(_val)	
		for line in ts.day_ids:
			_in=False
			_out=False
			paid_in=False
			paid_out=False
			#_val={}
			hrs_paid , hrs_unpaid = 0.0, 0.0	
			for item in line.paydtls_ids:
				if item.category_id.amt_type == "zero":
					hrs_unpaid+=item.hours
				else:
					hrs_paid+=item.hours
			
			_val={'hrs_tot_unpaid': hrs_unpaid,'hrs_paid':hrs_paid}
			#_tot_hrs=hrs_unpaid+hrs_paid
			 
			for item in line.daydtls_ids:
				if item.in_out=="IN" and _in==False:
					_in=item.time
					paid_in=item.time_adjust
					_val['paid_from']=item.time_adjust
				elif item.in_out=="OUT" and _out==False:
					_out=item.time	
					paid_out=item.time_adjust
					_val['paid_to']=item.time_adjust	
			if _in:
				_val['actual_from']=_in
			if _out:
				_val['actual_to']=_out	
				if _in:
					actual_hrs= self.env['hr.employee.group.attendance'].get_hrs_difference(_in, _out, True)
					_val['actual_hrs']=actual_hrs
			#if paid_in and paid_out:		
			#	paid_hrs= self.env['hr.employee.group.attendance'].get_hrs_difference(paid_in, paid_out, True)
			#	_val['paid_hrs']=paid_hrs
			
			line.write(_val)	
			line.check_hours_work()
		self.calculate_summary_new(ts)

	@api.multi
	def button_save_into_summary(self):
		self.calculate_summary_new(self)

	@api.multi
	def button_update_paidhrs(self):
		#self.update_paid_hours(self)
		self.update_pay_hours_calculation(self)
		
	@api.multi
	def button_update_rounding(self):
		if self.auto_calc_lock == False:
			self.update_rounding_hours(self)
			self.update_paid_hours(self)
			self.update_pay_hours_calculation(self)
		else:
			raise UserError("Warning! cound not continue due to auto calc lock flag is On.")
			
	def update_rounding_hours(self, ts):
		rounding		=	self.env['dincelaccount.settings'].get_rounding()
		
		rounding_trigger= 0
		rounding_back	= 0
		if rounding:
			rounding_trigger=rounding.trigger
			rounding_back	=rounding.round_back
			#roster_hrs_in		=	ts.employee_id.x_group_id.hrs_in or "8:30"
			#roster_hrs_out		=	ts.employee_id.x_group_id.hrs_out or "17:00"
			for line in ts.day_ids:
			
				roster_hrs_in	=line.roster_from
				roster_hrs_out	=line.roster_to
				
				for item in line.daydtls_ids:
					hh_mm	= item.time
					inout	= item.in_out
					if inout == "IN":
						roster_hrs = roster_hrs_in
					else:#out	
						roster_hrs = roster_hrs_out
					if rounding_trigger > 0 and roster_hrs and hh_mm:	
						hh_mm1 	= self.rounding_time(inout, roster_hrs, hh_mm, rounding_trigger, rounding_back)
						vals={'time_adjust':hh_mm1}
						#_logger.error("hh_mm[%s] new [%s] roster_hrs[%s]inout[%s] " % (hh_mm, hh_mm1, roster_hrs, inout))
						item.write(vals)
		return True
		
	def update_pay_hours_calculation(self, ts):
		# rounding		=	self.env['dincelaccount.settings'].get_rounding()
		attendance 	=   self.env['hr.employee.group.attendance']
		group_id	=	ts.employee_id.x_group_id.id
		for line in ts.day_ids:
			name 		=line.name
			
			for pay in line.paydtls_ids:
				pay.write({'hours': 0}) # reset to zero
			# name 		= 	"%s" %   (dt.strftime("%a")) #(dt.strftime("%A"))
			line.write({'hrs_breaks_paid': 0, 'hrs_breaks_unpaid': 0, 'is_miss_hours': False})
			roster	= None	
			attns 	= attendance.search([('name','=',name),('group_id','=',group_id)])	
			for attn in attns:
				roster=attn.roster_id
				
			if roster:	
				hrs_total	= float(line.hrs_paid)
				hrs_roster	= float(line.hrs_roster)
				if hrs_total > 0.0:
					#check fixed.............
					#---------------------------
					#step1
					tot_fixed = 0
					tot_balance = 0
					normal_hrs = 7.6
					for rosteritem in roster.item_ids:
						hour_type = rosteritem.hour_type
						if rosteritem.sequence == 1:
							normal_hrs = rosteritem.hours
						trigger_from = float(rosteritem.trigger_from)
						if hrs_total >= trigger_from:
							if hour_type == "fixed":
								for pay in line.paydtls_ids:
									if pay.category_id.id == rosteritem.category_id.id:
										pay_hours = rosteritem.hours
										if pay.category_id.code == "paid-break":
											line.write({'hrs_breaks_paid': rosteritem.hours})
										elif pay.category_id.code == "unpaid-break":
											#9.5 10
											if float(normal_hrs) < float(hrs_total):
												line.write({'hrs_breaks_unpaid': rosteritem.hours})
											else:
												line.write({'hrs_breaks_unpaid': 0})
												pay_hours = 0
										#tot_fixed += float(rosteritem.hours)
										tot_fixed += float(pay_hours)
										pay.write({'hours': pay_hours})
					#check balance.............
					#---------------------------
					#step2		
					for rosteritem in roster.item_ids:
						hour_type=rosteritem.hour_type
						trigger_from=float(rosteritem.trigger_from)
						if hrs_total >= trigger_from:
							if hour_type=="balance":
								for pay in line.paydtls_ids:
									if pay.category_id.id==rosteritem.category_id.id:
										balance=hrs_total-trigger_from
										pay.write({'hours':balance})	
										tot_balance+=balance
					#check balance with max.............
					#---------------------------
					#step3		
					for rosteritem in roster.item_ids:
						hour_type=rosteritem.hour_type
						trigger_from=float(rosteritem.trigger_from)
						bal2max=float(rosteritem.hours)
						if hrs_total >= trigger_from:
							if hour_type=="bal2max":
								for pay in line.paydtls_ids:
									if pay.category_id.id==rosteritem.category_id.id:
										total=tot_fixed+tot_balance
										net_hrs=hrs_total-total
										if net_hrs<0:
											total=0
										elif net_hrs>bal2max:
											net_hrs=bal2max
										pay.write({'hours':net_hrs})	

				hrs_other=float(line.hrs_unpaid)+float(line.leave_hrs)
				if (hrs_other+hrs_total) != hrs_roster:
					#_logger.error("%s hrs_other[%s] hrs_total[%s] hrs_roster[%s]" % (name, hrs_other, hrs_total, hrs_roster))
					line.write({'is_miss_hours':True})
		
		self.calculate_summary_new(ts)	
		return True
		
		
	def add_date_range_timesheet(self, ts_id, dtfrom, dtto, employee):
		date_from	=	parser.parse(dtfrom)
		date_to		=	parser.parse(dtto)
		copydays 	=   self.env['hr.timesheet.import.copydays']
		attendance 	=   self.env['hr.employee.group.attendance']
		holiday 	=   self.env['dincelpayroll.holiday']
		dt			=	date_from
		scan_ids 	=	[] #so that same date not processed twice
		rounding	=	self.env['dincelaccount.settings'].get_rounding()
		
		rounding_trigger=0
		rounding_back	=0
		if rounding:
			rounding_trigger=rounding.trigger
			rounding_back	=rounding.round_back
		emp_id		=	employee.id
		next_day_out=	employee.x_group_id.next_day_out
		employee_no	=	employee.x_emp_number
		hrs_in		=	employee.x_group_id.hrs_in or "8:30"
		hrs_out		=	employee.x_group_id.hrs_out or "17:00"
		group_id	=	employee.x_group_id.id	
		state_id	= 	employee.x_state_id and employee.x_state_id.id or None
		while (dt <= date_to):
			name 		= 	"%s" %   (dt.strftime("%a")) #(dt.strftime("%A"))
			
			_vals={
				'employee_id':emp_id,
				'timesheet_id':ts_id,
				'name':name,
				'date':dt
				}
			roster	= None	
			#for roster getting from db
			attns 	= attendance.search([('name','=',name),('group_id','=',group_id)])	
			for attn in attns:
				roster=attn.roster_id
				_vals['roster_from']=attn.hrs_in
				_vals['roster_to']	=attn.hrs_out
				_vals['hrs_roster']	=attn.sub_total
				#s_log="emp_id[%s]dt[%s]state_id[%s]"  % (emp_id, dt, state_id)
				#add to paid/hrs only if there is roster in/out.....
				if attn.hrs_in and attn.hrs_out:
					#search for holiday /public holiday if any
					hdays	= holiday.search([('date','=',dt)])			
					for hday in hdays:
						#s_log+="holiday_status_id[%s]"  % (hday.holiday_status_id.id)
						if hday.holiday_status_id:
							ok_state=False
							#s_log+="state_ids[%s]"  % (len(hday.state_ids))
							if len(hday.state_ids)==0: #no state means all states valid
								ok_state=True
							else:
								for hstate in hday.state_ids:
									#s_log+="code[%s]"  % (hstate.code)
									if hstate.code =="ALL":#all states valid
										ok_state=True
									else:
										if state_id and state_id == hstate.id: #specific state specific
											ok_state=True
							#s_log+="ok_state[%s]"  % (ok_state)
							#_logger.error("add_date_range_timesheet s_logs_logs_log[%s]" % (s_log))
							if ok_state:				
								_vals['leave_id']	= hday.holiday_status_id.id
								_vals['paid_from']	= attn.hrs_in
								_vals['paid_to']	= attn.hrs_out
								_vals['msg_code']	= hday.name
			#sql="select * from hr_timesheet_scan where employee_no='%s' and date='%s' "	 % ()
			lines	= copydays.search([('timesheet_id','=',ts_id),('date','=',dt)])	
			if len(lines) > 0:
				for line in lines:
					#line.write(_vals)
					copydays_id	= line.id
					scan_ids 	= self.day_details_update_insert(emp_id, employee_no, dt, copydays_id, next_day_out, hrs_in, hrs_out, scan_ids, rounding_trigger, rounding_back)
					hrs_paid, hrs_unpaid = self.pay_details_update_insert(emp_id, employee_no, dt, copydays_id, roster)
					#_newval	={'hrs_unpaid': hrs_unpaid, 'hrs_paid':hrs_paid}
					#line.write(_newval)
					#_vals['hrs_unpaid']=hrs_unpaid
					#_vals['hrs_paid']=hrs_paid
					line.write(_vals)
					#_logger.error("add_date_range_timesheet next_day_outnext_day_out[%s]" % (_vals))
			else:
				new			= copydays.create(_vals)
				copydays_id	= new.id
				scan_ids 	= self.day_details_update_insert(emp_id, employee_no, dt, copydays_id, next_day_out, hrs_in, hrs_out, scan_ids, rounding_trigger, rounding_back)
				hrs_paid, hrs_unpaid  = self.pay_details_update_insert(emp_id, employee_no, dt, copydays_id, roster)
				#_newval	={'hrs_unpaid': hrs_unpaid, 'hrs_paid':hrs_paid}
				#new.write(_newval)
				
			dt	=	dt + timedelta(days=1) #next day loop...
			
	def rounding_time(self, inout, roster_hrs, hh_mm, rounding_trigger, rounding_back):
		hh_mm1 = hh_mm
		str1="hh_mm1[%s][%s]" % (hh_mm1, inout)
		#str1="hh_mm1[%s][%s][%s][%s][%s][%s]" % (hh_mm1,inout, roster_hrs, hh_mm, rounding_trigger, rounding_back)
		if rounding_trigger > 0 and roster_hrs and hh_mm:
			t0			= roster_hrs.split(":")
			hh_roster			= int(t0[0])
			mm_roster			= int(t0[1])
			
			t1			= hh_mm.split(":")
			act_hh		= int(t1[0])
			act_mm		= int(t1[1])
			
			if inout == "IN":
				if act_hh < hh_roster:
					act_hh= hh_roster
					act_mm= mm_roster
					str1+="early i1n--"
				elif act_hh == hh_roster and act_mm <= mm_roster:	
					act_hh= hh_roster
					act_mm= mm_roster
					str1+="early in2--"
				else:#rounding starts	
					hh_diff=act_hh-hh_roster
					str1+="early out hh_diff[%s]-]-" % (hh_diff)
					if abs(hh_diff)<=1:
						#act_hh= hh0
						#act_mm= mm0
						#if mm0==0:
						#	mm0=60
						mm_diff=abs(mm_roster-act_mm)
						if mm_diff <= rounding_trigger:
							act_hh=hh_roster
							act_mm=mm_roster
							str1+="trigger in[%s]" % (rounding_trigger)
						else:
							#act_hh=hh0
							str1+="latelate in[%s]" % (rounding_back)
							act_mm=mm_roster+rounding_back #late in
			else:#OUT
				if act_hh > hh_roster:
					act_hh= hh_roster
					act_mm= mm_roster
					str1+="late out1--"
				elif act_hh == hh_roster and act_mm >= mm_roster:	
					act_hh= hh_roster
					act_mm= mm_roster
					str1+="late out2--"
				else:#rounding starts
					
					hh_diff=act_hh-hh_roster
					str1+="early out hh_diff[%s]-]-" % (hh_diff)
					if abs(hh_diff)<=1:
						#act_hh= hh0
						#act_mm= mm0
						if mm_roster==0:
							mm_roster1=60
						else:
							mm_roster1=mm_roster
						mm_diff=abs(mm_roster1-act_mm)
						str1+="lessby 1hr out--diff[%s]" % (mm_diff)
						if mm_diff <= rounding_trigger:
							act_hh=hh_roster
							act_mm=mm_roster
							str1+="lessby rounding_trigger[%s]" % (rounding_trigger)
						else:
							#act_hh=hh0
							str1+="early2 out[%s]" % (rounding_back)
							act_mm=mm_roster1-rounding_back #early out
			hh_mm1 = '%02d:%02d' % (act_hh, act_mm)
			str1+="time_hh_mm[%s]" % (hh_mm1)
		#_logger.error("rounding_time[%s]" % (str1))	
		return hh_mm1
		
		
	def day_details_update_insert(self, emp_id, employee_no, dt, copydays_id, next_day_out, roster_hrs_in, roster_hrs_out, scan_ids, rounding_trigger, rounding_back):
		
		def add_update_details(lines, copydays_id, emp_id, dt1, roster_hrs_in, roster_hrs_out, scan_ids, rounding_trigger, rounding_back, skip_in = False):
			daydtls 	=   self.env['hr.timesheet.import.copydaydtls']
			if len(lines) > 0:
				hrs_in1		=	float(roster_hrs_in.replace(":","")) - 100.0
				hrs_out1	=	float(roster_hrs_out.replace(":","")) + 100.0
				for line in lines:
				
					in_out	= line.in_out
					time	= line.time
					t1		= time.split(":")
					hh1		= int(t1[0])
					mm1		= int(t1[1])
					if "IN" in in_out:
						inout="IN"
					else:
						inout="OUT"
					hh_mm	= '%02d%02d' % (hh1, mm1)
					hh_mm	= float(hh_mm)
					okay=False
					str1="type[%s]" % (inout)
					if inout=="IN":
						roster_hrs=roster_hrs_in
						if not skip_in:
							in_time=hh_mm
							str1+="in_time[%s] " % (in_time)
							if in_time > hrs_in1 or in_time < hrs_out1:
								okay=True
								#str1+="okay[%s]" % (okay)
					else:#out	
						roster_hrs=roster_hrs_out
						out_time=hh_mm
						str1+="out_time[%s]" % (out_time)
						if out_time > hrs_in1 or out_time < hrs_out1:
							okay=True
							#str1+="okay[%s]" % (okay)
					str1+="okay111[%s]" % (okay)
					if(okay and scan_ids):
						for scan_id in scan_ids:
							if line.id==scan_id:
								okay=False #so that same record (in/out) not repeated/processed twice
					str1+="okay222[%s]" % (okay)
					#_logger.error("str1[%s]okayfinal[%s] dt [%s] copydays_id [%s] inout[%s] hh_mm[%s] roster-in[%s] out[%s]" % (str1, okay, dt1, copydays_id, inout, hh_mm, hrs_in1,hrs_out1 ))			
					if okay:			
						scan_ids.append(line.id)
						time_hh_mm = '%02d:%02d' % (hh1, mm1)
						
						_vals={
							'copydays_id': copydays_id,
							'in_out': inout,
							'employee_id': emp_id,
							'date': dt1,
							'time': time_hh_mm,
							}
						#_logger.error("add_edit dt [%s] _vals[%s] " % (dt, _vals ))	
						dtls	= daydtls.search([('employee_id','=',emp_id),('date','=',dt1),('in_out','=',inout),('time','=',time_hh_mm)])	
						if len(dtls) > 0:
							for dtl in dtls:
								dtl.write(_vals)
						else:
							time_hh_mm1=self.rounding_time(inout, roster_hrs, time_hh_mm, rounding_trigger, rounding_back)
							_vals['time_adjust']= time_hh_mm1
							daydtls.create(_vals)
			return scan_ids		
		'''					
		hrs_in1		=	float(hrs_in.replace(":","")) - 100.0
		hrs_out1	=	float(hrs_out.replace(":","")) + 100.0'''
		#name 		= 	"%s" %  (dt.strftime("%A"))
		
		scan 		=   self.env['hr.timesheet.scan']
		
		lines		=	scan.search([('employee_no','=',employee_no),('date','=',dt)])	
		scan_ids 	= 	add_update_details(lines, copydays_id, emp_id, dt, roster_hrs_in, roster_hrs_out, scan_ids, rounding_trigger, rounding_back)
		if next_day_out:#but skip next day IN entry
			#_logger.error("dt [%s] next_day_out[%s] " % (dt, next_day_out ))
			dt2	=	dt + timedelta(days=1)
			lines		= scan.search([('employee_no','=',employee_no),('date','=',dt2)])	
			scan_ids 	= add_update_details(lines, copydays_id, emp_id, dt2, roster_hrs_in, roster_hrs_out, scan_ids, rounding_trigger, rounding_back, True)
		return scan_ids
		
	#insert pay deatils..........
	#-----------------------------------------------------------------------------------	
	def pay_details_update_insert(self, emp_id, employee_no, dt, copydays_id, roster):
		paydtls 	=   self.env['hr.timesheet.import.copypaydtls']
		#name 		= 	"%s" %  (dt.strftime("%A"))
		hrs_paid, hrs_unpaid = 0.0, 0.0
		'''sql="select roster_id from hr_employee_group_attendance where name='%s' and group_id='%s'" % (name, group_id)
		self.env.cr.execute(sql)	
		rs2 = self.env.cr.dictfetchall()
		hrs_paid , hrs_unpaid = 0.0, 0.0
		for row in rs2:
			roster_id = row.get('roster_id')'''
		if roster:	
			#hr.employee.roster
			#lines	 =	self.env['hr.employee.roster.item'].search([('roster_id','=',roster_id)])
			#-------------------------------------------------------------------------------------------------------------------------------
			#e.g. weekend or fridays no roster or hours required to come in....but can be OT1.5/ OT2.0 so zerorise by default in hrs value
			#-------------------------------------------------------------------------------------------------------------------------------
			has_roster_hrs = True if roster.hrs_total and float(roster.hrs_total) > 0.0 else False
			#	has_roster_hrs=True
			#else:
			#	has_roster_hrs=False
			for line in roster.item_ids:		
				hrs = line.hours if has_roster_hrs else 0
				_vals={
					'copydays_id': copydays_id,
					'category_id': line.category_id.id,
					'hours': hrs,
					'employee_id':emp_id,
					}
				if line.category_id.amt_type=="zero":
					hrs_unpaid+=line.hours
				else:
					hrs_paid+=line.hours
				#_logger.error("add_edit dt [%s] _vals[%s] " % (dt, _vals ))
				dtls	= paydtls.search([('copydays_id','=',copydays_id),('category_id','=',line.category_id.id)])	
				if len(dtls) > 0:
					for dtl in dtls:
						dtl.write(_vals)
				else:
					paydtls.create(_vals)
		return hrs_paid , hrs_unpaid
		
	@api.multi
	def button_leave_balance(self):
		#dt=datetime.today() this is a test for this is taetdsafadf #test
		ctx = self._context.copy()
		#model = 'account.invoice'
		#from odoo.tools.translate import _
		ctx.update({'default_employee_id':self.employee_id.id, 
					'default_date_till':self.date, 
					'default_date_from':self.date, 
					'default_individual':True, 
					'default_reportcode':'entitlesumm'})
		return {
			'name': "Entitle Summary",
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
	def get_loading_expt_hours(self, ts_item, employee):
		loading_hrs_ex=0.0
		for day in ts_item.day_ids:
			#----------------------leave column ends---------------------------------------------------------		
			if day.leave_id:
				if day.leave_id.x_code in ["public","compensation"]:
					for pitem in day.paydtls_ids:
						for special_pay in employee.x_group_id.specialpay_ids:
							if special_pay.type=="loading":
								if pitem.category_id and (pitem.category_id.id==special_pay.parent_id.id):
									loading_hrs_ex+=float(pitem.hours)
			#--------------------------------------------------------------------------------------------------	
		return loading_hrs_ex
		
	def calculate_summary_new(self, copy):
		
		for line in copy.summary_ids:
			line.write({'hrs_net':0,'hrs':0,'xfactor':0}) #reset tot hrs
		employee	 = copy.employee_id
		payfreq_code = copy.payfrequency_id.code 
		_default_work_hrs=38.0
		_payperiod_annual=0.0
		_payperiod_personal=0.0
		_payperiod_lsl=0.0
		total_hrs=0
		hour_variance=False	
		#>> x_code [breavement, nopay, compensation, communit, parental,annual, personal, longservice]
		#>> hardcoded...in order to automatic or link with timesheets/payslip summary table/s...
		arr_leaves=self.env['hr.employee'].get_leave_hrs_arr(employee) #, payperiod="fortnight", pay_basis="S"
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
		tot_worked_hrs	=0.0
		tot_leave_hrs	=0.0
		_leave_ids		=[]
		is_time_half_pay=employee.x_group_id.is_time_half_pay or False
		is_break_pay	=employee.x_group_id.is_break_pay or False
		str1=""
		#---------------------------------------------------------------------------
		#--LEAVES starts-----STEP 1--required for loading calculation ...just in case.....
		#---------------------------------------------------------------------------
		for leaveitem in copy.leave_ids:
			if not leaveitem.category_id:
				continue
			_qty=0.0	
			for day in leaveitem.leave_days:
				if day.is_leave:
					_qty+=float(day.hours)
			#_qty		=	item.tot_hrs
			#todo fixe in the source location or while saving this data in first place..................
			if leaveitem.tot_hrs != _qty:
				leaveitem.write({'tot_hrs':_qty})
			#	
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
			factor_type	=	leaveitem.category_id.factor_type
			
			for line in copy.summary_ids:
				if line.category_id and (line.category_id.id==leaveitem.category_id.id):
					summary=line
					_qty+=float(line.hrs)
			vals_summary = {'category_id': leaveitem.category_id.id,'name':leaveitem.category_id.name}
			xfactor=1.0
			vals_summary['hrs']			=float(_qty)
			vals_summary['xfactor']		=float(xfactor)
			vals_summary['factor_type']	=factor_type
			vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)
			
			tot_leave_hrs	+=float(_qty)
			#if line.category_id.is_ts_sum:
			#	total_hrs	+=float(_qty)
			#xfactor					=vals_summary['xfactor']
			#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
			vals_summary['employee_id']		=copy.employee_id.id
			
			
			if summary:
				summary.write(vals_summary)	
			else:
				vals_summary['timesheet_id']	=copy.id
				summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)	
		#---------------leave end-----------------
		#---------------------------------------------------------------------------

		loading_hrs_ex = self.get_loading_expt_hours(copy, employee)
		# _logger.info("get_loading_expt_hours.........loading hour ex %s" % loading_hrs_ex)
		if len(copy.day_ids)>0:
			str1=""
		
			
			for day in copy.day_ids:
				#----------------------leave column start---------------------------------------------------------
				'''
				if day.leave_id and day.leave_hrs:
					summary			= None
					leave_category	= day.leave_id.x_category_id
					category_id		= leave_category.id
					factor_type		= leave_category.factor_type
					_qty			= day.leave_hrs
					for line in copy.summary_ids:
						if line.category_id and (line.category_id.id==category_id):
							summary=line
					vals_summary = {'category_id': category_id,'name':leave_category.name}
					xfactor=1.0
					vals_summary['hrs']			=float(_qty)
					vals_summary['xfactor']		=float(xfactor)
					vals_summary['factor_type']	=factor_type
					vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)
					
					tot_leave_hrs	+=float(_qty)
					#xfactor					=vals_summary['xfactor']
					#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
					vals_summary['employee_id']		=copy.employee_id.id
					
					
					if summary:
						summary.write(vals_summary)	
					else:
						vals_summary['timesheet_id']	=copy.id
						summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)	
				'''		
				#----------------------leave column ends---------------------------------------------------------		
				#if day.leave_id:
				#	if day.leave_id.x_code in ["public","compensation"]:
				#		for pitem in day.paydtls_ids:
				#			for special_pay in employee.x_group_id.specialpay_ids:
				#				if special_pay.type=="loading":
				#					if pitem.category_id and (pitem.category_id.id==special_pay.parent_id.id):
				#						loading_hrs_ex+=float(pitem.hours)
				#--------------------------------------------------------------------------------------------------						
				if day.is_miss_hours:
					hour_variance=True
				for item in day.paydtls_ids:
					if not item.category_id:
						continue
					if item.category_id.amt_type=="zero":
						continue
					#if not line.category_id.code=="unpaid-break":#do not get the unpaid break
					#	continue
					_qty		=	item.hours	
					xfactor		=item.category_id.factor_default
					factor_type =item.category_id.factor_type
					summary		= 	None
					vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name}
					for line in copy.summary_ids:
						if line.category_id and (line.category_id.id==item.category_id.id):
							_qty+=line.hrs
							
							#vals_summary['xfactor']		=float(xfactor)
							#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
							summary=line
					#if item.category_id.is_ts_sum:
					#	total_hrs	+=float(_qty)		
					if not item.category_id.is_loading:
						skip_hr=False
						for skip_cat in employee.x_group_id.skiphr_ids:
							if skip_cat.category_id.id==item.category_id.id:
								skip_hr=True
								str1+="skip[%s]" % (item.category_id.id)
						if not skip_hr:
							tot_worked_hrs+=float(item.hours)
							str1+="add[%s (%s)]" % (item.category_id.id, item.hours)
					vals_summary['hrs']			=float(_qty)
					vals_summary['xfactor']		=float(xfactor)
					vals_summary['factor_type']	=factor_type
					
					vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)
					#xfactor					=vals_summary['xfactor']
					#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
					vals_summary['employee_id']		=copy.employee_id.id
					
					#_logger.error("vals_summaryvals_summary [%s]" % (vals_summary))
					if summary:
						summary.write(vals_summary)	
					else:
						vals_summary['timesheet_id']	=copy.id
						summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)	
						
			#---------------------------------------------------------------------------------------			
			#----------------ADD special pay ------------- or loading ------------------------------			
			#---------------------------------------------------------------------------------------
			for special_pay in employee.x_group_id.specialpay_ids:
				if special_pay.type=="loading":
					loading_pay=None
					loading_hrs=0.0
					for line in copy.summary_ids:
						if line.category_id and (line.category_id.id==special_pay.parent_id.id):
							loading_pay=special_pay.category_id
							if special_pay.parent_id.holiday_status_id:# if leave then not leave laoding....deduction
								loading_hrs += float(line.hrs)# -float(loading_hrs_ex)
							else: #eg public holiday pay 30%
								loading_hrs += float(line.hrs)  - float(loading_hrs_ex) #this is only applicabe for normal hrs but not in leaves

					if loading_pay:
						summary		= 	None
						vals_summary = {'category_id': loading_pay.id,'name':loading_pay.name}
						#vals_summary['hrs']			=float(loading_hrs)
						#vals_summary['xfactor']		=float(loading_pay.factor_default)
						#vals_summary['factor_type']	=loading_pay.factor_type
						
						#vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)

						vals_summary['employee_id']		=copy.employee_id.id
						for line in copy.summary_ids:
							if line.category_id and (line.category_id.id==loading_pay.id):
								summary=line
								loading_hrs+=line.hrs
						vals_summary['hrs']			=float(loading_hrs)
						vals_summary['xfactor']		=float(loading_pay.factor_default)
						vals_summary['factor_type']	=loading_pay.factor_type		
						if summary:
							summary.write(vals_summary)	
						else:
							vals_summary['timesheet_id']	=copy.id
							summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)
						 
			
					
		else:
			
			for item in copy.line_ids:
				if not item.category_id:
					continue
				_qty		=	item.hrs
				xfactor		=	item.xfactor
				factor_type	=	item.factor_type
				summary		= 	None
				vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name}
				for line in copy.summary_ids:
					if line.category_id and (line.category_id.id==item.category_id.id):
						_qty+=line.hrs
						
						#vals_summary['xfactor']		=float(xfactor)
						#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
						summary=line
				#if item.category_id.is_ts_sum:
				#		total_hrs	+=float(_qty)		
				if not item.category_id.is_loading:
					skip_hr=False
					for skip_cat in employee.x_group_id.skiphr_ids:
						if skip_cat.category_id.id==item.category_id.id:
							skip_hr=True
							str1+="skip[%s]" % (item.category_id.id)
					if not skip_hr:
						tot_worked_hrs+=float(item.hrs)
						str1+="add[%s (%s)]" % (item.category_id.id, item.hrs)
				vals_summary['hrs']			=float(_qty)
				vals_summary['xfactor']		=float(xfactor)
				vals_summary['factor_type']	=factor_type
				
				vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)
				#xfactor					=vals_summary['xfactor']
				#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
				vals_summary['employee_id']		=copy.employee_id.id
				if summary:
					summary.write(vals_summary)	
				else:
					vals_summary['timesheet_id']	=copy.id
					summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)	
		#--LEAVES-----
		#moved above
		'''
		for item in copy.leave_ids:
			if not item.category_id:
				continue
			_qty		=	item.tot_hrs
			if _qty > 0: 
				if _qty >= item.holiday_id.x_total_hrs:
					sql="update hr_holidays set x_redeem='full' where id='%s'" % (item.holiday_id.id)
				else:
					sql="update hr_holidays set x_redeem='part' where id='%s'" % (item.holiday_id.id)
			else:
				sql="update hr_holidays set x_redeem='none' where id='%s'" % (item.holiday_id.id)

			self.env.cr.execute(sql)
			
			summary		= 	None
			amt_type	=	item.category_id.amt_type
			factor_type	=	item.category_id.factor_type
			
			for line in copy.summary_ids:
				if line.category_id and (line.category_id.id==item.category_id.id):
					summary=line
			vals_summary = {'category_id': item.category_id.id,'name':item.category_id.name}
			xfactor=1.0
			vals_summary['hrs']			=float(_qty)
			vals_summary['xfactor']		=float(xfactor)
			vals_summary['factor_type']	=factor_type
			vals_summary['hrs_net']		=round(float(_qty)*float(xfactor),2)
			
			tot_leave_hrs	+=float(_qty)
			#xfactor					=vals_summary['xfactor']
			#vals_summary['hrs_net']	=round(float(_qty)*float(xfactor),2)
			vals_summary['employee_id']		=copy.employee_id.id
			
			
			if summary:
				summary.write(vals_summary)	
			else:
				vals_summary['timesheet_id']	=copy.id
				summary = self.env['hr.timesheet.import.copysummary'].create(vals_summary)	'''
		total_hrs=0.0
		for line in copy.summary_ids:
			if line.category_id.is_ts_sum:
				total_hrs+=line.hrs
		offset_hrs=tot_worked_hrs + tot_leave_hrs - _default_work_hrs
		#if abs(offset_hrs) >0.0:
		#	hour_variance=True
		#else:
		#	hour_variance=False		
		sql="""update hr_timesheet_import_copy set 
				total_hrs='%s',
				offset_hrs='%s',
				hours_variance='%s' 
			where 
				id='%s' 
			""" % (total_hrs, offset_hrs, hour_variance, copy.id)
		self.env.cr.execute(sql)	
		#_logger.error("hr_timesheet_import_copyhr_timesheet_import_copy str1[%s]tot_worked_hrs[%s]tot_leave_hrs[%s] _default_work_hrs[%s] " % (str1, tot_worked_hrs, tot_leave_hrs, _default_work_hrs))	
		return True
	
	def update_payslip_from_ts(self, payslip, import_ts):
		#---------------------------------
		#timesheet------------------------
		#---------------------------------
		#_logger.error("update_payslip_from_tsupdate_payslip_from_ts11111 import_ts[%s] update_payslip_from_ts" % (import_ts))	
		obj_time	= self.env['hr.employee.timesheet']
		obj_leave	= self.env['hr.payslip.leave']
		obj_day		= self.env['hr.payslip.leave.day']	
		employee_id = payslip.employee_id.id
		if len(import_ts.day_ids)>0:
			for day in import_ts.day_ids:
				for item in day.paydtls_ids:
					if not item.category_id:
						continue
					_qty		=item.hours	
					xfactor		=item.category_id.factor_default
					factor_type =item.category_id.factor_type	
					hrs_net		=float(_qty)*float(xfactor)
					_vals={
						'employee_id': employee_id,
						'category_id': item.category_id.id,
						'hrs': _qty,
						'hrs_net': hrs_net,
						'xfactor': xfactor,
						'factor_type': factor_type,
						'date': day.date,
						'name': day.name,
						'payslip_id': payslip.id,
						'reversed':False,
						}
					lineitems 	= obj_time.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',item.category_id.id),('date','=',day.date)])	
					if len(lineitems)>0:
						for item_time in lineitems:
							item_time.write(_vals)
					else:
						obj_time.create(_vals)
		else:
			for item in import_ts.line_ids:
				_vals={
					'employee_id': employee_id,
					'category_id': item.category_id.id,
					'hrs': item.hrs,
					'hrs_net': item.hrs_net,
					'xfactor': item.xfactor,
					'factor_type': item.factor_type,
					'date': item.date,
					'name': item.name,
					'payslip_id': payslip.id,
					'reversed':False,
					}
				lineitems 	= obj_time.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',item.category_id.id),('date','=',item.date)])	
				if len(lineitems)>0:
					for item_time in lineitems:
						item_time.write(_vals)
				else:
					obj_time.create(_vals)
				#_logger.error("update_payslip_from_tsupdate_payslip_from_ts2222 [%s] update_payslip_from_ts" % (_vals))	
			
		#--------------------leaves-------------
		#---------------------------------
		#leaves---------------------------
		#---------------------------------	
		for item in import_ts.leave_ids:
			_vals={
				'employee_id': employee_id,
				'category_id': item.category_id.id,
				#'category_id': item.category_id.id,
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
				for item_leave in lineitems:
					item_leave.write(_vals)
			else:
				item_leave = obj_leave.create(_vals)
			
			
			
			for dayitem in item.leave_days:
				dayitems 	= obj_day.search([('payslip_leave_id','=',item_leave.id),('date','=',dayitem.date)])
				val_day={'date':dayitem.date,'name':dayitem.name,'is_leave':dayitem.is_leave,'hours':dayitem.hours,'payslip_leave_id':item_leave.id}
				
				if len(dayitems)>0:
					for day_found in dayitems:
						day_found.write(val_day)
				else:	
					obj_day.create(val_day)
						
		self.env['hr.payslip'].calculate_payslip(payslip)	
		#ids.append(payslip.id)
		
		#---------------------------------------
		#line.write({"state":'done'})
		payslip_ref=payslip.number
		import_ts.write({"state":'done','payslip_ref':payslip_ref})		
		return True
		
class DincelTimesheetImportCopyPayDtls(models.Model):
	_name = "hr.timesheet.import.copypaydtls"	
	copydays_id= fields.Many2one('hr.timesheet.import.copydays', string='In Out Day', ondelete='cascade',)
	employee_id = fields.Many2one("hr.employee", string="Employee")
	sequence 	= fields.Integer("Sequence", default=50)
	hours 		= fields.Float('Hours')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category') 
	holiday_id 	= fields.Many2one('hr.holidays', string='Leave')
	
	@api.onchange('holiday_id')
	def _onchange_holiday(self):
		if self.holiday_id:
			if self.holiday_id.holiday_status_id.x_category_id:
				self.category_id=self.holiday_id.holiday_status_id.x_category_id.id
			
class DincelTimesheetImportCopyDayDtls(models.Model):
	_name = "hr.timesheet.import.copydaydtls"	
	copydays_id= fields.Many2one('hr.timesheet.import.copydays', string='In Out Day', ondelete='cascade',)
	employee_id = fields.Many2one("hr.employee", string="Employee")
	sequence 	= fields.Integer("Sequence", default=50)
	date 		= fields.Date('Date')
	time 		= fields.Char("Time Actual")
	time_adjust	= fields.Char("Time Paid (adjusted)")
	in_out		= fields.Selection(dincelpayroll_vars.TS_INOUT_OPTIONS,string="In/Out")
	category_id 	= fields.Many2one('hr.pay.category', string='Pay Category') 
	
	@api.onchange('time_adjust')
	def _onchange_time_adjust(self):
		if self.time_adjust:
			txt = self.time_adjust
			self.time_adjust=self.env['hr.employee.group.attendance'].get_hh_mm_format(txt)
			'''
			txt = self.time_adjust
			if ":" in txt:
				arr = txt.split(":")
				hh	= arr[0]
				mm	= arr[1]
			else:	
				tt = txt
				if len(txt) < 4:
					tt = txt.zfill(4)
				else:
					tt = txt
					
				hh= tt[:2]	
				mm= tt[2:4]
				#self.time_adjust="%s:%s [%s]" % (hh, mm, tt)
				self.time_adjust="%s:%s" % (hh, mm)'''
#				
class DincelTimesheetImportCopyDays(models.Model):
	_name = "hr.timesheet.import.copydays"	
	name 		= fields.Char("Name")	
	timesheet_id= fields.Many2one('hr.timesheet.import.copy', string='Timesheet',ondelete='cascade',)
	employee_id = fields.Many2one("hr.employee", string="Employee")
	date 		= fields.Date('Date')
	roster_from	= fields.Char("Roster In")	
	roster_to	= fields.Char("Roster Out")
	paid_from	= fields.Char("Paid In")	
	paid_to		= fields.Char("Paid Out")		
	actual_from	= fields.Char("Actual In")	
	actual_to	= fields.Char("Actual Out")
	actual_hrs	= fields.Float("Actual Hrs")
	hrs_breaks_unpaid= fields.Float("Unpaid Break")
	hrs_breaks_paid	= fields.Float("Paid Break")
	#paid_hrs	= fields.Float("Paid Hrs")
	hrs_paid	= fields.Float("Paid Hrs")
	hrs_paid_read= fields.Float("Paid Hrs", compute="_hrs_paid")
	hrs_unpaid	= fields.Float("Unpaid Hrs")
	hrs_tot_unpaid	= fields.Float("Total Unpaid") #breaks unpaid = hrs unpaid [leave etc]
	hrs_tot_paid	= fields.Float("Total Paid")	#break paid + hrs paid 
	hrs_total	= fields.Float(string='Total Hrs', compute='_hrs_total')
	hrs_roster	= fields.Float("Roster Hrs")
	breaks		= fields.Char("Breaks")	
	user_id 	= fields.Many2one("res.users", string="Last Saved By")
	date_saved	= fields.Date('Saved Date')
	daydtls_ids = fields.One2many('hr.timesheet.import.copydaydtls', 'copydays_id', 'Time In/Out')
	paydtls_ids = fields.One2many('hr.timesheet.import.copypaydtls', 'copydays_id', 'Pay Lines')
	is_miss_hours= fields.Boolean(string='Confirm')
	leave_id	= fields.Many2one('hr.holidays.status', string='Leave Type')
	leave_hrs	= fields.Float("Leave Hrs")
	msg_code	= fields.Char("Message Code")	
	
	@api.onchange('hrs_paid')
	def _hrs_paid(self):
		for record in self:
			record.hrs_paid_read= record.hrs_paid
				
	'''
	@api.depends('hrs_paid', 'hrs_unpaid')
	def _compute_total(self):
		for record in self:
			is_miss_hours=False
			if self.date:
				hrs_total	= record.hrs_paid + record.hrs_unpaid
				group_id	= self.employee_id.x_group_id.id
				dt			= self.date
				#self.env['hr.employee.group.attendance']
				#name 		= "%s" %  (dt.strftime("%A"))
				attns 		= self.env['hr.employee.group.attendance'].search([('name','=',name),('group_id','=',group_id)])	
				for attn in attns:
					roster_total = attn.sub_total
					if roster_total!=hrs_total:
						is_miss_hours=True
			record.is_miss_hours =is_miss_hours
	'''		
	@api.depends('hrs_paid', 'hrs_unpaid', 'leave_hrs')
	def _hrs_total(self):
		for record in self:
			#record.hrs_total= record.hrs_paid + record.hrs_breaks_paid + record.hrs_breaks_unpaid + record.leave_hrs
			record.hrs_total= record.hrs_paid + record.leave_hrs + record.hrs_unpaid
	
	@api.onchange('leave_hrs','leave_id')
	def _hrs_leaves(self):
		for record in self:
			if record.leave_id and record.hrs_roster:
				#	
				hrs_leave	= 0.0
				if record.leave_id.x_code in ["public", "compensation"]:
					record.paid_from = record.roster_from
					record.paid_to = record.roster_to
					record.leave_hrs = 0
					record.hrs_unpaid = 0
				else:
					if record.leave_id.x_is_ts_fullday:
						# dt			= record.date
						name 		= record.name	# @"%s" %  (dt.strftime("%A"))
						group_id	= record.employee_id.x_group_id.id
						roster_id 	= self.env['hr.employee.group.attendance'].get_roster(name, group_id)
						if roster_id:
							hrs_leave 	= roster_id.hrs_leave or 0.0
						# attns 		= self.env['hr.employee.group.attendance'].search([('name','=',name),('group_id','=',group_id)])
						# for attn in attns:
						# hrs_leave = attn.roster_id and attn.roster_id.hrs_leave
						record.leave_hrs = hrs_leave or 0.0
					else:
						# record.hrs_paid = 0
						hrs_leave = record.leave_hrs
					#	hrs_leave = record.leave_hrs
					hrs_unpaid = float(record.hrs_roster)
					hrs_unpaid -= float(record.hrs_paid)
					hrs_unpaid -= float(hrs_leave)
				
					record.hrs_unpaid = hrs_unpaid
			else:
				record.hrs_unpaid = 0
				record.leave_hrs = 0
				
	def check_hours_work(self):
		if self.timesheet_id.auto_calc_lock == False:
			if self.paid_to and self.paid_from:	
				hrs_total = self.env['hr.employee.group.attendance'].get_hrs_difference(self.paid_from, self.paid_to, is_decimal=True)	
				hrs_total = float(hrs_total)
				'''if hrs_total<=4.0:
					self.hrs_paid=hrs_total
				elif hrs_total>4.0 and hrs_total<=9.5:
					self.hrs_breaks_paid=0.5
					self.hrs_paid=hrs_total-0.5
				else:
					self.hrs_breaks_paid=0.5
					self.hrs_breaks_unpaid=0.5
					self.hrs_paid=hrs_total-1.0'''
				self.hrs_paid=hrs_total	
				self.hrs_paid_read=hrs_total	
				if self.leave_id and self.leave_id.x_code == "public":
					self.msg_code = self.msg_code
				else:
					self.msg_code = ""
			else:
				if self.roster_from and self.roster_to:
					self.hrs_breaks_paid = 0
					self.hrs_breaks_unpaid = 0
					self.hrs_paid = 0
					self.hrs_paid_read = 0
					self.msg_code = "NoInOut"
	@api.multi
	def button_update_hours(self):
		#
		ctx = self._context.copy()
		for day in self:
			#self.calculate_payslip(payslip)
			#@ form_view = self.env.ref('crm.crm_case_form_view_oppor')
			#tree_view = self.env.ref('crm.crm_case_tree_view_oppor')
			view_id=None
			form_view = self.env.ref('dincelpayroll.dincelpayroll_timesheet_import_copydays_form_view')
			if form_view:
				view_id=form_view.id
			#_logger.error("dincelpayroll_timesheet_import_copydays_form_view000022222[%s]" % (view_id))
			return {
				'name': 'Day Details',
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'hr.timesheet.import.copydays',
				#'views': [(form_view, 'form')],
				'view_id': view_id,
				'target': 'new',
				'res_id':day.id,
				'context': ctx,
			}
			
		
	@api.onchange('paid_from')
	def _onchange_paid_from(self):
		if self.paid_from:
			txt = self.paid_from
			self.paid_from=self.env['hr.employee.group.attendance'].get_hh_mm_format(txt)
			self.check_hours_work()

	@api.onchange('paid_to')
	def _onchange_paid_to(self):
		if self.paid_to:
			txt = self.paid_to
			self.paid_to=self.env['hr.employee.group.attendance'].get_hh_mm_format(txt)		
			self.check_hours_work()
			
			
class DincelTimesheetImportCopySummary(models.Model):
	_name = "hr.timesheet.import.copysummary"	
	name 		= fields.Char("Name")	
	timesheet_id= fields.Many2one('hr.timesheet.import.copy', string='Timesheet',ondelete='cascade',)
	employee_id = fields.Many2one("hr.employee", string="Employee")
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	hrs_net 	= fields.Float("Hours Net")
	hrs 		= fields.Float("Hours")
	xfactor		= fields.Float(string='Factor', default=1.0, digits=(8, 4))
	factor_type = fields.Selection(dincelpayroll_vars.TS_FACTOR_TYPE_OPTIONS, 'Factor Type',  default='hrs') 
	
	@api.onchange('hrs','hrs_net','xfactor')
	def onchange_hrs(self):
		try:
			if self.hrs and self.xfactor:
				hrs_net = float(self.hrs)* float(self.xfactor)
			else:
				hrs_net=0.0
		except:
			hrs_net=0.0
		self.hrs_net=hrs_net
		
class DincelTimesheetImportCopyLine(models.Model):
	_name = "hr.timesheet.import.copyline"	
	_order = 'sequence, date'	
	sequence 	= fields.Integer("Sequence", default=50)	
	name 		= fields.Char("Name")	
	timesheet_id= fields.Many2one('hr.timesheet.import.copy', string='Timesheet',ondelete='cascade',)
	date 		= fields.Date('Date')
	employee_id = fields.Many2one("hr.employee", string="Employee")
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	hrs 		= fields.Float("Hours")
	hrs_net		= fields.Float("Net")
	dt_import	= fields.Datetime('Time Import')
	locked		= fields.Boolean(string='Locked', default=False)
	xfactor		= fields.Float(string='Factor', default=1.0, digits=(8, 4))
	factor_type = fields.Selection(dincelpayroll_vars.TS_FACTOR_TYPE_OPTIONS, 'Factor Type',  default='hrs') 
	
	# factor_default = fields.Float("Timesheet Factor Default", digits=(6, 4),default=1.0)
	@api.onchange('hrs', 'hrs_net', 'xfactor')
	def onchange_hrs(self):
		try:
			if self.hrs and self.xfactor:
				hrs_net = float(self.hrs)* float(self.xfactor)
			else:
				hrs_net = 0.0
		except:
			hrs_net = 0.0
		self.hrs_net = hrs_net
		
	@api.onchange('date')
	def onchange_date(self):
		#result = []
		if self.date:
			dt=parser.parse(self.date)
			name 	= "%s" %  (dt.strftime("%a"))
			self.name=name
		#return result 
		
	def get_timesheet_bydate(self, emp_id, date):
		_impobj		= self.env['hr.timesheet.import.copyline']
		items 		= _impobj.search([('employee_id','=',emp_id),('date','=',date)])	
		return items
		
	def save_update_timesheet(self, emp_id, cat_id, date, hrs, hrs_net, xfactor, factor_type,  dt_import):
		_impobj		= self.env['hr.timesheet.import.copyline']
		date_exists = _impobj.search([('employee_id','=',emp_id),('date','=',date),('category_id','=',cat_id)])	
		if date_exists:
			if not date_exists.locked:
				_vals = {
					'hrs': hrs,
					'hrs_net': hrs_net,
					'xfactor': xfactor,
					'factor_type':factor_type,
				}
				date_exists.write(_vals)
			return date_exists
		else:
			_vals={
				'employee_id': emp_id,
				'date': date,
				'category_id': cat_id,
				'hrs': hrs,
				'hrs_net': hrs_net,
				'xfactor': xfactor,
				'factor_type':factor_type,
				'dt_import': dt_import,
				}
			return _impobj.create(_vals)


class DincelTimesheetImportLeaveLine(models.Model):
	_name="hr.timesheet.import.leaveline"
	timesheet_id= fields.Many2one('hr.timesheet.import.copy', string='Timesheet',ondelete='cascade',)
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	holiday_id 	= fields.Many2one('hr.holidays', string='Leave')
	date_from = fields.Datetime(string='Date From')		
	date_to = fields.Datetime(string='Date To')		
	tot_hrs = fields.Float("Hours", store=True, readonly=True, compute='_compute_leaves_hrs',)	
	#days = fields.Float("Days")	
	category_id = fields.Many2one('hr.pay.category', string='Leave Category') #, 
	date = fields.Date(string='Date')
	holiday_status_id = fields.Many2one('hr.holidays.status', related='holiday_id.holiday_status_id')
	leave_days  	= fields.One2many('hr.timesheet.import.leaveday','timesheet_leave_id', string='Leave Days')
	balance_hrs		= fields.Float("Balance Hours")	 
	
	@api.depends('leave_days.hours')
	def _compute_leaves_hrs(self):
		
		try:
			tot_hrs=0
			if len(self.leave_days)>0:
				for line in self.leave_days:
					tot_hrs+=line.hours
				#tot_hrs = sum(line.hours for line in self.leave_days) 
			self.tot_hrs = tot_hrs	
		except:
			pass
		
		
	@api.onchange('holiday_id')
	def _onchange_holiday_id(self):
		if self.holiday_id:
			vals={'date_from': self.holiday_id.date_from, 'date_to': self.holiday_id.date_to	}
			
			if self.holiday_id.holiday_status_id and self.holiday_id.holiday_status_id.x_category_id:
				vals['category_id']=self.holiday_id.holiday_status_id.x_category_id.id or None
					
			#vals['tot_hrs']	= self.holiday_id.x_total_hrs
			vals['date']		= self.holiday_id.date_from
			vals['balance_hrs']	= self.holiday_id.x_balance_hrs
			#vals['date']	= self.holiday_id.date_from
			
			pay_from	= self.timesheet_id.date_from
			pay_to		= self.timesheet_id.date_to
			
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
						'timesheet_leave_id': self.id,#self.holiday_id.id,
						}
					items.append(item)
					dt	=	dt + timedelta(days=1) #next day loop...
				#return {'value':{'leave_days':items}}	
				vals['leave_days']=items
				
			return {'value':vals}
			
class DincelTimesheetImportLeaveDay(models.Model):
	_name="hr.timesheet.import.leaveday"
	timesheet_leave_id 		= fields.Many2one('hr.timesheet.import.leaveline', string='Timesheet Leave')	
	name	= fields.Char('Name')
	date	= fields.Date('Date')
	is_leave= fields.Boolean('Leave')
	hours	= fields.Float('Hours')
	
	@api.onchange('is_leave')
	def _onchange_is_leave(self):
		val={}
		if self.is_leave:
			leave_hrs=0.0
			dt=parser.parse(self.date)
			name 		= "%s" %  (dt.strftime("%a"))
			group_id	= self.timesheet_leave_id.employee_id.x_group_id.id
			#_logger.error("_onchange_is_leave_onchange_is_leave %s %s" % (name, group_id))
			roster_id 	= self.env['hr.employee.group.attendance'].get_roster(name, group_id)
			if roster_id:
				leave_hrs 	= roster_id.hrs_leave or 0.0
				
			#if self.timesheet_leave_id.employee_id.x_group_id:
			#	leave_hrs=self.timesheet_leave_id.employee_id.x_group_id.leave_hrs
			val['hours']=leave_hrs	
		else:
			val['hours']=0
		return {'value':val}
		
#hr.timesheet.import		
class DincelTimesheetImportLog(models.Model):
	_name = "hr.timesheet.import.log"		
	date 		= fields.Date('Date')
	employee_id = fields.Many2one("hr.employee", string="Employee")
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	hrs 		= fields.Float("Hours")
	hrs_net		= fields.Float("Net")
	dt_import	= fields.Datetime('Time Import')
	locked		= fields.Boolean(string='Locked', default=False, digits=(8, 4))
	xfactor		= fields.Float(string='Factor', default=1.0)
	
	def get_timesheet_bydate_log(self, emp_id, date):
		_impobj		= self.env['hr.timesheet.import.log']
		items 		= _impobj.search([('employee_id','=',emp_id),('date','=',date)])	
		return items
		
	def save_update_log(self, emp_id, cat_id, date, hrs, hrs_net, xfactor, factor_type, dt_import):
		_impobj		= self.env['hr.timesheet.import.log']
		date_exists = _impobj.search([('employee_id','=',emp_id),('date','=',date),('category_id','=',cat_id)])	
		if date_exists:
			if not date_exists.locked:
				_vals = {
					'hrs': hrs,
					'hrs_net': hrs_net,
					'xfactor': xfactor,
					'factor_type': factor_type,
				}
				date_exists.write(_vals)
			return date_exists
		else:
			_vals={
				'employee_id': emp_id,
				'date': date,
				'category_id': cat_id,
				'hrs': hrs,
				'hrs_net': hrs_net,
				'xfactor': xfactor,
				'factor_type': factor_type,
				'dt_import': dt_import,
				}
			return _impobj.create(_vals)
			
			
class DincelEmployeeHours(models.Model):
	_name = "hr.employee.attendance"
	_description = "Employee Work Hours"
	_order = 'dayofweek, hour_from'
	#The day of the week with Monday=0, Sunday=6 []#https://docs.python.org/2/library/datetime.html#date.weekday()
	name = fields.Char(required=True)
	dayofweek = fields.Selection(dincelpayroll_vars.WEEK_DAY_OPTIONS) #, required=True, index=True, default='0'
	'''[
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday')
		], 'Day of Week', required=True, index=True, default='0')'''
	category_id = fields.Many2one('hr.pay.category', string='Pay Category', domain=[('active','=',True),('is_summary', '=', False)])	
	hour_from = fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
	hour_to = fields.Float(string='Work to', required=True)
	employee_id = fields.Many2one("hr.employee", string="Employee", required=True, ondelete='cascade')
	normal_pay = fields.Float("Normal Pay") #9.5
	meal_unpaid = fields.Float("Unpaid meal")	#0.5
	paid_meal = fields.Float("Paid meal")	#0.5
	paid_t15 = fields.Float("T1.5")	#1.5
	paid_t20 = fields.Float("T2.0")	#[TOT=12 hrs]
	sub_total	= fields.Float(string='Subtotal', compute="_sub_total")
	is_weekend	= fields.Boolean(string='Is Weekend', compute='_is_weekend')
	
	@api.depends('dayofweek')
	def _is_weekend(self):
		for record in self:
			if record.dayofweek in ["5","6"]:
				record.is_weekend= True
			else:	
				record.is_weekend= False
				
	@api.onchange('dayofweek')
	def _onchange_dayofweek(self):
		if self.dayofweek:
			vals={'name': dict(self._fields['dayofweek'].selection).get(self.dayofweek)	}
			return {'value':vals}
			
	@api.depends('normal_pay','meal_unpaid','paid_meal','paid_t15','paid_t20')
	def _sub_total(self):
		for record in self:
			record.sub_total=record.normal_pay + record.meal_unpaid + record.paid_meal + record.paid_t15 + record.paid_t20 
			
			
	
		
#class DincelPayslipEmployee(models.Model):
#	_inherit = 'hr.salary.rule'		