# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class FhflAppraisalAccountCompany(models.Model):
    _inherit = "res.company"

    appraisal_account = fields.Many2one('account.account', readonly=False,
    								string="Account to be used when generating an Appraisal Invoice")


class FhflAppraisalAccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appraisal_account = fields.Many2one(related="company_id.appraisal_account", readonly=False,
                                string="Account to be used when generating an Appraisal Invoice")