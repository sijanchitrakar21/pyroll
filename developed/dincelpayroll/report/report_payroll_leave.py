import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields
import logging
_logger = logging.getLogger(__name__)

class ReportEmployeePayroll(models.Model):
	_name = 'report.employee.payroll'	
	
class ReportEmployeeLeaveBalance(models.Model):
	_name = 'report.employee.leavebalance'	
	#date = fields.Date('Date To')
	def exp_leave_balance_all(self, app_name, empids, date_till):
		''' #people key leave balance export
			#-----------------------------------------------------------------------------------------------
			PayRef / Pin, Matched to either the stored Payroll Ref field if present or the Pin if not.
			Leave Code, Matched to the Special Pay Code as per the configuration options
			Balance Amount, Integer expressing the Leave balance amount.
			Leave Date As On, Date format DD/MM/CCYY. As on date that the leave balance was correct.
		'''
		csv=""
		dt_csv	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")
		#values	= {'employee_id':employee_id,'emp_number':emp_number,'balance':balance,'accrud':accrud, 'taken':taken, 'code':code,'refcode':refcode}
		for empid in empids:
			ytd_leaves = self.get_leave_ytd(empid, date_till)
			for bal in ytd_leaves:
				net_balance=bal['net_balance']
				if net_balance:
					net_balance=round(net_balance,4)
					enabled=False
					if bal['code']=="longservice":
						if bal['lsl_enable']:
							enabled=True
					else:
						enabled=True
					if enabled:	
						
						csv+="\"%s\",\"%s\",\"%s\",\"%s\",\n" % (bal['emp_number'], bal['refcode'],net_balance, dt_csv)
		return csv 
	
	def get_csv_leave_lines_all(self, empids, date_from, date_till):
		emplines=self.get_leave_lines_all(empids, date_from, date_till)
		csv="leave details as at between [%s] and [%s]" % (date_from, date_till)
		csv+=",\n"
		csv+="empno, employee, ref, date,  annual accrued, annual taken, personal accrued, personal taken, parent taken,long service accrued, long service taken,\n"
		for empline in emplines:
			
			name	=empline['name']
			number	=empline['number']
			lines	=empline['lines']
			summary	=empline['summary']
			for item in lines:
				ref				=item['name']
				date			=item['date']
				leave_annual_a	=item['leave_annual_a']
				leave_annual_t	=item['leave_annual_t']
				leave_sick_a	=item['leave_sick_a']
				leave_sick_t	=item['leave_sick_t']
				leave_parent_a	=item['leave_parent_a']
				leave_parent_t	=item['leave_parent_t']
				leave_lsl_a		=item['leave_lsl_a']
				leave_lsl_t		=item['leave_lsl_t']
				
				csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (number, name, ref, date, leave_annual_a, leave_annual_t, leave_sick_a, leave_sick_t,  leave_parent_t, leave_lsl_a, leave_lsl_t)
			
			ref="BALANCE"
			date=""

			csv+="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\n" % (number, name, ref, date, "", summary['annual_net'], "", summary['sick_net'],  summary['parent_net'], "", summary['lsl_net'])
			
		return csv 

		
	def get_leave_lines_all(self, empids, date_from, date_till):
		res=[]
		for empid in empids:
			sql="select id,name,x_emp_number,x_lsl_leave from hr_employee where id='%s'" % (empid)
			self.env.cr.execute(sql)
			rows1 = self.env.cr.dictfetchall()
			for row1 in rows1:
				lsl_enable	= row1['x_lsl_leave']
				name	= row1['name']
				emp_number	= row1['x_emp_number']
				lines, summary 	= self.env['report.employee.leavebalance'].get_leave_lines(empid, date_from, date_till, lsl_enable)
				val={'id':empid,'name':name,'number':emp_number,'lsl_enable':lsl_enable,'lines':lines,'summary':summary}
				res.append(val)
		return res 

		
	def get_leave_lines(self, empid, dt_from, date_till, lsl_enable):
		#@empid		= employee_id[0]
		#employee	= self.env['hr.employee'].browse(empid)
		#lsl_enable=False
		#sql="select x_lsl_leave from hr_employee where id='%s'"  % (empid)
		#self.env.cr.execute(sql)
		#rows1 = self.env.cr.dictfetchall()
		#for row1 in rows1:
		#	lsl_enable	= row1['x_lsl_leave']
			#code	= row1['x_code']
			
		ytd 		= self.get_leave_ytd(empid, dt_from)
		res 		= self.get_leave_hrs(empid, dt_from, date_till)
		
		#lsl_enable	= employee.x_lsl_leave
		
		annual_net 		= sick_net = lsl_net = parent_net = leave_other = 0.0
		annual_net_a 	= sick_net_a = lsl_net_a = parent_net_a = leave_other_a = 0.0
		annual_net_t 	= sick_net_t = lsl_net_t = parent_net_t = leave_other_t = 0.0
		
		for item in ytd:
			accrud	=float(item['accrud'])
			taken	=float(item['taken'])
			balance =float(item['balance'])
			
			accrud	=round(accrud, 2)
			taken	=round(taken, 2)
			
			balance	+=(accrud-taken)
			balance	=round(balance, 2)
			
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
				if lsl_enable:
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
		results=[]
		#results={}
		#results["Opening Balance"]=values
		results.append(values)
		for item in res:
			values={}
			_found=False
			#results = self._update_results(results, item['number'], item['date'], res)
			for item2 in results:
				if item2['name']==item['number']:
					values=item2
					_found=True
					break
			if _found==False:
					
				values 	= {"name":item['number'],
						"date":item['date'],
						"leave_annual_a":0.0,
						"leave_sick_a":0.0,
						"leave_lsl_a":0.0,
						"leave_parent_a":0.0,
						"leave_other_a":0.0,
						"leave_annual_t":0.0,
						"leave_sick_t":0.0,
						"leave_lsl_t":0.0,
						"leave_parent_t":0.0,
						"leave_other_t":0.0
						}
				results.append(values)
				_found=True
				
			accrud	=float(item['accrud'])
			taken	=float(item['taken'])
			
			accrud	=round(accrud, 2)
			taken	=round(taken, 2)
			
			balance	=accrud-taken
			balance	=round(balance, 2)
			
			if item['code']=="annual":
				values['leave_annual_a'] 	= accrud
				values['leave_annual_t'] 	= taken
				annual_net+=balance
			elif item['code']=="personal":
				values['leave_sick_a'] 		= accrud
				values['leave_sick_t'] 		= taken
				sick_net+=balance
			elif item['code']=="parental":
				values['leave_parent_a'] 	= accrud
				values['leave_parent_t'] 	= taken
				parent_net+=balance
			elif item['code']=="longservice":
				if lsl_enable:
					values['leave_lsl_a'] 	= accrud
					values['leave_lsl_t'] 	= taken
					lsl_net+=balance
			else:
				values['leave_other_a'] 	= accrud
				values['leave_other_t'] 	= taken
				leave_other+=balance
		
			items.append(values)
			
		summary['annual_net']	= round(annual_net,2)
		summary['sick_net']		= round(sick_net,2)
		summary['lsl_net']		= round(lsl_net,2)
		summary['parent_net']	= round(parent_net,2)
		summary['leave_other']	= round(leave_other,2)	
		
		return results, summary#, results
		
		
	def _update_results(self, results, number, date, res):
		for item in res:
			if item['number']==number:
				if number in results:
					values=results[number]
				else:
					values 	= {"name":item['number'],
						"date":item['date'],
						"leave_annual_a":0.0,
						"leave_sick_a":0.0,
						"leave_lsl_a":0.0,
						"leave_parent_a":0.0,
						"leave_other_a":0.0,
						"leave_annual_t":0.0,
						"leave_sick_t":0.0,
						"leave_lsl_t":0.0,
						"leave_parent_t":0.0,
						"leave_other_t":0.0
						}
					results[number]=values
				
		return results
		
	def get_leave_ytd(self, employee_id, date_till):	
		ytd= []
		emp_number=0
		lsl_enable=0
		fiscal_id 	= self.env['account.fiscalyear'].finds(date_till)
		cr 	= self.env.cr
		sql="select x_emp_number,x_lsl_leave from hr_employee where id='%s'" % (employee_id)
		cr.execute(sql)
		rows1 = cr.dictfetchall()
		for row1 in rows1:
			emp_number	= row1['x_emp_number']
			lsl_enable	= row1['x_lsl_leave']
			
		sql="select id,name,x_code,x_refcode from hr_holidays_status where active='t'"
		cr.execute(sql)
		rows1 = cr.dictfetchall()
		for row1 in rows1:
			leave_id	= row1['id']
			code	= row1['x_code']
			refcode	= row1['x_refcode']
			accrud=0.0
			taken=0.0
			sql	= """select sum(a.accrud_in) as accrud,sum(a.taken_out) as taken  
					from hr_payslip_leave_balance a,hr_holidays_status h where h.id=a.holiday_status_id 
					and a.date < '%s' and a.employee_id='%s' and h.id='%s' """ % (date_till, employee_id, leave_id)
			#_logger.error('get_leave_ytd sql[ %s ], ' % (sql))						
			cr.execute(sql)
			rows2 = cr.dictfetchall()
			for row2 in rows2:
				accrud	= row2['accrud']
				taken	= row2['taken']	
				if not accrud:
					accrud=0
				if not taken:
					taken=0	
				accrud=float(accrud)	
				taken=float(taken)
			if fiscal_id:
				balance	= self.env['hr.payslip'].get_ytd_archive(fiscal_id, employee_id, code)
			else:
				balance=0.0
			#_logger.error('get_leave_ytd.get_ytd_archive sql[%s][%s][%s][%s] ' % (balance, fiscal_id, employee_id, code))		
			#val['gross_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="gross")
			#val['tax_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="tax")
			#val['net_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="net")
			#val['super_amt']  +=self._get_ytd_archive(fiscal_id, employee_id, code="super")
			#val['annual_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="annual")
			#val['sick_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="personal")
			#val['lsl_leave']  +=self._get_ytd_archive(fiscal_id, employee_id, code="longservice")
			if accrud != 0.0 or taken != 0.0 or balance != 0.0:
				net_balance=balance+accrud-taken
				values	= {'employee_id':employee_id,'emp_number':emp_number,'lsl_enable':lsl_enable,'balance':balance,'accrud':accrud, 'taken':taken, 'code':code,'refcode':refcode,'net_balance':net_balance}
				ytd.append(values)
		
		_logger.error("ytdytd[%s]" % (ytd))
		return ytd
		
	def get_leave_hrs(self, employee_id, dt_from, date_till):
		cr 				= self.env.cr
		res=[]
		accrud, taken	= 0.0, 0.0
		
		sql	= """select a.payslip_id,h.x_code,sum(a.accrud_in) as accrud,sum(a.taken_out) as taken  
				from hr_payslip_leave_balance a,hr_holidays_status h where h.id=a.holiday_status_id 
				and a.date between '%s' and '%s' and a.employee_id='%s'  group by a.payslip_id,h.x_code""" % (dt_from, date_till, employee_id)
		#_logger.error('get_leave_hrs sql[ %s ], ' % (sql))				
		cr.execute(sql)
		rows2 = cr.dictfetchall()
		for row2 in rows2:
			payslip_id	= row2['payslip_id']
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
				sql="select date,number from hr_payslip where id='%s'" % (payslip_id)
				cr.execute(sql)
				rows3 = cr.dictfetchall()
				for row3 in rows3:
					#payslip_id	= row3['payslip_id']
					#payslip	= self.env['hr.payslip'].browse(payslip_id)
					_date	= datetime.strptime(row3['date'], "%Y-%m-%d").strftime("%d/%m/%Y")
					values	= {'accrud':accrud, 'taken':taken, 'code':code, 'payslip_id':payslip_id, 'number':row3['number'],'date':_date}
					res.append(values)	
		return res
			
	def get_leave_summary_lines(self, empid, dt_from, date_till):
		#empid		=employee_id[0]
		cr 				= self.env.cr
		employee1	=self.env['hr.employee'].browse(empid)
		#base_rate	=self.env['hr.employee'].get_default_rate(empid)
		rate_base, leave_rate, other_rate, salary_annual = self.env['hr.payslip'].get_employee_base_rate(employee1, date_till)
		#base_rate=0
		if rate_base:
			rate_base	= round(float(rate_base),2)
		lsl_enable	= employee1.x_lsl_leave
		fiscal_id 	= self.env['account.fiscalyear'].finds(dt_from)
		
		res 		= []
		sql="select id,name,x_code from hr_holidays_status where active='t'"
		cr.execute(sql)
		rows1 = cr.dictfetchall()
		for row1 in rows1:
		#_logger.error('_get_lines_get_lines base_rate[ %s ]empid[ %s ]' %  (base_rate, empid))
		#sql="select distinct h.holiday_status_id from hr_holidays h,hr_payslip p,hr_payslip_leave l where p.id=l.payslip_id and l.holiday_id=h.id"
		#sql+=" and p.x_fiscal_id='%s'" % (fiscal_id)
		#cr.execute(sql)
		#rows1 = cr.dictfetchall()
		#for row1 in rows1:
			#_code=None
			_status_id		= row1['id']
			#sql="select name,x_code from hr_holidays_status where id='%s'" % (_status_id)
			#cr.execute(sql)
			#rows2 = cr.dictfetchall()
			#for row2 in rows2:
			_name		= row1['name']
			_code		= row1['x_code']
			if _code and _name:	
			#for item in employee1.x_group_id.leave_ids: 
				values 					= {}
				values['name'] 			= _name
				#values['name'] 			= item.holiday_status_id.name
				#_status_id				= item.holiday_status_id.id
				#_code					= item.holiday_status_id.x_code
				_disabled=False
				if _code=="longservice" and lsl_enable==False:
					accrud, taken = 0.0,0.0
					_disabled=True
					#for opening balance....
				else:
					accrud, taken			= self.get_leave_hrs_byid(empid, dt_from, _status_id)
					#for opening balance....
				if not _disabled:
					if fiscal_id:
						balance_open	= self.env['hr.payslip'].get_ytd_archive(fiscal_id, empid, _code)
					else:
						balance_open=0.0
					#get_leave_hrs_byid(self, employee_id, date_till, _status_id, dt_from=None):
					#----------------------------------------------------------------------------
					#_logger.error('get_leave_ytd.get_ytd_archive sql[%s][%s][%s][%s] ' % (balance, fiscal_id, empid, _code))		
					balance_open	+= (accrud-taken)
					balance_open	= round(float(balance_open),2)
					values['hrs_open'] 		= balance_open
					if _code=="longservice" and lsl_enable==False:
						accrud, taken = 0.0,0.0
					else:
						accrud, taken	= self.get_leave_hrs_byid(empid, date_till, _status_id, dt_from)
					#get_leave_hrs_byid(self, employee_id, date_till, _status_id, dt_from=None):
					#----------------------------------------------------------------------------
					values['hrs_accrued'] 	= accrud
					values['hrs_taken'] 	= taken
					
					balance		= balance_open+accrud-taken
					balance		= round(float(balance),2)
					hrs_value	= round(float(rate_base*balance),2)
					values['hrs_balance'] 	= balance
					values['hrs_value'] 	= hrs_value
					if balance!=0.0:
						res.append(values)
			
		return res
		
	def get_leave_hrs_byid(self, employee_id, date_till, _status_id, dt_from=None):
		
		
		accrud, taken	= 0.0, 0.0
		if _status_id:
			cr 				= self.env.cr
			if dt_from:
				sql="""select sum(accrud_in) as accrud,sum(taken_out) as taken 
						from hr_payslip_leave_balance where 
						date between '%s' and '%s' and employee_id='%s' and holiday_status_id='%s' """ % (dt_from, date_till, employee_id, _status_id)
			else:
				sql="""select sum(accrud_in) as accrud,sum(taken_out) as taken 
						from hr_payslip_leave_balance where 
						date < '%s' and employee_id='%s' and holiday_status_id='%s' """ % (date_till, employee_id, _status_id)
			#_logger.error('get_leave_hrs_byidget_leave_hrs_byid dt_from[ %s ]sql[ %s ]' %  (dt_from, sql))			
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
	
	def to_number(self,no):
		if no:
			try:
				no1=round(float(no),4)
				return no1
			except:
				pass
		return 0.0
		
	def get_leave_balances(self, employee_id, date_till):
		 
		
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
			sql="select * from hr_payslip where employee_id='%s' and  date<='%s' order by date desc" % (employee_id[0], date_till)
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
		
class ReportLeaveBalance(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavebalance'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		#_logger.error('get_report_valuesget_report_values 111[ %s ]datadata[ %s ]' %  (docids, data))
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model = 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs = self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till = data['form'].get('date_till', time.strftime('%Y-%m-%d'))

		lines, summary = self.env[model].get_leave_balances(employee_id, date_till)
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
		

class ReportLeaveDetails(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavedetails'
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		model 		= 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		employee_id = data['form'].get('employee_id')
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		individual	= data['form'].get('individual')
		
		#individual	= data['form'].get('individual')
		if individual:
			#empids	= data['form'].get('empids')
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')
			
		#if individual:
		#	lines, summary 	= self.env['report.employee.leavebalance'].get_leave_lines(employee_id[0], date_from, date_till)
		#else:
		emplines = self.env['report.employee.leavebalance'].get_leave_lines_all(empids, date_from, date_till)
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
			#'employee': employee_id,
			'emplines': emplines,
			#'summary': summary,
		}
		
		return val
		
		
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
		empid		= employee_id[0]
		lines 		= self.env[model].get_leave_summary_lines(empid, date_from, date_till) 
		#lines 		= self._get_lines(employee_id[0], date_from, date_till)
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
		
		
class ReportLeaveSummaryAll(models.AbstractModel):
	_name = 'report.dincelpayroll.report_leavesummary_all'
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
		
		model 		= 'report.employee.leavebalance'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		empids		= data['form'].get('empids')
		
		emplines 	= []
		 
		for empid in empids:
			obj1=self.env['hr.employee'].browse(empid)
			lines =self.env[model].get_leave_summary_lines(empid, date_from, date_till)
		
			val= {'employee':obj1.name,'employeeno':obj1.x_emp_number,
					'lines':lines}
			emplines.append(val) 
		
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
			'emplines': emplines,
		}
		
		return val
	 