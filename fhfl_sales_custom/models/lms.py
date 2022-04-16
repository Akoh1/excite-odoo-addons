# -*- coding: utf-8 -*-
import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LoanSchedule(models.Model):
    _name = 'loan.schedule'
    _description = 'Loan Schedule'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    install_num = fields.Char('Installment Number')
    due_date = fields.Date()
    event_type = fields.Char()
    principal_amount = fields.Float()
    intrest_amount = fields.Float()
    insurance_premium = fields.Char()
    loan_fees = fields.Float()
    late_fees = fields.Float()
    total_amount = fields.Float()
    service_amount = fields.Float()
    outstanding_amount = fields.Float()
    serviced_date = fields.Date()
    days_late = fields.Integer()


class LoanJournal(models.Model):
    _name = 'loan.journal'
    _description = 'Loan Journals'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _rec_name = 'application_id'

    journal_id = fields.Many2one('account.journal', readonly=True)
    transaction_date = fields.Date()
    value_date = fields.Date()
    account_num = fields.Char('Account Number')
    contra_acct_num = fields.Char('Contra Account Number')
    product_type = fields.Char()
    account_title = fields.Char()
    transaction_type = fields.Char()
    transaction_ref = fields.Char('Transaction Reference')
    loan_status = fields.Selection([
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ], copy=False, index=True, tracking=True)
    currency = fields.Char()
    transaction_amount = fields.Float()
    # transaction_date = fields.Datetime()
    transaction_timestamp = fields.Datetime()
    status = fields.Char()
    customer_id = fields.Many2one('res.partner')
    application_id = fields.Char()
    # company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
    #                              index=True, default=lambda self: self.env.company,
    #                              help="Company related to this journal")

    def create_journal_entry(self):
        _logger.info("Create Journal Entry")
        currency_id = self.env.ref('base.main_company').currency_id
        loan_account = self.env.company.loan_account
        disburse_account = self.env.company.disburse_account
        for rec in self:
            entry_vals = {
                'ref': rec.application_id or '',
                'move_type': 'entry',
                # 'narration': rec.board_comment,
                'currency_id': currency_id.id,
                'user_id': self.env.user.id,
                # 'invoice_user_id': self.env.user.id,
                # 'team_id': self.team_id.id,
                'partner_id': rec.customer_id.id or None,
                'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
                'journal_id': rec.journal_id.id,  # company comes from the journal
                'date': rec.transaction_date,
                'company_id': self.env.user.company_id.id,

                'line_ids': [(0, 0, {
                    # 'move_id': moves.id,
                    'account_id': loan_account.id,
                    'partner_id': rec.customer_id.id or None,
                    'name': 'Loan',
                    'debit': rec.transaction_amount
                  }),
                  (0, 0, {
                    # 'move_id': moves.id,
                    'account_id': disburse_account.id,
                    'partner_id': rec.customer_id.id or None,
                    'name': 'Disbursement',
                    'credit': rec.transaction_amount
                })],
              
            }

        
            moves = self.env['account.move'].with_context(default_move_type='entry').create(entry_vals)
            if moves:
              _logger.info("Journal entry Created: %s", moves)
              if moves.line_ids:
                _logger.info("Journal lines created:")

    @api.model_create_multi
    def create(self, vals_list):
        res = super(LoanJournal, self).create(vals_list)
        _logger.info("LMS Journal values: %s", vals_list)
        journal_id = self.env.company.lms_journal
        res.journal_id = journal_id.id
        _logger.info('company journal: %s', journal_id)
        res.create_journal_entry()
        # for vals in vals_list:
        #     vals['journal_id'] = journal_id.id or None
        return res
