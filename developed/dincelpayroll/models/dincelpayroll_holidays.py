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
#import dateparser
#import datetime
import logging
_logger = logging.getLogger(__name__)

 		
class DincelEmployeeHolidayStatus(models.Model):
	_inherit = 'hr.holidays.status'	
	x_code = fields.Selection(dincelpayroll_vars.LEAVE_TYPE_OPTIONS, "Code") 
	x_refcode = fields.Char("Ref Code (Peoplekey)") 
	x_accrued = fields.Boolean("Accrued", default=False)
	x_is_ts_fullday = fields.Boolean("Full Day Timesheet Calculate", default=False)
	x_category_id = fields.Many2one('hr.pay.category', string='Pay Category' )	
	
	#= fields.Selection(dincelpayroll_vars.PAY_CATEGORY_OPTIONS, string='Category/Header',  default='wage') fields.Char("Code")
	
class DincelEmployeeHolidays(models.Model):
	_inherit = 'hr.holidays'	
	x_total_hrs = fields.Float("Total Hours", digits=(10, 3))	
	x_paidleave_ids = fields.One2many('hr.payslip.leave','holiday_id', string='Paid Leaves')
	x_sub_category = fields.Selection([
			('annual', 'Annual'),
			('longservice', 'Long Service Leave'),
			('personal', 'Personal Leave'),
			('parental', 'Parental Leave'),
			('other', 'Other Leave'),
			], string='Sub Category')
	x_redeem = fields.Selection([
			('none', 'None'),
			('part', 'Part'),
			('full', 'Full'),
			], string='Redeemed', default='none')
	x_first_name = fields.Char(related='employee_id.x_first_name', store=True)
	x_last_name = fields.Char(related='employee_id.x_last_name', store=True)
	x_date_from = fields.Date("From Date",help="Date only. no time for date compare with payslip")
	x_date_to = fields.Date("From To",help="Date only. no time for date compare with payslip")
	x_redeem_stage	= fields.Integer(string='Redeem Stage', compute="_redeem_stage")
	x_redeem_count	= fields.Integer(string='Redeem Count', compute="_redeem_count")
	x_balance_hrs	= fields.Float(string='Balance Hours', compute="_balance_hrs", digits=(10, 3))
	
	#@api.depends('x_redeem')
	def _redeem_stage(self):
		for record in self:
			if record.x_redeem=="part":
				_stage="1"
			elif record.x_redeem=="full":
				_stage="2"
			else:
				_stage="0"
			record.x_redeem_stage=_stage
			
	def _balance_hrs(self):
		for record in self:
			used_hrs=0.0
			sql="select sum(h.tot_hrs) from hr_payslip_leave as h where h.holiday_id='%s'" % (record.id)
			self.env.cr.execute(sql)
			rs = self.env.cr.fetchall()
			for row in rs:
				if row[0]:
					used_hrs+=float(row[0])
			record.x_balance_hrs = self.x_total_hrs - used_hrs
			
	def _redeem_count(self):
		for record in self:
			sql="select distinct h.payslip_id from hr_payslip_leave as h where h.holiday_id='%s'" % (record.id)
			self.env.cr.execute(sql)
			rs = self.env.cr.fetchall()
			record.x_redeem_count = len(rs)
	'''@api.model
	def create(self, vals):
		if vals.get('holiday_status_id'):
			_name=self.env['hr.holidays.status'].browse(vals.get('holiday_status_id')).name
			vals['name'] = _name
		record = super(DincelEmployeeHolidays, self.create(vals))
		return record'''
	#// YqBCk$6yEN keypay password	
	'''@api.multi
	def name_get(self):
		res = []
		for leave in self:
			if leave.holiday_status_id and self.date_to and self.date_from:
				#dt 		=  parser.parse(self.date_from)#datetime.strptime(self.date_to)
				dt 		=  parser.parse(self.env['account.account'].get_au_date(self.date_from))
				dt2 	=  parser.parse(self.date_to)
				dtpart 	=  "%s-%s/%s/%s" % (dt.day, dt2.day, dt2.month, dt2.year)
				res.append((leave.id, _("%s : %s") % (leave.holiday_status_id.name, dtpart)))
			
			else:
				res.append((leave.id, _("%s") % (leave.holiday_status_id.name)))
		return res'''
		
	@api.multi	
	def action_open_payslips(self):
		ids=[]
		
		ctx = self._context.copy()
		
		ctx.update({'default_employee_id':self.employee_id.id,})
		sql="select distinct h.payslip_id from hr_payslip_leave as h where h.holiday_id='%s'" % (self.id)
		self.env.cr.execute(sql)
		rs = self.env.cr.fetchall()
		for row in rs:
			ids.append(row[0])
		
		vals= {
			'name': _('Payslips'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.payslip',
			'domain':[('employee_id','=',self.employee_id.id), ('id','in',(ids))],
			#'views': [(view.id, 'form')],
			#'view_id': view.id,
			'target': 'current',
			#'res_id':self.id,
			'context': ctx,
		}
		#_logger.error("valsvalsvalsvals[%s]" % (vals))
		return vals
		 
		
	@api.onchange('date_from','date_to')
	def _onchange_dates(self):
		if self.date_from:
			self.x_date_from 	= self.env['account.account'].get_au_date(self.date_from)
		if self.date_to:
			self.x_date_to 	= self.env['account.account'].get_au_date(self.date_to)
		if self.x_date_from and self.x_date_to: 
			date_from 	= parser.parse(self.x_date_from)
			date_to 	= parser.parse(self.x_date_to)
			group_id 	= self.employee_id.x_group_id.id
			dt	=	date_from
			days=0
			leave_hrs=0.0
			while (dt <= date_to):
				name 	= "%s" %  (dt.strftime("%a"))
				roster_id 	= self.env['hr.employee.group.attendance'].get_roster(name, group_id)
				if roster_id:
					leave_hrs 	+= roster_id.hrs_leave or 0.0	
					days+=1
				
				dt	=	dt + timedelta(days=1) #next day loop...		
			#self.number_of_days_temp = (datetime.strptime(self.x_date_to, "%Y-%m-%d") - datetime.strptime(self.x_date_from, "%Y-%m-%d")).days + 1
			self.number_of_days_temp = days
			self.x_total_hrs=leave_hrs
			
	@api.onchange('number_of_days_temp')
	def _onchange_number_of_days(self):
		if self.number_of_days_temp and self.employee_id:
			#leave_hrs=7.6
			#if self.employee_id.x_group_id:
			#	#hrs_normal=self.employee_id.x_group_id.normal_hrs
			#	leave_hrs=self.employee_id.x_group_id.leave_hrs
			'''for item in self.employee_id.x_attendance_ids:
				if item.dayofweek=="1":#monday..for example
					hrs_normal=item.normal_pay
					break'''
					
			#vals={'x_total_hrs': round((leave_hrs*self.number_of_days_temp),2)	}
			vals={}
			return {'value':vals}