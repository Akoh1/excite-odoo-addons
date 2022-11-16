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
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    amount = fields.Float()
    description = fields.Char()
    state = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        # ('installment', 'Installment'),
        # ('mortgage', 'Mortgage'),
    ], string='Status', copy=False, index=True, default='unpaid')
    invoice_ids = fields.Many2one('account.move',
                                   string='Invoices', copy=False, readonly=True)

    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string='Invoice')
    sale_state = fields.Selection(related='sale_order_id.state')

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for trans in self:
            trans.invoice_count = len(trans.invoice_ids)

    def action_view_invoices(self):
        action = {
            'name': _('Invoice(s)'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
        }
        invoice_ids = self.invoice_ids.id
        if invoice_ids:
            action['res_id'] = invoice_ids
            action['view_mode'] = 'form'
        # else:
        #     action['view_mode'] = 'tree,form'
        #     action['domain'] = [('id', 'in', sale_order_ids)]
        return action

    @api.model
    def _send_mail_before_payment_date(self):
        """
        This Function is called as a cron job to send mails to various
        groups some specified time before paymenr.

        """
        install_model = self.env['installment.schedule']. \
            search([])
        employees = self.env['hr.employee']. \
            search([])
        sales_mgt_filter = employees.filtered(lambda l: l.user_id.id and
                                        self.env.ref("sales_team.group_sale_manager").id in l.user_id.groups_id.ids)

        _logger.info("Sales Mgt users: %s", sales_mgt_filter)
        sales_mgt_email = [e.work_email for e in sales_mgt_filter]
     
        _logger.info("Company: %s", self.env.user.company_id.name)
        _logger.info("Sales manager emails: %s", sales_mgt_email )

        # installment_model = self.env[]

        # for rec in self.filtered(lambda l: l.end_date is not False and l.invoice_ids.id):
        for rec in install_model.filtered(lambda l: l.end_date is not False):

            two_weeks_days = datetime.timedelta(days=14)
            two_weeks = rec.end_date - two_weeks_days
            _logger.info("2 weeks: %s", two_weeks)
            today = datetime.date.today()

            if today == two_weeks:

                body = "<p>Dear Sales Managers,<br/><br/> "
                body += "This is to remind you pending payment of <br/> "
                body += "an installment plan for sale order %s <br/> " % (rec.sale_order_id.name)
                body += "coming up on %s <br/> " % (rec.end_date)
                body += "%s</p>" % (self.env.user.company_id.name)

                vals = {
                    'subject': 'Payment Reminder',
                    'body_html': body,
                    'email_to': ",".join(sales_mgt_email),
                    # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                    # 'email_cc': [emp.work_email for emp in employees],
                    'auto_delete': False,
                    'email_from': self.env.user.company_id.email,
                }
                
                _logger.info("Sent Reminder mail successfully")
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()

            one_day_days = datetime.timedelta(days=1)
            one_day = rec.end_date - one_day_days

            if today == one_day:
                body = "<p>Dear %s,<br/><br/> " % (rec.sale_order_id.partner_id.name)
                body += "This is to remind you pending payment of <br/> "
                body += "an installment plan for sale order %s <br/> " % (rec.sale_order_id.name)
                body += "coming up on %s <br/> " % (rec.end_date)
                body += "%s</p>" % (self.env.user.company_id.name)

                vals = {
                    'subject': 'Payment Reminder',
                    'body_html': body,
                    'email_to': rec.sale_order_id.partner_id.email,
                    # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                    # 'email_cc': [emp.work_email for emp in employees],
                    'auto_delete': False,
                    'email_from': self.env.user.company_id.email,
                }
                
                _logger.info("Sent Reminder mail successfully")
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()
            

        _logger.info("Sent email for confirmation")

    def _prepare_invoice_lines(self):
      _logger.info("Preparing Lines")
      self.ensure_one()
      appraisal_acct = self.env.user.company_id.appraisal_account
      inv_lines = {
          'name': self.description,
          # 'account_id': appraisal_acct.id,
            # 'quantity': 1,
          'price_unit': self.amount,
        }
      _logger.info("Lines: %s", inv_lines)
      return inv_lines

    def _prepare_invoice(self):
      
        self.ensure_one()
        
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        currency_id = self.env.ref('base.main_company').currency_id
        _logger.info("Currency: %s", currency_id)
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
            self.env.user.company_id.name, self.env.user.company_id.id))
        
        invoice_vals = {
            'ref': self.description or '',
            'move_type': 'out_invoice',
            # 'narration': self.appraisal_comment,
            'currency_id': currency_id.id,
            'user_id': self.env.user.id,
            'invoice_user_id': self.env.user.id,
            # 'team_id': self.team_id.id,
            'partner_id': self.sale_order_id.partner_id.id,
            'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.sale_order_id.name,
            'invoice_date': self.end_date,
            # 'invoice_payment_term_id': self.payment_term_id.id,
            # 'payment_reference': self.application_id,
            # 'invoice_line_ids': [[0, 0, {
            #     # 'product_id': 15,
            #     # 'display_type': 'line_section',
            #     'name': 'Appraisal Fee',
            #     'account_id': appraisal_acct.id,
            #     'quantity': 1.0,
            #     'price_unit': self.appraisal_amount,
            #   }]],
            'invoice_line_ids': [[0,0, self._prepare_invoice_lines()]],
            'company_id': self.env.user.company_id.id,
            'crm_sale': self.id
        }
        return invoice_vals

    def _add_invoice(self, moves):
      _logger.info("Adding invoice to Investment")
      for rec in self:
        rec.invoice_ids = moves.id

    def _invoice_generated(self):
      self.write({
          'state': 'pending'
        })

    def generate_installment_invoice(self):
        _logger.info("Generate Installment Invoice")
        inv_vals = []
        inv_vals_lines = []
      # inv_vals_list = None
        for rec in self:
        
            inv_vals_list = rec._prepare_invoice()
            # inv_vals_lines.append((0, 0, rec._prepare_invoice_lines()))
            # inv_vals_list['invoice_line_ids'] += inv_vals_lines
            inv_vals.append(inv_vals_list)

            _logger.info("Inv vals: %s", inv_vals)
            # _logger.info("Inv vals: %s", inv_vals_list)

        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(inv_vals_list)
        if moves:
            _logger.info("Moves Created")

            if moves.invoice_line_ids:
                _logger.info("Moves Line created")
        
                for lines in moves.invoice_line_ids:
                    _logger.info("Moves line just created id: %s", lines.id)
                    _logger.info("Moves line just created: %s", lines.name)
            else:
                _logger.info("Move line was not created")
            self._add_invoice(moves)
            self._invoice_generated()
        return moves


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
    # installment_plan = fields.Many2one('sale.order.installment')
    tenure = fields.Integer(string='Number of Installments')
    # check_install = fields.Boolean(default=False, compute='_compute_calculate_installment')
    install_months = fields.Integer('Installment Months', related='opportunity_id.num_months',
                                    readonly=False)
    start_date = fields.Date(related='opportunity_id.start_date',
                             readonly=False)
    # crm_sale_lead = fields.Many2one('crm.lead')
    opportunity_id = fields.Many2one(
        'crm.lead', string='Investment Sale', check_company=True, readonly=True)
    # opportunity_id = fields.Many2one(
    #     'crm.lead', string='Opportunity', check_company=True,
    #     domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    # @api.depends('opportunity_id', 'install_months')
    def compute_calculate_installment(self):
        _logger.info('Calculate Installment')
        period = 0
        installs = []
        for rec in self:

            if rec.tenure or rec.amount_total:
                rec.install_schedule_line = [(5,0,0)]
                if rec.start_date:
                    
                    # period = 0
                    for i in range(rec.tenure):
                        _logger.info("I: %s", i)
                        _logger.info("Periods: %s", period)
                        date = rec.start_date
                        
                        end_date = date + relativedelta(months=period)
                        days_in_month = calendar. \
                            monthrange(end_date.year,
                                       end_date.month)[1]
                        end_date = end_date + datetime.timedelta(days=days_in_month)
                        

                        _logger.info("First Start Date: %s", date)
                        _logger.info("First End Date: %s", end_date)

                        # end_date = date + relativedelta(months=period)
                        # # # end_date = date.replace(day = calendar.monthrange(date.year, date.month)[1])
                        # last_date = calendar.monthrange(end_date.year, end_date.month)[1]
                        # end_date = end_date.replace(day=last_date)

                        # next_date = end_date + datetime.timedelta(days=1)
                        # _logger.info("Next start Date: %s", next_date)
                        description = rec.opportunity_id.product_id.get_product_multiline_description_sale()
                        amount = rec.amount_total / rec.tenure
                        if i > 0:
                            period+=1
                            date = end_date
                            _logger.info("Loop Next start Date: %s", date)
                            days_in_month = calendar. \
                                monthrange(date.year,
                                           date.month)[1]
                            end_date = date + datetime.timedelta(days=days_in_month)
                            _logger.info("Loop End Date: %s", end_date)

                            # next_date = end_date + datetime.timedelta(days=1)
                            # date = next_date
                            # end_date = date.replace(day = calendar.monthrange(date.year, date.month)[1])    
                        # _logger.info("Periods: %s", period)
                        # _logger.info("Start Date: %s", rec.opportunity_id.start_date)
                        # _logger.info("End Date: %s", rec.opportunity_id.end_date)
                        # _logger.info("Description: %s", description)
                        # _logger.info("Amount: %s", amount)
                        rec.install_schedule_line = [(0,0, {
                                's_n': period+1,
                                'start_date': date,
                                'end_date': end_date,
                                'amount': amount,
                                'description': description,
                                'state': 'unpaid'
                            })]
                        # rec.check_install = True
                else:
                    raise UserError(_("No Start Date to calculate installment"))
            else:
                    raise UserError(_("No duration or Amount"))


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

    def print_offer_letter(self):
       data = {
       # 'from_date': self.from_date,
       # 'to_date': self.to_date
       }
       # docids = self.env['sale.order'].search([]).ids
       return self.env.ref('fhfl_sales_custom.action_sales_installment').report_action(None, data=data)


class FhflSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    estate_id = fields.Many2one(related='product_id.estate_id', store=True)


class StudentCard(models.AbstractModel):
    _name = 'report.report_sales_installment'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
              'doc_ids': docids,
              'doc_model': 'sale.order',
              'docs': docs,
              'data': data,
              # 'get_something': self.get_something,
        }
