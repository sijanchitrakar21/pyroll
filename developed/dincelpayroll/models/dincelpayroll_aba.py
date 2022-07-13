# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from time import gmtime, strftime
import math
import logging
_logger = logging.getLogger(__name__)
 

class DincelPayrollAba(models.Model):
	_name = 'dincelpayroll.aba'
	_description="Payroll Aba"
	name 	= fields.Char('Name')
	date 	= fields.Datetime('Date')
	bank_bsb 	= fields.Char('BSB')
	bank_acno 	= fields.Char('Account Number')
	bank_name	= fields.Char("Bank")
	bank_username= fields.Char("User Name")
	remitter	= fields.Char("Remitter")
	apca_userid	= fields.Char("APCA Id") # digit uid by APCA
	description	= fields.Char("Description")
	line_ids 	= fields.One2many('dincelpayroll.aba.line', 'aba_id', 'Aba Lines')
	user_id		= fields.Many2one('res.users','Created By')
	downloaded  = fields.Boolean("Downloaded", default=False)
	#total_amount = fields.Float("Total Amount", digits=(10, 2))
	
	@api.multi
	def button_download_aba_file(self):
		transactions=[]
		_aba =self.env['dincelaccount.aba']  
		 
		pay_date=None
		
		d_description	=self.description#@ 'PAYMENT DATA'
		d_bsb			=self.bank_bsb
		d_accountNumber =self.bank_acno
		d_bankName		=self.bank_name
		d_remitter		=self.remitter
		d_userName		=self.bank_username
		d_directEntryUserId=self.apca_userid
		pay_date		=self.date
		
		for line in self.line_ids:
				 
			#emp = line.employee_id 
			#payslip=line.payslip_id
			#amount_total	=round(payslip.x_net_amt,2)	 
			#amount_cents	=int(amount_total*100)	#to CENTS
			'''
			if emp.x_pay_text and len(emp.x_pay_text)>0:
				reference	= emp.x_pay_text#line.ref_aba
			else:
				reference	= "DINCEL CONS SYSTEM"
			'''	
			#if not pay_date:
			#	pay_date=payslip.date
			paid_net=0.0
			amt_net=line.amount
			amount_cents	=int(float(amt_net)*100)	#to CENTS
			bsb				=line.bank_bsb
			accountNumber	=line.bank_acno
			bankName		=line.bank_name
			remitter		=line.remitter
			userName		=line.bank_acname
			reference		=line.reference
			indicator		=""
			taxWithholding	=""
			transactionCode	=_aba.PAYROLL_PAYMENT
			vals = {
				'accountName':userName,
				'accountNumber':accountNumber,
				'bsb':bsb,
				'amount':amount_cents,
				'indicator':indicator,
				'transactionCode':transactionCode,
				'reference':reference,
				'remitter':remitter, #receiver name
				'taxWithholding':taxWithholding,
				}
			#_logger.info("button_download_aba_file negative amount found in transaction...vals[%s]" % (vals))	
			if float(amt_net)> 0:
				transactions.append(vals)
			else:
				_logger.info("button_download_aba_file negative amount found in transaction...vals[%s]" % (vals))
		_aba._init(d_bsb, d_accountNumber, d_bankName, d_userName, d_remitter, d_directEntryUserId, d_description)
		_aba.payDate=pay_date
		_str=_aba.generate_aba(transactions)
		if _aba.errorMessage!="":
			raise UserError(_(_aba.errorMessage))
		fname="ABA_%s.aba" % (self.name)
		save_path=self.env['dincelaccount.settings'].get_odoo_tmp_folder() + "/aba/"	
		#save_path="/var/tmp/odoo/aba/"
		temp_path=save_path+fname
		
		
		f=open(temp_path,'w')
		f.write(_str)
		f.close()
		
		self.write({'downloaded':True})
		#sql="update dincelpayroll_aba set aba_downloaded='t' where id='%s' " % (self.id)
		#cr.execute(sql)
		
		return {
			'name': 'Aba File',
			'res_model': 'ir.actions.act_url',
			'type' : 'ir.actions.act_url',
			'url': '/web/binary/download_file?model=dincelaccount.aba&field=datas&id=%s&path=%s&filename=%s' % (self.id,save_path,fname),
			'context': {}}	
				
class DincelPayrollAbaLine(models.Model):
	_name = 'dincelpayroll.aba.line'
	_description = "Payroll Aba Line"
	aba_id 		= fields.Many2one('dincelpayroll.aba', string='Payroll Aba',ondelete='cascade',)
	employee_id = fields.Many2one('hr.employee', string='Employee')	
	payslip_id 	=  fields.Many2one('hr.payslip', string='Payslip')	
	amount 		= fields.Float("Amount", digits=(10, 2))
	bank_bsb 	= fields.Char("BSB")
	bank_acno 	= fields.Char("Account Number")
	bank_acname	= fields.Char("Account Name")
	bank_name	= fields.Char("Bank")
	remitter	= fields.Char("Remitter")
	reference	= fields.Char("Reference")
	