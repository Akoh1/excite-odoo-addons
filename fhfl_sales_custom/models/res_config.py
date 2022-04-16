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
    lms_journal = fields.Many2one('account.journal', string="LMS Journal", readonly=False)
    loan_account = fields.Many2one('account.account', readonly=False,
                                    string="Debit Account to be used when generating a Journal Entry from LMS")
    disburse_account = fields.Many2one('account.account', readonly=False,
                                    string="Credit Account to be used when generating a Journal Entry from LMS")


class FhflAppraisalAccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appraisal_account = fields.Many2one(related="company_id.appraisal_account", readonly=False,
                                string="Account to be used when generating an Appraisal Invoice")
    lms_journal = fields.Many2one(related="company_id.lms_journal", string="LMS Journal", readonly=False)
    loan_account = fields.Many2one(related="company_id.loan_account", readonly=False,
                                    string="Debit Account to be used when generating a Journal Entry from LMS")
    disburse_account = fields.Many2one(related="company_id.disburse_account", readonly=False,
                                    string="Credit Account to be used when generating a Journal Entry from LMS")