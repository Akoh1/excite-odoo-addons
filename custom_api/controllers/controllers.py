# -*- coding: utf-8 -*-
import ast
import functools
import json
import logging
import re

from odoo import http
# from odoo.addons.restful.common import (extract_arguments, invalid_response,
#                                         valid_response)
from odoo.exceptions import AccessError
from odoo.http import request, route

_logger = logging.getLogger(__name__)

class APIController(http.Controller):

	@route('/custom/api/customers/', type="http", auth="none", methods=["POST"], csrf=False)
	def post(self, id=None, **payload):
		data = request.httprequest.data.decode()
		# payload = json.loads(**payload)
		# datas = request
		_logger.info("Customers: %s", **payload)
		_logger.info("Customers: %s", data)
		return data





