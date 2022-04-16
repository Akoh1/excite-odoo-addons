# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

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
    fhfl_sequence = fields.Char('Squence ID', readonly=True)
    crm_sale = fields.Many2one('installment.schedule')

    # api.onchange('state')
    # def _onchange_fhfl_sequence(self):
    #     for rec in self:
    #         if rec.state == 'posted':
    #             if rec.fhfl_sequence == '/':
    #                 sequence_id = self.env['ir.sequence'].search([('code', '=', 'fhfl.journal.sequence')])
    #                 sequence_pool = self.env['ir.sequence']
    #                 application_no = sequence_pool.sudo().get_id(sequence_id.id)
    #                 rec.fhfl_sequence = application_no

    def button_cancel(self):
        res = super(fhflAccountInvoice, self).button_cancel()
        for rec in self:
            rec.investment_id.appraisal_fee_status = 'draft'
            if rec.investment_id.appraisal_fee_status == 'draft':
                # rec.investment_id = False
                rec.investment_id.invoice_ids = False
            # rec.investment_id.state = '2_mcc_one'
        return res

    # def action_post(self):
    #     res = super(fhflAccountInvoice, self).action_post()
    #     _logger.info("Fhfl sequence")
    #     for rec in self:
    #         # if rec.state == 'posted':
    #         _logger.info("sequence posted")
    #         _logger.info("fhfl_sequence: %s", rec.fhfl_sequence)
    #         if rec.fhfl_sequence is False or '/' and rec.move_type == 'entry':
    #             _logger.info("Fhfl sequence is here")
    #                 # sequence_id = self.env['ir.sequence'].search([('code', '=', 'fhfl.journal.sequence')])
    #                 # sequence_pool = self.env['ir.sequence']
    #                 # application_no = sequence_pool.sudo().get_id(sequence_id.id)
    #             number = self.env['ir.sequence'].next_by_code('fhfl.journal.sequence') or 'New'
    #             _logger.info("sequence: %s", number)
    #             rec.fhfl_sequence = number
    #                 # self.write({'application_no': application_no})
    #         # else:
    #         #     rec.fhfl_sequence = '/'
    #     return res

    def _post(self, soft=True):
        res = super(fhflAccountInvoice, self)._post()
        _logger.info("Fhfl sequence")
        for rec in self:
            # if rec.state == 'posted':
            _logger.info("sequence posted")
            _logger.info("fhfl_sequence: %s", rec.fhfl_sequence)
            if rec.fhfl_sequence is False or '/' and rec.move_type == 'entry':
                _logger.info("Fhfl sequence is here")
                    # sequence_id = self.env['ir.sequence'].search([('code', '=', 'fhfl.journal.sequence')])
                    # sequence_pool = self.env['ir.sequence']
                    # application_no = sequence_pool.sudo().get_id(sequence_id.id)
                number = self.env['ir.sequence'].next_by_code('fhfl.journal.sequence') or 'New'
                _logger.info("sequence: %s", number)
                rec.fhfl_sequence = number
                    # self.write({'application_no': application_no})
            # else:
            #     rec.fhfl_sequence = '/'

        return res

    # @api.depends('state')
    # def _compute_fhfl_sequence(self):
    #     _logger.info("Fhfl sequence")
    #     for rec in self:
    #         if rec.state == 'posted':
    #             _logger.info("sequence posted")
    #             _logger.info("fhfl_sequence: %s", rec.fhfl_sequence)
    #             if rec.fhfl_sequence is False:
    #                 _logger.info("Fhfl sequence is here")
    #                 # sequence_id = self.env['ir.sequence'].search([('code', '=', 'fhfl.journal.sequence')])
    #                 # sequence_pool = self.env['ir.sequence']
    #                 # application_no = sequence_pool.sudo().get_id(sequence_id.id)
    #                 number = self.env['ir.sequence'].get('fhfl.journal.sequence') or '/'
    #                 _logger.info("sequence: %s", number)
    #                 rec.fhfl_sequence = number
    #                 # self.write({'application_no': application_no})
    #         else:
    #             rec.fhfl_sequence = '/'

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
                'crm_sale': self.crm_sale.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.model_create_multi
    def create(self, vals_list):
        res = super(fhflAccountInvoice, self).create(vals_list)
        today = datetime.date.today()
        group_backdate = self.env.user.\
            has_group('fhfl_sales_custom.group_accounting_allow_backdate')

        _logger.info("Account Move Vals list: %s", vals_list)
        if not group_backdate:
            _logger.info("No Group Backdate")
            for vals in vals_list:
                # date = vals['date']
                if 'date' in vals:
                    date = datetime.datetime.strptime(vals['date'], '%Y-%m-%d').date() if type(vals['date']) is str else \
                        vals['date']
                    _logger.info("Date: %s, Today: %s", date, today)
                    if date and date < today:
                        raise UserError(_("You cannot post into the past. Please contact the Head of Accounts"))
        return res


class FhflAccountPayment(models.Model):
    _inherit = "account.payment"

    remita_rr_num = fields.Char(string="Remita RR Number")

