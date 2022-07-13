# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from time import gmtime, strftime
import math
import logging
_logger = logging.getLogger(__name__)
class DincelPayrollScale(models.Model):
	_name = 'dincelpayroll.tax.scale'
	_description="Tax Scale"
	name = fields.Char('Name')
	description = fields.Char('Description')
	
class DincelPayrollScale(models.Model):
	_name = 'dincelpayroll.scale'
	_description="Tax Scale Table"
	name = fields.Char('Name')
	tax_scale_id = fields.Many2one('dincelpayroll.tax.scale', string='Tax Scale')
	scale = fields.Selection([
			('1', 'Scale 1'),
			('2', 'Scale 2'),
			('3', 'Scale 3'),
			('4', 'Scale 4'),
			('5', 'Scale 5'),
			('6', 'Scale 6'),], string='Scale')
	'''amount_from=fields.Float("Weekly Earning From")		
	amount_to=fields.Float("Weekly Earning To")	
	tax_rate=fields.Float("Tax Rate")
	coefficient_a=fields.Float("Coefficient a")		
	coefficient_b=fields.Float("Coefficient b")
	resident_type = fields.Selection([
			('1', 'Resident'),
			('2', 'Foreign Resident'),
			], string='Resident Type')'''
	date_start = fields.Date(string='Start date', required=True)
	date_end = fields.Date(string='End date', required=True)
	state = fields.Selection([
			('open', 'Open'),
			('closed', 'Closed'),
			], string='Status', default="open")
	scale_line_ids = fields.One2many('dincelpayroll.scale.line', 'scale_id', 'Scale Lines')
	tax_line_ids = fields.One2many('dincelpayroll.tax.line', 'scale_id', 'Tax Lines')
	fiscal_id = fields.Many2one('account.fiscalyear', string='Fiscal year')
	super_pc = fields.Float("Super %", digits=(4, 2), default="0")	
	notes = fields.Text('Notes')
	
	@api.onchange('fiscal_id')
	def onchange_fiscal_id(self):
		if self.fiscal_id:
			dt_frm=self.fiscal_id.date_start
			dt_to=self.fiscal_id.date_stop
			vals={'date_start':dt_frm,'date_end':dt_to}
			return {'value':vals}
		#return True
	
	def get_super_pc(self, tax_scale_id):
		super_pc = 0.0
		if tax_scale_id:
			sql ="""select a.super_pc from 
					dincelpayroll_scale a  
					where 
					a.tax_scale_id='%s' and 
					a.state='open'   """ % (tax_scale_id)
			self.env.cr.execute(sql) 
			rows = self.env.cr.dictfetchall()
			for row in rows:
				super_pc	=row['super_pc']
			
		return super_pc
	
	#source url <https://www.ato.gov.au/uploadedFiles/Content/MEI/downloads/Calculating-amounts-to-be-withheld-2018-19.pdf>
	#source <https://www.ato.gov.au/Rates/Schedule-1---Statement-of-formulas-for-calculating-amounts-to-be-withheld/>	
	def calculate_tax_amt_old(self, employee, week_earned_amt):
		a, b, tax, super_pc = 0.0, 0.0, 0.0, 0.0
		if employee.x_tax_scale_id:
			tax_scale_id	= employee.x_tax_scale_id.id 
			sql ="""select b.*,a.super_pc from 
					dincelpayroll_scale a,dincelpayroll_scale_line b 
					where 
					a.id=b.scale_id and 
					a.tax_scale_id='%s' and 
					a.state='open' and 
					%s between b.amount_from and b.amount_to """ % (tax_scale_id, week_earned_amt)
			self.env.cr.execute(sql) 
			rows = self.env.cr.dictfetchall()
			for row in rows:
				a	= row['coefficient_a']
				b	= row['coefficient_b']
				super_pc	=row['super_pc']
			tax	= a*(round(week_earned_amt + 0.50)) - b	#tax formula [y=ax-b] (ato.gov.au)
		return tax, super_pc
		
	def get_tax_amount_final(self, employee, payfreq, gross_amt, salary_annual):
		tax_amt, super_amt, super_pc = 0.0, 0.0,0.0
		gross_amt=abs(gross_amt)
		if employee.x_tax_scale_id:
			if payfreq=="week":
				factor=52.0
				week_earned_amt=gross_amt
				yearly_amt	= float(gross_amt)*factor
			elif payfreq=="fortnight":
				factor=26.0
				
				yearly_amt	= float(gross_amt)*factor
				
				week_earned_amt=float(gross_amt)/2.0
				week_earned_amt=math.floor(week_earned_amt)+0.99
			elif payfreq=="month":
				factor=12.0
				yearly_amt	= float(gross_amt)*factor
				week_earned_amt=float(yearly_amt)/12.0
			else:
				factor=1.0
				yearly_amt	= float(gross_amt)*factor
				week_earned_amt=float(yearly_amt)/52.0
			if salary_annual:
				yearly_amt=salary_annual
			tax_scale_id	= employee.x_tax_scale_id.id 
			sql ="""select b.*,a.super_pc from 
					dincelpayroll_scale a,dincelpayroll_scale_line b 
					where 
					a.id=b.scale_id and 
					a.tax_scale_id='%s' and 
					a.state='open' and 
					%s >= b.amount_from and %s < b.amount_to """ % (tax_scale_id, week_earned_amt, week_earned_amt)
			self.env.cr.execute(sql) 
			rows = self.env.cr.dictfetchall()
			for row in rows:
				a	= float(row['coefficient_a'])
				b	= float(row['coefficient_b'])
				super_pc	=float(row['super_pc'])
				tax_amt	= 	a*(week_earned_amt) - b
				tax_amt	=	round(tax_amt)
			#yearly_amt	= float(yearly_amt)
			#super_amt1=super_pc*0.01*yearly_amt
			#super_amt	= round(super_amt1,2)
			#_logger.error('get_tax_amount_finalget_tax_amount_final yearly_amt[ %s ]name[ %s ] super_amt1[ %s ]super_amt[ %s ]' %  (yearly_amt, employee.name, super_amt1,super_amt ))
			if payfreq=="fortnight":
				tax_amt=round(tax_amt*2.0)
				#super_amt=round(super_amt/26.0,2)
				
			elif payfreq=="month":
				tax_amt=round(tax_amt*52.0/12.0)
				#super_amt=round(super_amt/12.0,2)
			elif payfreq=="year":	
				tax_amt=round(tax_amt*52.0)
			else:#week
				tax_amt=round(tax_amt*1.0)
				#super_amt=round(super_amt/52.0,2)
			super_amt1=super_pc*0.01*gross_amt	
			super_amt	= round(super_amt1,2)	
			'''
			sql ="""select b.*,a.super_pc from 
					dincelpayroll_scale a,dincelpayroll_tax_line b 
					where 
					a.id=b.scale_id and 
					a.tax_scale_id='%s' and 
					a.state='open' and 
					%s between b.amount_from and b.amount_to """ % (tax_scale_id, yearly_amt)
			self.env.cr.execute(sql) 
			rows = self.env.cr.dictfetchall()
			for row in rows:
				amount_from	= float(row['amount_from'])
				amount_to	= float(row['amount_to'])
				offset_value= float(row['offset_value'])
				tax_rate	= float(row['tax_rate'])
				super_pc	= float(row['super_pc'])
				yearly_amt	= float(yearly_amt)
				super_amt	= super_pc*0.01*yearly_amt
				tax_offset	= (yearly_amt-amount_from)*tax_rate
				tax_amt		= offset_value+tax_offset
			
				tax_amt=tax_amt/factor
				super_amt=tax_amt/factor
				#elif payfreq=="year":
				#	week_amt=_amt/52.0
				#else:
				#	tax_amt=_amt
				'''	
		return tax_amt, super_amt, super_pc

		
class DincelPayrollTaxLine(models.Model):
	_name = 'dincelpayroll.tax.line'
	_description = "Payroll Tax Line"
	scale_id = fields.Many2one('dincelpayroll.scale', string='Payroll Scale',ondelete='cascade',)
	amount_from = fields.Float("Annual Earning From",digits=(16, 2))		
	amount_to = fields.Float("Annual Earning Less Than", digits=(16, 2))	
	tax_rate = fields.Float("Tax Per Dollar", digits=(6, 4))
	offset_value = fields.Float("Tax Offset", digits=(10, 2))
	notes = fields.Char("Notes")
	
	
	
class DincelPayrollScaleLine(models.Model):
	_name = 'dincelpayroll.scale.line'
	_description = "Tax Scale Line"
	scale_id = fields.Many2one('dincelpayroll.scale', string='Payroll Scale',ondelete='cascade',)
	amount_from = fields.Float("Weekly Earning From (inc)",digits=(16, 4))		
	amount_to = fields.Float("Weekly Earning Less Than (ex)", digits=(16, 4))	
	tax_rate = fields.Float("Tax Rate", digits=(6, 4))
	coefficient_a = fields.Float("Coefficient a", digits=(6, 4))	
	#tax_a = fields.Float("a",digits_compute= dp.get_precision('Payroll Rate'))			
	coefficient_b = fields.Float("Coefficient b", digits=(6, 4))
	resident_type = fields.Selection([
			('1', 'Resident'),
			('2', 'Foreign Resident'),
			], string='Resident Type')
			
			
 
class DincelPayrollFiscalyear(models.Model):
	_inherit = 'account.fiscalyear'	
	x_super = fields.Float('Super %', default=9.5, digits=(6, 2))	
	x_weeks = fields.Integer('# Weeks', default=52)	
	x_fortnights = fields.Integer('# Fortnights', default=26)	
	company_id = fields.Many2one('res.company', string='Company', required=True, index=True, default=lambda self: self.env.user.company_id, help="Company related to this period")
	x_holiday_ids = fields.One2many('dincelpayroll.holiday','fiscalyear_id', string='Holidays')
	x_extra_tax_ids = fields.One2many('dincelpayroll.extra.tax','fiscalyear_id', string='Extra Tax')
	_order = 'date_stop desc'
	
	def finds(self, dt=None, _company_id=None, exception=True):
		
		if not dt:
			dt=datetime.today()
		args = [('date_start', '<=' ,dt), ('date_stop', '>=', dt)]
		if _company_id:
			company_id = _company_id
		else:
			company_id = self.env.user.company_id.id
		args.append(('company_id', '=', company_id))
		item = self.search(args, limit=1)
		if not item:
			if exception:
				action = self.env.ref('account_fiscalyear.action_account_period')
				msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
				raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
			else:
				return []
		return item.id

class DincelPayrollHoliday(models.Model):
	_name = 'dincelpayroll.holiday'
	_description = "Holiday"
	name = fields.Char('Description')	
	fiscalyear_id = fields.Many2one('account.fiscalyear', string='Fiscal Year', ondelete='cascade',)
	date = fields.Date('Date')	
	state_id = fields.Many2one("res.country.state", string='State')
	state_ids = fields.Many2many('res.country.state', 'holiday_state_rel', 'holiday_id', 'state_id', 'States')
	category_id = fields.Many2one('hr.pay.category', string='Leave Category'	, domain=[('holiday_status_id','!=',False)])
	holiday_status_id = fields.Many2one("hr.holidays.status", string='Leave Type', default=lambda self: self._default_holiday_status_id())
	notes = fields.Char('Notes')	
	current_year = fields.Boolean('Current Year', default=True)	
	_order= "current_year desc, date"
	
	def _default_holiday_status_id(self):
		items = self.env['hr.holidays.status'].search([('x_code', '=', 'public')], limit=1) #dayofweek=0=monday 
		for item in items:
			return item.id
		return None

	@api.onchange('holiday_status_id')
	def _onchange_holiday_id(self):
		if self.holiday_status_id:
			vals={'category_id': self.holiday_status_id.x_category_id and self.holiday_status_id.x_category_id.id or None}
			return {'value':vals}
	
	@api.onchange('date')
	def _onchange_date(self):
		if self.date:
			fiscal_id 	= self.env['account.fiscalyear'].finds(self.date)
			vals={'fiscalyear_id': fiscal_id or None}
			return {'value':vals}
			
	'''
	@api.onchange('category_id')
	def _onchange_holiday_id(self):
		if self.category_id:
			vals={'name': self.category_id.name	}
			return {'value':vals}'''
			
class DincelPayrollExtraTax(models.Model):
	_name = 'dincelpayroll.extra.tax'
	_description = "Extra Tax"
	name = fields.Char('Description')	
	fiscalyear_id = fields.Many2one('account.fiscalyear', string='Fiscal Year',ondelete='cascade',)
	amount_from = fields.Float("Earning From",digits=(16, 4))		
	amount_to = fields.Float("Earning Less Than", digits=(16, 4))	
	amount_tax = fields.Float("Tax Amount", digits=(6, 4))
	payfrequency_id = fields.Many2one("hr.payroll.payfrequency", string='Pay Frequency')
	
class DincelPayrollTimesheet(models.Model):
	_inherit = 'account.analytic.line'			
	x_act_start = fields.Char('Actual Start',help="HH:MM")	
	x_act_stop = fields.Char('Actual End',help="HH:MM")	
	x_round_start = fields.Char('Rounded Start',help="HH:MM")	
	x_round_stop = fields.Char('Rounded End',help="HH:MM")	
	#x_breaks = fields.Char('Breaks',help="From-to text")
	#x_unpaid = fields.Float('Unpaid', digits=(6, 2),help="Hours with decimal")	
	#x_paid = fields.Float('Paid', digits=(6, 2),help="Hours with decimal")	
	#$x_special_pay = fields.Float('Special/Leave Pay', digits=(6, 2),help="Hours with decimal")	
	x_comments = fields.Char('Special Comments',help="Holiday pay etc")	
	x_batch_id = fields.Many2one('hr.timesheet.batch', string='Timesheet Import Batch',ondelete='cascade',)
	x_category_id = fields.Many2one('hr.pay.category', string='Pay Category' )
	#x_tot_hrs		= fields.Float(string='Total Hours', compute='_compute_total')
	x_break_unpaid	= fields.Float(string='Unpaid Break', default="0.0")
	x_break_paid	= fields.Float(string='Paid Break', default="0.0")
	x_hrs_normal	= fields.Float(string='Normal Hours', default="0.0")
	x_hrs_t15		= fields.Float(string='OT 1.5', default="0.0")
	x_hrs_t20		= fields.Float(string='OT 2.0', default="0.0")
	x_loading_noon	= fields.Float(string='Afternoon Shift Ldg @15%', default="0.0")
	x_loading_night	= fields.Float(string='Night Shift Ldg @30%', default="0.0")
	x_leave_annual= fields.Float(string='Annual Leave',default="0.0")
	x_leave_sick	= fields.Float(string='Sick Leave',default="0.0")
	x_leave_unpaid= fields.Float(string='Unpaid Leave',default="0.0")
	x_leave_part	= fields.Float(string='Part Day Leave',default="0.0")
	x_tot_hrs		= fields.Float(string='Total Hours', compute='_compute_total')
	
	@api.depends('x_break_unpaid', 'x_break_paid','x_hrs_normal','x_hrs_t15','x_hrs_t20','x_leave_annual','x_leave_sick','x_leave_unpaid','x_leave_part')
	def _compute_total(self):
		for record in self:
			tot_worked_hrs = record.x_break_paid + record.x_hrs_normal + record.x_hrs_t15 + record.x_hrs_t20 + record.x_leave_annual + record.x_leave_sick+ record.x_leave_unpaid + record.x_leave_part
			record.x_tot_hrs =tot_worked_hrs+record.x_break_unpaid
			
class DincelPayrollTimesheetBatch(models.Model):
	_name = 'hr.timesheet.batch'
	_inherit = ['mail.thread']	
	_description = "Timesheet Batch"		
	name = fields.Char('Name')
	date = fields.Date(string='Date')
	date_start = fields.Date(string='Date From')
	date_end = fields.Date(string='Date To')	
	employee_id = fields.Many2one('hr.employee', string='Employee')
	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done'),
			], string='Status', default="draft", track_visibility='onchange')
	#timesheet_ids = fields.One2many('account.analytic.line', 'x_batch_id', 'Timesheet Lines')	
	#timesheet_ids2 = fields.One2many('hr.employee.timesheet', 'batch_id', 'Timesheet Lines')	
	description= fields.Text('Notes')
	csv_dcs = fields.Boolean('DCS Excel ?', default=False)
	#_order = "date_start desc, id desc"
	_order = "id desc"
	
	@api.multi
	def action_import_wizard(self):
		#""" Skip this wizard line. Don't compute any thing, and simply redirect to the new step."""
		#if self.current_line_id:
		#	self.current_line_id.unlink()
		return {
			'name': _('Timesheet Import'),
			'res_model': 'hr.timesheet.import',
			#'res_id': self.id,
			'view_type': 'form',
			'view_mode': 'form',
			'type': 'ir.actions.act_window',#'type': 'ir.actions.act_window',
			'target': 'new'
		}
	
	@api.multi
	def action_confirm_timesheet(self):
		self.write({'state':'confirmed'})
	