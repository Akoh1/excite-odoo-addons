# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class FhflAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    remita_rr_num = fields.Char(string="Remita RR Number",
                                compute='_compute_remita_rr_num')

    @api.model
    def _get_remita_rr_num(self, batch_result):
        ''' Helper to compute the communication based on the batch.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                A string representing a communication to be set on payment.
        '''
        rr_num = set(line.move_id.remita_rr_num or '' for line in batch_result['lines'])
        _logger.info("Payment register RR num: %s", rr_num)
        # if not rr_num:
        #     return None
        return ' '.join(sorted(rr_num))
    #
    @api.depends('can_edit_wizard')
    def _compute_remita_rr_num(self):
        # The communication can't be computed in '_compute_from_lines' because
        # it's a compute editable field and then, should be computed in a separated method.
        for wizard in self:
            batches = wizard._get_batches()
            _logger.info("Batches: %s", batches)
            wizard.remita_rr_num = wizard._get_remita_rr_num(batches[0])
            # if wizard.can_edit_wizard:
            #     batches = wizard._get_batches()
            #     wizard.communication = wizard._get_batch_communication(batches[0])
            # else:
            #     wizard.communication = False

    def _create_payment_vals_from_wizard(self):
        res = super(FhflAccountPaymentRegister, self). \
            _create_payment_vals_from_wizard()
        res['remita_rr_num'] = self.remita_rr_num
        return res

    def _create_payments(self):
        res = super(FhflAccountPaymentRegister, self). \
            _create_payments()

        _logger.info("Investment context: %s", self._context.get('investment_id'))
        _logger.info("Crm Sale context: %s", self._context.get('crm_sale'))
        invest_id = self._context.get('investment_id')
        crm_sale = self._context.get('crm_sale')
        if crm_sale:
            install_schedule = self.env['installment.schedule'].\
                        search([('id', '=', crm_sale)])
            if install_schedule:
                _logger.info("There is installment schedule")
                install_schedule.write({
                        'state': 'paid'
                    })
        if invest_id:
            crm_invest = self.env['crm.investment'].\
                        search([('id', '=', invest_id)])
            if crm_invest:
                _logger.info("There is crm invest")
                crm_invest.write({
                        'appraisal_fee_status': 'paid'
                    })
        return res