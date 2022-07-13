# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from time import gmtime, strftime
from odoo.exceptions import UserError
import math
import logging
_logger = logging.getLogger(__name__)
class DincelWebMember(models.Model):
	_name = 'dincelweb.member'
	_description="Web member"
	name = fields.Char('Name')
	notes = fields.Char('Notes')
	username = fields.Char('Username')
	password = fields.Char('Password')
	employee_id = fields.Many2one('hr.employee', string='Employee')
	active = fields.Boolean('Active', default=True)
	
	@api.model
	def create(self, vals):
		if vals.get('username'):
			items = self.env['dincelweb.member'].search([('username', '=', vals.get('username'))])
			if len(items)>0:
				raise UserError(("Username already exists!"))
		record = super(DincelWebMember, self.create(vals))
		return record
	@api.multi
	def write(self, values):
		record = super(DincelWebMember, self).write(values)
		copy 	= self.browse(self.id)
		items = self.env['dincelweb.member'].search([('username', '=', copy.username)])
		for item in items:
			#if len(items)>0:
			if item.id != self.id:
				raise UserError(("Username already exists [%s]!" % (copy.username)))
		return record	