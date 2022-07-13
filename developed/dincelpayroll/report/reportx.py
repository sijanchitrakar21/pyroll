# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.osv import osv
import logging
#import base64
#import csv
#from io import StringIO
from datetime import date, datetime, timedelta
import datetime as dt
#from datetime import date
#from datetime import datetime
#import datetime
import dateutil
from dateutil import parser
#import pyexcel as pe

_logger = logging.getLogger(__name__)

class PayrollReport(models.TransientModel):
	_name = 'hr.payroll.report'
	_description = 'Payroll Report'
	date = fields.Date('Date')
	
	def _build_comparison_context(self, data):
		result = {}
		
		return result

	@api.multi
	def check_payroll_report(self):
		res = super(PayrollReport, self).check_payroll_report()
		data = {}
		data['form'] = self.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
		for field in ['account_report_id']:
			if isinstance(data['form'][field], tuple):
				data['form'][field] = data['form'][field][0]
		comparison_context = self._build_comparison_context(data)
		res['data']['form']['comparison_context'] = comparison_context
		return res
	def _print_report(self, data):
		#data['form'].update(self.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move'])[0])
		return self.env.ref('account.action_report_financial').report_action(self, data=data, config=False)	