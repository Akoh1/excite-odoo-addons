# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class fhflAccountInvoice(models.Model):
    _inherit = 'account.move'

    sales_type = fields.Selection([
        ('outright', 'Outright'),
        ('installment', 'Installment'),
        ('mortgage', 'Mortgage'),
    ], string='Sales Order Type', copy=False, index=True, tracking=True)
    remita_rr_num = fields.Char(string="Remita RR Number")
    investment_id = fields.Many2one('crm.investment')

    # @api.onchange('payment_state', 'state')
    # def _onchange_investment_appraisal_state(self):
    #     _logger.info("Changing Appraisal state")
    #     for rec in self:
    #         if rec.payment_state is 'paid' and rec.state is 'posted' and rec.investment_id.id:
    #             crm_invest = self.env['crm.investment'].\
    #                 search([('id', '=', rec.investment_id)])
    #             crm_invest.write({
    #                     'appraisal_fee_status': 'paid'
    #                 })

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''

        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'remita_rr_num': self.remita_rr_num,
                'investment_id': self.investment_id.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class FhflAccountPayment(models.Model):
    _inherit = "account.payment"

    remita_rr_num = fields.Char(string="Remita RR Number")

