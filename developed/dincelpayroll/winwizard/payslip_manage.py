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
from odoo.addons.dincelpayroll.models import dincelpayroll_vars 
import time
import base64
import io
#import dateparser
#import datetime
import logging
_logger = logging.getLogger(__name__)


class PayslipManage(models.TransientModel):
	_name = 'hr.payslip.manage'
	_description = 'Payslip Manage'
	items = fields.One2many('hr.payslip.manage.line','manage_id', string='Items')
	check_all = fields.Boolean("Check All", default=True)
	qty=fields.Integer("Qty test",default=lambda self: self._get_init_qty(),)
	check_pdf = fields.Boolean("Check for Pdf")
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	type  = fields.Selection(dincelpayroll_vars.PAYSLIP_MANAGE_OPTIONS, string='Action') 	
	
	def _get_init_qty(self):
		return 1
		
	@api.onchange('type')
	def _onchange_type(self):
		if self.type:
			
			return
	@api.onchange('qty')
	def _onchange_qty(self):
		context = dict(self._context or {})
		active_ids = context.get('active_ids', []) or []
		_items=[]
		for record in self.env['hr.payslip'].browse(active_ids):
			_items.append({'employee_id':record.employee_id.id, 
							'selected':True,
							'date':record.date,
							'number':record.number,
							'net_amt':record.x_net_amt,
							'payslip_id':record.id,
							})
		return {'value': {'items': _items}}	
		
	@api.onchange('check_all')
	def _onchange_check_all2(self):
		
		for line in self.items:	
			line['selected']= self.check_all
		return {'value': {'items': self.items}}
		
	def get_payslip_prevew_data(self, payslip, employee):
		value={}
		#employee=line.employee_id
		employee_id=employee.id
		
		lines, summary = self.payslip_get_lines(payslip)
		'''
		summary={'gross_amt':"${:,.2f}".format(round(payslip.x_gross_amt,2)),
				'tax_amt':"${:,.2f}".format(round(payslip.x_tax_amt,2)),
				'net_amt':"${:,.2f}".format(round(payslip.x_net_amt,2)),
				'super_amt':"${:,.2f}".format(round(payslip.x_super_amt,2)),
				'annual_leave':"{:,.2f}".format(round(payslip.x_annual_leave,2)),
				'sick_leave':"{:,.2f}".format(round(payslip.x_sick_leave,2)),
				'lsl_leave':"{:,.2f}".format(round(payslip.x_lsl_leave,2)),
				'lsl_enable':employee.x_lsl_leave,#@lpayslip.x_lsl_enable,
				} 
		lines	= []
		gross_payslip_amt=0.0
		for item in payslip.x_summary_ids:
			values 					= {}
			values['name'] 			= item.name
			values['type'] 			= "Wages"
			if item.category_id and item.category_id.calc4gross:
				gross_payslip_amt+= float(item.sub_total)
			if item.tot_hrs or item.ytd_total: 
				if item.tot_hrs:
					values['net_hrs'] 	= "{:,.2f}".format(round(item.net_hrs or 0.0,2))
					values['tot_hrs'] 	= "{:,.2f}".format(round(item.tot_hrs,2))
					values['pay_rate'] 	= "${:,.4f}".format(round(item.pay_rate,4))
					values['sub_total'] 	="${:,.2f}".format(round(item.sub_total,2))
				else:
					values['net_hrs'] 	= ""	
					values['pay_rate'] 	= ""	
					values['sub_total']	= ""	
					values['tot_hrs'] 	= ""	
				if item.ytd_total:	
					values['ytd_total'] 	= "${:,.2f}".format(round(item.ytd_total,2))# "${:,.4}".format(item.ytd_total)
				else:
					values['ytd_total'] 	= ""	
					
				lines.append(values)	
				
		summary['gross_payslip_amt']="${:,.2f}".format(round(gross_payslip_amt,2))
		'''
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
		#_logger.error("22222222pay_basis[%s] leave_rate[%s] other_rate[%s] rate_base[%s] salary_annual[%s ] " % (pay_basis, leave_rate, other_rate, rate_base, salary_annual))	
		super=""		
		for sline in employee.x_super_ids:
			super+="%s " % (sline.name)
		_line2="%s" % (employee.x_suburb)
		if employee.x_state_id and employee.x_state_id.code:
			_line2+=" %s" % (employee.x_state_id.code)
		if employee.x_postcode:
			_line2+=" %s" % (employee.x_postcode)
		_line3=""	
		
		#date = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_from = datetime.strptime(payslip.date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_to = datetime.strptime(payslip.date_to, "%Y-%m-%d").strftime("%d/%m/%Y")
		
		ytd_sick, ytd_annual, ytd_super, ytd_tax = self.env['hr.payslip'].get_values_ytd(payslip)	
		value= {'date': date,
			'date_from':date_from,
			'date_till':date_to,
			'job_position': job_position,
			'employee_id': employee_id,
			'employee': employee.name,
			'employeeno': employee.x_emp_number,
			'address_line1': employee.x_street,
			'address_line2': _line2,
			'address_line3': _line3,
			'payfrequency':payslip.x_payfrequency_id.name,
			'salary': salary,
			'lines': lines,
			'chequeno': payslip.x_chequeno,
			'super': super,
			'summary': summary,
			'ytd_sick': "{:,.2f}".format(round(ytd_sick,2)),
			'ytd_annual': "{:,.2f}".format(round(ytd_annual,2)),
			'ytd_super': "${:,.2f}".format(round(ytd_super,2)),
			'ytd_tax': "${:,.2f}".format(round(ytd_tax,2)),
		} 
		#_logger.error('get_payslip_prevew_data[ %s ]value[ %s ]' %  (date, value))	
		return 	value
		
	def payslip_get_lines(self, payslip):
		 
		
		summary={'gross_amt':"${:,.2f}".format(round(payslip.x_gross_amt,2)),
				'tax_amt':"${:,.2f}".format(round(payslip.x_tax_amt,2)),
				'net_amt':"${:,.2f}".format(round(payslip.x_net_amt,2)),
				'super_amt':"${:,.2f}".format(round(payslip.x_super_amt,2)),
				'annual_leave':"{:.2f}".format(round(payslip.x_annual_leave,2)),
				'sick_leave':"{:.2f}".format(round(payslip.x_sick_leave,2)),
				'lsl_leave':"{:.2f}".format(round(payslip.x_lsl_leave,2)),
				'lsl_enable':payslip.x_lsl_enable,
				#'gross_payslip_amt':"{:.2f}".format(round(payslip.x_gross_payslip_amt,2)),
				} 
		res	= []
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
					values['sub_total'] 	= "${:,.2f}".format(round(item.sub_total,4))#"${:,.4}".format(round(item.sub_total,4))
				else:
					values['tot_hrs'] 	= ""	
					values['pay_rate'] 	= ""	
					values['sub_total']	= ""	
					values['net_hrs']	= ""	
				if item.ytd_total:	
					values['ytd_total'] 	= "${:,.2f}".format(item.ytd_total)
				else:
					values['ytd_total'] 	= ""	
					
				res.append(values)	
			 
		summary['gross_payslip_amt']="${:,.2f}".format(round(gross_payslip_amt,2))	
		#_logger.error("payslip_get_linespayslip_get_lines[%s] summary[%s]"% (res, summary))
		return res, summary
		
		
	@api.multi
	def button_manage_continue(self):
		payslips=[]
		for line in self.items:
			if line.selected:
				if self.type=="print":	
					payslip=line.payslip_id
					employee=line.employee_id
					val=self.get_payslip_prevew_data(payslip, employee)
					payslips.append(val)
				else:
					payslips.append(line.payslip_id)
		if self.type=="payevent":
			return self.env['dincelpayroll.ato'].create_payevent_xml(payslips)
		elif self.type=="print":	
			data 			= {}
			model 			= 'report.employee.payroll'
			data['model'] 	= model
			data['form'] 	= {'payslips':payslips,'active_id':self.id}
			return self.env.ref('dincelpayroll.action_report_payslip_all').report_action(self, data=data, config=False)	
		elif self.type == "email":	
			return self.generate_emails(payslips)
		elif self.type=="aba":	
			return self.env['hr.payslip'].generate_aba_file(payslips)
		return True
	
	def generate_emails(self, payslips):
		return True
			
	@api.multi	
	def button_previw_payslips(self):
		payslips=[]
		#model 		= 'report.employee.payroll'
		#docs 		= self.env[model].browse(_active_id)
		for line in self.items:
			if line.selected:
				payslip=line.payslip_id
				employee=line.employee_id
				val=self.get_payslip_prevew_data(payslip, employee)
				payslips.append(val)
		
		
		data 			= {}
		#data['ids'] 	= self.ids
		#active_id 		= self.env.context.get('active_id')
		model 			= 'report.employee.payroll'#self.env.context.get('active_model')
		data['model'] 	= model#self.env.context.get('active_model', 'ir.ui.menu')
		#data['form'] 	= {'payslips':payslips,'active_id':self.id, 'time':time}
		data['form'] 	= {'payslips':payslips,'active_id':self.id}
		if self.check_pdf:
			'''report_name="report.dincelpayroll.report_payslip_all"
			report		= self.env.ref('dincelpayroll.action_report_payslip_all_pdf')
			txt 		= report.with_context(self.env.context).render_qweb_html(None, data=data)[0]
			txt 		= report.with_context(self.env.context).render_qweb_pdf(None, data=data)[0]
			txt1= io.BytesIO(txt)
			txt2=base64.encodestring(txt1.getvalue())
			#txt 		= self.env.ref('dincelpayroll.action_report_payslip_all_pdf').report_action(self, data=data, config=False)
			pdf = self.env['report'].sudo().get_pdf([self.id], report_name, data=data)
			#pdf_file = base64.encodestring(pdf)
			#pdf_file = base64.b64encode(txt),
			_filename="report_payslip_all.html"
			_rootpath  	= "/var/tmp/odoo/payslips"
			_path		= _rootpath + "/" + _filename
			with open(_rootpath + "/payslip_all.html", "w+") as _file:
				_file.write("%s" % txt) 
			with open(_rootpath + "/payslip_all1.html", "w+") as _file:
				_file.write("%s" % txt1) 
			with open(_rootpath + "/payslip_all2.html", "w+") as _file:
				_file.write("%s" % txt2) 	
			#abc=report._post_pdf({}, pdf_content=txt, None)#, 'pdf'	
			#_logger.error("action_report_payslip_all_pdf		["+str(abc)+"]")	'''
			
			return self.env.ref('dincelpayroll.action_report_payslip_all_pdf').report_action(self, data=data, config=False)	
		else:
			return self.env.ref('dincelpayroll.action_report_payslip_all').report_action(self, data=data, config=False)		
	
	@api.multi	
	def button_validate_payslips(self):
		#payslips=[]
		#model 		= 'report.employee.payroll'
		#docs 		= self.env[model].browse(_active_id)
		for line in self.items:
			if line.selected:
				payslip=line.payslip_id
				self.env['hr.payslip'].post_leave_journal(payslip)
				move_id=self.env['dincelaccount.journal'].payslip2journals(payslip.id)
				if move_id:
					payslip.write({'state':'done'})			
				#employee=line.employee_id
				#val=self.get_payslip_prevew_data(payslip, employee)
				#payslips.append(val)
				
	@api.multi			
	def button_generate_pdf_payslips(self):
		for line in self.items:
			if line.selected:
				payslip=line.payslip_id
				self.env['hr.payslip'].save_pdf_file_byobj(payslip)
				
	@api.multi			
	def button_generate_payevent(self):
		payslips=[]
		for line in self.items:
			if line.selected:
				payslips.append(line.payslip_id)
		self.env['dincelpayroll.ato'].create_payevent_xml(payslips)
		
		
	@api.multi			
	def button_reverse_payslips(self):
		ids=[]
		for line in self.items:
			if line.selected:
				payslip=self.reverse_payslip(line.payslip_id)	
				if payslip:
					ids.append(payslip.id)
					
					
		value = {
			'type': 'ir.actions.act_window',
			'name': _('Payslips'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.payslip',
			'domain':[('id','in',ids)],
			'context':{},#{'search_default_partner_id': partner_id},
			'view_id': False,#view_id,
		}

		return value
				
	def reverse_payslip(self, pprev):
		obj_payslip	= self.env['hr.payslip']
		obj_time	= self.env['hr.employee.timesheet']
		obj_leave	= self.env['hr.payslip.leave']
		payslip		= None
		employee	= pprev.employee_id
		employee_id	= employee.id
		vals = {'date': pprev.date,
				'employee_id': employee_id,
				'x_payfrequency_id': pprev.x_payfrequency_id.id,
				'date_from': pprev.date_from,
				'date_to': pprev.date_to,
				'x_is_timesheet':pprev.x_is_timesheet,
				'x_origin_id':pprev.id,
			}
		if employee.x_group_id:
			vals['x_group_id'] =	employee.x_group_id.id
		if pprev.x_fiscal_id:
			vals['x_fiscal_id'] =	pprev.x_fiscal_id.id
		
		if pprev.x_clearing_account_id:
			vals['x_clearing_account_id']	=	pprev.x_clearing_account_id.id
		
		items 		= obj_payslip.search([('employee_id','=',employee_id),('x_origin_id','=',pprev.id)])	
		if len(items) > 0:
			for item in items:
				item.write(vals)
				payslip = item
		else:
			_number			= self.env['ir.sequence'].next_by_code('payslip.reverse')
			vals['name']	= "%s %s - %s" % (_number, pprev.date_from, pprev.date_to)
			vals['number']	= _number
			payslip 		= self.env['hr.payslip'].create(vals)
			
		if payslip:
			#---------------------------------
			#timesheet------------------------
			#---------------------------------
			for item in pprev.x_timesheet_ids2:
				_vals={
					'employee_id': employee_id,
					'category_id': item.category_id.id,
					'hrs': float(item.hrs)*(-1.0),			#item.hrs, #making negative for reverse
					'hrs_net': float(item.hrs_net)*(-1.0),	#item.hrs_net, #making negative for reverse
					'xfactor': item.xfactor,
					'date': item.date,
					'name': item.name,
					'payslip_id': payslip.id,
					'reversed':True,
					}
				lineitems 	= obj_time.search([('reversed','=',True), ('employee_id','=',employee_id),('category_id','=',item.category_id.id),('date','=',item.date)])	
				if len(lineitems)>0:
					for item in lineitems:
						item.write(_vals)
				else:
					obj_time.create(_vals)
			#---------------------------------
			#leaves---------------------------
			#---------------------------------	
			for item in pprev.x_leave_ids:
				_vals={
					'employee_id': employee_id,
					'category_id': item.category_id.id,
					'tot_hrs': float(item.tot_hrs)*(-1.0), #making negative for reverse
					'date': item.date,
					'date_from':item.date_from,
					'date_to':item.date_to,
					'holiday_id': item.holiday_id.id,
					'payslip_id': payslip.id,
					'reversed':True,
					}
				lineitems 	= obj_leave.search([('reversed','=',True),('employee_id','=',employee_id),('category_id','=',item.category_id.id), ('date','=',item.date), ('holiday_id','=',item.holiday_id.id)])	
				if len(lineitems)>0:
					for item in lineitems:
						item.write(_vals)
				else:
					obj_leave.create(_vals)	 
			#---------------------------------------
			self.env['hr.payslip'].calculate_payslip(payslip)	
			pprev.write({'state':'reversed'})
		return payslip
		
#class ReportPayrollPagePayslip(models.AbstractModel):		
class ReportPayslipAllNew(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payslip_all'
	
	@api.model
	def get_report_values(self, docids, data=None):
	
		if not data.get('form'):
			raise UserError(_("Payslip report content is missing, this report cannot be printed."))
		_ids		=self.ids	
		_active_id	=data['form'].get('active_id')
		payslips	=data['form'].get('payslips')
		
		model 		= 'report.employee.payroll'
		docs 		= self.env[model].browse(_active_id)
		
		val	= {
			'doc_ids':	 _ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'payslips': payslips,#str(date_till).strftime("%d/%m/%Y"),
			}
		return val
		
		
class PayslipManageLine(models.TransientModel):
	_name = 'hr.payslip.manage.line'
	_description = 'Manage line'
	manage_id = fields.Many2one('hr.payslip.manage', string='Manage')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	payslip_id = fields.Many2one('hr.payslip', string='Payslip')
	selected = fields.Boolean("Select", default=True) 
	net_amt = fields.Float("Net amount")	
	number = fields.Char('Reference')
	date = fields.Date('Pay Date')