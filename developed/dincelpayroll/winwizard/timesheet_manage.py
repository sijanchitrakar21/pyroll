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
from odoo.addons.dincelpayroll.models import dincelpayroll_vars 

#import pyexcel as pe 
#_logger = logging.getLogger('hr.timesheet.import')
_logger = logging.getLogger(__name__)
class TimesheetManage(models.TransientModel):
	_name = 'hr.timesheet.manage'
	_description = 'Manage timesheet'
	date = fields.Date('Date')
	date_from = fields.Date('Date From')
	date_to = fields.Date('Date To')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	import_id = fields.Many2one('hr.timesheet.import.copy', string='Import')
	line_ids = fields.One2many('hr.timesheet.manage.line', 'manage_id', 'Lines')
	
	@api.onchange('import_id')
	def onchange_import(self):
		values={}
		if self.import_id:
			items=[]
			for line in self.import_id.day_ids:
				dt=parser.parse(line.date)
				name 	= "%s" %  (dt.strftime("%a"))
				item={'date':line.date,
					'name':name
					}
				items.append(item)
			values['line_ids']=items
		return {'value':values} 
		
class TimesheetManageLine(models.TransientModel):
	_name="hr.timesheet.manage.line"
	manage_id= fields.Many2one('hr.timesheet.manage', string='Timesheet',ondelete='cascade',)
	employee_id 	= fields.Many2one('hr.employee', string='Employee')
	name 	= fields.Char('Day')
	date 		= fields.Date('Date')
	time_in		= fields.Char("Time In")
	time_out	= fields.Char("Time Out")
	paid_in		= fields.Char("Paid In")
	paid_out	= fields.Char("Paid Out")
	paid_hours	= fields.Float("Paid Hrs")
	leave_id	= fields.Many2one('hr.holidays.status', string='Leave')
	time 		= fields.Char("Time Actual")
	time_adjust	= fields.Char("Time Paid (adjusted)")
	in_out		= fields.Selection(dincelpayroll_vars.TS_INOUT_OPTIONS,string="In/Out")
	
	
	