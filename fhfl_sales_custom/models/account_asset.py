# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class fhflAccountAssetLocation(models.Model):
    _name = 'asset.location'
    _description = "Asset Location"

    name = fields.Char()


class fhflAccountAsset(models.Model):
    _inherit = 'account.asset'

    serial_num = fields.Char('Serial Number')
    asset_tag = fields.Char()
    asset_status = fields.Selection([
        ('unallocated', 'Unallocated'),
        ('allocated', 'Allocated'),
        ('damaged', 'Damaged'),
        ('disposed', 'Disposed'),
        ('lost', 'Lost'),
    ], default='unallocated', copy=False, index=True, tracking=True)
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one(related='employee_id.department_id')
    location = fields.Many2one('asset.location')
    check_allocated = fields.Boolean(compute="_compute_allocated")

    @api.depends('asset_status')
    def _compute_allocated(self):
    	for rec in self:
    		rec.check_allocated = rec.asset_status == 'allocated'
