import babel.messages.pofile
import base64
import datetime
import functools
import glob
import hashlib
import imghdr
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile
import time
import zlib

import werkzeug
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict
from werkzeug.urls import url_decode, iri_to_uri
from xml.etree import ElementTree


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_resource_path
from odoo.tools import crop_image, topological_sort, html_escape, pycompat
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlwt, file_open
from odoo.tools.safe_eval import safe_eval
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError
from odoo.models import check_method_name
from odoo.service import db

_logger = logging.getLogger(__name__)

#script, filename = argv

#txt = open(filename)

#print "Here's your file %r:" % filename
#print txt.read()

class MyController(http.Controller):
	
	
	@http.route('/web/binary/download_file', type='http', auth="public")
	def download_file(self, model, field, id, path, filename):

		 
		Model = request.registry[model]
		cr, uid, context = request.cr, request.uid, request.context
		#_logger.error('download_filedownload_file idsids[ %s ]data[ %s ]filename[%s]' %  (id, path, filename))
		if path and filename:
			#filecontent = base64.b64decode(path + "/" + filename)
			temp_path=path + "/" + filename
			
			if temp_path.lower().endswith(('.pdf')):
				f=open(temp_path,'rb')
				filecontent = f.read()
				pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(filecontent)),('Content-Disposition', content_disposition(filename))]
				return request.make_response(filecontent, headers=pdfhttpheaders)
			else:	
				#filecontent = base64.b64encode(_data)
				f=open(temp_path,'r')
				filecontent = f.read()
				return request.make_response(filecontent,
								[('Content-Type', 'application/octet-stream'),
								('Content-Disposition', content_disposition(filename))])
			