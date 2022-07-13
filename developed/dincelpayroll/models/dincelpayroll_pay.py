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
#import dateparser
#import datetime
import time
import logging
_logger = logging.getLogger(__name__)
'''
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
class DincelHrUOM(models.Model):
	_name = 'hr.uom' #week/month/day/hour/etc
	_description = 'HR UOM'			
	name = fields.Char("UOM")
	code = fields.Char("Code")
	active = fields.Boolean("Active", default=True) 

	
class PayrollPayFrequency(models.Model):
	_name = 'hr.payroll.payfrequency' #weekly/monthly/etc
	_description = 'Pay Frequency'			
	name = fields.Char("Pay Frequency")
	code = fields.Char("Code")
	active = fields.Boolean("Active", default=True) 

class PayrollHrGroupLeave(models.Model):
	_name = 'hr.employee.group.leave'
	pay_basis = fields.Selection([
			('year', 'Yearly'),
			('once', 'Once'),
			], string='Pay Basis')
	group_id 	= fields.Many2one('hr.employee.group', string='Employee Group')
	quantity 	= fields.Float("Entitlement", digits=(8, 4))	
	uom_code = fields.Selection(dincelpayroll_vars.HR_UOM_OPTIONS, string='UOM Code', default='day')
	holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type')
	
	
class DincelEmployeeGroupSkipHour(models.Model):
	_name = 'hr.employee.group.skiphr' #day shift/night shift
	_description = "Employee Group Skip Hr Calculation"
	group_id 	= fields.Many2one('hr.employee.group', string='Employee Group')
	name = fields.Char(required=True)
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )		


	
class DincelEmployeeRoster(models.Model):
	_name = 'hr.employee.roster' 	
	_description = 'Employee Roster'			
	name = fields.Char("Roster")
	hrs_in = fields.Char("In (HH:MM)")
	hrs_out = fields.Char("Out (HH:MM)")
	hh_mm_total = fields.Char("Total (HH:MM)")
	hrs_total = fields.Float("Hrs Total")
	hrs_leave = fields.Float("Hrs Leave")
	item_ids = fields.One2many('hr.employee.roster.item', 'roster_id', 'Roster items', copy=True)
	#hour_ids = fields.One2many('hr.employee.roster.hour', 'roster_id', 'Roster items', copy=True)
	
	@api.onchange('hrs_in', 'hrs_out')
	def _onchange_hrs_inout(self):
		if self.hrs_in:
			ret1 = self.env['dincelaccount.settings'].is_time_format(self.hrs_in)
			if not ret1:
				raise UserError("Warning! invalid time format found (%s)! Please use HH:MM format only." % (self.hrs_in))
		if self.hrs_out:
			ret1 = self.env['dincelaccount.settings'].is_time_format(self.hrs_out)
			if not ret1:
				raise UserError("Warning! invalid time format found (%s)! Please use HH:MM format only." % (self.hrs_out))		
		if self.hrs_out and self.hrs_in: 
			t1= self.hrs_in.split(":")
			hh1=int(t1[0])
			mm1=int(t1[1])
			
			t2= self.hrs_out.split(":")
			hh2=int(t2[0])
			mm2=int(t2[1])
			
			t1=time.strptime(self.hrs_in, '%H:%M') 
			t2=time.strptime(self.hrs_out, '%H:%M')
			t1new=time.mktime(t1)
			t2new=time.mktime(t2)	
			str1="[%s][%s] " % (t1new, t2new)
			if hh2>hh1:
				diff= t2new-t1new 
			else:
				t1mid = time.strptime("23:59", '%H:%M') 
				t1mid2=time.mktime(t1mid)
				diff1 = t1mid2-t1new+60 #for 59 offset 
				t1zero = time.strptime("00:00", '%H:%M') 
				t1zero2=time.mktime(t1zero)
				diff2 = t2new-t1zero2 
				diff = diff1+diff2
				str1+="diff1[%s]diff2[%s]" % (diff1, diff2)
			
			str1+="diff[%s]" % (diff)	
			hrs		=diff/3600
			hrs		=int(hrs)
			secs	=diff- int(hrs*3600)	
			mins=0
			if (secs>0):
				mins	=secs/60
				mins	=int(mins)
			else:
				mins=0
			mins = '%02d' % mins
			hrs = '%02d' % hrs
			str1+="secs[%s]" % (secs)		
			hh_mm_total	="%s:%s" % (hrs, mins)
			hrs_total=round((diff/3600.0),2)
			#_logger.error("_onchange_hrs_inout_onchange_hrs_inout str1[%s]hrs_total[%s] " % (str1, hrs_total)) 
			return {'value':{'hrs_total':hrs_total,'hh_mm_total':hh_mm_total}}	
			
class DincelEmployeeRosterItem(models.Model):
	_name = 'hr.employee.roster.item' 	
	_description = 'Employee Roster Item'	
	_order = 'sequence asc'	
	roster_id 	= fields.Many2one('hr.employee.roster', string='Employee Roster')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	hours = fields.Float("Hrs")
	sequence = fields.Integer("Sequence")
	trigger_from = fields.Float("Trigger From (hrs)")
	hour_type = fields.Selection(dincelpayroll_vars.HOUR_TYPE_OPTIONS, string='Hour Type') 
	
	
'''	
class DincelEmployeeRosterHour(models.Model):
	_name = 'hr.employee.roster.hour' 	
	_description = 'Employee Roster Hour'			
	roster_id 	= fields.Many2one('hr.employee.roster', string='Employee Roster')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	hrs_from = fields.Float("Hrs From")
	hrs_to = fields.Float("Hrs To")'''
	
class DincelEmployeeGroupSpecialPay(models.Model):
	_name = 'hr.employee.group.specialpay' 	
	_description = 'Employee group sepecial pay'			
	group_id 	= fields.Many2one('hr.employee.group', string='Employee Group')
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	parent_id = fields.Many2one('hr.pay.category', string='Parent Pay' )
	type = fields.Selection(dincelpayroll_vars.SPECIALPAY_OPTIONS, string='Pay Type') 
	
class DincelEmployeeGroup(models.Model):
	_name = 'hr.employee.group' #day shift/night shift
	_description = 'Employee Group'			
	name = fields.Char("Group")
	code = fields.Char("Code")
	notes = fields.Char("Notes")
	active = fields.Boolean("Active", default=True) 
	is_timesheet = fields.Boolean("Timesheet Group?", default=False) 
	attendance_ids = fields.One2many('hr.employee.group.attendance', 'group_id', 'Working Time', copy=True)
	skiphr_ids = fields.One2many('hr.employee.group.skiphr', 'group_id', 'Skip Hour Sum', copy=False)
	specialpay_ids = fields.One2many('hr.employee.group.specialpay', 'group_id', 'Special Pay', copy=False)
	leave_ids = fields.One2many('hr.employee.group.leave', 'group_id', 'Leave Accruals', copy=True)
	summary_ids = fields.One2many('hr.employee.group.summary', 'group_id', 'Payslip Summary')
	category_ids = fields.Many2many('hr.pay.category', 'employeegroup_category_rel','group_id', 'category_id', 'Entitlements/Allowances/Deductions')
	#type_control_ids = fields.Many2many('account.account.type', 'account_journal_type_rel', 'journal_id', 'type_id', string='Account Types Allowed')
	category_id = fields.Many2one('hr.pay.category', string='Default Pay Category', domain=[('active','=',True),('is_summary', '=', False)] ) 
	nopay_id = fields.Many2one('hr.pay.category', string='No Pay Category', domain=[('active','=',True),('is_summary', '=', False)] ) 
	leave_loading = fields.Boolean("Leave Loading?", default=False) 
	hrs_variance = fields.Boolean("Day2Day Hour Variance?", default=False) 
	tot_paid_hr = fields.Float("Total Paid Hours (Payperiod)") #duplicate....for future...just incase...eg. 92...for calculation of leave etc.
	payperiod_hrs = fields.Float("Pay Period Hours") #new 1
	#payperiod_hrs = fields.Float("Pay Period Hours") #new 1
	annual_leave = fields.Float("Annual Leave Hours")
	sick_leave = fields.Float("Sick Leave Hours")
	leave_hrs = fields.Float("Leave Hours")
	normal_hrs = fields.Float("Work Hrs (Daily)")
	daily_net_hrs = fields.Float("Net Hours (Daily)",help="For annual salary calculation")
	week_work_days = fields.Float("Weekly Working Days")
	payfrequency_id = fields.Many2one("hr.payroll.payfrequency", string="Pay Frequency")
	factor_hr_rate=fields.Float("Hourly Rate Factor", default=1.0, digits=(10, 6))
	#super_calc_rule = fields.Char("Super Rule(Payperiod)")
	#salary_calc_rule = fields.Char("Super Rule(Annual)")
	factor_super_rate=fields.Float("Super Rate Factor", default=1.0, digits=(10, 6))
	factor_annual_salary=fields.Float("Annual Salary Factor", default=0.0)
	factor_annual_type= fields.Selection([
		('0', 'None'),
		('factor', 'Factor'),
		('pc', 'Percent'),
		], 'Salary Facto Type',  default='0') 	
	employee_count=fields.Integer("Employees", compute='_count_employees')	
	is_time_half_pay = fields.Boolean("Paid Time & Half?", default=False) 
	is_break_pay = fields.Boolean("Paid break?", default=False) 
	next_day_out = fields.Boolean("Next day out", default=False) 
	hrs_in = fields.Char("Roster In (hh:mm)")
	hrs_out = fields.Char("Roster Out (hh:mm)")
	early_in = fields.Float("Early In")
	late_in = fields.Float("Late In")
	early_out = fields.Float("Early Out")
	late_out = fields.Float("Late Out")
	_order = 'name'	
	
	def action_view_employees(self):
		for	record in self:
			#employees = self.env['hr.employee'].search([('x_group_id', '=', record.id),('active', '=', True)]) 
			value = {
					'type': 'ir.actions.act_window',
					'name': _('Employees'),
					'view_type': 'form',
					'view_mode': 'tree,form',
					'res_model': 'hr.employee',
					'domain':[('x_group_id', '=', record.id),('active', '=', True)],
					'context':{},#{'search_default_partner_id': partner_id},
					'view_id': False,#view_id,
				}

			return value
			
		return True
	
	def action_init_salary_super(self):
		for	record in self:
			employees = self.env['hr.employee'].search([('x_group_id', '=', record.id),('active', '=', True)]) 
			
			#_logger.error('action_init_salary_s1111 employees[ %s ]   ' % (employees))
			for emp in employees:
				#_logger.error('action_init_salary_s1111 employees[ %s ]   x_rate_ids[ %s ]' % (employees, emp.x_rate_ids))
				for rate in emp.x_rate_ids:
					if rate.pay_basis and rate.pay_basis=="H":
						emp_id		=emp.id
						group_id	=record.id
						tax_scale_id=emp.x_tax_scale_id.id
						_rate		=rate.salary_rate
						leave_rate, super_amount, salary = self.env['hr.employee.rate'].calc_salary(emp_id,group_id,rate.pay_basis,_rate, tax_scale_id)
						
						#_rate=float(record.salary_rate)*float(_factor)
						vals={'leave_rate':leave_rate}
						#if super_amount:
						vals['super_amount']=super_amount
						#if salary:
						vals['salary_annual']=salary	
						#_logger.error('action_init_salary_super [ %s ]  name[ %s ][ %s ]' % (vals,emp.name, emp.id))
						rate.write(vals)
					else:	
						vals={'salary_annual':rate.salary_rate,'pay_basis':'S','leave_rate':0.0,'super_amount':0.0}
						rate.write(vals)	
	def _count_employees(self):
		for	record in self:
			employees = self.env['hr.employee'].search([('x_group_id', '=', record.id),('active', '=', True)]) 
			record.update({'employee_count': len(employees)})
			
	@api.onchange('daily_net_hrs','week_work_days','payfrequency_id')
	def _onchange_dayofweek(self):
		for record in self:
			_hrs=float(record.daily_net_hrs)
			_days=float(record.week_work_days)
			_code= record.payfrequency_id.code
			_net=0.0
			if _code=="fortnight":
				_net=_hrs*_days*2.0
			elif _code=="week":
				_net=_hrs*_days
			vals={'payperiod_hrs':_net}
			return {'value':vals}
			
class DincelEmployeeAttendance(models.Model):
	_name = "hr.employee.group.summary"
	_description = "Payslip Summary"
	#_order = 'id' #, sequence
	name = fields.Char(required=True)
	group_id = fields.Many2one("hr.employee.group", string="Employee Group", required=True, ondelete='cascade', domain=[('active','=',True),('is_summary', '=', False)])
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )
	account_id = fields.Many2one('account.account', string='GL Account')
	sequence = fields.Integer("Sequence")
	
class DincelEmployeeGroupAttendance(models.Model):
	_name = "hr.employee.group.attendance"
	_description = "Work Detail"
	_order = 'dayofweek, hour_from'
	##The day of the week with Monday=0, Sunday=6 []# https://docs.python.org/2/library/datetime.html#date.weekday()
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
	category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	roster_id 	= fields.Many2one('hr.employee.roster', string='Roster' )	
	hrs_in 		= fields.Char("Roster In")
	hrs_out 	= fields.Char("Roster Out")
	hrs_total 	= fields.Char("Hrs Total")
	hour_from 	= fields.Float(string='Work from', required=True, index=True, help="Start and End time of working.")
	hour_to 	= fields.Float(string='Work to', required=True)
	group_id 	= fields.Many2one("hr.employee.group", string="Employee Group", required=True, ondelete='cascade')
	normal_pay 	= fields.Float("Normal Pay") #9.5
	meal_unpaid = fields.Float("Unpaid meal")	#0.5
	paid_meal 	= fields.Float("Paid meal")	#0.5
	paid_t15 	= fields.Float("T1.5")	#1.5
	paid_t20 	= fields.Float("T2.0")	#[TOT=12 hrs]
	sub_total	= fields.Float(string='Subtotal', compute="_sub_total")
	is_weekend	= fields.Boolean(string='Is Weekend', compute='_is_weekend')
	work_type 	= fields.Selection(dincelpayroll_vars.WORK_TYPE_OPTIONS)
	
	@api.depends('dayofweek')
	def _is_weekend(self):
		for record in self:
			if record.dayofweek in ["5","6"]:
				record.is_weekend= True
			else:	
				record.is_weekend= False
				
	@api.onchange('hrs_in', 'hrs_out')
	def _onchange_hrs_inout(self):
		if self.hrs_in:
			ret1 = self.env['dincelaccount.settings'].is_time_format(self.hrs_in)
			if not ret1:
				raise UserError("Warning! invalid time format found (%s)! Please use HH:MM format only." % (self.hrs_in))
		if self.hrs_out:
			ret1 = self.env['dincelaccount.settings'].is_time_format(self.hrs_out)
			if not ret1:
				raise UserError("Warning! invalid time format found (%s)! Please use HH:MM format only." % (self.hrs_out))		
		if self.hrs_out and self.hrs_in: 
			hrs_total = self.get_hrs_difference(self.hrs_in, self.hrs_out)
			#_logger.error("_onchange_hrs_inout_onchange_hrs_inout str1[%s]hrs_total[%s] " % (str1, hrs_total)) 
			return {'value':{'hrs_total':hrs_total}}	
			
	def get_hrs_difference(self, hrs_in, hrs_out, is_decimal=False):		
		t1= hrs_in.split(":")
		hh_in=int(t1[0])
		mm_in=int(t1[1])
		
		t2= hrs_out.split(":")
		hh_out=int(t2[0])
		mm_out=int(t2[1])
		str1="11..hhout(%s) hh_in[%s]" % (hh_out, hh_in)
		if hh_out<hh_in:
			hh_out+=24
			str1+="--22--hh_out[%s]" % (hh_out)
		hh_diff= hh_out-hh_in 
		mm_diff= mm_out-mm_in 
		str1+="--33--hh_diff[%s]mm_diff[%s]" % (hh_diff, mm_diff)
		# _logger.error("%s %s" % ())
		
		if mm_diff<0:
			mm_diff=60+mm_diff
			hh_diff-=1
			str1+="--44--hh_diff[%s]mm_diff[%s]" % (hh_diff, mm_diff)
		mins = '%02d' % int(mm_diff)
		hrs = '%02d' % int(hh_diff)
		str1+="--55--hrs[%s]mins[%s]" % (hrs, mins)
		# else:#next day out
		if is_decimal:
			mins = (float(mins)/60.00) * 100.00
			mins	=int(mins)
			hrs_total	="%s.%s" % (hrs, mins)
		else:	
			hrs_total	="%s:%s" % (hrs, mins)
		# _logger.error("get_hrs_difference str1[%s]hrs_total[%s]" % (str1, hrs_total))
		return hrs_total	
		
	def get_hh_mm_format(self, txt):
		#txt = time_str
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
		return "%s:%s" % (hh, mm)
		
			
	def get_hrs_differenceXX(self, hrs_in, hrs_out, is_decimal=False):
		t1= hrs_in.split(":")
		hh1=int(t1[0])
		mm1=int(t1[1])
		
		t2= hrs_out.split(":")
		hh2=int(t2[0])
		mm2=int(t2[1])
		# _logger.error("get_hrs_differenceget_hrs_difference hrs_in[%s]hrs_total[%s] " % (hrs_in, hrs_out))
		t1=time.strptime(hrs_in, '%H:%M') 
		t2=time.strptime(hrs_out, '%H:%M')
		t1new=time.mktime(t1)
		t2new=time.mktime(t2)	
		str1="[%s][%s] " % (t1new, t2new)
		if hh2>hh1:
			diff= t2new-t1new 
		else:
			t1mid = time.strptime("23:59", '%H:%M') 
			t1mid2=time.mktime(t1mid)
			diff1 = t1mid2-t1new+60 #for 59 offset 
			t1zero = time.strptime("00:00", '%H:%M') 
			t1zero2=time.mktime(t1zero)
			diff2 = t2new-t1zero2 
			diff = diff1+diff2
			str1+="diff1[%s]diff2[%s]" % (diff1, diff2)
		
		str1+="diff[%s]" % (diff)	
		hrs		=diff/3600
		hrs		=int(hrs)
		secs	=diff- int(hrs*3600)	
		mins=0
		if (secs>0):
			mins	=secs/60
			mins	=int(mins)
		else:
			mins=0
		mins = '%02d' % mins
		hrs = '%02d' % hrs
		str1+="secs[%s]" % (secs)		
		
		if is_decimal:
			mins = (float(mins)/60.00) * 100.00
			mins	=int(mins)
			hrs_total	="%s.%s" % (hrs, mins)
		else:	
			hrs_total	="%s:%s" % (hrs, mins)
			
		return hrs_total
		
	'''@api.onchange('hrs_out')
	def _onchange_hrs_in(self):
		if self.hrs_out:
			ret1 = self.env['dincelaccount.settings'].is_time_format(self.hrs_out)
			if not ret1:
				raise UserError("Warning! invalid time format found (%s)! Please use HH:MM format only." % (self.hrs_out))'''
				
	@api.onchange('dayofweek')
	def _onchange_dayofweek(self):
		if self.dayofweek:
			vals={'name': dict(self._fields['dayofweek'].selection).get(self.dayofweek)	}
			return {'value':vals}
			
	@api.depends('normal_pay','meal_unpaid','paid_meal','paid_t15','paid_t20')
	def _sub_total(self):
		for record in self:
			record.sub_total=record.normal_pay + record.meal_unpaid + record.paid_meal + record.paid_t15 + record.paid_t20 
			
	def get_roster(self, name, group_id):
		#name 		= record.name#@"%s" %  (dt.strftime("%A"))
		#group_id	= record.employee_id.x_group_id.id
		attns 		= self.env['hr.employee.group.attendance'].search([('name','=',name),('group_id','=',group_id)])	
		for attn in attns:
			return attn.roster_id# and attn.roster_id.hrs_leave
		return None	
	
class PayrollPayCategory(models.Model):
	_name = 'hr.pay.category' #A/L, DS, S/L, etc
	_description = 'Pay Category'			
	name = fields.Char("Description")
	code = fields.Char("Code")
	mapping_txt = fields.Char("Mapping Text")
	active = fields.Boolean("Active", default=True) 
	taxable = fields.Boolean("Taxable") 
	is_dcstime = fields.Boolean("DCS Primary Category?", default=False) 
	is_directpay = fields.Boolean("Direct/Manual Payslip Summary Item?", default=False) 
	super = fields.Boolean("Super", help="Calculate Super eg. do not tick for salary sacrifice")  #NOT IN USE???
	is_tax = fields.Boolean("Is Tax?", help="Check if this PAYG Tax", default=False)
	#is_child = fields.Boolean("Is child/auto linked", help="Eg leave loading") 
	sequence = fields.Integer("Sequence")
	parent_id = fields.Many2one("hr.pay.category", string="Root / Parent", domain=[('is_summary','=',True)])
	auto_category_id = fields.Many2one("hr.pay.category", string="Auto Add Parent (eg Loading)") #is_child = fields.Boolean("Is child/auto linked", help="Eg leave loading") 
	pc_amt = fields.Float("Amount / Percent")
	uom_id = fields.Many2one("hr.uom", string="UOM")
	uom_code = fields.Selection(dincelpayroll_vars.HR_UOM_OPTIONS, string='UOM Code')
	amt_type= fields.Selection([
		('0', 'None'),
		('amt', 'Fixed Amount'),
		('pc', 'Percent'),
		('calc', 'Calculated'),
		('times', 'Fold/Times'),
		('zero', 'Zero Factor (no pay)'),
		], 'PC/Amt Type',  default='0') 	
	subtype= fields.Selection([
		('0', 'None'),
		('1', 'Amount'),
		('2', 'Percent'),
		], 'Sub Type',  default='0') 	
	category = fields.Selection(dincelpayroll_vars.PAY_CATEGORY_OPTIONS, string='Category/Header',  default='wage') 
	super_type = fields.Selection(dincelpayroll_vars.SUPER_TYPE_OPTIONS, string='Super Type',  default='super')
	allowance_type = fields.Selection(dincelpayroll_vars.ALLOWANCE_OPTIONS, string='Allowance Type')
	deduction_type = fields.Selection(dincelpayroll_vars.DEDUCTION_OPTIONS, string='Deduction Type')
	pay_type = fields.Selection(dincelpayroll_vars.PAY_TYPE_OPTIONS, string='Pay Type',  default='na')
	holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type')
	loading_ratio = fields.Float("Loading Ratio", default=0.0)
	#category= fields.Selection([
	#	('allowance', 'Allowance'),
	#	('deduction', 'Deduction'),
	#	('wage', 'Wage'),
	#	('entitle', 'Entitlements'),
	#	('leave', 'Leaves'),
	#	('summary', 'Summary'),
	#	], 'Category',  default='wage') 
	type= fields.Selection([
		('0', 'Default'),
		('1', 'Summary'),
		], 'Type',  default='0') 
	is_summary = fields.Boolean("Is Summary/Payslip Category", default=False) 	
	is_loading = fields.Boolean("Is Loading", default=False) 
	is_ts_sum = fields.Boolean("Is Timesheet Sum", default=False) 
	summary_type = fields.Selection([
			('na', 'NA'),
			('base', 'Base'),
			('ot15', 'OT1.5'),
			('ot20', 'OT2.0'),
			('personal', 'Personal Leave'),
			('annual', 'Annual Leave'),
			('loadingleave', 'Loading Annual'),
			('loadingshift', 'Loading Shift'),
			('paidbreak', 'Paid Break'),
			('partdayleave', 'Part Day Leave'),
			], string='Summary Type', default='na')	
	expense_account_id = fields.Many2one('account.account', string='GL Expense Account')
	payable_account_id = fields.Many2one('account.account', string='GL Payable Account')
	tax_id = fields.Many2one("account.tax", string='Tax')
	tax_type= fields.Selection([
		('pre', 'PRE'),
		('post', 'POST'),
		], 'Tax Type') 
	print_type= fields.Selection([
		('seperate', 'Print Seperately'),
		('payslip', 'Print on Payslip'),
		('hide', 'Hide on Payslip'),
		], 'Print Type') 
	allow_enter = fields.Boolean("Allow User Entry") 	
	accrued = fields.Boolean("Leave Accrued") 	
	balance_fw = fields.Boolean("Balance Carried Forward?") 	
	comments = fields.Char("Comments")
	sub_category = fields.Selection([
			('annual', 'Annual'),
			('longservice', 'Long Service Leave'),
			('personal', 'Personal Leave'),
			('parental', 'Parental Leave'),
			], string='Sub Category')
	pay_basis = fields.Selection([
			('year', 'Yearly'),
			('once', 'Once'),
			], string='Pay Basis')
	entitlement = fields.Float("Entitlement (days)", digits=(8, 4))		
	calc4gross = fields.Boolean("Calculated in Gross (payslip)", default=True) 
	factor_type= fields.Selection(dincelpayroll_vars.TS_FACTOR_TYPE_OPTIONS, 'Timesheet Factor Type',  default='hrs') 
	factor_default = fields.Float("Timesheet Factor Default", digits=(6, 4),default=1.0)		
	#todo...entitlement unit /days/hours/etc if required...
	
	def get_xfactor(self, amt_type, pc_amt):
		xfactor = 1
		if amt_type == "pc":
			xfactor = float(pc_amt)*0.01
		elif amt_type == "times":
			xfactor = pc_amt
		elif amt_type == "zero":
			xfactor = 0
		return xfactor
		
class DincelEmployeeWorkHours(models.Model):
	_name = 'hr.employee.workhrs'		
	_description = "Employee Work Hours"
	employee_id = fields.Many2one('hr.employee', string='Employee')	
	description = fields.Char("Description")
	category_id = fields.Many2one('hr.pay.category', string='Pay Category', domain=[('active','=',True),('is_summary', '=', False)] )
	mon_hrs = fields.Float("MON")
	tue_hrs = fields.Float("TUE")
	wed_hrs = fields.Float("WED")
	thu_hrs = fields.Float("THU")
	fri_hrs = fields.Float("FRI")
	sat_hrs = fields.Float("SAT")
	sun_hrs = fields.Float("SUN")
	sub_total	= fields.Float(string='Subtotal', compute="_sub_total")
	
	@api.depends('mon_hrs','tue_hrs','wed_hrs','thu_hrs','fri_hrs','sat_hrs','sun_hrs')
	def _sub_total(self):
		for record in self:
			record.sub_total=record.mon_hrs + record.tue_hrs + record.wed_hrs + record.thu_hrs + record.fri_hrs + record.sat_hrs + record.sun_hrs
			
	@api.onchange('category_id')
	def _onchange_category_id(self):
		if self.category_id:
			vals={'description': self.category_id.name	}
			return {'value':vals}
			
class DincelPayrollEntitlements(models.Model):
	_name = 'hr.payroll.entitlement'		
	_description = "Payroll Entitlement"
	sequence 	= fields.Integer("Sequence")
	description = fields.Char("Description")
	employee_id = fields.Many2one('hr.employee', string='Employee')			
	category = fields.Selection(dincelpayroll_vars.PAY_CATEGORY_OPTIONS, string='Category/Header',  default='wage')
	category_id = fields.Many2one('hr.pay.category', string='Title', domain=[('active','=',True),('is_summary', '=', False)] )
	amount = fields.Float("Amount / Percent")
	hours = fields.Float("Hours")
	amt_type= fields.Selection([
		('amt', 'Fixed Amount'),
		('pc', 'Percent'),
		('calc', 'Calculated'),
		], 'Type') 	
	account_id 	= fields.Many2one('account.account', string='GL Code', domain=[('active','=',True)])
	cost_state_id = fields.Many2one("res.country.state", string='Cost State')
	costcentre_id = fields.Many2one("hr.cost.centre", string='Cost Centre')
	uom_id = fields.Many2one("hr.uom", string="UOM")
	uom_code = fields.Selection(dincelpayroll_vars.HR_UOM_OPTIONS, string='UOM Code', default='day')
			
	@api.onchange('category')
	def _onchange_category(self):
		if self.category:
			domain={'category_id': [('category','=',self.category)]}
			return {'domain':domain}
			
	@api.onchange('category_id')
	def _onchange_category_id(self):
		if self.category_id:
			vals={'description': self.category_id.name	}
		else:
			vals={'description': ''	}
		return {'value':vals}
				
''' 
class ResBaseConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"
	payroll_clearing_code = fields.Char(string='Clearing Account Code')
	
	@api.model
	def get_values(self):
		res = super(ResBaseConfigSettings, self).get_values()
		res.update(
			payroll_clearing_code=self.env['ir.config_parameter'].sudo().get_param('payroll.clearing_code'),
		)
		return res

	@api.multi
	def set_values(self):
		super(ResBaseConfigSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('payroll.clearing_code', self.payroll_clearing_code)
'''