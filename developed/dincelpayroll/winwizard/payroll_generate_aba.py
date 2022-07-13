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
from odoo.exceptions import RedirectWarning, UserError, ValidationError
#import dateparser
#import datetime
import logging
_logger = logging.getLogger(__name__)


class PayrollGenerateAba(models.TransientModel):
	_name = 'hr.payroll.aba'
	_description = 'Payroll generate aba'
	employee_lines = fields.One2many('hr.payroll.aba.line','payroll_aba_id', string='Employees')
	check_all = fields.Boolean("Check All", default=True)
	qty=fields.Integer("Qty test",default=lambda self: self._get_init_qty(),)
	
	def _get_init_qty(self):
		return 1
		
	@api.onchange('qty')
	def _onchange_qty(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids', []) or []
		_lines=[]
		for record in self.env['hr.payslip'].browse(active_ids):
			_lines.append({'employee_id':record.employee_id.id, 
							'selected':True,
							'date':record.date,
							'number':record.number,
							'net_amt':record.x_net_amt,
							'payslip_id':record.id,
							})
		return {'value': {'employee_lines': _lines}}	
		
	@api.onchange('check_all')
	def _onchange_check_all2(self):
		 
		employee_lines = self.employee_lines
		for line in employee_lines:	
			line['selected']= self.check_all
		return {'value': {'employee_lines': employee_lines}}
		
	 
	@api.multi
	def button_payslip_aba_create_new(self):
		''' EXAMPLE -----------------------------
		bsb="123-564"
		accountNumber="112233449"
		bankName="CBA"
		userName="DINCEL const"
		remitter="DINCEL"
		directEntryUserId="123456"
		description="DINCEL BDFD"
		-----------------------------------------
			accountName="CBA"
			bsb="111-444"
			amount="12500"
			indicator=""
			
			reference="RefText11"
			remitter="Shukra Rai"
			taxWithholding=""
			-----------------------------------------
		'''
		 
		transactions=[]
		_aba =self.env['dincelaccount.aba']  
		_config	=self.env['dincelaccount.settings'].load_default()
		if _config.pay_bank_id:
			
			_bank			= _config.pay_bank_id
			
			#d_date			= datetime.today()
			
			d_description	= 'PAYMENT DATA'
			d_bsb			= _bank.x_bsb
			d_accountNumber = _bank.x_account_no
			d_bankName		= _bank.bic # SWIFT code  or  Bank Identifier Code (BIC).
			d_remitter		= _bank.x_owner_name
			d_userName		= _bank.x_owner_name
			d_directEntryUserId	= _bank.x_bank_userid
			
			user_id	=self.env.uid
			
			date=datetime.now()
			name=""		
			name		=self.env['ir.sequence'].next_by_code('payslip.aba')
			value = {
				'name':name,
				'date':date,
				'bank_bsb':d_bsb,
				'bank_acno':d_accountNumber,
				'bank_name':d_bankName,
				'bank_username':d_userName,
				'remitter':d_remitter,
				'apca_userid':d_directEntryUserId,
				'description':d_description,
				'user_id':user_id
				}
			aba = self.env['dincelpayroll.aba'].create(value)
			if aba:
				aba_id=aba.id
				for line in self.employee_lines:
					if line.selected:
						emp = line.employee_id 
						payslip=line.payslip_id
						
						payslip_id=payslip.id
						employee_id=emp.id
						
						amount_total	=round(payslip.x_net_amt,2)	 
						
						if emp.x_pay_text and len(emp.x_pay_text)>0:
							reference	= emp.x_pay_text#line.ref_aba
						else:
							reference	= "DINCEL CONS SYSTEM"
							
						pay_date=payslip.date
						
						paid_net=0.0
						sql="select * from hr_employee_bank where employee_id='%s' and type='part'" % (emp.id)
						self.env.cr.execute(sql)	
						rs2 = self.env.cr.dictfetchall()
						if len(rs2)>0:
							for row2 in rs2:
								part_type=row2['part_type']
								part_salary_amt=row2['part_salary_amt']
								pc_amt = round(float(part_salary_amt),2)
								if part_type=="amt": #or pc 
									if pc_amt>amount_total:
										amt_net=amount_total
									else:
										amt_net=pc_amt
								else:#pc
									amt_net=pc_amt*amount_total*0.01
								
								paid_net+=amt_net	
								bsb				=row2['bsb']
								accountNumber	=row2['account_number']
								bankName		=row2['bank_name']
								remitter		=row2['name']
								userName		=row2['name']	
								
								vals = {
									'bank_acno':accountNumber,
									'bank_name':bankName,
									'bank_bsb':bsb,
									'amount':amt_net,
									'bank_acname':userName,
									'reference':reference,
									'remitter':remitter,
									'employee_id':employee_id,
									'aba_id':aba_id,
									'payslip_id':payslip_id,
									}
								self.env['dincelpayroll.aba.line'].create(vals)	
									
							if paid_net<amount_total:
								sql="select * from hr_employee_bank where employee_id='%s' and type='balance'" % (emp.id)
								self.env.cr.execute(sql)	
								rs3 = self.env.cr.dictfetchall()
								for row3 in rs3:
									amt_net=amount_total-paid_net
									bsb				=row3['bsb']
									accountNumber	=row3['account_number']
									bankName		=row3['bank_name']
									remitter		=row3['name']
									userName		=row3['name']
									vals = {
										'bank_acno':accountNumber,
										'bank_name':bankName,
										'bank_bsb':bsb,
										'amount':amt_net,
										'bank_acname':userName,
										'reference':reference,
										'remitter':remitter,
										'employee_id':employee_id,
										'aba_id':aba_id,
										'payslip_id':payslip_id,
										}
									self.env['dincelpayroll.aba.line'].create(vals)	
						else:
							sql="select * from hr_employee_bank where employee_id='%s'" % (emp.id)
							self.env.cr.execute(sql)	
							rs1 = self.env.cr.dictfetchall()
							for row1 in rs1:
								amt_net=amount_total
								bsb				=row1['bsb']
								accountNumber	=row1['account_number']
								bankName		=row1['bank_name']
								remitter		=row1['name']
								userName		=row1['name']
			
								amount_cents	=int(amt_net*100)
								paid_net+=amt_net	
								
								
								vals = {
									'bank_acno':accountNumber,
									'bank_name':bankName,
									'bank_bsb':bsb,
									'amount':amt_net,
									'bank_acname':userName,
									'reference':reference,
									'remitter':remitter,
									'employee_id':employee_id,
									'aba_id':aba_id,
									'payslip_id':payslip_id,
									}
									
								self.env['dincelpayroll.aba.line'].create(vals)
				ids=[aba.id]			
				value = {
					'type': 'ir.actions.act_window',
					'name': _('Payroll Payslip ABA'),
					'view_type': 'form',
					'view_mode': 'tree,form',
					'res_model': 'dincelpayroll.aba',
					'domain':[('id','in',ids)],
					'context':{},#{'search_default_partner_id': partner_id},
					'view_id': False,#view_id,
				}

				return value
				
	@api.multi
	def button_payslip_aba_create(self):
		transactions=[]
		_aba =self.env['dincelaccount.aba']  
		_config	=self.env['dincelaccount.settings'].load_default()
		if _config.pay_bank_id:
			pay_date=None
			_bank=_config.pay_bank_id
			d_description	= 'PAYMENT DATA'
			d_bsb			=_bank.x_bsb
			d_accountNumber =_bank.x_account_no
			d_bankName		=_bank.bic
			d_remitter		=_bank.x_owner_name
			d_userName		=_bank.x_owner_name
			d_directEntryUserId=_bank.x_bank_userid
			for line in self.employee_lines:
				if line.selected:
					emp = line.employee_id 
					payslip=line.payslip_id
					amount_total	=round(payslip.x_net_amt,2)	 
					amount_cents	=int(amount_total*100)	#to CENTS
					#partner_id	= line.supplier_id.id
					if emp.x_pay_text and len(emp.x_pay_text)>0:
						reference	= emp.x_pay_text#line.ref_aba
					else:
						reference	= "DINCEL CONS SYSTEM"
						
					if not pay_date:
						pay_date=payslip.date
					paid_net=0.0
					for bank in emp.x_bank_ids: 
						bsb				=bank.bsb
						accountNumber	=bank.account_number
						bankName		=bank.bank_name
						remitter		=bank.name
						userName		=bank.name
						if userName: 
							indicator		=""
							taxWithholding	=""
							transactionCode	=_aba.PAYROLL_PAYMENT
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
						else:
							raise UserError(_("Error found, incomplete bank setup for employee %s." % (emp.name)))
			_aba._init(d_bsb, d_accountNumber, d_bankName, d_userName, d_remitter, d_directEntryUserId, d_description)
			_aba.payDate=pay_date
			_str=_aba.generate_aba(transactions)
			if _aba.errorMessage!="":
				raise UserError(_(_aba.errorMessage))
			fname="pay_slip.aba"
			save_path=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/aba/"	
			#save_path="/var/tmp/odoo/aba/"
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
				'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (self.id, save_path, fname),
				'context': {}}			
	 
class PayrollEmployeeAbaLine(models.TransientModel):
	_name = 'hr.payroll.aba.line'
	_description = 'Employee aba line'
	payroll_aba_id = fields.Many2one('hr.payroll.aba', string='Aba')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	payslip_id = fields.Many2one('hr.payslip', string='Payslip')
	selected = fields.Boolean("Select", default=True) 
	net_amt = fields.Float("Net amount")	
	number = fields.Char('Reference')
	date = fields.Date('Pay Date')