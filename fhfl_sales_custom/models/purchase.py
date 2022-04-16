# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class fhflPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('cfo_approve', 'CFO Approval'), ('purchase',)],
                             ondelete={'draft': 'set default'}, default='draft')

    def button_cfo_approve(self):
        _logger.info("CFO approve")
        for rec in self:
            rec.state = 'cfo_approve'

    def button_confirm(self):
        res = super(fhflPurchaseOrder, self).button_confirm()
        for rec in self:
            if rec.state == 'cfo_approve':
                rec.state = 'purchase'
        return res