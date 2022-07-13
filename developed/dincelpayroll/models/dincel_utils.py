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
from . import dincelpayroll_vars 
from odoo.exceptions import UserError
#import dateparser
#import datetime
import time
import logging
_logger = logging.getLogger(__name__)

class DincelUtils(models.Model):
	_name = 'dincel.utils'
	_description = 'Dincel Utils'		
	
	def download_file(self, model, idid, title, save_path, fname):
		return {
				'name': title,
				'res_model': 'ir.actions.act_url',
				'type' : 'ir.actions.act_url',
				'url': '/web/binary/download_file?model=%s&field=datas&id=%s&path=%s&filename=%s' % (model, str(idid),save_path,fname),
				'context': {}}		
		
	def write_file(self, save_path, fname, txt):
		try:
			temp_path=save_path+"/"+fname
			f=open(temp_path,'w')
			f.write(txt)
			f.close()
			return True
		except ValueError as ex:
			_logger.error('DincelUtils.write_file ex[ %s ] save_path[ %s ] fname[ %s ] txt[%s]' % (ex, save_path,fname, txt))
			pass	
		return False