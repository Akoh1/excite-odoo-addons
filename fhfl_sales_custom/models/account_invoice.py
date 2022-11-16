# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang

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
    check_line = fields.Boolean(compute="_compute_line_for_balance")

    # @api.onchange('line_ids')
    # def _onchange_line_for_balance(self):
    #     _logger.info("Checking for move lines")

    #     for rec in self:
    #         for line in rec.line_ids:
    #             _logger.info("move lines ids: %s", lines)

    # @api.depends('line_ids')
    # def _compute_line_for_balance(self):
    #     _logger.info("Checking for move lines")

    #     for rec in self:
    #         for line in rec.line_ids:
    #             _logger.info("move lines ids: %s", lines)


    def button_cancel(self):
        res = super(fhflAccountInvoice, self).button_cancel()
        for rec in self:
            rec.investment_id.appraisal_fee_status = 'draft'
            if rec.investment_id.appraisal_fee_status == 'draft':
                # rec.investment_id = False
                rec.investment_id.invoice_ids = False
            # rec.investment_id.state = '2_mcc_one'
        return res


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

    def _get_tax_force_sign(self):
        """ The sign must be forced to a negative sign in case the balance is on credit
            to avoid negatif taxes amount.
            Example - Customer Invoice :
            Fixed Tax  |  unit price  |   discount   |  amount_tax  | amount_total |
            -------------------------------------------------------------------------
                0.67   |      115      |     100%     |    - 0.67    |      0
            -------------------------------------------------------------------------"""
        self.ensure_one()
        return -1 if self.move_type in ('out_invoice', 'in_refund', 'out_receipt', 'in_invoice') else 1

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            purchase = move.line_ids.mapped('purchase_line_id.order_id')
            _logger.info("Move type: %s", move.move_type)

            for line in move.line_ids:
                _logger.info("Lines ids in comoute amount: %s", line)
                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance

                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        # _logger.info("Lines ids payable in comoute amount: %s", line)
                        # _logger.info("Lines ids credit in comoute amount: %s", line.credit)
                        # _logger.info("Lines ids debit in comoute amount: %s", line.debit)
                        # if purchase:
                        #     move_line_ids = self.env['account.move.line'].\
                        #         search([])
                        #     get_move_lines = self.line_ids.filtered(lambda l:
                        #                                             l.account_id.user_type_id.type in ('receivable', 'payable'))
                        #     _logger.info("move line_ids search: %s", get_move_lines)
                        #     # move_line_ids.write({'balance': - total_untaxed})
                        #     _logger.info("Total untaxed: %s", total_untaxed)
                        #     # line.write({
                        #     #     'credit': -total_untaxed,
                        #     #     'debit': 0.0
                        #     #     })
                        #     # line.debit = 0.0
                        #     line.credit = total_untaxed
                        #     if line.credit > 0:
                        #         line.debit = 0
                            
                        #     _logger.info("Lines ids balance in comoute amount: %s", line.credit)
                        #     _logger.info("Lines ids debit in comoute amount: %s", line.debit)
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            _logger.info("Total curr or total: %s or %s", total_currency, total)
            
            move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            if move.move_type == 'in_invoice':
                move.amount_total = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed) + abs(total_tax_currency or total_tax)
                move.amount_total_signed = abs(total_untaxed) \
                    if move.move_type == 'entry' else -total_untaxed

            currency = len(currencies) == 1 and currencies or move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':

                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search([('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped('line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state


    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group(self):
        for move in self:

            # Not working on something else than invoices.
            if not move.is_invoice(include_receipts=True):
                move.amount_by_group = []
                continue

            balance_multiplicator = -1 if move.is_inbound() else 1

            tax_lines = move.line_ids.filtered('tax_line_id')
            base_lines = move.line_ids.filtered('tax_ids')
            # _logger.info("Tax lines: %s", tax_lines)
            # _logger.info("Base lines: %s", base_lines)

            tax_group_mapping = defaultdict(lambda: {
                'base_lines': set(),
                'base_amount': 0.0,
                'tax_amount': 0.0,
            })

            # Compute base amounts.
            for base_line in base_lines:
                base_amount = balance_multiplicator * (base_line.amount_currency if base_line.currency_id else base_line.balance)

                for tax in base_line.tax_ids.flatten_taxes_hierarchy():

                    if base_line.tax_line_id.tax_group_id == tax.tax_group_id:
                        continue

                    tax_group_vals = tax_group_mapping[tax.tax_group_id]
                    if base_line not in tax_group_vals['base_lines']:
                        tax_group_vals['base_amount'] += base_amount
                        tax_group_vals['base_lines'].add(base_line)

            purchase = move.line_ids.mapped('purchase_line_id.order_id')
            
            # Compute tax amounts.
            for tax_line in tax_lines:
                tax_amount = balance_multiplicator * (tax_line.amount_currency if tax_line.currency_id else tax_line.balance)
                if move.move_type == 'in_invoice':
                    tax_amount = abs(tax_amount)
                tax_group_vals = tax_group_mapping[tax_line.tax_line_id.tax_group_id]
                tax_group_vals['tax_amount'] += tax_amount

            tax_groups = sorted(tax_group_mapping.keys(), key=lambda x: x.sequence)
            amount_by_group = []
            for tax_group in tax_groups:
                tax_group_vals = tax_group_mapping[tax_group]
                _logger.info("Tax group vals: %s", tax_group_vals)
                amount_by_group.append((
                    tax_group.name,
                    tax_group_vals['tax_amount'],
                    tax_group_vals['base_amount'],
                    formatLang(self.env, tax_group_vals['tax_amount'], currency_obj=move.currency_id),
                    formatLang(self.env, tax_group_vals['base_amount'], currency_obj=move.currency_id),
                    len(tax_group_mapping),
                    tax_group.id
                ))
            
            move.amount_by_group = amount_by_group


    def _recompute_tax_lines(self, recompute_tax_base_amount=False):
        """ Compute the dynamic tax lines of the journal entry.
        :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
        """
        self.ensure_one()
        in_draft_mode = self != self._origin

        def _serialize_tax_grouping_key(grouping_dict):
            ''' Serialize the dictionary values to be used in the taxes_map.
            :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
            :return: A string representing the values.
            '''
            return '-'.join(str(v) for v in grouping_dict.values())


        def _compute_base_line_taxes(base_line):
            ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
            amount_currency & balance could not be the same as the expected currency rate.
            The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
            :param base_line:   The account.move.line owning the taxes.
            :return:            The result of the compute_all method.
            '''
            move = base_line.move_id

            if move.is_invoice(include_receipts=True):
                handle_price_include = True
                sign = -1 if move.is_inbound() else 1
                quantity = base_line.quantity
                is_refund = move.move_type in ('out_refund', 'in_refund')
                price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
            else:
                handle_price_include = False
                quantity = 1.0
                tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
                is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
                price_unit_wo_discount = base_line.amount_currency

            balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
                price_unit_wo_discount,
                currency=base_line.currency_id,
                quantity=quantity,
                product=base_line.product_id,
                partner=base_line.partner_id,
                is_refund=is_refund,
                handle_price_include=handle_price_include,
            )

            if move.move_type == 'entry':
                repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
                repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
                tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
                if tags_need_inversion:
                    balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
                    for tax_res in balance_taxes_res['taxes']:
                        tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

            return balance_taxes_res

        taxes_map = {}

        # ==== Add tax lines ====
        to_remove = self.env['account.move.line']
        for line in self.line_ids.filtered('tax_repartition_line_id'):
            grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
            grouping_key = _serialize_tax_grouping_key(grouping_dict)
            if grouping_key in taxes_map:
                # A line with the same key does already exist, we only need one
                # to modify it; we have to drop this one.
                to_remove += line
            else:
                taxes_map[grouping_key] = {
                    'tax_line': line,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                }
        if not recompute_tax_base_amount:
            self.line_ids -= to_remove

        # ==== Mount base lines ====
        for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
            # Don't call compute_all if there is no tax.
            if not line.tax_ids:
                if not recompute_tax_base_amount:
                    line.tax_tag_ids = [(5, 0, 0)]
                continue

            compute_all_vals = _compute_base_line_taxes(line)

            # Assign tags on base line
            if not recompute_tax_base_amount:
                line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

            tax_exigible = True
            for tax_vals in compute_all_vals['taxes']:
                grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
                grouping_key = _serialize_tax_grouping_key(grouping_dict)

                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

                if tax.tax_exigibility == 'on_payment':
                    tax_exigible = False

                taxes_map_entry = taxes_map.setdefault(grouping_key, {
                    'tax_line': None,
                    'amount': 0.0,
                    'tax_base_amount': 0.0,
                    'grouping_dict': False,
                })
                taxes_map_entry['amount'] += tax_vals['amount']
                taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
                taxes_map_entry['grouping_dict'] = grouping_dict
            if not recompute_tax_base_amount:
                line.tax_exigible = tax_exigible

        # ==== Pre-process taxes_map ====
        taxes_map = self._preprocess_taxes_map(taxes_map)

        # ==== Process taxes_map ====
        for taxes_map_entry in taxes_map.values():
            # The tax line is no longer used in any base lines, drop it.
            if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
                if not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

            # Don't create tax lines with zero balance.
            if currency.is_zero(taxes_map_entry['amount']):
                if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
                    self.line_ids -= taxes_map_entry['tax_line']
                continue

            # tax_base_amount field is expressed using the company currency.
            tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

            # Recompute only the tax_base_amount.
            if recompute_tax_base_amount:
                if taxes_map_entry['tax_line']:
                    taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
                continue

            balance = currency._convert(
                taxes_map_entry['amount'],
                self.company_currency_id,
                self.company_id,
                self.date or fields.Date.context_today(self),
            )
            purchase = self.line_ids.mapped('purchase_line_id.order_id')
            # move_type = self.line_ids
            _logger.info("Compute lines move type: %s", self.move_type)
            
            to_write_on_line = {
                'amount_currency': taxes_map_entry['amount'],
                'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
                'debit': balance > 0.0 and balance or 0.0 if self.move_type != 'in_invoice' else 0.0,
                'credit': balance < 0.0 and -balance or 0.0 if self.move_type != 'in_invoice' else balance,
                'tax_base_amount': tax_base_amount,
            }
            _logger.info("Amount currency on account move to to_write_on_line: %s", to_write_on_line)
            # to_write_on_line = {
            #     'amount_currency': taxes_map_entry['amount'],
            #     'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
            #     'debit': balance > 0.0 and balance or 0.0,
            #     'credit': balance < 0.0 and -balance or 0.0,
            #     'tax_base_amount': tax_base_amount,
            # }

            # if purchase:
            #     _logger.info("There is purchase for tax: %s", purchase)
            #     to_write_on_line = {
            #         'amount_currency': taxes_map_entry['amount'],
            #         'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
            #         'debit': 0.0,
            #         'credit': balance > 0.0 and balance or 0.0,
            #         'tax_base_amount': tax_base_amount,
            #     }

            if taxes_map_entry['tax_line']:
                # Update an existing tax line.
                taxes_map_entry['tax_line'].update(to_write_on_line)
            else:
                # Create a new tax line.
                create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
                tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)
                tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
                taxes_map_entry['tax_line'] = create_method({
                    **to_write_on_line,
                    'name': tax.name,
                    'move_id': self.id,
                    'company_id': self.company_id.id,
                    'company_currency_id': self.company_currency_id.id,
                    'tax_base_amount': tax_base_amount,
                    'exclude_from_invoice_tab': True,
                    'tax_exigible': tax.tax_exigibility == 'on_invoice',
                    **taxes_map_entry['grouping_dict'],
                })
                _logger.info("taxes map entry: %s", taxes_map_entry['tax_line'])

            if in_draft_mode:
                taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


    # def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):
    #     """ Compute the dynamic tax lines of the journal entry.
    #     :param recompute_tax_base_amount: Flag forcing only the recomputation of the `tax_base_amount` field.
    #     """
    #     self.ensure_one()
    #     in_draft_mode = self != self._origin

    #     def _serialize_tax_grouping_key(grouping_dict):
    #         ''' Serialize the dictionary values to be used in the taxes_map.
    #         :param grouping_dict: The values returned by '_get_tax_grouping_key_from_tax_line' or '_get_tax_grouping_key_from_base_line'.
    #         :return: A string representing the values.
    #         '''
    #         return '-'.join(str(v) for v in grouping_dict.values())

    #     def _compute_base_line_taxes(base_line):
    #         ''' Compute taxes amounts both in company currency / foreign currency as the ratio between
    #         amount_currency & balance could not be the same as the expected currency rate.
    #         The 'amount_currency' value will be set on compute_all(...)['taxes'] in multi-currency.
    #         :param base_line:   The account.move.line owning the taxes.
    #         :return:            The result of the compute_all method.
    #         '''
    #         move = base_line.move_id

    #         if move.is_invoice(include_receipts=True):
    #             handle_price_include = True
    #             sign = -1 if move.is_inbound() else 1
    #             quantity = base_line.quantity
    #             is_refund = move.move_type in ('out_refund', 'in_refund', 'in_invoice')
    #             price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
    #         else:
    #             handle_price_include = False
    #             quantity = 1.0
    #             tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
    #             is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
    #             price_unit_wo_discount = base_line.amount_currency

    #         balance_taxes_res = base_line.tax_ids._origin.with_context(force_sign=move._get_tax_force_sign()).compute_all(
    #             price_unit_wo_discount,
    #             currency=base_line.currency_id,
    #             quantity=quantity,
    #             product=base_line.product_id,
    #             partner=base_line.partner_id,
    #             is_refund=is_refund,
    #             handle_price_include=handle_price_include,
    #         )
    #         _logger.info("balance_taxes_res: %s", balance_taxes_res)

    #         if move.move_type == 'entry':
    #             repartition_field = is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids'
    #             repartition_tags = base_line.tax_ids.flatten_taxes_hierarchy().mapped(repartition_field).filtered(lambda x: x.repartition_type == 'base').tag_ids
    #             tags_need_inversion = self._tax_tags_need_inversion(move, is_refund, tax_type)
    #             if tags_need_inversion:
    #                 balance_taxes_res['base_tags'] = base_line._revert_signed_tags(repartition_tags).ids
    #                 for tax_res in balance_taxes_res['taxes']:
    #                     tax_res['tag_ids'] = base_line._revert_signed_tags(self.env['account.account.tag'].browse(tax_res['tag_ids'])).ids

    #         return balance_taxes_res

    #     taxes_map = {}

    #     # ==== Add tax lines ====
    #     to_remove = self.env['account.move.line']
    #     for line in self.line_ids.filtered('tax_repartition_line_id'):
    #         grouping_dict = self._get_tax_grouping_key_from_tax_line(line)
    #         grouping_key = _serialize_tax_grouping_key(grouping_dict)
    #         if grouping_key in taxes_map:
    #             # A line with the same key does already exist, we only need one
    #             # to modify it; we have to drop this one.
    #             to_remove += line
    #         else:
    #             taxes_map[grouping_key] = {
    #                 'tax_line': line,
    #                 'amount': 0.0,
    #                 'tax_base_amount': 0.0,
    #                 'grouping_dict': False,
    #             }
    #     if not recompute_tax_base_amount:
    #         self.line_ids -= to_remove

    #     # ==== Mount base lines ====
    #     for line in self.line_ids.filtered(lambda line: not line.tax_repartition_line_id):
    #         # Don't call compute_all if there is no tax.
    #         if not line.tax_ids:
    #             if not recompute_tax_base_amount:
    #                 line.tax_tag_ids = [(5, 0, 0)]
    #             continue

    #         compute_all_vals = _compute_base_line_taxes(line)

    #         # Assign tags on base line
    #         if not recompute_tax_base_amount:
    #             line.tax_tag_ids = compute_all_vals['base_tags'] or [(5, 0, 0)]

    #         tax_exigible = True
    #         for tax_vals in compute_all_vals['taxes']:
    #             grouping_dict = self._get_tax_grouping_key_from_base_line(line, tax_vals)
    #             grouping_key = _serialize_tax_grouping_key(grouping_dict)

    #             tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_vals['tax_repartition_line_id'])
    #             tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id

    #             if tax.tax_exigibility == 'on_payment':
    #                 tax_exigible = False

    #             taxes_map_entry = taxes_map.setdefault(grouping_key, {
    #                 'tax_line': None,
    #                 'amount': 0.0,
    #                 'tax_base_amount': 0.0,
    #                 'grouping_dict': False,
    #             })
    #             taxes_map_entry['amount'] += tax_vals['amount']
    #             taxes_map_entry['tax_base_amount'] += self._get_base_amount_to_display(tax_vals['base'], tax_repartition_line, tax_vals['group'])
    #             taxes_map_entry['grouping_dict'] = grouping_dict
    #         if not recompute_tax_base_amount:
    #             line.tax_exigible = tax_exigible

    #     # ==== Pre-process taxes_map ====
    #     taxes_map = self._preprocess_taxes_map(taxes_map)

    #     # ==== Process taxes_map ====
    #     for taxes_map_entry in taxes_map.values():
    #         # The tax line is no longer used in any base lines, drop it.
    #         if taxes_map_entry['tax_line'] and not taxes_map_entry['grouping_dict']:
    #             if not recompute_tax_base_amount:
    #                 self.line_ids -= taxes_map_entry['tax_line']
    #             continue

    #         currency = self.env['res.currency'].browse(taxes_map_entry['grouping_dict']['currency_id'])

    #         # Don't create tax lines with zero balance.
    #         if currency.is_zero(taxes_map_entry['amount']):
    #             if taxes_map_entry['tax_line'] and not recompute_tax_base_amount:
    #                 self.line_ids -= taxes_map_entry['tax_line']
    #             continue

    #         # tax_base_amount field is expressed using the company currency.
    #         tax_base_amount = currency._convert(taxes_map_entry['tax_base_amount'], self.company_currency_id, self.company_id, self.date or fields.Date.context_today(self))

    #         # Recompute only the tax_base_amount.
    #         if recompute_tax_base_amount:
    #             if taxes_map_entry['tax_line']:
    #                 taxes_map_entry['tax_line'].tax_base_amount = tax_base_amount
    #             continue

    #         balance = currency._convert(
    #             taxes_map_entry['amount'],
    #             self.company_currency_id,
    #             self.company_id,
    #             self.date or fields.Date.context_today(self),
    #         )
    #         to_write_on_line = {
    #             'amount_currency': taxes_map_entry['amount'],
    #             'currency_id': taxes_map_entry['grouping_dict']['currency_id'],
    #             'debit': balance > 0.0 and balance or 0.0,
    #             'credit': balance < 0.0 and -balance or 0.0,
    #             'tax_base_amount': tax_base_amount,
    #         }

    #         if taxes_map_entry['tax_line']:
    #             # Update an existing tax line.
    #             if tax_rep_lines_to_recompute and taxes_map_entry['tax_line'].tax_repartition_line_id not in tax_rep_lines_to_recompute:
    #                 continue

    #             taxes_map_entry['tax_line'].update(to_write_on_line)
    #         else:
    #             # Create a new tax line.
    #             create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
    #             tax_repartition_line_id = taxes_map_entry['grouping_dict']['tax_repartition_line_id']
    #             tax_repartition_line = self.env['account.tax.repartition.line'].browse(tax_repartition_line_id)

    #             if tax_rep_lines_to_recompute and tax_repartition_line not in tax_rep_lines_to_recompute:
    #                 continue

    #             tax = tax_repartition_line.invoice_tax_id or tax_repartition_line.refund_tax_id
    #             taxes_map_entry['tax_line'] = create_method({
    #                 **to_write_on_line,
    #                 'name': tax.name,
    #                 'move_id': self.id,
    #                 'company_id': self.company_id.id,
    #                 'company_currency_id': self.company_currency_id.id,
    #                 'tax_base_amount': tax_base_amount,
    #                 'exclude_from_invoice_tab': True,
    #                 'tax_exigible': tax.tax_exigibility == 'on_invoice',
    #                 **taxes_map_entry['grouping_dict'],
    #             })

    #         if in_draft_mode:
    #             taxes_map_entry['tax_line'].update(taxes_map_entry['tax_line']._get_fields_onchange_balance(force_computation=True))


    @api.model_create_multi
    def create(self, vals_list):
        res = super(fhflAccountInvoice, self).create(vals_list)
        today = datetime.date.today()
        group_backdate = self.env.user.\
            has_group('fhfl_sales_custom.group_accounting_allow_backdate')
        _logger.info("self move lines ids: %s", self.line_ids)
        if not group_backdate:
        
            for vals in vals_list:
                # date = vals['date']
                _logger.info("Move vals: %s", vals)
                if 'line_ids' in vals:
                    _logger.info("Move lines ids: %s", vals['line_ids'])
                if 'date' in vals:
                    date = datetime.datetime.strptime(vals['date'], '%Y-%m-%d').date() if type(vals['date']) is str else \
                        vals['date']
                    
                    if date and date < today:
                        raise UserError(_("You cannot post into the past. Please contact the Head of Accounts"))
        return res


class fhflAccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    estate_id = fields.Many2one(related='product_id.estate_id', store=True)

    def _get_fields_onchange_balance(self, quantity=None, discount=None, amount_currency=None, move_type=None, currency=None, taxes=None, price_subtotal=None, force_computation=False):
        self.ensure_one()
        test = self._get_fields_onchange_balance_model(
            quantity=self.quantity if quantity is None else quantity,
            discount=self.discount if discount is None else discount,
            amount_currency=self.amount_currency if amount_currency is None else amount_currency,
            move_type=self.move_id.move_type if move_type is None else move_type,
            currency=(self.currency_id or self.move_id.currency_id) if currency is None else currency,
            taxes=self.tax_ids if taxes is None else taxes,
            price_subtotal=self.price_subtotal if price_subtotal is None else price_subtotal,
            force_computation=force_computation,
        )
        _logger.info("fields onchange balance; %s", test)
        
        # return self._get_fields_onchange_balance_model(
        #     quantity=self.quantity if quantity is None else quantity,
        #     discount=self.discount if discount is None else discount,
        #     amount_currency=self.amount_currency if amount_currency is None else amount_currency,
        #     move_type=self.move_id.move_type if move_type is None else move_type,
        #     currency=(self.currency_id or self.move_id.currency_id) if currency is None else currency,
        #     taxes=self.tax_ids if taxes is None else taxes,
        #     price_subtotal=self.price_subtotal if price_subtotal is None else price_subtotal,
        #     force_computation=force_computation,
        # )
        return test

    @api.model
    def _get_fields_onchange_balance_model(self, quantity, discount, amount_currency, move_type, currency, taxes, price_subtotal, force_computation=False):
        ''' 
        :return:                A dictionary containing 'quantity', 'discount', 'price_unit'.
        '''
        if move_type in self.move_id.get_outbound_types():
            sign = 1
        elif move_type in self.move_id.get_inbound_types():
            sign = -1
        else:
            sign = 1
        amount_currency *= sign
        purchase = self.move_id.line_ids.mapped('purchase_line_id.order_id')
        test = {
            'amount_currency': amount_currency,
            'quantity': quantity,
            'taxes': taxes,
            'price_subtotal': price_subtotal,
            'force_computation': force_computation
        }
        # _logger.info("get fields onchange balance vals: %s", test)

        # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
        # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
        # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
        # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
        # issue.
        if not force_computation and currency.is_zero(amount_currency - price_subtotal):
            return {}

        taxes = taxes.flatten_taxes_hierarchy()
        if taxes and any(tax.price_include for tax in taxes):
            _logger.info("There is taxes")
            # Inverse taxes. E.g:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 110           | 10% incl, 5%  |                   | 100               | 115
            # 10            |               | 10% incl          | 10                | 10
            # 5             |               | 5%                | 5                 | 5
            #
            # When setting the balance to -200, the expected result is:
            #
            # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
            # -----------------------------------------------------------------------------------
            # 220           | 10% incl, 5%  |                   | 200               | 230
            # 20            |               | 10% incl          | 20                | 20
            # 10            |               | 5%                | 10                | 10
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(amount_currency, currency=currency, handle_price_include=False)
            _logger.info("Onchange balance tax res: %s", taxes_res)
            for tax_res in taxes_res['taxes']:
                tax = self.env['account.tax'].browse(tax_res['id'])
                if tax.price_include:
                    amount_currency += tax_res['amount']

        discount_factor = 1 - (discount / 100.0)
        _logger.info("purchase is present: %s", self.move_id.line_ids.mapped('purchase_line_id.order_id'))
        if purchase:
            _logger.info("purchase is present")
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': self.move_id.amount_untaxed
            }
        if amount_currency and discount_factor:
            # discount != 100%
            vals = {
                'quantity': quantity or 1.0,
                'price_unit': amount_currency / discount_factor / (quantity or 1.0),
            }
        elif amount_currency and not discount_factor:
            # discount == 100%
            vals = {
                'quantity': quantity or 1.0,
                'discount': 0.0,
                'price_unit': amount_currency / (quantity or 1.0),
            }
        elif not discount_factor:
            # balance of line is 0, but discount  == 100% so we display the normal unit_price
            vals = {}
        else:
            # balance is 0, so unit price is 0 as well
            vals = {'price_unit': 0.0}
        _logger.info("Vals: %s", vals)
        return vals



class FhflAccountPayment(models.Model):
    _inherit = "account.payment"

    remita_rr_num = fields.Char(string="Remita RR Number")

