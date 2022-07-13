# -*- coding: utf-8 -*-
#https://www.slideshare.net/TaiebKristou/odoo-icon-smart-buttons
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import logging
import base64
import csv
from odoo.addons.dincelpayroll.models import dincelpayroll_vars 
#from io import StringIO
#from datetime import date, datetime, timedelta
#import datetime as dt
from datetime import date
from datetime import datetime
from datetime import timedelta
import datetime
#from datetime import date
#from datetime import datetime
#import datetime
import dateutil
from dateutil import parser
#import pandas
import xlrd
import os
from odoo.tools.config import config
_logger = logging.getLogger(__name__)

class employee_import:
	#emp_id=0
	def __init__(self, emp_id):
		self.emp_id = emp_id
		self.timesheet_arr=[]
		
		
class PayrollGenerate(models.TransientModel):
	_name = 'hr.payroll.generate'
	_description = 'Payroll generate'

	individual = fields.Boolean("Individual")  #, default=False
	group_id = fields.Many2one('hr.employee.group', string='Employee Group')	
	paydate = fields.Date('Pay Date')
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	employee_lines = fields.One2many('hr.employee.line','payroll_id', string='Employees')
	employee_id = fields.Many2one('hr.employee', string='Employee')#, domain=[('x_payslip_create_type','in',['manual'])])
	employee_ids = fields.Many2many('hr.employee', 'payroll_generate_employee_rel', 'generate_id', 'employee_id', string='Employees')
	check_all = fields.Boolean("Check All", default=True)
	timesheet_file = fields.Binary('Timesheet File')
	is_timesheet = fields.Boolean('Timesheet File?', default=True)
	upload_new = fields.Boolean('Upload New', default=False)
	qty=fields.Integer("Qty test",default=lambda self: self._get_init_qty(),)
	payslip_create_type  = fields.Selection(dincelpayroll_vars.PAYSLIP_CREATE_OPTIONS, string='Payslip Creation') 		
	ts_imort_type  = fields.Selection(dincelpayroll_vars.TS_IMPORT_TYPE_OPTIONS, string='TS File Type')
	ts_import_only = fields.Boolean("Timesheet Import Only", default=False)
	is_termination = fields.Boolean("Termination Pay", default=False) 
	import_lines = fields.One2many('hr.timesheet.import.line','payroll_id', string='Imports')
	check_all_ts = fields.Boolean("Check All", default=True)
	notes	= fields.Char("Notes")
	
	def _get_init_qty(self):
		#_logger.error("_onchange_qty_onchange_qty000 [%s]" % (11))
		return 1
		
	@api.onchange('qty')
	def _onchange_qty(self):
		context 	= dict(self._context or {})
		active_ids 	= context.get('active_ids', []) or []
		_lines		= []
		#groups		= self.env['hr.employee.group'].search([('is_timesheet', '=',False)])
		
		#config 		= self.env['dincelpayroll.config'].get_config()
		config 		= self.env['dincelaccount.settings'].get_config()
		value		= {}
		today 		= datetime.date.today()
		
		value['date_to']=today
		value['paydate']=today
		if config.payfrequency_id:
			value['payfrequency_id']=config.payfrequency_id.id
		#emps=""
		#for grp in groups:
		#empids=self.env['hr.employee'].search([('x_group_id', '=',grp.id)], order='x_last_name')
		sequence=1
		if self.payslip_create_type:
			empids=self.env['hr.employee'].search([('x_payslip_create_type', '=', self.payslip_create_type)], order='x_last_name')
			for emp in empids:
				#employee_ids=[emp.id]
				#_lines.append({'employee_ids':employee_ids, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type})
				_lines.append({'employee_id':emp.id, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type,'sequence':sequence})
				sequence+=1
		else:	
			empids=self.env['hr.employee'].search([('x_payslip_create_type', '=','autopay')], order='x_last_name')
			for emp in empids:
				
				#if emp.x_payslip_create_type:
					'''
					add=True
					
					if emp.x_payslip_create_type not in ['autopay','timesheet','manual']: #'manual' on individual
						add=False
					else:
						if emp.x_date_stop:#terminated then do it manually
							add=False
				
					if self.payslip_create_type != emp.x_payslip_create_type:
						add=False
					if add:	'''
					#emps+="[%s]" % (emp.name)
					_lines.append({'employee_id':emp.id, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type,'sequence':sequence})
					sequence+=1
					#employee_ids=[emp.id]
					#_lines.append({'employee_ids':employee_ids, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type})
				
		value['employee_lines']=	_lines
		value['notes']=	self.env['dincelaccount.settings'].get_scan_ts_file() 
		#_logger.error("_onchange_qty_onchangempsemps[%s]" % (emps))
		return {'value': value}
		
	@api.onchange('payslip_create_type')
	def _onchange_create_type(self):
		_lines=[]
		if self.payslip_create_type:
			empids=self.env['hr.employee'].search([('x_payslip_create_type', '=', self.payslip_create_type)])
			for emp in empids:
				#if not emp.x_date_stop:#terminated then do it manually
				#	_lines.append({'employee_id':emp.id, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type})
				if emp.x_payslip_create_type:
					#if emp.x_emp_status in ["full","part"]: #full time / part time only [no casual/other]
					add = True
					#if emp.x_payslip_enable == False:
					if emp.x_payslip_create_type not in ['autopay','timesheet','manual']: #'manual' on individual
						add = False
					else:
						if emp.x_date_stop:#terminated then do it manually
							add = False
					
					if self.payslip_create_type != emp.x_payslip_create_type:
						add = False
					if add:	
						#employee_ids=[emp.id]
						_lines.append({'employee_id':emp.id, 'selected':True, 'payslip_create_type':emp.x_payslip_create_type})
		#_logger.error('_onchange_create_type values _lines[ %s ] ' % (_lines))
		#return {'value': {'employee_lines': _lines}}
	'''
	@api.multi
	def get_todate(self, code, dt):
		dt2=dt
		if dt:
			if code=="week":
				dt2
			elif code=="fortnight":
			elif code=="month":
		return dt2'''
		
	@api.onchange('check_all_ts')
	def _onchange_check_all_ts(self):
		#for line in self.import_lines:
		import_lines = self.import_lines
		for line in import_lines:	
			line['selected']= self.check_all_ts
		return {'value': {'import_lines': import_lines}}
		
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
		
	@api.onchange('date_from')
	def _onchange_date_from(self):
		if self.payfrequency_id and self.date_from:
			code=self.payfrequency_id.code 
			_reverse=False
			dt=self.env['hr.payslip.run'].calculate_end_date(code, self.date_from, _reverse)	
			values = {
				'date_to': dt,
			}
			if self.upload_new==False and self.payslip_create_type=="timesheet":
				values['import_lines']=self.list_ts_import_if()
			return {'value':values} 
			
	@api.onchange('payfrequency_id')
	def _onchange_payfrequency(self):
		if self.payfrequency_id and self.date_from:
			code=self.payfrequency_id.code 
			_reverse=False
			dt=self.env['hr.payslip.run'].calculate_end_date(code, self.date_from, _reverse)	
			values = {
				'date_to': dt,
			}
			if self.upload_new==False and self.payslip_create_type=="timesheet":
				values['import_lines']=self.list_ts_import_if()
			return {'value':values} 
			
	@api.onchange('date_to')
	def _onchange_date_to(self):
		
		if self.payfrequency_id and self.date_to:
			code=self.payfrequency_id.code 
			_reverse=True
			dt=self.env['hr.payslip.run'].calculate_end_date(code, self.date_to, _reverse)	
			values = {
				'date_from': dt,
			}
			if self.upload_new==False and self.payslip_create_type=="timesheet":
				values['import_lines']=self.list_ts_import_if()
			return {'value':values} 
			
	@api.onchange('paydate')
	def _onchange_paydate(self):
		#if self.paydate:
		#	values = {
		#		'date_to': self.paydate,
		#	}
		#	return {'value':values} 
		return {'value':{}} 
		
	
	@api.onchange('individual')
	def _onchange_individual(self):
		if self.individual:
			self.check_all=False
			
	@api.onchange('group_id')
	def _onchange_group(self):
		ret=False
		_lines=[]
		if self.group_id:
			if self.group_id.code=="ALL":
				ids1 = self.env['hr.employee'].search([('x_current', '=', True),('active', '=', True)])
			else:
				ids1 = self.env['hr.employee'].search([('x_current', '=', True),('x_group_id', '=', self.group_id.id),('active', '=', True)])
				if self.group_id.code == "individual":
					ret=True
			for emp in ids1:
				_lines.append({'employee_id':emp.id, 'selected':True,})
			
		values = {
			'employee_lines': _lines,
			#'individual': ret,
			'check_all': True,
		}
		#_logger.error('_onchange_individual_onchange_individual values[ %s ] _lines[ %s ]',self.group_id, _lines)
		#return {'value':values} 
		
	def get_emp_item(self, emparr, emp_id):
		
		for item in emparr:
			if item['emp_id']==emp_id:
				return item 
		#emp = employee_import(emp_id)
		emp={'emp_id':emp_id, 'timesheet_arr':{}}
		emparr.append(emp)
		return emp, emparr
		
	def list_ts_import_if(self):	
		
		lines	= []
		args	= [('date_from', '=', self.date_from),('date_to', '=', self.date_to)]
		#_logger.error('list_ts_import_iflist_ts_import_if valuesargs[ %s ]', args)
		ids1 	= self.env['hr.timesheet.import.copy'].search(args)
		for line in ids1:
			_vals2 = {
				'employee_id':line.employee_id.id,
				'import_id':line.id,
				'import_name':line.name,
				'selected':True,
				}
			lines.append(_vals2)
		if len(self.import_lines) > 0:
			self.import_lines = [(5,)]
		
		return lines	
		
	def get_rows_timesheet_file(self, path1, ts_app, delimiter="comma"):
		rows= []
		if ts_app=="peoplekey":
			c_empid		=0
			c_date		=1 
			c_units		=3
			c_factor	=4
			c_codespecial=5
			c_paytype	=6
			c_payspecial=7
			if delimiter=="comma":
				with open(path1) as f:
					data 	= csv.reader(f)#csv.reader(f, delimiter="\t") #comma by default
					#d 		= list(reader)
					count1	=0
					xfactor	=1
					rowindex=-1
					for item in data:
						rowindex+=1
						#if rowindex==0:#skip header column
						#	continue
						hrs			=item[c_units]
						date		=item[c_date]
						emp_number	=item[c_empid]
						codespecial	=item[c_codespecial]
						payspecial	=item[c_payspecial]
						xfactor		=item[c_factor]
						paytype		=item[c_paytype]
						#, 'codespecial':codespecial, 'payspecial':payspecial
						hrs=float(hrs)
						if hrs==0.0 and payspecial:
							hrs=payspecial
						row={'rowindex':rowindex, 'hrs':hrs,'date':date,'paytype':paytype, 'emp_number':emp_number, 'xfactor':xfactor}
						rows.append(row)
		else:
			#myob payslip
			#delimiter	 is tab by default
			c_lname		=0
			c_fname		=1 
			c_paytype	=2 
			c_job		=3 
			c_date		=7
			c_units		=8 
			c_empid		=9
			with open(path1) as f:
				reader 	= csv.reader(f, delimiter="\t")
				data 		= list(reader)
				count1	=0
				xfactor	=1
				rowindex=-1
				for item in data:
					rowindex+=1
					if rowindex==0:#skip header column
						continue
					hrs		=item[c_units]
					date	=item[c_date]
					number	=item[c_empid]
					paytype	=item[c_paytype]
					lname	=item[c_lname]
					fname	=item[c_fname]
					row={'rowindex':rowindex,'hrs':hrs,'date':date,'paytype':paytype, 'emp_number':emp_number, 'xfactor':xfactor}
					rows.append(row)
		return rows
		
	def import_payslip_timesheet(self, path1, 	ts_app):
		
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		project 	= self.env['project.project'].search([('id','>',0)], limit=1)
		emp_arr		= []
		timesheet_arr	= []
		ids	= []
		project_id	= project.id
		account_id	= project.analytic_account_id.id
		user_id		= self.env.user.id
		company_id	= self.env.user.company_id.id
		obj_time	= self.env['hr.employee.timesheet']
		today 		= datetime.date.today()
		obj_import	= self.env['hr.timesheet.import']
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		_batch		= "%s-%s" % (date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"))
		_config		= self.env['dincelaccount.settings'].load_default()
		
		import_log	= self.env['hr.timesheet.import.log']
		obj_payslip	= self.env['hr.payslip']
		dt_import 	= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		impname 	= self.env['account.account'].get_au_datetime(dt_import)#.strftime("%Y-%m-%d %H:%M:%S")
		
		#dt_import#datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		period_id 	= self.env['account.period'].finds(paydate)
		fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
		rows = self.get_rows_timesheet_file(path1, 	ts_app) 
		for row in rows:
			hrs			= row['hrs']
			date		= row['date']
			number		= row['emp_number']
			paytype		= row['paytype']
			rowindex	= row['rowindex']
			
			employee_id, skip_ts_import, payslip_enable = obj_import.get_emp_bynumber(number)
			#{'category_id':category_id, 'pc_amt':pc_amt, 'amt_type':amt_type, 'xfactor': xfactor, 'factor_type': factor_type}
			#category_id, pc_amt, amt_type = obj_import.get_paycategory(paytype)
			paycat 		= obj_import.get_paycategory(paytype)
			category_id	= paycat['category_id']
			pc_amt		= paycat['pc_amt']
			amt_type	= paycat['amt_type']
			xfactor		= paycat['xfactor']
			factor_type	= paycat['factor_type']
			#xfactor	=1
			#dt=parser.parse(date)
			
			if hrs and employee_id and date:
				if skip_ts_import:
					_logger.error('timesheet.import.log001 skip_ts_import date [ %s ]  row[ %s ] number[%s]' % (date, rowindex, number))
					#_logger.error('timesheet.import.log001 skip_ts_import date [ %s ]  name[ %s ] paytype[%s]' % (date, fname + " " + lname, paytype))
				else:	
					try:
						hrs_net	= hrs
						if amt_type:
							#@xfactor=self.env['hr.pay.category'].get_xfactor(amt_type, pc_amt)
							#if amt_type=="pc":
							#	xfactor=float(pc_amt)*0.01
							hrs_net = float(hrs)*float(xfactor)
							#xfactor=1
							#elif amt_type=="times":
							#	xfactor=pc_amt
							#elif amt_type=="zero":
							#	xfactor=0	
						_logger.error('import_log.save_update_logsave_update_log [ %s ]  factor[ %s ]_type[ %s ]' % (category_id, xfactor, factor_type))
						import_log.save_update_log(employee_id, category_id, date, hrs, hrs_net, xfactor, factor_type, dt_import)
						if employee_id not in emp_arr:
							emp_arr.append(employee_id)
					except:
						_logger.error('timesheet.import.log err date [ %s ]  name[ %s ]' % (date,fname + " " + lname))
						pass		
			else:
				#if date:
				try:
					comments=""
					if not employee_id:
						comments+="[NO_ACTIVE_EMP_FOUND] "
					if not hrs:
						comments+="[HRS_MISSING] "
					if not date:
						comments+="[DATE_MISSING] "	
					#dt=parser.parse(date)
					vals11={'date':date,
					'name':impname,
					'empnumber':number,
					'paytype':paytype,
					'hrs':hrs,
					'row':rowindex,
					'comments':comments,
					}
						
					self.env['hr.log.record'].create(vals11)
				except:
					_logger.error('timesheet.import.debug err date [ %s ]  name[ %s ]' % (date,fname + " " + lname))
					pass
							
						
		count1=0
		
		for employee_id in emp_arr:	
			#if count1>0:
			#	continue
			#str1+="-------------- \n"
			payslip=None
			count1+=1	
			
			employee	= self.env['hr.employee'].browse(employee_id)
			vals = {'date': paydate,
					'employee_id': employee_id,
					'x_payfrequency_id': self.payfrequency_id.id,
					'date_from': self.date_from,
					'date_to': self.date_to,
					'x_batch':_batch,
					'x_is_timesheet':True,
					#'x_group_id':self.group_id.id,
				}
			if employee.x_group_id:
				vals['x_group_id']=employee.x_group_id.id
			if fiscal_id:
				vals['x_fiscal_id']=fiscal_id
			
			if _config:
				vals['x_clearing_account_id']=_config.payroll_clearing_code.id
			
			#------------------------------------------------------------------------------	
			#if "576"!=str(employee_id):	#for testing only...
			#	continue
			items 		= obj_payslip.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
			if len(items)>0:
				#raise UserError(_("Timesheet/s for the date range exists or have been imported already for the employee [%s] " %  (employee.name)))
				#continue
				for item in items:
					item.write(vals)
					payslip=item
				#payslip = self.env['hr.payslip'].create(vals)
				_first_time=False
			else:
				_first_time=True
				_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
				chequeno=_number.replace("SLIP/","")
				vals['name']=_number#"%s %s - %s" % (_number, self.date_from, self.date_to)
				vals['number']=_number
				vals['x_chequeno']=chequeno
				payslip = self.env['hr.payslip'].create(vals)
			if payslip:
				dt	=	date_from
				while (dt <= date_to):
					
					name 	= "%s" %  (dt.strftime("%a"))
					foundlines=import_log.get_timesheet_bydate_log(employee_id, dt)
					
					if len(foundlines)>0:
						
						for line in foundlines:
							_vals={
								'employee_id':line.employee_id.id,
								'category_id':line.category_id.id,
								'hrs':line.hrs,
								'hrs_net':line.hrs_net,
								'xfactor':line.xfactor,
								'date':line.date,
								'name': name,
								'payslip_id': payslip.id,
								'reversed':False,
								}
							lineitems 	= obj_time.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',line.category_id.id),('date','=',line.date)])	
							if len(lineitems)>0:
								for item in lineitems:
									item.write(_vals)
							else:
								obj_time.create(_vals)
					else:
						if _first_time: #just to make blank for the days not available in timesheet file...so that re-upload will not create duplicate entry (blank ones)
							_blank = {
								'name': name,
								'date': dt,
								'payslip_id': payslip.id,
								'hrs': 0,
								'hrs_net': 0,
								'employee_id': employee_id,
								}
							
							obj_time.create(_blank)
						
					dt	=	dt + timedelta(days=1) #next day loop...
					
				#------------------------------------------------------------------------------
				self.env['hr.payslip'].calculate_payslip(payslip)	
				ids.append(payslip.id)
				
		return ids
		
	def import_timesheet2payslip_myob(self, path1):
		c_lname		=0
		c_fname		=1 
		c_paytype	=2 
		c_job		=3 
		c_date		=7
		c_units		=8 
		c_empid		=9
		
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		project 	= self.env['project.project'].search([('id','>',0)], limit=1)
		emp_arr		= []
		timesheet_arr	= []
		ids	= []
		project_id	= project.id
		account_id	= project.analytic_account_id.id
		user_id		= self.env.user.id
		company_id	= self.env.user.company_id.id
		obj_time	= self.env['hr.employee.timesheet']
		today 		= datetime.date.today()
		obj_import	= self.env['hr.timesheet.import']
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		_batch		= "%s-%s" % (date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"))
		_config		= self.env['dincelaccount.settings'].load_default()
		
		import_log	= self.env['hr.timesheet.import.log']
		obj_payslip	= self.env['hr.payslip']
		dt_import 	= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		impname 	= self.env['account.account'].get_au_datetime(dt_import)#.strftime("%Y-%m-%d %H:%M:%S")
		
		#dt_import#datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		period_id 	= self.env['account.period'].finds(paydate)
		fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
			
		#paydate		=self.paydate
		with open(path1) as f:
			reader 	= csv.reader(f, delimiter="\t")
			d 		= list(reader)
			count1	=0
			xfactor	=1
			index=-1
			for item in d:
				index+=1
				if index==0:#skip header column
					continue
				hrs		=item[c_units]
				date	=item[c_date]
				number	=item[c_empid]
				paytype	=item[c_paytype]
				lname	=item[c_lname]
				fname	=item[c_fname]
				
				employee_id, skip_ts_import,payslip_enable = obj_import.get_emp_bynumber(number)
				#category_id, pc_amt, amt_type = obj_import.get_paycategory(paytype)
				#xfactor	=1
				paycat 		= obj_import.get_paycategory(paytype)
				category_id	= paycat['category_id']
				pc_amt		= paycat['pc_amt']
				amt_type	= paycat['amt_type']
				xfactor		= paycat['xfactor']
				factor_type	= paycat['factor_type']
				#dt=parser.parse(date)
				
				if hrs and employee_id and date:
					if skip_ts_import:
						_logger.error('timesheet.import.log001 skip_ts_import date [ %s ]  name[ %s ] paytype[%s]' % (date, fname + " " + lname, paytype))
					else:	
						try:
							hrs_net=hrs
							if amt_type:
								#xfactor=self.env['hr.pay.category'].get_xfactor(amt_type,pc_amt)
								#if amt_type=="pc":
								#	xfactor=float(pc_amt)*0.01
								hrs_net = float(hrs)*float(xfactor)
									#xfactor=1
								#elif amt_type=="times":
								#	xfactor=pc_amt
								#elif amt_type=="zero":
								#	xfactor=0	
							import_log.save_update_log(employee_id, category_id, date, hrs, hrs_net, xfactor, factor_type, dt_import)
							
							if employee_id not in emp_arr:
								emp_arr.append(employee_id)
						except:
							_logger.error('timesheet.import.log err date [ %s ]  name[ %s ]' % (date,fname + " " + lname))
							pass		
				else:
					#if date:
					try:
						comments=""
						if not employee_id:
							comments+="[NO_ACTIVE_EMP_FOUND] "
						if not hrs:
							comments+="[HRS_MISSING] "
						if not date:
							comments+="[DATE_MISSING] "	
						#dt=parser.parse(date)
						vals11={'date':date,
						'name':impname,
						'empnumber':number,
						'paytype':paytype,
						'hrs':hrs,
						'fname':fname,
						'lname':lname,
						'comments':comments,
						}
							
						self.env['hr.log.record'].create(vals11)
					except:
						_logger.error('timesheet.import.debug err date [ %s ]  name[ %s ]' % (date,fname + " " + lname))
						pass
							
						
		count1=0
		
		for employee_id in emp_arr:	
			#if count1>0:
			#	continue
			#str1+="-------------- \n"
			payslip=None
			count1+=1	
			
			employee	= self.env['hr.employee'].browse(employee_id)
			vals = {'date': paydate,
					'employee_id': employee_id,
					'x_payfrequency_id': self.payfrequency_id.id,
					'date_from': self.date_from,
					'date_to': self.date_to,
					'x_batch':_batch,
					'x_is_timesheet':True,
					#'x_group_id':self.group_id.id,
				}
			if employee.x_group_id:
				vals['x_group_id']=employee.x_group_id.id
			if fiscal_id:
				vals['x_fiscal_id']=fiscal_id
			
			if _config:
				vals['x_clearing_account_id']=_config.payroll_clearing_code.id
			
			#------------------------------------------------------------------------------	
			#if "576"!=str(employee_id):	#for testing only...
			#	continue
			items 		= obj_payslip.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
			if len(items)>0:
				#raise UserError(_("Timesheet/s for the date range exists or have been imported already for the employee [%s] " %  (employee.name)))
				#continue
				for item in items:
					item.write(vals)
					payslip=item
				#payslip = self.env['hr.payslip'].create(vals)
				_first_time=False
			else:
				_first_time=True
				_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
				chequeno=_number.replace("SLIP/","")
				vals['name']=_number#"%s %s - %s" % (_number, self.date_from, self.date_to)
				vals['number']=_number
				vals['x_chequeno']=chequeno
				payslip = self.env['hr.payslip'].create(vals)
			if payslip:
				dt	=	date_from
				while (dt <= date_to):
					
					name 	= "%s" %  (dt.strftime("%a"))
					foundlines=import_log.get_timesheet_bydate_log(employee_id, dt)
					
					if len(foundlines)>0:
						
						for line in foundlines:
							_vals={
								'employee_id':line.employee_id.id,
								'category_id':line.category_id.id,
								'hrs':line.hrs,
								'hrs_net':line.hrs_net,
								'xfactor':line.xfactor,
								'date':line.date,
								'name': name,
								'payslip_id': payslip.id,
								'reversed':False,
								}
							lineitems 	= obj_time.search([('reversed','=',False),('employee_id','=',employee_id),('category_id','=',line.category_id.id),('date','=',line.date)])	
							if len(lineitems)>0:
								for item in lineitems:
									item.write(_vals)
							else:
								obj_time.create(_vals)
					else:
						if _first_time: #just to make blank for the days not available in timesheet file...so that re-upload will not create duplicate entry (blank ones)
							_blank = {
								'name': name,
								'date': dt,
								'payslip_id': payslip.id,
								'hrs': 0,
								'hrs_net': 0,
								'employee_id': employee_id,
								}
							
							obj_time.create(_blank)
						
					dt	=	dt + timedelta(days=1) #next day loop...
					
				#------------------------------------------------------------------------------
				self.env['hr.payslip'].calculate_payslip(payslip)	
				ids.append(payslip.id)
				
		return ids
		
	def get_emp_timeshseet_bydt(self, timesheet_arr, emp_id, dt):
		
		lines=[]
		
		for line in timesheet_arr:
			date=parser.parse(line['date'])
			delta = date - dt
			
			if delta.days==0 and str(emp_id)==str(line['employee_id']):
				lines.append(line)
				
		return lines
		
	def import_timesheet2payslip(self, path1, 	ts_app):
		'''c_lname	=0
		c_fname	=1 
		c_paytype=2 
		c_job	=3 
		c_date	=7
		c_units	=8 
		c_empid	=9'''
		#user_id=1
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		project 	= self.env['project.project'].search([('id','>',0)], limit=1)
		emp_arr		= []
		line_arr	= []
		project_id	= project.id
		account_id	= project.analytic_account_id.id
		user_id		= self.env.user.id
		company_id	= self.env.user.company_id.id
		obj_time	= self.env['hr.employee.timesheet']
		today 		= datetime.date.today()
		obj_import	= self.env['hr.timesheet.import']
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		
		_batch		= "%s-%s" % (date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"))
		
		_config		= self.env['dincelaccount.settings'].load_default()
		
		period_id 	= self.env['account.period'].finds(paydate)
		fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
		rows = self.get_rows_timesheet_file(path1, 	ts_app) 
		for row in rows:
			hrs		=row['hrs']
			date	=row['date']
			number	=row['emp_number']
			paytype	=row['paytype']
			rowindex	=row['rowindex']	
			'''#paydate		=self.paydate
			with open(path1) as f:
				reader 	= csv.reader(f, delimiter="\t")
				d 		= list(reader)
				count1	= 0
				xfactor	= 1
				for item in d:
					hrs		=item[c_units]
					date	=item[c_date]
					number	=item[c_empid]
					paytype	=item[c_paytype]'''
			employee_id,skip_ts_import,payslip_enable = obj_import.get_emp_bynumber(number)
			#category_id, pc_amt, amt_type=obj_import.get_paycategory(paytype)
			#xfactor	=1
			paycat 		= obj_import.get_paycategory(paytype)
			category_id	= paycat['category_id']
			pc_amt		= paycat['pc_amt']
			amt_type	= paycat['amt_type']
			xfactor		= paycat['xfactor']
			factor_type	= paycat['factor_type']
			#dt=parser.parse(date)
			
			if hrs and employee_id and date:
				if skip_ts_import:
					_logger.error('timesheet.import.log002 skip_ts_import date [ %s ]  number[ %s ] paytype[%s]' % (date, number, paytype))
				else:
					if employee_id not in emp_arr:
						emp_arr.append(employee_id)
					#now2 = "%s" %  (date)
					dt=dateutil.parser.parse(str(date))
					name = "%s" %  (dt.strftime("%a"))
					sql="select id from hr_employee_timesheet where employee_id='%s' and date='%s' and category_id='%s'" % (employee_id, date, category_id)	 
					self._cr.execute(sql)
					rows1 = self._cr.fetchall()
					if len(rows1)>0:
						recordid	= rows1[0][0]
						date_exists = obj_time.browse(recordid)
					else:
						_vals2 = {
							'name': name,
							'date': date,
							#'dayofweek': dt.weekday(),
							'qty': hrs,
							'employee_id': employee_id,
							'category_id': category_id,
							}
						#if amt_type:
						#	xfactor=self.env['hr.pay.category'].get_xfactor(amt_type,pc_amt)
						#	'''if amt_type=="pc":
						#		xfactor=float(pc_amt)*0.01
						#	elif amt_type=="times":
						#		xfactor=pc_amt
						#	elif amt_type=="zero":
						#		xfactor=0'''
						_vals2['xfactor']= xfactor
						#_logger.error('obj_timeobj_time _vals2[ %s ] ' % (_vals2))	
						line = obj_time.create(_vals2)
						line_arr.append(line)
							
			if len(line_arr) > 0:			
				for employee_id in emp_arr:
					now2 		= "%s" %  (date)
					_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
					chequeno=_number.replace("SLIP/","")
					employee	= self.env['hr.employee'].browse(employee_id)
					vals = {'date': paydate,
							'employee_id': employee_id,
							'x_payfrequency_id': self.payfrequency_id.id,
							'name':_number,#"%s %s - %s" % (_number, self.date_from, self.date_to),
							'date_from': self.date_from,
							'date_to': self.date_to,
							'x_batch':_batch,
							'number':_number,
							'x_chequeno':chequeno,
							#'x_group_id':self.group_id.id,
						}
					if employee.x_group_id:
						vals['x_group_id']=employee.x_group_id.id
					if fiscal_id:
						vals['x_fiscal_id']=fiscal_id
					#clearing_code = config.get("payroll_clearing_code")		
					#if clearing_code:
					#account = self.env['dincelaccount.settings'].search([], limit=1)
					#	_logger.error('button_payslip_createbutton_payslip_create clearing_code[ %s ][ %s ]',clearing_code, account)
					#if account and account.payroll_clearing_code:
					#	vals['x_clearing_account_id']=account.payroll_clearing_code.id
					#else:	
					if _config:
						vals['x_clearing_account_id']=_config.payroll_clearing_code.id
						
					payslip = self.env['hr.payslip'].create(vals)
					for line in line_arr:
						if line.employee_id.id==employee_id:
							sql="update hr_employee_timesheet set payslip_id='%s' where id='%s'" % (payslip.id, line.id)	 
							self._cr.execute(sql) 	
					if payslip:
						self.env['hr.payslip'].calculate_payslip(payslip)
		return True
		
	@api.multi
	def button_wiz_payslip_create(self):
		var1		=""
		str1		=""
		count1		=0
		payslip		=None
		ids			=[]
		ts_app=self.env['dincelaccount.settings'].get_timesheet_app()
		if self.ts_import_only:
			if not self.timesheet_file:
				#------------------------------------------------------------------------------------------------
				#import from TA.date 
				#------------------------------------------------------------------------------------------------
				#import from ta.dat in case latest file /in/out
				self.env['hr.timesheet.scan'].import_scan_ts(ts_app)
				return self.create_timesheet_from_ts_scan()
				#------------------------------------------------------------------------------------------------
				#raise UserError(_("Warning! no file to upload. Please select a file and try again."))
			else:
				return self.import_timesheet_copy(ts_app)
		else:
			if self.payslip_create_type == "timesheet":
				if self.upload_new:
					if not self.timesheet_file:
						raise UserError(_("Warning! no file to upload. Please select a file and try again."))
					path1 	 =  os.path.normpath("/var/log/odoo")
					dt		 =  datetime.datetime.today().strftime("%Y-%m-%d")
					path1	+= "/timesheet%s.txt" % (dt)
					#if self.timesheet_file:
					path1	+= ""
					str1	=base64.b64decode(self.timesheet_file)
					f=open(path1,'wb') #write-binary 
					f.write(str1)
					f.close()	
					#return self.import_timesheet2payslip(path1, ts_app)
					#if ts_app=="peoplekey":
					#	ids = self.import_timesheet2payslip_peoplekey(path1)
					#else:
					#	ids = self.import_timesheet2payslip_myob(path1)
					ids = self.import_payslip_timesheet(path1, ts_app)
				else:
					ids = self.create_payslip_frm_ts()
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
			else:
				paydate		= self.paydate
				date_from	= self.date_from
				date_to		= self.date_to
				date_to		= parser.parse(date_to)
				date_from	= parser.parse(date_from)
				_batch		= "%s-%s" % (date_from.strftime("%Y%m%d"), date_to.strftime("%Y%m%d"))
				#_number	=_batch
				
				obj_time	= self.env['hr.employee.timesheet']
				period_id 	= self.env['account.period'].finds(paydate)
				fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
				
				if self.individual and self.employee_id:
					#dt = date_from
					_config	=self.env['dincelaccount.settings'].load_default()
					_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
					chequeno=_number.replace("SLIP/","")
					vals = {#'x_date': paydate,
							'date': paydate,
							'employee_id': self.employee_id.id,
							'x_payfrequency_id': self.payfrequency_id.id,
							'name':_number,#"%s %s - %s" % (_number, self.date_from, self.date_to),
							'date_from': self.date_from,
							'date_to': self.date_to,
							'x_batch':_batch,
							'number':_number,
							'x_is_timesheet':False,
							'x_chequeno':chequeno,
							#'x_group_id':self.group_id.id,
						}
					if self.employee_id.x_group_id:
						vals['x_group_id']=self.employee_id.x_group_id.id
					if fiscal_id:
						vals['x_fiscal_id']=fiscal_id
					#clearing_code = config.get("payroll_clearing_code")		
					#if clearing_code:
					#account = self.env['dincelaccount.settings'].search([], limit=1)
					#	_logger.error('button_payslip_createbutton_payslip_create clearing_code[ %s ][ %s ]',clearing_code, account)
					#if account and account.payroll_clearing_code:
					#	vals['x_clearing_account_id']=account.payroll_clearing_code.id
					#else:	
					if _config:
						vals['x_clearing_account_id']=_config.payroll_clearing_code.id
					if self.payslip_create_type=="terminate":	
						vals['x_termination_pay']=True
						
					payslip = self.env['hr.payslip'].create(vals)
					
					self._create_timesheet(payslip,  self.employee_id, date_from, date_to)
					
					count1+=1
							
					if payslip:
						#self.env['hr.payslip'].init_summarytable(payslip.id)
						self.env['hr.payslip'].calculate_payslip(payslip)	
						#self.env['hr.payslip'].calculate_summary(payslip.id)
						ids.append(payslip.id)
				else:
					for row in self.employee_lines:
						 
						if row.selected: 
							_number		= self.env['ir.sequence'].next_by_code('payslip.ref')
							chequeno=_number.replace("SLIP/","")
							vals = {'date': paydate,
									'employee_id': row.employee_id.id,
									'x_payfrequency_id': self.payfrequency_id.id,
									'name':_number,#"%s %s - %s" % (_number, self.date_from, self.date_to),
									'date_from': self.date_from,
									'date_to': self.date_to,
									'x_batch':_batch,
									'number':_number,
									'x_chequeno':chequeno,
									'x_is_timesheet':False,
									#'x_group_id':self.group_id.id,
								}
							if fiscal_id:
								vals['x_fiscal_id']=fiscal_id	
							if row.employee_id.x_group_id:
								vals['x_group_id']=row.employee_id.x_group_id.id			
							payslip = self.env['hr.payslip'].create(vals)
							self._create_timesheet(payslip,  row.employee_id, date_from , date_to)
							count1+=1
									
							if payslip:
								#self.env['hr.payslip'].init_summarytable(payslip.id)
								self.env['hr.payslip'].calculate_payslip(payslip)	
								#self.env['hr.payslip'].calculate_summary(payslip.id)
								ids.append(payslip.id)
				if count1>0:
					value = {
						'type': 'ir.actions.act_window',
						'name': _('Payslips'),
						'view_type': 'form',
						'view_mode': 'tree,form',
						'res_model': 'hr.payslip',
						'domain':[('id','in',ids)],#'domain':[('number','=',_number)],
						'context':{},#{'search_default_partner_id': partner_id},
						'view_id': False,#view_id,
					}

					return value
					
	def create_payslip_frm_ts(self):
		ids			= []
		var1		= ""
		str1		= ""
		count1		= 0
		payslip		= None
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		
		#emp_arr		= []
		obj_payslip	= self.env['hr.payslip']
		#obj_time	= self.env['hr.employee.timesheet']
		#obj_leave	= self.env['hr.payslip.leave']
		#user_id		= self.env.user.id
		
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		period_id 	= self.env['account.period'].finds(paydate)
		fiscal_id 	= self.env['account.fiscalyear'].finds(paydate)
		_config		= self.env['dincelaccount.settings'].load_default()
		
		for line in self.import_lines:
			if line.selected:
				count1+=1	
				payslip		= None
				employee	= line.employee_id
				employee_id	= employee.id
				vals = {'date': paydate,
						'employee_id': employee_id,
						'x_payfrequency_id': self.payfrequency_id.id,
						'date_from': self.date_from,
						'date_to': self.date_to,
						'x_is_timesheet':True,
					}
				if employee.x_group_id:
					vals['x_group_id'] 	=	employee.x_group_id.id
				if fiscal_id:
					vals['x_fiscal_id'] =	fiscal_id
				if line.import_id:
					vals['x_time_import_id']	=	line.import_id.id
				if _config:
					vals['x_clearing_account_id']	=	_config.payroll_clearing_code.id
				
				items 		= obj_payslip.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
				if len(items) > 0:
					for item in items:
						item.write(vals)
						payslip = item
				else:
					_number			= self.env['ir.sequence'].next_by_code('payslip.ref')
					chequeno=_number.replace("SLIP/","")
					vals['name']	= _number#"%s %s - %s" % (_number, self.date_from, self.date_to)
					vals['number']	= _number
					vals['x_chequeno']	= chequeno
					payslip 		= self.env['hr.payslip'].create(vals)
				if payslip:
					self.env['hr.timesheet.import.copy'].update_payslip_from_ts(payslip, line.import_id)
					ids.append(payslip.id)
		return ids		
				
				
	def import_timesheet_copy(self, ts_app):
		ids=[]
		path1 	 =  os.path.normpath("/var/log/odoo")
		dt		 =  datetime.datetime.today().strftime("%Y-%m-%d")
		path1	+= "/timesheetonly%s.txt" % (dt)
		#if self.timesheet_file:
		path1	+= ""
		str1	=base64.b64decode(self.timesheet_file)
		f=open(path1,'wb') #write-binary 
		f.write(str1)
		f.close()	
		#return self.import_timesheet2payslip(path1)
		#ids = self.import_timesheet2payslip_new(path1)
		#---------------------------------------------------------------------------------------------------------------------
		#---------------------------------------------------------------------------------------------------------------------
		'''
		c_lname		=0
		c_fname		=1 
		c_paytype	=2 
		c_job		=3 
		c_date		=7
		c_units		=8 
		c_empid		=9'''
		
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		
		emp_arr		= []
	
		user_id		= self.env.user.id
		
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		
		obj_import	= self.env['hr.timesheet.import']
		import_line	= self.env['hr.timesheet.import.copyline']
		
		dt_import 	= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		rows 		= self.get_rows_timesheet_file(path1, 	ts_app) 
		for row in rows:
			hrs			=row['hrs']
			date		=row['date']
			number		=row['emp_number']
			paytype		=row['paytype']
			rowindex	=row['rowindex']
			'''#paydate		=self.paydate
			with open(path1) as f:
				reader 	= csv.reader(f, delimiter="\t")
				d 		= list(reader)
				count1	= 0
				xfactor	= 1
				index	= -1
				for item in d:
					index+=1
					if index==0:#skip header column
						continue
					hrs		=item[c_units]
					date	=item[c_date]
					number	=item[c_empid]
					paytype	=item[c_paytype]
					lname	=item[c_lname]
					fname	=item[c_fname]'''
				
			employee_id, skip_ts_import, payslip_enable = obj_import.get_emp_bynumber(number)
			#category_id, pc_amt, amt_type = obj_import.get_paycategory(paytype)
			#xfactor	=1
			paycat 		= obj_import.get_paycategory(paytype)
			category_id	= paycat['category_id']
			pc_amt		= paycat['pc_amt']
			amt_type	= paycat['amt_type']
			xfactor		= paycat['xfactor']
			factor_type	= paycat['factor_type']
			#dt=parser.parse(date)
			
			if hrs and employee_id and date:
				if skip_ts_import:#skip for certain employee....
					_logger.error('timesheet.import.log001 skip_ts_import date [ %s ]  rowindex[ %s ] number[%s]' % (date, rowindex, number))
				else:	
					try:
						hrs_net=hrs
						if amt_type:
							#---------------------------------------------------------------------------------
							#assumed the factor is always 1.0 in hrs and the rate only converted as multiply
							#---------------------------------------------------------------------------------
							#xfactor=1#self.env['hr.pay.category'].get_xfactor(amt_type, pc_amt)
							#if amt_type=="pc":
							#	xfactor=float(pc_amt)*0.01
							hrs_net = float(hrs)*float(xfactor)
							#xfactor=1
							#elif amt_type=="times":
							#	xfactor=pc_amt
							#elif amt_type=="zero":
							#	xfactor=0	
						import_line.save_update_timesheet(employee_id, category_id, date, hrs, hrs_net, xfactor, factor_type, dt_import)
						
						if employee_id not in emp_arr:
							emp_arr.append(employee_id)
					except ValueError as ex:
						_logger.error('timesheet.import.log err ex [ %s ]dt[ %s ] name[ %s ]amt_type[%s]' % (ex, date,fname, amt_type))
						pass		
			else:
				#if date:
				try:
					comments=""
					if not employee_id:
						comments+="[NO_ACTIVE_EMP_FOUND] "
					if not hrs:
						comments+="[HRS_MISSING] "
					if not date:
						comments+="[DATE_MISSING] "	
					#dt=parser.parse(date)
					impname="%s %s - %s" % (fname, self.date_from, self.date_to)
					vals11={'date':date,
						'name':impname,
						'empnumber':number,
						'paytype':paytype,
						'hrs':hrs,
						'row':rowindex,
						'comments':comments,
						}
						
					self.env['hr.log.record'].create(vals11)
				except ValueError as ex:
					_logger.error('timesheet.import.log err ex [ %s ] dt[ %s ] name[ %s ] debug' % (ex, date,fname))
					pass
							
						
		count1=0
		import_copy=self.env['hr.timesheet.import.copy']
		for employee_id in emp_arr:	
			#if count1>0:
			#	continue
			#str1+="-------------- \n"
			objimport=None
			count1+=1	
			
			#employee	= self.env['hr.employee'].browse(employee_id)
			vals = {'date': paydate,
					'employee_id': employee_id,
					'payfrequency_id': self.payfrequency_id.id,
					'date_from': self.date_from,
					'date_to': self.date_to,
					'user_id':user_id,
				}
			
		
			items 		= import_copy.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
			if len(items)>0:
				for item in items:
					item.write(vals)
					objimport=item
				_first_time=False
			else:
				_first_time=True
				_number		= self.env['ir.sequence'].next_by_code('timesheet.import')
				vals['name']= _number
				objimport 	= import_copy.create(vals)
			if objimport:
				dt	=	date_from
				while (dt <= date_to):
					name 	= "%s" %  (dt.strftime("%a"))
					foundlines=import_line.get_timesheet_bydate(employee_id, dt)
					if len(foundlines)>0:
						for line in foundlines:
							_vals={
								'timesheet_id':objimport.id, #link with current import copy id
								'name': name,
								}
							line.write(_vals)
					dt	=	dt + timedelta(days=1) #next day loop...
				import_copy.calculate_summary_new(objimport)
				ids.append(objimport.id)
		value = {
			'type': 'ir.actions.act_window',
			'name': _('Timesheets'),
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'hr.timesheet.import.copy',
			'domain':[('id','in',ids)],
			'context':{},#{'search_default_partner_id': partner_id},
			'view_id': False,#view_id,
		}

		return value
		
	def create_timesheet_from_ts_scan(self):
		paydate		= self.paydate
		date_from	= self.date_from
		date_to		= self.date_to
		ids=[]
		count1=0
		emp_arr		= [] 
		if self.individual:
			for line in self.employee_ids:
				#employee_id=self.employee_id.id
				emp_arr.append(line.id)
		else:
			for line in self.employee_lines:
				#employee_id=self.employee_id.id
				if line.selected:
					emp_arr.append(line.employee_id.id)
			'''	
			sql="select distinct employee_no from hr_timesheet_scan where date between '%s' and '%s'" % (date_from, date_to)
			self.env.cr.execute(sql)
			rs = self.env.cr.fetchall()
			for row in rs:
				employee_no=row[0]
				sql="select id from hr_employee where x_emp_number='%s'" %  (employee_no)
				self.env.cr.execute(sql)
				rs1 = self.env.cr.fetchall()
				if len(rs1)==0:
					comments=""
					rowindex=0
					comments+="[EMP_MISSING] "
					paytype=""
					hrs=0
					impname="%s %s - %s" % (employee_no, self.date_from, self.date_to)
					vals11={'date':paydate,
						'name':impname,
						'empnumber':employee_no,
						'paytype':paytype,
						'hrs':hrs,
						'row':rowindex,
						'comments':comments,
						}
						
					self.env['hr.log.record'].create(vals11)
				else:
					for row1 in rs1:
						employee_id=row1[0]
						if employee_id not in emp_arr:
							emp_arr.append(employee_id)
				'''		
		user_id		= self.env.user.id
		
		date_to		= parser.parse(date_to)
		date_from	= parser.parse(date_from)
		
		#obj_import	= self.env['hr.timesheet.import']
		#import_line	= self.env['hr.timesheet.import.copyline']
		
		dt_import 	= datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")				
		count1count1=0
		import_copy=self.env['hr.timesheet.import.copy']
		for employee_id in emp_arr:	
			#if count1>0:
			#	continue
			#str1+="-------------- \n"
			objimport=None
			count1+=1	
			
			#employee	= self.env['hr.employee'].browse(employee_id)
			vals = {'date': paydate,
					'employee_id': employee_id,
					'payfrequency_id': self.payfrequency_id.id,
					'date_from': self.date_from,
					'date_to': self.date_to,
					'user_id':user_id,
				}
			
		
			items 		= import_copy.search([('employee_id','=',employee_id),('date_from','=',self.date_from),('date_to','=',self.date_to)])	
			if len(items)>0:
				for item in items:
					if item.state=="draft":#import only if it is draft else do not overwrite
						item.write(vals)
						objimport=item
				#_first_time=False
			else:
				#_first_time=True
				_number		= self.env['ir.sequence'].next_by_code('timesheet.import')
				vals['name']= _number
				objimport 	= import_copy.create(vals)
			if objimport:
				'''dt	=	date_from
				while (dt <= date_to):
					#name 	= "%s" %  (dt.strftime("%A"))
					foundlines=import_line.get_timesheet_bydate(employee_id, dt)
					if len(foundlines)>0:
						for line in foundlines:
							_vals={
								'timesheet_id':objimport.id, #link with current import copy id
								'name': name,
								}
							line.write(_vals)
					dt	=	dt + timedelta(days=1) #next day loop...'''
				obj	=import_copy.browse(objimport.id)
				#import_copy.add_date_range_timesheet(objimport.id, self.date_from, self.date_to, import_copy.employee_id)
				import_copy.add_date_range_timesheet(objimport.id, self.date_from, self.date_to, obj.employee_id)
				#import_copy.update_paid_hours(objimport) #>> calculate_summary_new() includes....
				#import_copy.calculate_summary_new(objimport)
				
				#_logger.error("create_timesheet_from_ts_scan dt [%s] objimport.id[%s] " % (vals, objimport.id ))	
				import_copy.init_ts_after_import(obj)
				ids.append(objimport.id)
		
		if len(ids)>0:
			value = {
				'type': 'ir.actions.act_window',
				'name': _('Timesheets'),
				'view_type': 'form',
				'view_mode': 'tree,form',
				'res_model': 'hr.timesheet.import.copy',
				'domain':[('id','in',ids)],
				'context':{},#{'search_default_partner_id': partner_id},
				'view_id': False,#view_id,
			}

			return value
		
	def _create_timesheet(self, payslip,  employee, date_from , date_to):
		dt 				= date_from
		amt_pc_loading	= 0
		loading_type	= ""
		group			= None
		obj_time		= self.env['hr.employee.timesheet']		
		
		while dt <= date_to:
			
			_vals={
				'employee_id':employee.id,
				'xfactor':1,
				'date':dt,
				'name': dt.strftime("%a"),
				'payslip_id': payslip.id,
				}
			#_found=False	
			if employee.x_group_id:
				for line in employee.x_group_id.attendance_ids:
					if (int(line.dayofweek)-dt.weekday())==0:
						_vals['hrs']		=	line.normal_pay
						_vals['hrs_net']	=	line.normal_pay
						if line.category_id:
							_vals['category_id']=	line.category_id.id
						break	
					#_found=True	
			'''if not _found:		
				if employee.x_group_id.category_id:
					_vals['category_id']=employee.x_group_id.category_id.id
					_vals['hrs']=employee.x_group_id.normal_hrs
					_vals['hrs_net']=employee.x_group_id.normal_hrs'''
			#if _found:	
			#_logger.error('get_emp_timeshseet_bydtget_2222 _vals[ %s ] ' % (_vals))
			obj_time.create(_vals)
			dt=dt+  timedelta(days = 1) #next day...	
		return True	
		
	def _create_timesheet_xx2(self, payslip,  employee, date_from , date_to):
		dt = date_from
		amt_pc_loading=0
		loading_type=""
		group=None
				
		#if row.employee_id.x_pay_basis and row.employee_id.x_pay_basis=="H":#hourly pay basis 
		while dt <= date_to:
			_vals2 = {
				'name': dt.strftime("%a"), #dt.strftime("%A"),#Monday/Tuesday/...
				'date': dt,
				'employee_id':employee.id,
				#'unit_amount': 0,
				#'amount': 0,
				#'ref': 0,
				'payslip_id':payslip.id
				}
			_not_found = True 
			sql="select id from account_analytic_line where employee_id='%s' and date='%s'" % (employee.id, dt)	 
			self._cr.execute(sql)
			rows1 = self._cr.fetchall()
			if len(rows1)>0:
				recordid	= rows1[0][0]
				line = self.env['account.analytic.line'].browse(recordid)
				_not_found = False
				_vals2['break_unpaid']	=	line.x_break_unpaid
				_vals2['break_paid']	=	line.x_break_paid
				_vals2['hrs_normal']	=	line.x_hrs_normal
				_vals2['hrs_t15']		=	line.x_hrs_t15
				_vals2['hrs_t20']		=	line.x_hrs_t20
				if line.x_category_id:
					_vals2['category_id']=	line.x_category_id.id
				_vals2['loading_noon']		=	line.x_loading_noon
				_vals2['loading_night']		=	line.x_loading_night
				_vals2['leave_annual']		=	line.x_leave_annual
				_vals2['leave_sick']		=	line.x_leave_sick
				_vals2['leave_unpaid']		=	line.x_leave_unpaid
				_vals2['leave_part']		=	line.x_leave_part
				#date_exists = self.env['account.analytic.line'].search([('employee_id','=',employee_id),('date','=',today_dt)])	
				#else:
				#date_exists = False
			if _not_found:			
				for line in employee.x_attendance_ids:
					if (int(line.dayofweek)-dt.weekday())==0:
						if line.hour_from:
							_vals2['time_in'] 	= 	line.hour_from
						if line.hour_to:
							_vals2['hour_to'] 	= 	line.hour_to	
							
						_vals2['break_unpaid']	=	line.meal_unpaid
						_vals2['break_paid']	=	line.paid_meal
						_vals2['hrs_normal']	=	line.normal_pay
						_vals2['hrs_t15']		=	line.paid_t15
						_vals2['hrs_t20']		=	line.paid_t20
						if line.category_id:
							_vals2['category_id']=	line.category_id.id

						break
						
			#_logger.error('employee_linesemployee_lines _vals2[ %s ]attendance_ids[ %s ]',_vals2, group)			
			timesheet = self.env['hr.payslip.timesheet'].create(_vals2) #create the time data
			
			dt=dt+  timedelta(days = 1) #next day...
						
		return True		
		
	def _create_timesheet_xx(self, payslip,  employee, date_from , date_to):
		dt = date_from
		amt_pc_loading=0
		loading_type=""
		group=None
		if employee.x_group_id:
			group=employee.x_group_id
			for line in group.category_ids:
				if line.code=="S-NSL":#summary night shift loading
					loading_type=line.subtype
					amt_pc_loading=line.pc_amt
				
		#if row.employee_id.x_pay_basis and row.employee_id.x_pay_basis=="H":#hourly pay basis 
		while dt <= date_to:
			_vals2 = {
				'name': dt.strftime("%a"),
				'date': dt,
				'employee_id':employee.id,
				#'unit_amount': 0,
				#'amount': 0,
				#'ref': 0,
				'payslip_id':payslip.id
				}
			if group:
				
				for line in group.attendance_ids:
					if dt.strftime("%w") == line.dayofweek:#0/1/2/3
						if line.hour_from:
							_vals2['time_in'] 	= 	line.hour_from
						if line.hour_to:
							_vals2['hour_to'] 	= 	line.hour_to	
							
						_vals2['break_unpaid']	=	line.meal_unpaid
						_vals2['break_paid']	=	line.paid_meal
						_vals2['hrs_normal']	=	line.normal_pay
						_vals2['hrs_t15']		=	line.paid_t15
						_vals2['hrs_t20']		=	line.paid_t20
						
						if line.normal_pay > 0.0:
							if loading_type == "2":#night shift loading....
								_vals2['rate_loading']		=	amt_pc_loading
							if group.category_id:
								_vals2['category_id']=	group.category_id.id
						else:
							if group.nopay_id:
								_vals2['category_id']=	group.nopay_id.id
						#else:
							
						break
			#_logger.error('employee_linesemployee_lines _vals2[ %s ]attendance_ids[ %s ]',_vals2, group)			
			timesheet = self.env['hr.payslip.timesheet'].create(_vals2) #create the time data
			
			dt=dt+  timedelta(days = 1) #next day...
						
		return True			 
		#_logger.error('employee_linesemployee_lines count1count1[ %s ]paydate[ %s ]',count1, paydate)					
		#raise UserError(_("Warning if needed. [%s] [%s]count1[%s]" %  (count2, str1, count1)))
		
class PayrollEmployeeLine(models.TransientModel):
	_name = 'hr.employee.line'
	_description = 'Employee line'
	payroll_id = fields.Many2one('hr.payroll.generate', string='Payroll')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	job_id = fields.Many2one('hr.job', related='employee_id.job_id')
	group_id = fields.Many2one('hr.employee.group', related='employee_id.x_group_id')
	emp_number = fields.Char(related='employee_id.x_emp_number')
	selected = fields.Boolean("Select", default=True) 
	payslip_create_type  = fields.Selection(dincelpayroll_vars.PAYSLIP_CREATE_OPTIONS, string='Payslip Creation') 	
	first_name = fields.Char(related='employee_id.x_first_name', store=True)
	last_name = fields.Char(related='employee_id.x_last_name', store=True)	
	sequence	= fields.Integer("SN")
	#_order = 'last_name asc, first_name asc'
	
class PayrollTimesheetImportLine(models.TransientModel):
	_name = 'hr.timesheet.import.line'
	_description = 'Timesheet import line'
	payroll_id 	= fields.Many2one('hr.payroll.generate', string='Payroll')
	import_name	= fields.Char("Import")
	employee_id = fields.Many2one('hr.employee', string='Employee')
	job_id 		= fields.Many2one('hr.job', related='employee_id.job_id')
	group_id 	= fields.Many2one('hr.employee.group', related='employee_id.x_group_id')
	emp_number 	= fields.Char(related='employee_id.x_emp_number')
	selected 	= fields.Boolean("Select", default=True) 
	first_name 	= fields.Char(related='employee_id.x_first_name', store=True)
	last_name 	= fields.Char(related='employee_id.x_last_name', store=True)	
	import_id 	= fields.Many2one('hr.timesheet.import.copy', string='Import')
	date 		= fields.Date(related='import_id.date')
	date_from 	= fields.Date(related='import_id.date_from')
	date_to 	= fields.Date(related='import_id.date_to')
	#_order = 'last_name asc, first_name asc'	