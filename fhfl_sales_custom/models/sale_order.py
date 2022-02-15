# -*- coding: utf-8 -*-
import calendar
import datetime
# from datetime import datetime, timedelta
from dateutil.relativedelta import *
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SalesWizard(models.Model):

    _name = 'sale.order.wizard'
    _description = "Wizard for Sale order Rejection"

    sale_order_id = fields.Many2one('sale.order')
    refuse_request = fields.Char()

    def reject_sale_order(self):
        for record in self:
            body = "<p>Dear %s ,<br/><br/> " % record.sale_order_id.submit_user.name
            body += "This is to inform you that your sales order "
            body += "has been rejected <br/> "
            body += "<stong>Reasons for rejection: </strong> "
            body += "%s <br/>" % record.refuse_request
            body += "%s</p>" % (self.env.user.company_id.name)

            vals = {
                'subject': 'Sale Rejection',
                'body_html': body,
                'email_to': record.sale_order_id.submit_user.email,
                # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                # 'email_cc': [emp.work_email for emp in employees],
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()
            record.sale_order_id.state = 'reject'
            var_for_pep = record.refuse_request
            record.sale_order_id.message_post(
                body=_("Sale Order has been rejected."))
            record.sale_order_id.message_post(body=_(
                "Reason : {}").format(var_for_pep))


class FhflSaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(FhflSaleAdvancePaymentInv, self). \
            _prepare_invoice_values(order, name, amount, so_line)
        _logger.info("Prepare values: %s", res)
        res['sales_type'] = order.sales_type
        # invoice_vals = {
        #     'ref': order.client_order_ref,
        #     'move_type': 'out_invoice',
        #     'invoice_origin': order.name,
        #     'invoice_user_id': order.user_id.id,
        #     'narration': order.note,
        #     'partner_id': order.partner_invoice_id.id,
        #     'fiscal_position_id': (order.fiscal_position_id or order.fiscal_position_id.get_fiscal_position(
        #         order.partner_id.id)).id,
        #     'partner_shipping_id': order.partner_shipping_id.id,
        #     'currency_id': order.pricelist_id.currency_id.id,
        #     'payment_reference': order.reference,
        #     'invoice_payment_term_id': order.payment_term_id.id,
        #     'partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
        #     'team_id': order.team_id.id,
        #     'campaign_id': order.campaign_id.id,
        #     'medium_id': order.medium_id.id,
        #     'source_id': order.source_id.id,
        #     'invoice_line_ids': [(0, 0, {
        #         'name': name,
        #         'price_unit': amount,
        #         'quantity': 1.0,
        #         'product_id': self.product_id.id,
        #         'product_uom_id': so_line.product_uom.id,
        #         'tax_ids': [(6, 0, so_line.tax_id.ids)],
        #         'sale_line_ids': [(6, 0, [so_line.id])],
        #         'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
        #         'analytic_account_id': order.analytic_account_id.id or False,
        #     })],
        # }

        return res


class SalesOrderInstallmentSchedule(models.Model):
    _name = 'installment.schedule'
    _description = 'Installment Schedule'

    sale_order_id = fields.Many2one('sale.order')
    s_n = fields.Integer(string='S/N')
    start_date = fields.Date('Date')
    amount = fields.Float()
    description = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        # ('installment', 'Installment'),
        # ('mortgage', 'Mortgage'),
    ], string='Status', copy=False, index=True, default='draft')


class SalesOrderInstallment(models.Model):
    _name = 'sale.order.installment'
    _description = 'Installment Plans'

    name = fields.Char()
    tenure = fields.Integer(string='Tenure(in months)')


class fhflSalesOrder(models.Model):
    _inherit = 'sale.order'

    install_schedule_line = fields.One2many('installment.schedule', 'sale_order_id')
    state = fields.Selection(selection_add=[
        ('submit', 'Submit'),
        ('approve', 'Approved'),
        ('sent',),
        ('reject', 'Rejected'),
    ], ondelete={'draft': 'set default'},
        tracking=True)
    submit_user = fields.Many2one('res.users')
    sales_type = fields.Selection([
        ('outright', 'Outright'),
        ('installment', 'Installment'),
        ('mortgage', 'Mortgage'),
        ], string='Sales Order Type', copy=False, index=True, tracking=True)
    installment_plan = fields.Many2one('sale.order.installment')
    tenure = fields.Integer(related='installment_plan.tenure', string='Tenure(in months)')
    start_date = fields.Date()
    
    def calculate_installment(self):
        _logger.info('Calculate Installment')
        installs = []
        for rec in self:
            if rec.start_date:
                for i in range(rec.tenure):
                    period = i
                    date = rec.start_date
                    description = 'Down Payment'
                    amount = rec.amount_total / rec.tenure
                    if period > 0:
                        description = '%s Installment' % period
                        date = rec.start_date + relativedelta(months=period)
                        last_date = calendar.monthrange(date.year, date.month)[1]
                        date = date.replace(day=last_date)
                    _logger.info("Periods: %s", period)
                    _logger.info("Date: %s", date)
                    _logger.info("Description: %s", description)
                    _logger.info("Amount: %s", amount)
            else:
                raise UserError(_("No Start Date to calculate installment"))

    def action_submit(self):
        _logger.info("Move to Submit state")
        employees = self.env['hr.employee']. \
            search([])
        managing_dir = employees.filtered(lambda l: l.user_id.id and
                                                    self.env.ref("fhfl_sales_custom.group_sale_manager_approval").id in
                                                    l.user_id.groups_id.ids)
        _logger.info("Managing Dir: %s", managing_dir)
        body = ""
        if managing_dir:
            for mg in managing_dir:
                body = "<b> Dear %s </br>" % mg.name
                body += "This Sale Order has been submitted to you "
                body += "for your approval"
                body += "</b>"
        self.message_post(body=body)
        self.write({
            'state': 'submit',
            'submit_user': self.env.user.id,
        })

    def action_approve(self):
        _logger.info("Move to Approve state")
        for rec in self:
            body = "<p>Dear %s ,<br/><br/> " % rec.submit_user.name
            body += "This is to inform you that your sales order "
            body += "has been approved <br/> "
            body += "%s</p>" % (self.company_id.name)

            vals = {
                'subject': 'Employee Confirmation',
                'body_html': body,
                'email_to': rec.submit_user.email,
                # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                # 'email_cc': [emp.work_email for emp in employees],
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()
        self.write({'state': 'approve'})

    def call_popup_reject_menu(self):
        wizard = self.env['sale.order.wizard'].sudo().create(
            {'sale_order_id': self.id, 'refuse_request': ''})
        return {
            'name': "Rejection Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order.wizard',
            'res_id': int(wizard.id),
            'view_id': self.env.ref("fhfl_sales_custom.view_sale_order_reject")
                .id,
            'target': 'new',
            "context": {'record': self}
        }

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        res = super(fhflSalesOrder, self). \
            _prepare_invoice()
        _logger.info("Prepare Sales values: %s", res)
        res['sales_type'] = self.sales_type
        # journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        # if not journal:
        #     raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
        #     self.company_id.name, self.company_id.id))
        #
        # invoice_vals = {
        #     'ref': self.client_order_ref or '',
        #     'move_type': 'out_invoice',
        #     'narration': self.note,
        #     'currency_id': self.pricelist_id.currency_id.id,
        #     'campaign_id': self.campaign_id.id,
        #     'medium_id': self.medium_id.id,
        #     'source_id': self.source_id.id,
        #     'user_id': self.user_id.id,
        #     'invoice_user_id': self.user_id.id,
        #     'team_id': self.team_id.id,
        #     'partner_id': self.partner_invoice_id.id,
        #     'partner_shipping_id': self.partner_shipping_id.id,
        #     'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(
        #         self.partner_invoice_id.id)).id,
        #     'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
        #     'journal_id': journal.id,  # company comes from the journal
        #     'invoice_origin': self.name,
        #     'invoice_payment_term_id': self.payment_term_id.id,
        #     'payment_reference': self.reference,
        #     'transaction_ids': [(6, 0, self.transaction_ids.ids)],
        #     'invoice_line_ids': [],
        #     'company_id': self.company_id.id,
        # }
        return res
