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


class PayrollPayslipQueue(models.TransientModel):
	_name = 'hr.payslip.queue'
	_description = 'payslip queue'
	employee_lines = fields.One2many('hr.payslip.queue.line','payslip_que_id', string='Employees')
	check_all = fields.Boolean("Check All", default=True)
	qty=fields.Integer("Qty test",default=lambda self: self._get_init_qty(),)
	type = fields.Char("Type")
	
	def _get_init_qty(self):
		return 1
		
	@api.onchange('qty')
	def _onchange_qty(self):
		context = dict(self._context or {})
		_lines=[]
		type=False
		if self.type:
			type=True
			if self.type=="email":
				ids = self.env['hr.payslip'].search([('x_payslip_deli','in',['email','emailprint']),('x_emailed','=',False)])
				for line in ids:
					_lines.append({'employee_id':line.employee_id.id, 
							'selected':True,
							'date':line.date,
							'number':line.number,
							'net_amt':line.x_net_amt,
							'payslip_id':line.id,
							})
			elif self.type=="print":
				ids = self.env['hr.payslip'].search([('x_payslip_deli','in',['print','emailprint']),('x_printed','=',False)])
				for line in ids:
					_lines.append({'employee_id':line.employee_id.id, 
							'selected':True,
							'date':line.date,
							'number':line.number,
							'net_amt':line.x_net_amt,
							'payslip_id':line.id,
							})
		_logger.error("_onchange_qty_onchange_qty [%s]" % (self.type))
		if not type:		
			active_ids = context.get('active_ids', []) or []
			
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
	def button_payslip_que_create(self):
		
		ids=""
		for line in self.employee_lines:
			if line.selected:
				#emp = line.employee_id 
				ids += "'%s'," % (line.payslip_id.id)
				 
		if ids !="":
			ids=ids[:-1]
			sql="update hr_payslip set x_email_que='t' where id in (%s)" % (ids)
			_logger.error('button_payslip_que_createbutton_payslip_que_create[ %s ][ %s ]' %  (ids, sql))				
			self.env.cr.execute(sql)	
					 
	 
class PayrollPayslipQueueLine(models.TransientModel):
	_name = 'hr.payslip.queue.line'
	_description = 'Payslip Queue line'
	payslip_que_id = fields.Many2one('hr.payslip.queue', string='Queue')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	payslip_id = fields.Many2one('hr.payslip', string='Payslip')
	selected = fields.Boolean("Select", default=True) 
	net_amt = fields.Float("Net amount")	
	number = fields.Char('Reference')
	date = fields.Date('Pay Date')