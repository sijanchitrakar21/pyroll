# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import logging
import base64
import csv
from io import StringIO
from datetime import date
from datetime import datetime
import datetime
import dateutil
from dateutil import parser
#import pandas
import xlrd
import os
import math

#import pyexcel as pe
#_logger = logging.getLogger('hr.timesheet.import')
_logger = logging.getLogger(__name__)
class TimesheetImport(models.TransientModel):
	_name = 'hr.timesheet.import'
	_description = 'Import timesheet'

	csv_file = fields.Binary('Timesheet File')
	xls_dcs = fields.Boolean('DCS Excel ?')
	paydate = fields.Date('Pay Date')
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	payfrequency_id = fields.Many2one('hr.payroll.payfrequency', string='Payment Frequency')
	
	@api.onchange('payfrequency_id')
	def onchange_payfrequency(self):
		#_logger.error('_onchange_payfrequency:, payfrequency_id[ %s ] date_from[ %s ]' % (self.payfrequency_id, self.date_from))
		if self.payfrequency_id and self.date_from:
			code=self.payfrequency_id.code 
			_reverse=False
			dt=self.env['hr.payslip.run'].calculate_end_date(code, self.date_from, _reverse)	
			values = {
				'date_to': dt,
			}
			return {'value':values} 
			
	def to_number(self,number):
		try:
			number=self.isNaN(number)
			return int(float(number))
		except e:
			_logger.error('to_numberto_number:, eee[ %s ]' % e)
			return 0
		return 0	
		
	def get_emp_bynumber(self, number):
		skip_ts_import=False
		payslip_enable=True
		if number:
			try:
				
				number=self.to_number(number)
				sql="select id,x_skip_ts_import,x_payslip_enable from hr_employee where x_emp_number='%s'" % (number)
				self._cr.execute(sql)
				rows1 = self._cr.fetchall()
				#_logger.error('get_emp_bynumberget_emp_bynumber, number[ %s ]' % number)
				for row1 in rows1:
					recordid=row1[0]
					if row1[1]:
						skip_ts_import=row1[1]#x_skip_ts_import
					if row1[2]:	
						payslip_enable=row1[2]#x_payslip_enable
					return recordid, skip_ts_import, payslip_enable
			except Exception as ex:
				_logger.error('get_emp_bynumberexceptexcept, number[ %s ][ %s ]' % (number,ex))
				pass
				#return False, skip_ts_import, payslip_enable
		return False, skip_ts_import, payslip_enable
		
	def get_emp_info(self, name):
		if name:
			sql="select id from hr_employee where name='%s'" % (name)
			self._cr.execute(sql)
			rows1 = self._cr.fetchall()
			for row1 in rows1:
				recordid=row1[0]
				return recordid
		return False
		
	def date_validate(self, date_text):
		try:
			today_dt 	= dateutil.parser.parse(str(date_text))
			today_dt	= str(today_dt)[:10]
			dt = datetime.datetime.strptime(str(today_dt), '%Y-%m-%d')
			return dt
		except:
			return False
			
	def isNaN(self, num):
		x=float(num)
		if math.isnan(x):
			return 0
		else:
			return x 
			
	def get_pay_info(self, code):
		if code:
			sql="select id from hr_pay_category where mapping_txt='%s'" % (code)
			self._cr.execute(sql)
			rows1 = self._cr.fetchall()
			
			for row1 in rows1:
				recordid=row1[0]
				return recordid
		return False		
	
	def _import_xls_file(self, path1):
		#path1 = os.path.normpath("/var/log/odoo")
		#path1="/opt/log/odoo/timesheet.xls"
		#path1+="/timesheet.xlsx"
		ok=True
		
		project = self.env['project.project'].search([('id','>',0)], limit=1)
 
		lines=[]
		project_id=project.id
		account_id=project.analytic_account_id.id
		user_id=self.env.user.id
		company_id=self.env.user.company_id.id
		
		today = datetime.date.today()
		none_arr=[]
		emp_arr=[]
		tot_records=0
		dt1=None
		dt2=None
		count2=0	
		if ok:
			df = None#pandas.read_excel(path1, engine='xlrd')
			c_empid="" #1
			c_payday=""
			c_emp="" #3
			c_day=""
			c_date=""
			c_payname="" #6
			c_in=""
			c_out="" #8
			c_tothrs=""
			c_unpaid_br=""
			c_hrs_normal="" #11
			c_paid_br=""
			c_hrs15=""
			c_hrs20="" #14
			c_annual=""
			c_sick=""      #16
			c_unpaid_leave=""
			c_part_leave=""
			c_noon="" #19
			c_night="" # 
			c_nethrs="" #21
			i=0
			employee_id=0
			now2=""
			skip_ts_import, payslip_enable = False, True
			#_logger.error('action_import_xls:, columns[ %s ]',df.columns)
			 
			for colname in df.columns:
				i+=1
				if i==1:
					c_empid=colname
				elif i==2:
					c_payday=colname
				elif i==3:
					c_emp=colname
				elif i==4:
					c_day=colname
				elif i==5:
					c_date=colname
				elif i==6:
					c_payname=colname
				elif i==7:
					c_in=colname
				elif i==8:
					c_out=colname
				elif i==9:
					c_tothrs=colname
				elif i==10:
					c_unpaid_br=colname
				elif i==11:
					c_hrs_normal=colname
				elif i==12:
					c_paid_br=colname
				elif i==13:
					c_hrs15=colname
				elif i==14:
					c_hrs20=colname
				elif i==15:
					c_annual=colname
				elif i==16:
					c_sick=colname
				elif i==17:
					c_unpaid_leave=colname
				elif i==18:
					c_part_leave=colname
				elif i==19:
					c_noon=colname
				elif i==20:
					c_night=colname	
				elif i==21:
					c_nethrs=colname
				#_logger.error('action_import_xls:, colname[ %s ]',colname)
				
			prevname=""	
			count1=0
			
			for i in df.index:
				# print(df['Sepal width'][i])
				count1+=1
				tot_records+=1
				empnumber	= str(df[c_empid][i]).strip()
				name		= str(df[c_emp][i]).strip()
				
				day			= df[c_day][i]
				date		= df[c_date][i]
				invalid=False
				if  'nan' in str(day)  or 'nan' in str(date):
					#_logger.error('err isnan [%s ][ %s ]' % (day, date))
					#continue
					invalid=True
				else:
					date=self.date_validate(date)
					if not date:
						#_logger.error('err validatevalidate[ %s ][ %s ]' % (day, date))
						#continue
						invalid=True
					#else:	
					#	_logger.error('batch_idbatch_idbatch_dddddd[ %s ][ %s ]' % (day, date))
				paytype		= str(df[c_payname][i]).strip()
				timein		= df[c_in][i]
				timeout		= df[c_out][i]
							#=self.to_number(
				tothrs		= self.to_number(df[c_tothrs][i]) #Total Hours 
				
				break_unpaid	= self.to_number(df[c_unpaid_br][i])
				hrs_normal		= self.to_number(df[c_hrs_normal][i])
				break_paid		= self.to_number(df[c_paid_br][i])
				hrs15			= self.to_number(df[c_hrs15][i])
				hrs20			= self.to_number(df[c_hrs20][i])
				
				annual_leave	= self.to_number(df[c_annual][i])
				sick_leave		= self.to_number(df[c_sick][i])
				leave_unpaid	= self.to_number(df[c_unpaid_leave][i])
				partday_leave	= self.to_number(df[c_part_leave][i])

				noon_loading	= self.to_number(df[c_noon][i])
				night_loading	= self.to_number(df[c_night][i])

				nethrs			= self.to_number(df[c_nethrs][i]) #Total Hrs Worked

				unit_amount		= nethrs
				
				pay_id			=self.get_pay_info(paytype)
				recordid		=0
				#if tothrs and tothrs>0:
				#if day and date and date is not None:
				if prevname=="":
					prevname	=name
					count2		=0
					if not invalid:	
						dt1			=date
						#employee_id=self.get_emp_info(name)
						employee_id, skip_ts_import, payslip_enable	=self.get_emp_bynumber(empnumber)
					lines		=[]
					
				if not invalid:	
					dt2	 = date
					now2 = "%s %s" %  (day, date)
					
				if name != prevname:
					prevname=name
					if count2>0:
						count2=0
						_vals = {
							'name': now2,
							'date': today,
							#s'date_start': dt1,
							#'date_end': dt2,
							'state': 'draft',
						}
						if not invalid:	
							if dt1:
								_vals['date_start']=dt1
							if dt2:
								_vals['date_end']=dt2
						if employee_id:
							_vals['employee_id']=employee_id
						#_logger.error('batch_idbatch_idbatch_id11000 _vals[ %s ' % (_vals))	
						batch_id = self.env['hr.timesheet.batch'].create(_vals)
						#_logger.error('batch_idbatch_idbatch_id11 _vals[ %s ][ %s ]' % (_vals, batch_id))
						for _id in lines:	
							sql="update account_analytic_line set x_batch_id='%s' where id='%s'" % (batch_id.id, _id)	 
							self._cr.execute(sql)
						lines=[]
							
					
					if not invalid:	
						dt1=date
						#employee_id=self.get_emp_info(name)
						employee_id, skip_ts_import, payslip_enable = self.get_emp_bynumber(empnumber)
						if skip_ts_import==False and payslip_enable==True:
							if employee_id:
								emp_arr.append(name)
							else:
								none_arr.append(name)
				if skip_ts_import==False and payslip_enable==True:
					if employee_id and not invalid:
						sql="select id from account_analytic_line where employee_id='%s' and date='%s'" % (employee_id, date)	 
						self._cr.execute(sql)
						rows1 = self._cr.fetchall()
						if len(rows1)>0:
							recordid	= rows1[0][0]
							date_exists = self.env['account.analytic.line'].browse(recordid)
							#date_exists = self.env['account.analytic.line'].search([('employee_id','=',employee_id),('date','=',today_dt)])	
						else:
							date_exists = False
						#_logger.error('date_existsdate_exists22 date[ %s ]date_exists[ %s ][ %s ]',today_dt, date_exists, sql)
						
						_vals2 = {
							'name': now2,
							'date': date,
							'user_id': user_id,
							'employee_id': employee_id,
							'account_id': account_id,
							'project_id': project_id,
							'company_id':company_id,
							'unit_amount':unit_amount,
							'x_break_unpaid': break_unpaid,
							'x_break_paid': break_paid,
							'x_hrs_normal': hrs_normal,
							'x_hrs_t15': hrs15,
							'x_hrs_t20': hrs20,
							'x_loading_noon': noon_loading,
							'x_loading_night': night_loading,
							'x_leave_annual': annual_leave,
							'x_leave_sick': sick_leave,
							'x_leave_unpaid': leave_unpaid,
							'x_leave_part': partday_leave,
						}
						if paytype:
							_vals2['ref']=paytype
						if pay_id:
							_vals2['x_category_id']=pay_id
							
						#count2+=1
						#_logger.error('date_existsdate_exists22 [ %s ][ %s ]' % (recordid, _vals2))
						if date_exists:
							date_exists.write(_vals2)
							#count2+=1 #just in case parent is deleted....+ creates the duplicate..just in case re-uploaded....[todo warnig]
						else:
							count2+=1
							#_logger.error('analyticanalyticanalytic _vals2[ %s ' % (_vals2))	
							line_id = self.env['account.analytic.line'].create(_vals2)
							#_logger.error('date_existsdate_existsrecordidrecordid [ %s ]line_id[ %s ]paytype[ %s ]pay_id[ %s ]' % (recordid, line_id, paytype, pay_id))
							lines.append(line_id.id)
							#if line_id:
							#	lines.append(line_id.id)
							#else:	
							
				'''
				if count2>0:
					_vals = {
						'name': now2,
						'date': today,
						#'date_start': dt1,
						#'date_end': dt2,
						'state': 'draft',
					}
					if not invalid:	
						if dt1:
							_vals['date_start']=dt1
						if dt2:
							_vals['date_end']=dt2
					if employee_id:
						_vals['employee_id']=employee_id
						
					batch_id = self.env['hr.timesheet.batch'].create(_vals)
					#_logger.error('batch_idbatch_idbatch_id22 _vals[ %s ][ %s ]' % (_vals, batch_id))
					for _id in lines:	
						sql="update account_analytic_line set x_batch_id='%s' where id='%s'" % (batch_id.id, _id)	 
						self._cr.execute(sql)
					lines=[]
					count2=0'''
			if len(none_arr)>0:	
				#str1="Total %s timesheet record/s found.\n\n%s employee's timesheet/s are valid.\n"	%(tot_records, len(emp_arr))
				#if len(none_arr)>0:
				str1=""
				str1+="Below %s employee/s have mismatch card name/s found or do not have their employee card setup in the system.\n" % (len(none_arr))
				#count1=0
				sn=1
				for emp in none_arr:
					str1+="%s. %s  " % (sn, emp)
					str1+="\n"
					#if count1>5:
					#	#str1+="\n"
					#	count1=0
					#count1+=1
					sn+=1
				#raise UserError(_("%s" % (str1)))
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				autime=self.env['account.fiscalyear'].get_au_datetime(now)
				_vals = {
					'name': "Import Error %s" %(autime),
					'date': today,
					'date_start': today,
					'date_end': today,
					'state': 'draft',
				}
				#if employee_id:
				_vals['description']=str1
					
				batch_id = self.env['hr.timesheet.batch'].create(_vals)
				#_logger.error('action_import_xls:, count1count1[ %s ][ %s ]' % (count1,len(df.index)))
				
	 
					
	@api.multi
	def action_import_new(self):
		if not self.csv_file:
			raise UserError(_("Warning! no file to upload. Please select a file and try again."))
		if self.xls_dcs:
			path1 	 =  os.path.normpath("/var/log/odoo")
			dt		 =  datetime.datetime.today().strftime("%Y-%m-%d")
			path1	+= "/timesheet%s.xlsx" % (dt)
			if self.csv_file:
				path1	+= ""
				str1	=base64.b64decode(self.csv_file)
				f=open(path1,'wb')
				f.write(str1)
				f.close()
				
			return self._import_xls_file(path1)
		else:
			path1 	 =  os.path.normpath("/var/log/odoo")
			dt		 =  datetime.datetime.today().strftime("%Y-%m-%d")
			path1	+= "/timesheet%s.txt" % (dt)
			if self.csv_file:
				path1	+= ""
				str1	=base64.b64decode(self.csv_file)
				f=open(path1,'wb')
				f.write(str1)
				f.close()
			#else:
			#	raise UserError(_("Warning! no file to upload. Please select a file and try again.")
			return self._import_jetstream_timesheet(path1)
		#return self._import_xls_payslip(path1)
		
	def get_paycategory(self, txt):
		category_id=0
		pc_amt=0
		amt_type=0
		factor_type='hrs'
		xfactor=1
		sql="select id,pc_amt,amt_type,factor_type,factor_default from hr_pay_category where mapping_txt='%s' limit 1" % (txt.strip())
		self._cr.execute(sql)
		rows1 	= self._cr.dictfetchall()
		for row1 in rows1:
			category_id	=row1['id']
			pc_amt		=row1['pc_amt']
			amt_type	=row1['amt_type']
			xfactor		=row1['factor_default']
			factor_type	=row1['factor_type']
		return {'category_id':category_id, 'pc_amt':pc_amt, 'amt_type':amt_type, 'xfactor': xfactor, 'factor_type': factor_type}
	
		
	def _import_jetstream_timesheetxx(self, path1):
		c_lname=0
		c_fname=1 
		c_paytype=2 
		c_job=3 
		c_date=7
		c_units=8 
		c_empid=9
		#user_id=1
		project = self.env['project.project'].search([('id','>',0)], limit=1)
		emp_arr=[]
		line_arr=[]
		project_id=project.id
		account_id=project.analytic_account_id.id
		user_id=self.env.user.id
		company_id=self.env.user.company_id.id
		obj_time=self.env['hr.employee.timesheet']
		today = datetime.date.today()
		
		with open(path1) as f:
			reader = csv.reader(f, delimiter="\t")
			d = list(reader)
			#print d[0][2] # 248
			count1=0
			xfactor=1
			for item in d:
				hrs=item[c_units]
				date=item[c_date]
				number=item[c_empid]
				paytype=item[c_paytype]
				employee_id, skip_ts_import, payslip_enable = self.get_emp_bynumber(number)
				#category_id, pc_amt, amt_type=self.get_paycategory(paytype)
				#xfactor=1
				paycat 		= obj_import.get_paycategory(paytype)
				category_id	= paycat['category_id']
				pc_amt		= paycat['pc_amt']
				amt_type	= paycat['amt_type']
				xfactor		= paycat['xfactor']
				factor_type	= paycat['factor_type']
				#dt=parser.parse(date)
				if skip_ts_import==False and payslip_enable==True:
					if hrs and employee_id and date:
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
							_vals2['factor_type']= factor_type
							#_logger.error('obj_timeobj_time _vals2[ %s ] ' % (_vals2))	
							line = obj_time.create(_vals2)
							line_arr.append(line)
			for employee_id in emp_arr:
				now2 = "%s" %  (date)
				_vals = {
						'name': now2,
						'date': today,
						#s'date_start': dt1,
						#'date_end': dt2,
						'state': 'draft',
					}
				
				if employee_id:
					_vals['employee_id']=employee_id
					
				#_logger.error('batch_idbatch_idbatch_id11000 _vals[ %s ] ' % (_vals))	
				batch_id = self.env['hr.timesheet.batch'].create(_vals)
				for line in line_arr:
					if line.employee_id.id==employee_id:
						sql="update hr_employee_timesheet set batch_id='%s' where id='%s'" % (batch_id.id, line.id)	 
						self._cr.execute(sql)
						#_logger.error('hr_employee_timesheethr_employee_timesheet sql[ %s ]' % (sql))		
		return True
		
	@api.multi
	def action_import_csv(self):
		var1=""
		str1=""
		count1=0
		if self.csv_file:
			#_logger.debug('_update_reference_fields for action_importaction_import: %s ', self.csv_file)
			#var1=1
			#var1=self.csv_file.decode('utf-8')
			rows=[]
			dt1=None
			dt2=None
			var1=base64.decodestring(self.csv_file).decode('utf-8')
			f = StringIO(str(var1))
			reader = csv.reader(f, delimiter=',')
			for row in reader:
				#str1+="["+str(row)+"]<br>"
				count1+=1
				if count1>1:
					if count1==2:
						dt1=row[2]
					dt2=row[2]	
					rows.append(row)
					#staff id,name,date,actual 1,actual 2,round 1,round 2,breaks ,unpaid,paid,special pay,comment print(row[0],row[1],row[2],)
			#_logger.error('_batchbatch_import:_vals[ %s ][ %s ]',batch_id, _vals)
			project = self.env['project.project'].search([('id','>',0)], limit=1)
			#if project:		
			if dt1 and dt2 and project:		
				today = datetime.date.today()
				now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				now2=self.env['account.fiscalyear'].get_au_datetime(now)
				#_logger.error('_batchbatch_import1111 now[ %s ]now2[ %s ]',now, now2)
				
				lines=[]
				project_id=project.id
				account_id=project.analytic_account_id.id
				count2=0	
				for row in rows:	
					staffid	=row[0]
					name	=row[1]
					date	=row[2]
					act1	=row[3]
					act2	=row[4]
					round1	=row[5]
					round2	=row[6]
					breaks	=row[7]
					unpaid	=row[8]
					paid	=row[9]
					specialpay	=row[10]
					comments	=row[11]
					company_id	=self.env.user.company_id.id
					user_id		=self.env.user.id
					employee_id	=staffid
					unit_amount	=paid
					#'partner_id': partner_id,
					today_dt 	= dateutil.parser.parse(str(date))
					today_dt	=str(today_dt)[:10]
					sql="select id from account_analytic_line where employee_id='%s' and date='%s'" % (employee_id, today_dt)	 
					self._cr.execute(sql)
					rows1 = self._cr.fetchall()
					if len(rows1)>0:
						recordid	= rows1[0][0]
						date_exists = self.env['account.analytic.line'].browse(recordid)
						#date_exists = self.env['account.analytic.line'].search([('employee_id','=',employee_id),('date','=',today_dt)])	
					else:
						date_exists=False
					#_logger.error('date_existsdate_exists22 date[ %s ]date_exists[ %s ][ %s ]',today_dt, date_exists, sql)
					
					_vals2 = {
						'name': now2,
						'date': date,
						'user_id': user_id,
						'employee_id': employee_id,
						'account_id': account_id,
						'project_id': project_id,
						'company_id':company_id,
						'unit_amount':unit_amount,
						'x_act_start': act1,
						'x_act_stop': act2,
						'x_round_start': round1,
						'x_round_stop': round2,
						'x_breaks': breaks,
						'x_unpaid': unpaid,
						'x_paid': paid,
						'x_special_pay': specialpay,
						#'x_batch_id':batch_id.id,
					}
					
					if date_exists:
						date_exists.write(_vals2)
					else:
						count2+=1
						
						line_id = self.env['account.analytic.line'].create(_vals2)
						lines.append(line_id.id)
						
				if count2>0:
					_vals = {
						'name': now2,
						'date': today,
						'date_start': dt1,
						'date_end': dt2,
						'state': 'draft',
					}
					
					batch_id = self.env['hr.timesheet.batch'].create(_vals)
					for _id in lines:	
						sql="update account_analytic_line set x_batch_id='%s' where id='%s'" % (batch_id.id, _id)	 
						self._cr.execute(sql)
						
		#raise UserError(_("Warning if needed. [%s] [%s]count1[%s]" %  (count2, str1, count1)))
	
	def _import_jetstream_timesheet(self, path1):
		c_lname=0
		c_fname=1 
		c_paytype=2 
		c_job=3 
		c_date=7
		c_units=8 
		c_empid=9
		#user_id=1
		project = self.env['project.project'].search([('id','>',0)], limit=1)
		emp_arr=[]
		line_arr=[]
		project_id=project.id
		account_id=project.analytic_account_id.id
		user_id=self.env.user.id
		company_id=self.env.user.company_id.id
		obj_time=self.env['hr.employee.timesheet']
		today = datetime.date.today()
		
		with open(path1) as f:
			reader = csv.reader(f, delimiter="\t")
			d = list(reader)
			
			count1=0
			xfactor=1
			for item in d:
				hrs=item[c_units]
				date=item[c_date]
				number=item[c_empid]
				paytype=item[c_paytype]
				employee_id, skip_ts_import, payslip_enable = self.get_emp_bynumber(number)
				#category_id, pc_amt, amt_type=self.get_paycategory(paytype)
				#xfactor=1
				paycat 		= obj_import.get_paycategory(paytype)
				category_id	= paycat['category_id']
				pc_amt		= paycat['pc_amt']
				amt_type	= paycat['amt_type']
				xfactor		= paycat['xfactor']
				factor_type	= paycat['factor_type']
				#dt=parser.parse(date)
				if skip_ts_import==False and payslip_enable==True:
					if hrs and employee_id and date:
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
							_vals2['factor_type']= factor_type
							#_logger.error('obj_timeobj_time _vals2[ %s ] ' % (_vals2))	
							line = obj_time.create(_vals2)
							line_arr.append(line)
						
			for employee_id in emp_arr:
				now2 = "%s" %  (date)
				_vals = {
						'name': now2,
						'date': today,
						#s'date_start': dt1,
						#'date_end': dt2,
						'state': 'draft',
					}
				
				if employee_id:
					_vals['employee_id']=employee_id
					
				#_logger.error('batch_idbatch_idbatch_id11000 _vals[ %s ] ' % (_vals))	
				batch_id = self.env['hr.timesheet.batch'].create(_vals)
				for line in line_arr:
					if line.employee_id.id==employee_id:
						sql="update hr_employee_timesheet set batch_id='%s' where id='%s'" % (batch_id.id, line.id)	 
						self._cr.execute(sql)
						#_logger.error('hr_employee_timesheethr_employee_timesheet sql[ %s ]' % (sql))		
		return True
		
			