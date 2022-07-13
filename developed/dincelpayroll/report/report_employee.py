import time
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import os
import base64
from io import StringIO
import csv
from datetime import date, datetime, timedelta
import datetime as dt
from dateutil import parser
import logging
_logger = logging.getLogger(__name__)

class EmployeeReport(models.TransientModel):
	_name = 'hr.employee.report'
	_description = 'Employee Report'
	
	def get_csv_employee_details(self, empids, date_till):
		csv ="employee_details as at [%s]" % (date_till)
		csv +="\n"
		csv +="name, number, grpname,jobname,pay_basis, leave_rate,  rate_base, salary_annual, date_stop,"
		csv +="\n"
		lines = self.env['hr.employee.report'].get_employee_details(empids, date_till)
		for row in lines:
			name=row['name']
			number=row['number']
			pay_basis=row['pay_basis']
			leave_rate=row['leave_rate']
			other_rate=row['other_rate']
			rate_base=row['rate_base']
			salary_annual=row['salary_annual']
			date_stop=row['date_stop']
			grpname=row['grpname']
			jobname=row['jobname']
			csv +="\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\","	 % (name, number, grpname,jobname, pay_basis, leave_rate,  rate_base, salary_annual, date_stop)
			csv +="\n"
		return csv
		
	def get_employee_details(self, empids, date_till):
		res 	= []
		for empid in empids:
			sql="""select e.*,g.name as grpname,j.name as jobname 
				from hr_employee e left join hr_employee_group g on e.x_group_id=g.id 
				left join hr_job j on e.job_id=j.id 
				where e.id='%s'""" % (empid)
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			for row in rows1:
				name 			=row['name']	
				number 			=row['x_emp_number']
				date_stop 			=row['x_date_stop']
				active=row['active']
				grpname=row['grpname']
				jobname=row['jobname']
				if not date_stop:
					date_stop=""
				if not grpname:
					grpname=""
				if not jobname:
					jobname=""
				pay_basis, leave_rate, other_rate, rate_base, salary_annual = self.env['hr.employee.rate'].get_employee_rates(empid, date_till)
				val={'name':name, 
					'id':empid,
					'number':number,
					'active':	active,
					'pay_basis':	pay_basis,
					'leave_rate':	round(leave_rate,4),
					'other_rate':	round(other_rate,4),
					'rate_base':	round(rate_base,4),
					'salary_annual':	round(salary_annual,4),
					'date_till':	date_till,
					'grpname':	grpname,
					'jobname':	jobname,
					'date_stop':	date_stop,
					}
				res.append(val)
		return res
		
	def get_payg_summary_annual(self,empids, date_till):
		res 	= []
		for empid in empids:
			sql="""select e.*,g.name as grpname,j.name as jobname 
				from hr_employee e left join hr_employee_group g on e.x_group_id=g.id 
				left join hr_job j on e.job_id=j.id 
				where e.id='%s'""" % (empid)
			self._cr.execute(sql)
			rows1 = self._cr.dictfetchall()
			for row in rows1:
				name 			=row['name']	
				number 			=row['x_emp_number']
				date_stop 		=row['x_date_stop']
				active=row['active']
				grpname=row['grpname']
				jobname=row['jobname']
				state_id=row['x_state_id']
				dt=parser.parse(date_till)
				year=dt.strftime("%Y")
				if not date_stop:
					date_stop=""
				if not grpname:
					grpname=""
				if not jobname:
					jobname=""
				statename=""
				if state_id:
					sql="select name from res_country_state where id='%s'" % (state_id)
					self._cr.execute(sql)
					rows2 = self._cr.dictfetchall()
					for row2 in rows2:
						statename =row2['name']	
						
				address_line1=row['x_street']		
				address_line2=("%s %s %s") % (row['x_suburb'] ,statename , row['x_postcode'])
				address_line3=""
				#pay_basis, leave_rate, other_rate, rate_base, salary_annual = self.env['hr.employee.rate'].get_employee_rates(empid, date_till)
				val={'employee':name, 
					'id':empid,
					'number':number,
					'active':	active,
					'address_line1':	address_line1,
					'address_line2':	address_line2,
					'address_line3':	address_line3,
					'date':	date_till,
					'grpname':	grpname,
					'jobname':	jobname,
					'date_stop':	date_stop,
					'year': year,
					}
				res.append(val)
		return res
		
class EmployeeReportDetails(models.AbstractModel):
	_name = 'report.dincelpayroll.report_employee_details'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')

		lines		= self.env['hr.employee.report'].get_employee_details(empids, date_till)
		#_logger.error('report_employee_detailsreport_employee_details lines[ %s ]',lines)
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'lines': lines,
			'report_title': "Employee Details",
			}
		
		return val	
class EmployeeReportDetails(models.AbstractModel):
	_name = 'report.dincelpayroll.report_payg_summary_annual'	
	
	@api.model
	def get_report_values(self, docids, data=None):
		
		if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
			raise UserError(_("Form content is missing, this report cannot be printed."))
			
		model 		= 'report.employee.payroll'#self.env.context.get('active_model')
		docs 		= self.env[model].browse(self.env.context.get('active_id'))
		
		date_till 	= data['form'].get('date_till', time.strftime('%Y-%m-%d'))
		date_from 	= data['form'].get('date_from', time.strftime('%Y-%m-%d'))
		date_from	= datetime.strptime(date_from, "%Y-%m-%d").strftime("%d/%m/%Y")
		date_till	= datetime.strptime(date_till, "%Y-%m-%d").strftime("%d/%m/%Y")#time.strftime(date_till,"%d/%m/%Y")
		
		individual	= data['form'].get('individual')
		if individual:
			empids = [data['form'].get('employee_id')[0]]
		else:
			empids	= data['form'].get('empids')

		lines		= self.env['hr.employee.report'].get_payg_summary_annual(empids, date_till)
		#_logger.error('report_employee_detailsreport_employee_details lines[ %s ]',lines)
		val= {
			'doc_ids': self.ids,
			'doc_model': model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'date_from': date_from,
			'date_till': date_till,
			'summary_line': lines,
			'report_title': "Payment Summary Report",
			}
		
		return val			