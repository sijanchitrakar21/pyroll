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
import openpyxl
#import pyexcel as pe
#_logger = logging.getLogger('hr.timesheet.import')
_logger = logging.getLogger(__name__)
class TimesheetImportXls(models.TransientModel):
	_name = 'hr.timesheet.import.xls'
	_description = 'Import timesheet xls'

	xls_file = fields.Binary('Xls file')

	@api.multi
	def action_import_xls(self):
		var1=""
		str1=""
		count1=0
		if self.xls_file:
			#_logger.debug('_update_reference_fields for action_importaction_import: %s ', self.csv_file)
			#var1=1
			#var1=self.csv_file.decode('utf-8')
			rows=[]
			dt1=None
			dt2=None
			
			with open('var/tmp/csv_file.xls','wb+') as f:
				f.write(base64.b64decode(self.file))
				
			var1=base64.decodestring(self.xls_file).decode('utf-8')
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
					company_id=self.env.user.company_id.id
					user_id=self.env.user.id
					employee_id=staffid
					unit_amount=paid
					#'partner_id': partner_id,
					today_dt = dateutil.parser.parse(str(date))
					today_dt=str(today_dt)[:10]
					sql="select id from account_analytic_line where employee_id='%s' and date='%s'" % (employee_id, today_dt)	 
					self._cr.execute(sql)
					rows1 = self._cr.fetchall()
					if len(rows1)>0:
						recordid=rows1[0][0]
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
