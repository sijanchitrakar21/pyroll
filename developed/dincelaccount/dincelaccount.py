#from odoo import models, fields, api
from odoo import api, fields, models, _
from datetime import datetime, timedelta
#import datetime as dtt
import pytz
import calendar
import time
from dateutil import parser
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
# class openacademy(models.Model):
#     _name = 'openacademy.openacademy'

#     name = fields.Char()

class DincelCompany(models.Model):
	_inherit = 'res.company'	
	x_contact_id = fields.Many2one('res.partner', string='Electronic Contact (ATO)') 
	x_declarer_id = fields.Many2one('res.partner', string='Payer Declarer (ATO)')
	x_branchcode = fields.Char("Branch Code")
	
class DincelAccount(models.Model):
	_inherit = 'account.account'		
	parent_id = fields.Many2one('account.account', 'Parent', ondelete='cascade', domain=[('type','=','view')])
	type = fields.Selection([
			('view', 'View'),
			('other', 'Regular'),
			('receivable', 'Receivable'),
			('payable', 'Payable'),
			('liquidity','Liquidity'),
			('consolidation', 'Consolidation'),
			('closed', 'Closed'),
		], 'Internal Type', help="The 'Internal Type' is used for features available on "\
			"different types of accounts: view can not have journal items, consolidation are accounts that "\
			"can have children accounts for multi-company consolidations, payable/receivable are for "\
			"partners accounts (for debit/credit computations), closed for depreciated accounts.")
	active = fields.Boolean("Active")	
	'''def local_to_utc(self,t):
		secs = time.mktime(t)
		return time.gmtime(secs)

	def utc_to_local(self,t):
		t=parser.parse(t)
		dt=t.timetuple()
		secs = calendar.timegm(dt)
		return time.localtime(secs)
	'''	
	def get_au_date(self,dttime=None):
		try:
			if dttime:
				dttime1= str(dttime)[:19] #no milli seconds 
			else:
				dttime1=str(datetime.now())
				dttime1= str(dttime1)[:19]
			_from_date 	= datetime.strptime(str(dttime1),"%Y-%m-%d %H:%M:%S")
			time_zone	= 'Australia/Sydney'
			tz 			= pytz.timezone(time_zone)
			tzoffset 	= tz.utcoffset(_from_date)
			
			dt2 	= str((_from_date + tzoffset).strftime("%Y-%m-%d"))
			
			#utc = pytz.utc
			#sydney = pytz.timezone('Australia/Sydney')
			#am_dt = sydney.localize(_from_date)
			#return am_dt.astimezone(utc).strftime("%Y-%m-%d")
		except:
			_logger.error("error in dincelaccount.get_au_date() dttime[%s]" % (dttime))
			dt2=str(dttime)
			pass	
		return dt2
		
	# dt	 dt2
	def test_method(self,tst):
		return tst
		
	def get_au_datetime(self, dttime=None):
		try:
			if dttime:
				dttime1= str(dttime)[:19]
			else:
				dttime1=str(datetime.now())
				dttime1= str(dttime1)[:19]
			_from_date 	= datetime.strptime(str(dttime1),"%Y-%m-%d %H:%M:%S")
			time_zone	= 'Australia/Sydney'
			tz 			= pytz.timezone(time_zone)
			tzoffset 	= tz.utcoffset(_from_date)
			
			dt2 	= str((_from_date + tzoffset).strftime("%Y-%m-%d %H:%M:%S"))
			dt2		= str(dt2)[:19]
			
			#utc = pytz.utc
			#sydney = pytz.timezone('Australia/Sydney')
			#am_dt = sydney.localize(_from_date)
			#return am_dt.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
		except:
			_logger.error("error in dincelaccount.get_au_datetime() dttime[%s]" % (dttime))
			dt2=str(dttime)
			pass
		return dt2
		
	def get_gmt_datetime(self, dttime=None):
		try:
			if dttime:
				dttime1= str(dttime)[:19]
			else:
				dttime1=str(datetime.now())
				dttime1= str(dttime1)[:19]
				
			_from_date 	= datetime.strptime(str(dttime1),"%Y-%m-%d %H:%M:%S")
			time_zone	= 'Australia/Sydney'
			tz 			= pytz.timezone(time_zone)
			
			aware_d = tz.localize(_from_date, is_dst=None)
			dt2		= aware_d.astimezone(pytz.utc)
			dt2		= str(dt2)[:19]
		except:
			_logger.error("error in dincelaccount.get_gmt_datetime() dttime[%s]" % (dttime))
			dt2=str(dttime)
			pass
		return dt2
		
		
class DincelAccountMoveLine(models.Model):
	_inherit = 'account.move.line'	
	x_period_id= fields.Many2one('account.period', string='Period')
	
class DincelBankAccount(models.Model):
	_inherit = 'res.bank'		
	x_bsb = fields.Char("BSB")
	x_account_no = fields.Char("Account Number")
	x_bank_userid= fields.Char("Bank UserID")
	x_owner_name= fields.Char("Owner/Remitter")
	
class DincelAccountMove(models.Model):
	_inherit = 'account.move'	
	x_coststate_id=fields.Many2one("res.country.state","Cost Centre")
	x_employee_id = fields.Many2one('hr.employee', string='Employee')
	x_period_id= fields.Many2one('account.period', string='Period')
	x_payslip_id= fields.Many2one('hr.payslip', string='Payslip')
	
class DincelAccountFiscalPeriod(models.Model):
	_inherit = 'account.period'	
	company_id = fields.Many2one('res.company', string='Company', required=True, index=True, default=lambda self: self.env.user.company_id, help="Company related to this period")
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
		
class DincelAccountFiscalYear(models.Model):
	_inherit='account.fiscalyear'
	@api.multi
	def close_fy(self):
		self.write({'state':'done'})
	@api.multi
	def open_fy(self):
		self.write({'state':'draft'})
	
class DincelAccountJournal(models.Model):
	_name = "dincelaccount.journal"
	_description = "Account Journal"
	journal_id 	=None
	move_id 	=None
	name		=None
	ref			=None
	company_id	=None
	coststate_id=None
	period_id	=None
	date		=None
	partner_id	=None
	invoice_id	=None
	narration	=None
	employee_id	=None 
	partner_lang=None
	payslip_id	=None
	
	ac_tax_account=None
	#ac_super_assets=None
	ac_super_liability=None
	
	clearing_account=None
	tot_credit=0.0
	tot_debit=0.0
	
	def _get_config_data(self):
		_config =self.env['dincelaccount.settings']
		items		= _config.search([], limit=1) 
		for _obj in items:
			#_logger.error("_get_config_data_get_config_data_id[%s]" % (_id))
			#_obj = _config.browse(_id[0])
			self.ac_tax_account		=_obj.tax_account_id
			#self.ac_super_assets	=_obj.super_assets_id
			self.ac_super_liability	=_obj.super_liability_id
			self.clearing_account	=_obj.payroll_clearing_code
		return True
		
	def get_journal_moveline(self,account_id, debit,credit, label):
		
		#obj_move_line = self.env['account.move.line']
		#state_line	  = "valid"
		quantity	  = 1
		self.tot_credit+=credit
		self.tot_debit+=debit
		vals1 = {
			'journal_id': self.journal_id,
			#'move_id': self.move_id,
			'account_id': account_id,
			'debit': debit,
			'credit': credit,
			#'ref': self.ref,
			'name': label,
			'company_id': self.company_id,
			#'state': state_line,
			'date': self.date,
			'quantity': quantity,
			'x_period_id': self.period_id,
		}
		if self.partner_id:
			vals1['partner_id']= self.partner_id	
		if self.coststate_id:
			vals1['x_coststate_id']= self.coststate_id			
		 
		return vals1
		
	def add_journal_moveline(self,account_id, debit,credit):
		
		obj_move_line = self.env['account.move.line']
		#state_line	  = "valid"
		quantity	  = 1

		vals1 = {
			'journal_id': self.journal_id,
			'move_id': self.move_id,
			'account_id': account_id,
			'debit': debit,
			'credit': credit,
			#'ref': self.ref,
			'name': self.name,
			'company_id': self.company_id,
			#'state': state_line,
			'date': self.date,
			'quantity': quantity,
			'x_period_id': self.period_id,
		}
		if self.partner_id:
			vals1['partner_id']= self.partner_id	
		if self.coststate_id:
			vals1['x_coststate_id']= self.coststate_id			
		#_logger.error("add_journal_movelinevals1[%s]" % (vals1))
		obj = obj_move_line.create(vals1)		
		if obj == None or obj == False:
			_logger.error("add_journal_moveline.move_id[%s]debit[%s]credit[%s]account_id[%s]" % (self.move_id, debit, credit, account_id))
			
		return obj
		
	def add_journal_move(self, lines):
		
		obj_move = self.env['account.move']
		state	 = "draft"
		vals={
			'journal_id': self.journal_id,
			'name': self.name,
			'ref': self.ref,
			'company_id': self.company_id,
			'state': state,
			'date': self.date,
			'x_period_id': self.period_id,
			'narration': self.narration,
			
		}
		if self.payslip_id:
			vals['x_payslip_id']= self.payslip_id		
		if lines:
			vals['line_ids']= lines	
		if self.employee_id:
			vals['x_employee_id']= self.employee_id		
		if self.partner_id:
			vals['partner_id']= self.partner_id		
		#ctx = dict(self._context, lang=self.partner_lang)
		#ctx['company_id'] = self.company_id
		
		#ctx_nolang = ctx.copy()
		#ctx_nolang.pop('lang', None)
		#move = obj_move.with_context(ctx_nolang).create(vals)
		dr=cr=0.0
		#_logger.error("start. could not add add_journal_move lines[%s]" % (lines))	
		
		for line in lines:
			a,b,c=list(line)
			#_logger.error("item...  [%s]%s%s" % (a,b,c))
			if c['debit']: 
				dr+=round(float(c['debit']),2)
			if c['credit']:	
				cr+=round(float(c['credit']),2)
		#_logger.error("adding_add_journal_move0000 dr[%s]cr[%s] lines[%s]vals[%s]" % (dr,cr,lines,vals))		
		if dr>0.0 and round((dr-cr),2)==0.0:
			move = obj_move.create(vals)
			if not move:
				_logger.error("could not add add_journal_move11111 dr[%s]cr[%s] lines[%s]vals[%s]" % (dr,cr,lines,vals))	
				raise UserError(_("Error in journal entry found.\nPlease contact administrator."))
			move.post()
			self.move_id=move.id
		else:
			_logger.error("unbalanced journal. could not add add_journal_move22222 dr[%s]cr[%s] lines[%s]" % (dr,cr,lines))	
			raise UserError(_("Unbalanced journal entry found dr[%s]cr[%s]. \nPlease contact administrator." % (dr, cr)))
		#_logger.error("add_journal_moveadd_journal_move[%s] added [%s] [%s]" % (vals,self.move_id,lines))	
		return self.move_id
		
		
	def payslip2journals(self, payslip_id):
		
		self._get_config_data()
		#self.partner_id	=1 #for testing only #todo...check later...
		#partner = self.env['res.partner'].browse(self.partner_id)	
		#self.partner_lang=partner.lang
		payslip 	= self.env['hr.payslip'].browse(payslip_id)	
		self.date 	= payslip.date 
		self.period_id = self.env['account.period'].finds(self.date)
		self.journal_id= self.env['account.journal'].search([('type', '=', 'general'),('code', '=', 'PAY')], limit=1).id	
		
		
		if self.period_id and self.journal_id:
			_txt = "%s %s - %s" % (payslip.employee_id.name, payslip.date_from, payslip.date_to )
			self.narration	= _txt 
			self.name		= payslip.name 
			self.ref		= payslip.number
			self.employee_id= payslip.employee_id.id 
			self.company_id = self.env.user.company_id.id
			self.payslip_id	= payslip_id
			 
			lines=[]
			 
			#addline=True
			#if addline:
			self.tot_credit=0.0
			self.tot_debit=0.0
			for line in payslip.x_summary_ids:
				if abs(line.tot_hrs) and line.sub_total and line.account_id:
					if line.sub_total>0.0:
						debit	=round(line.sub_total,2)
						credit	=0.0
					else:
						credit	=round(abs(line.sub_total),2)
						debit	=0.0
					 
					account_id=line.account_id.id 
					 
					newline=self.get_journal_moveline(account_id, debit, credit, line.name)
					#lines.append(newline)
					lines.append((0, 0, newline))
					 
				
			if self.ac_tax_account:
				account_id=self.ac_tax_account.id
				if payslip.x_tax_amt>0.0:
					debit	=0.0
					credit	=round(payslip.x_tax_amt,2)
				else:
					debit	=round(abs(payslip.x_tax_amt),2)
					credit	=0.0
					
				#net_balance-=payslip.x_tax_amt 
				
				newline=self.get_journal_moveline(account_id, debit, credit, self.ac_tax_account.name)
				lines.append((0, 0, newline))
			if payslip.x_super_amt:
				if payslip.employee_id.x_super_id:
					account_id=payslip.employee_id.x_super_id.id	#@self.ac_super_assets.id
					_name=payslip.employee_id.x_super_id.name
					
					if payslip.x_super_amt>0.0:
						debit	=round(payslip.x_super_amt, 2)
						credit	=0.0
					else:
						debit	=0.0
						credit	=round(abs(payslip.x_super_amt), 2)
						
					newline	=self.get_journal_moveline(account_id, debit, credit, _name) #self.ac_super_assets.name)
					lines.append((0, 0, newline))
					
					account_id	=self.ac_super_liability.id
					tmp			=debit
					debit		=credit
					credit		=tmp
						
					newline	=self.get_journal_moveline(account_id, debit, credit, self.ac_super_liability.name)
					lines.append((0, 0, newline))
					
			if self.clearing_account:
				net_balance1=self.tot_debit-self.tot_credit
				 
				net_balance=round(net_balance1,2)
				
				#_logger.error("add_journal_moveadd_net_balance1net_balance1 [%s][%s]" % (net_balance1,net_balance))	
				
				if net_balance>0.0:
					debit=0.0
					credit=net_balance#payslip.x_net_amt
				else:
					debit=abs(net_balance)
					credit=0.0
				account_id=self.clearing_account.id#payslip.x_clearing_account_id.id
				newline=self.get_journal_moveline(account_id, debit, credit, payslip.x_clearing_account_id.name)
				lines.append((0, 0, newline))
			else:
				raise UserError(_("Payroll settings missing for clearing account. \nPlease contact administrator."))
			#_logger.error("add_journal_moveadd_journal_lineslines [%s]" % (lines))		
			#_logger.error("payslip2journalspayslip2journals dr[%s] cr[%s]" % (self.tot_debit,self.tot_credit))	
			self.move_id	= self.add_journal_move(lines)
			return self.move_id
		return False 