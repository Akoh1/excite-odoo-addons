# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class FhflStockPicking(models.Model):
    _inherit = 'stock.picking'