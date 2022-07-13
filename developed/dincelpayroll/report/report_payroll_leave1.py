import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields
import logging
_logger = logging.getLogger(__name__)

class ReportLeaveBalance(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavebalance'	
	
	def to_number(self,no):
		if no:
			return round(float(no),4)
		return 0.0
		
	def _get_lines(self, employee_id, date_till):
		 
		
		summary={}
		res = []
		total = []
		cr = self.env.cr
		#employee_id="713"
		#date_till="2018-06-26"#datetime.today()
		
		annual_net=0.0
		sick_net=0.0
		lsl_net=0.0
		parent_net=0.0
		
		if employee_id and  date_till:
			date_till = datetime.strptime(date_till, "%Y-%m-%d")
			sql="select * from hr_payslip where employee_id='%s' and date<='%s' order by date desc" % (employee_id[0], date_till)
			cr.execute(sql)
			payslips = cr.dictfetchall()
			for row in payslips:
				
				annual_leave	=self.to_number(row['x_annual_leave'])
				lsl_leave		=self.to_number(row['x_lsl_leave'])
				sick_leave		=self.to_number(row['x_sick_leave'])
				number			=row['number']
				date			=row['date']
				payslip_id		=row['id']
				date=datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
				values = {}
				parent_leave=0.0
				values['name'] = number
				values['date'] = date
				values['annual_leave'] = annual_leave
				values['lsl_leave'] = lsl_leave
				values['sick_leave'] = sick_leave
				values['parent_leave'] = parent_leave
				res.append(values)
				
				#----------------------------------------
				annual_net+=annual_leave
				sick_net+=sick_leave
				lsl_net+=lsl_leave
				parent_net+=parent_leave
				#----------------------------------------
				
				#leaves taken
				annual_leave=0.0
				sick_leave=0.0
				lsl_leave=0.0
				parent_leave=0.0
				
				sql="select s.*,p.code  from hr_payslip_summary s,hr_pay_category p where p.id=s.category_id and s.payslip_id='%s' " % (payslip_id)
				cr.execute(sql)
				rows2 = cr.dictfetchall()
				for row2 in rows2:
					_code=row2['code']
					if row2['tot_hrs']:
						tot_hrs=float(row2['tot_hrs'])
						if tot_hrs and tot_hrs>0.0:
							if _code == "S-AL":
								annual_leave=tot_hrs
							elif _code == "S-SL": #sick leave
								sick_leave=tot_hrs
				sql="select s.*,p.code,p.sub_category  from hr_payslip_payline s,hr_pay_category p where p.id=s.category_id and s.payslip_id='%s' " % (payslip_id)
				cr.execute(sql)
				rows2 = cr.dictfetchall()
				for row2 in rows2:
					sub_category=row2['sub_category']
					hrs_qty=float(row2['hrs_qty'])
					if sub_category=="longservice":
						lsl_leave+=hrs_qty
					elif sub_category=="parental":
						parent_leave+=hrs_qty
					
					
					
				if annual_leave >0.0 or 	sick_leave >0.0 or lsl_leave >0.0 or parent_leave >0.0:
					annual_leave	=round(annual_leave,4)
					sick_leave		=round(sick_leave,4)
					lsl_leave		=round(lsl_leave,4)
					parent_leave	=round(parent_leave,4)
					
					values 			= {}
					values['name'] 	= number
					values['date'] 	= date
					values['annual_leave'] 	= -annual_leave
					values['lsl_leave'] 	= -lsl_leave
					values['sick_leave'] 	= -sick_leave
					values['parent_leave'] 	= -parent_leave
					res.append(values)
					#----------------------------------------
					annual_net	-=annual_leave
					sick_net	-=sick_leave
					lsl_net		-=lsl_leave
					parent_net	-=parent_leave
					#----------------------------------------
					
			#----------------------------------------		
			annual_net	=round(annual_net,4)
			sick_net	=round(sick_net,4)
			lsl_net		=round(lsl_net,4)
			parent_net	=round(parent_net,4)
			#----------------------------------------
			
		summary['annual_net']	=annual_net
		summary['sick_net']		=sick_net
		summary['lsl_net']		=lsl_net
		summary['parent_net']	=parent_net
		return res, summary
		
	@api.model
	def get_report_values(self, docids, data=None):
		#_logger.error('get_report_valuesget_report_values 111[ %s ]datadata[ %s ]' %  (docids, data))
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model = 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till = data['form'].get('date_till', time.strftime('%Y-%m-%d'))

		lines, summary = self._get_lines(employee_id, date_till)
		date_till=datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_till': date_till,#str(date_till).strftime("%d/%m/%Y"),
			'employee': employee_id,
			'lines': lines,
			'summary': summary,
		}
		#_logger.error('get_report_valuesget_report_values 222[ %s ]valval[ %s ]' %  (self.ids, val))
		return val
		
class ReportEmployeeLeaveBalance(models.Model):
	_name = 'report.employee.leavebalance'	
	#date = fields.Date('Date To')
	
class ReportLeaveDetails(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavedetails'
	
	@api.model
	def get_report_values(self, docids, data=None):
		#_logger.error('get_report_valuesget_report_values 111[ %s ]datadata[ %s ]' %  (docids, data))
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model 		= 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		#_logger.error('get_report_values data [ %s ] date_from[ %s ] date_till[ %s ] ' % (data['form'], date_from, date_till))	
		lines, summary 	= self._get_lines(employee_id, date_from, date_till)
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_till': date_till,#str(date_till).strftime("%d/%m/%Y"),
			'date_from': date_from,
			'employee': employee_id,
			'lines': lines,
			'summary': summary,
		}
		
		return val
		
	def _get_lines(self, employee_id, dt_from, date_till):
		empid		= employee_id[0]
		employee	= self.env['hr.employee'].browse(empid)
		 
		ytd 		= self.get_leave_ytd(empid, dt_from)
		res 		= self.get_leave_hrs(empid, dt_from, date_till)
		
		annual_net 		= sick_net = lsl_net = parent_net = leave_other = 0.0
		annual_net_a 	= sick_net_a = lsl_net_a = parent_net_a = leave_other_a = 0.0
		annual_net_t 	= sick_net_t = lsl_net_t = parent_net_t = leave_other_t = 0.0
		
		for item in ytd:
			accrud	=float(item['accrud'])
			taken	=float(item['taken'])
			balance=accrud-taken
			 
			if item['code']=="annual":
				annual_net+=balance
				annual_net_a=accrud
				annual_net_t=taken
			elif item['code']=="personal":
				sick_net+=balance
				sick_net_a=accrud
				sick_net_t=taken
			elif item['code']=="parental":
				parent_net+=balance
				parent_net_a=accrud
				parent_net_t=taken
			elif item['code']=="longservice":
				lsl_net+=balance
				lsl_net_a=accrud
				lsl_net_t=taken
			else:
				leave_other+=balance
				leave_other_a=accrud
				leave_other_t=taken
		summary		= {}
		dt_from	= datetime.strptime(dt_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		values 	= {"name":"Opening Balance",
					"date":dt_from,
					"leave_annual_a":annual_net_a,
					"leave_sick_a":sick_net_a,
					"leave_lsl_a":lsl_net_a,
					"leave_parent_a":parent_net_a,
					"leave_other_a":leave_other_a,
					"leave_annual_t":annual_net_t,
					"leave_sick_t":sick_net_t,
					"leave_lsl_t":lsl_net_t,
					"leave_parent_t":parent_net_t,
					"leave_other_t":leave_other_t,
					}
		items=[]
		items.append(values)
		
		for item in res:
			accrud	=float(item['accrud'])
			taken	=float(item['taken'])
			balance=accrud-taken
			if item['code']=="annual":
				annual_net+=balance
			elif item['code']=="personal":
				sick_net+=balance
			elif item['code']=="parental":
				parent_net+=balance
			elif item['code']=="longservice":
				lsl_net+=balance
			else:
				leave_other+=balance
		
			items.append(values)
			
		summary['annual_net']	= annual_net
		summary['sick_net']		= sick_net
		summary['lsl_net']		= lsl_net
		summary['parent_net']	= parent_net
		summary['leave_other']	= leave_other	
		
		return items, summary
	def _get_leaves_val(self, number, dt, res):
		annual_net_a 	= sick_net_a = lsl_net_a = parent_net_a = leave_other_a = 0.0
		annual_net_t 	= sick_net_t = lsl_net_t = parent_net_t = leave_other_t = 0.0
		for item in res:
			if item['number']==number:
				accrud	=float(item['accrud'])
				taken	=float(item['taken'])
				if item['code']=="annual":
					annual_net_a 	= accrud
					annual_net_t 	= taken
					
				elif item['code']=="personal":
					sick_net_a 		= accrud
					sick_net_t 		= taken
					
				elif item['code']=="parental":
					parent_net_a 	= accrud
					parent_net_t 	= taken
					
				elif item['code']=="longservice":
					lsl_net_a 		= accrud
					lsl_net_t 		= taken
				else:
					leave_other_a 	= accrud
					leave_other_t 	= taken
		values 	= {"name":number,
					"date":dt,
					"leave_annual_a":annual_net_a,
					"leave_sick_a":sick_net_a,
					"leave_lsl_a":lsl_net_a,
					"leave_parent_a":parent_net_a,
					"leave_other_a":leave_other_a,
					"leave_annual_t":annual_net_t,
					"leave_sick_t":sick_net_t,
					"leave_lsl_t":lsl_net_t,
					"leave_parent_t":parent_net_t,
					"leave_other_t":leave_other_t
					}
		return values
		
	def get_leave_ytd(self, employee_id, date_till):	
		ytd= []
		cr 	= self.env.cr
		sql	= """select h.x_code,sum(a.accrud_in) as accrud,sum(a.taken_out) as taken  
				from hr_payslip_leave_balance a,hr_holidays_status h where h.id=a.holiday_status_id 
				and a.date < '%s' and a.employee_id='%s'  group by h.x_code""" % (date_till, employee_id)
		#_logger.error('get_leave_ytd sql[ %s ], ' % (sql))						
		cr.execute(sql)
		rows2 = cr.dictfetchall()
		for row2 in rows2:
			accrud	= row2['accrud']
			taken	= row2['taken']	
			code	= row2['x_code']	
			if accrud != 0.0 or _taken != 0.0:
				values	= {'accrud':accrud, 'taken':taken, 'code':code}
				ytd.append(values)
		return ytd
		
	def get_leave_hrs(self, employee_id, dt_from, date_till):
		cr 				= self.env.cr
		res=[]
		accrud, taken	= 0.0, 0.0
		curr_id=-1
		sql	= """select a.payslip_id,h.x_code,sum(a.accrud_in) as accrud,sum(a.taken_out) as taken  
				from hr_payslip_leave_balance a,hr_holidays_status h where h.id=a.holiday_status_id 
				and a.date between '%s' and '%s' and a.employee_id='%s'  group by a.payslip_id,h.x_code""" % (dt_from, date_till, employee_id)
		#_logger.error('get_leave_hrs sql[ %s ], ' % (sql))				
		cr.execute(sql)
		rows2 = cr.dictfetchall()
		for row2 in rows2:
			payslip_id	= row2['payslip_id']
			#if curr_id==-1:
			#	curr_id=payslip_id #for the first time
			accrud		= row2['accrud']
			taken		= row2['taken']		
			code		= row2['x_code']	
			if accrud:
				accrud	= float(accrud)
				accrud	= round(float(accrud), 2)
			else:
				accrud	= 0.0
			if taken:
				taken	= float(taken)
				taken	= round(float(taken), 2)
			else:	
				taken	= 0.0
			
			if accrud != 0.0 or taken != 0.0:
			#if curr_id!=payslip_id:	
				payslip	= self.env['hr.payslip'].browse(payslip_id)
				_date	= datetime.strptime(payslip.date, "%Y-%m-%d").strftime("%d/%m/%Y")
				values	= {'accrud':accrud, 'taken':taken, 'code':code, 'payslip_id':payslip_id, 'number':payslip.number,'date':_date}
				res.append(values)	
		return res
			
		#return 0.0, 0.0	
		
class ReportLeaveSummary(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavesummary'
	
	@api.model
	def get_report_values(self, docids, data=None):
		#_logger.error('get_report_valuesget_report_values 111[ %s ]datadata[ %s ]' %  (docids, data))
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model 		= 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		
		lines 		= self._get_lines(employee_id, date_from, date_till)
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_till': date_till,#str(date_till).strftime("%d/%m/%Y"),
			'date_from': date_from,
			'employee': employee_id,
			'lines': lines,
			#'summary': summary,
		}
		#_logger.error('report_leavesummaryreport_leavesummary 222[ %s ]lines[ %s ]' %  (self.ids, lines))
		return val
		
	def _get_lines(self, employee_id, dt_from, date_till):
		empid		=employee_id[0]
		employee	=self.env['hr.employee'].browse(empid)
		base_rate	=self.env['hr.employee'].get_default_rate(empid)
		base_rate	= round(float(base_rate),2)
		#_logger.error('_get_lines_get_lines base_rate[ %s ]empid[ %s ]' %  (base_rate, empid))
		res 		= []
		for item in employee.x_leave_ids:
			values 					= {}
			values['name'] 			= item.holiday_status_id.name
			_status_id				= item.holiday_status_id.id
			accrud, taken			= self.get_leave_hrs(empid, dt_from, _status_id)
			
			balance	= accrud-taken
			balance	= round(float(balance),2)
			values['hrs_open'] 		= balance
			
			accrud, taken			= self.get_leave_hrs(empid, date_till, _status_id, dt_from)
			values['hrs_accrued'] 	= accrud
			values['hrs_taken'] 	= taken
			
			balance		= balance+accrud-taken
			balance		= round(float(balance),2)
			hrs_value	= round(float(base_rate*balance),2)
			values['hrs_balance'] 	= balance
			values['hrs_value'] 	= hrs_value
			if balance!=0.0:
				res.append(values)
			
		return res
		
	def get_leave_hrs(self, employee_id, date_till, _status_id, dt_from=None):
		cr 				= self.env.cr
		accrud, taken	= 0.0, 0.0
		if dt_from:
			sql="""select sum(accrud_in) as accrud,sum(taken_out) as taken 
					from hr_payslip_leave_balance where 
					date between '%s' and '%s' and employee_id='%s' and holiday_status_id='%s' """ % (dt_from, date_till, employee_id, _status_id)
		else:
			sql="""select sum(accrud_in) as accrud,sum(taken_out) as taken 
					from hr_payslip_leave_balance where 
					date < '%s' and employee_id='%s' and holiday_status_id='%s' """ % (date_till, employee_id, _status_id)
					
		cr.execute(sql)
		rows2 = cr.dictfetchall()
		for row2 in rows2:
			accrud		= row2['accrud']
			taken		= row2['taken']		
			if accrud:
				accrud	= float(accrud)
				accrud	= round(float(accrud), 2)
			else:
				accrud	= 0.0
			if taken:
				taken	= float(taken)
				taken	= round(float(taken), 2)
			else:	
				taken	= 0.0
				
		return accrud, taken
			
		#return 0.0, 0.0	