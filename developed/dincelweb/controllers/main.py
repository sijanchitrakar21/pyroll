# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json
import lxml
import requests
import werkzeug.exceptions
import werkzeug.urls
import werkzeug.wrappers

from datetime import datetime

from odoo import http, modules, SUPERUSER_ID, tools, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.web.controllers.main import binary_content
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.http import request


class WebsiteStaffs(http.Controller):
	#_post_per_page = 10
	#_user_per_page = 30

	@http.route(['/staff'], type='http', auth="public", website=True)
	def staff(self, **kwargs):
		staffs = request.env['dincelweb.member'].search([])
		return request.render("dincelweb.staff_all", {'staffs': staffs})
		
	@http.route([
		'''/staff/<model("dincelweb.member"):member>'''],
		type='http', auth="public", website=True)
	def member(self, member, search=None, **kw):
		user = request.env.user
		member = request.env['dincelweb.member']
		domain = [('active', '=', True)]
		pager_url = "/staff/%s" % (member.id)
		pager_args = {}

		values = {
			'staffs': member,
			}
		
		return request.render('dincelweb.staff_all', values)	