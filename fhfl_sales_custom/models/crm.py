# -*- coding: utf-8 -*-
import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
    ('4', 'Extremely High'),
    ('5', 'Highest'),
]


class FhflAppraisalFeeConfig(models.Model):
    _name = 'appraisal.fee.config'
    _description = 'Appraisal Fee'

    income_account = fields.Many2one('account.account')


class RejectInvestmentWizard(models.Model):

    _name = 'investment.reject.wizard'
    _description = "Wizard for Investment Rejection"

    investment_id = fields.Many2one('crm.investment')
    refuse_request = fields.Char()

    def reject_sale_order(self):
        for record in self:
            body = "<p>Dear %s ,<br/><br/> " % record.investment_id.customer_name
            body += "This is to inform you that your request "
            body += "has been rejected <br/> "
            body += "<stong>Reasons for rejection: </strong> "
            body += "%s <br/>" % record.refuse_request
            body += "%s</p>" % (self.env.user.company_id.name)

            vals = {
                'subject': 'Affordable Housing request Rejection',
                'body_html': body,
                'email_to': record.investment_id.customer.email,
                # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                # 'email_cc': [emp.work_email for emp in employees],
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()
            record.investment_id.state = 'refuse'
            var_for_pep = record.refuse_request
            record.investment_id.message_post(
                body=_("Your Request has been rejected."))
            record.investment_id.message_post(body=_(
                "Reason : {}").format(var_for_pep))


class FhflInvestment(models.Model):
    _name = 'crm.investment'
    _description = 'Investment'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    def domain_bank_cash_account(self):
      bank_cash = self.env['account.account.type'].\
        search([('name', '=', 'Bank and Cash')], limit=1)

      return [('user_type_id', '=', bank_cash.id)]

    name = fields.Char('Subject')
    priority = fields.Selection(
        AVAILABLE_PRIORITIES, string='Rating', index=True,
        default=AVAILABLE_PRIORITIES[0][0])
    customer = fields.Many2one('res.partner')
    customer_name = fields.Char(related='customer.name')
    date = fields.Date(default=datetime.today())
    appraisal_amount = fields.Float()
    invest_type = fields.Selection([
        ('affordable', 'Affordable Housing'),
        ('mortgage', 'Mortgage'),
    ], string='Investment Type', copy=False, index=True, tracking=True)
    state = fields.Selection([
        ('new', 'New'),
        ('mcc_one', 'MCC1 Review'),
        ('appraisal', 'Appraisal Fee'),
        ('dilligence', 'Due Dilligence'),
        ('mcc_two', 'MCC 2'),
        ('board', 'Board Approval'),
        ('disburse', 'Disbursement'),
        ('done', 'Done'),
        ('refuse', 'Refuse'),
    ], string='Status', copy=False, index=True, tracking=True, default='new')
    appraisal_fee_status = fields.Selection([
        ('draft', 'Draft'),
        ('not_paid', 'Generated'),
        ('paid', 'Paid'),
    ], string='Appraisal fee status', copy=False, index=True, tracking=True, default='draft')
    mcc_one_comment = fields.Text()
    appraisal_comment = fields.Text('Comment for Appraisal fee')
    dilligence_comment = fields.Text('Comment for Due Dilligence')
    mcc_two_comment = fields.Text('Cmment for MCC 2')
    board_comment = fields.Text('Comment for Board Approval')
    disburse_comment = fields.Text('Comment for Disbursement')
    application_id = fields.Char(string="Application ID")
    company_name = fields.Char()
    company_email = fields.Char()
    company_phone = fields.Char()
    contact_email = fields.Char()
    contact_phone = fields.Char()
    project_experience = fields.Char()
    rc_number = fields.Char()
    tin_or_vax_number = fields.Char()
    directors_names = fields.Text()
    director_addresses = fields.Text()
    director_emails = fields.Text()
    director_phones = fields.Text()
    director_nins = fields.Text()
    invoice_ids = fields.Many2one('account.move',
                               string='Invoices', copy=False, readonly=True)

    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string='# of Invoice')
    total_appr_amount = fields.Float('Total Approved Amount')
    first_dis_amount = fields.Float('First Disbursement Amount')
    application_date = fields.Date()
    effective_date = fields.Date()
    credit_purpose = fields.Char()
    intrest_rate = fields.Float()
    journal_id = fields.Many2one('account.journal', string='Journal')
    loan_account = fields.Many2one('account.account')
    disburse_account = fields.Many2one('account.account', string="Disbursement Account",
                                       domain=domain_bank_cash_account)
    remain_amount = fields.Float('Remaining Amount')
    journal_entry = fields.Many2one('account.move')
    files_url = fields.Char()
    company_website = fields.Char()
    # account_number = fields.Char()

    def call_popup_reject_menu(self):
        wizard = self.env['investment.reject.wizard'].sudo().create(
            {'investment_id': self.id, 'refuse_request': ''})
        return {
            'name': "Rejection Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'investment.reject.wizard',
            'res_id': int(wizard.id),
            'view_id': self.env.ref("fhfl_sales_custom.view_investment_reject")
                .id,
            'target': 'new',
            "context": {'record': self}
        }

    def _lms_create_customer(self):
      self.ensure_one()
      test_ip = '51.145.88.82'
      test_port = '8080'
      url = 'http://%s:%s/neptune/rest/createCustomer' % (test_ip, test_port)
      headers = {
          "content-type": "application/json"
      }
      # url = 'http://%s:%s/FamilyHomes/services/FamilyHomesPort?WSDL' %\
      #   (test_ip, test_port)

      data = {
        'organisationName': self.company_name or '',
        'registrationNumber': self.application_id,
        # 'registrationDate': self.date.strftime("%Y-%m-%d"),
        'FirstName': self.customer_name,
        'CustomerName': self.customer_name,
        # 'Tin': self.tin_or_vax_number or '',
        # 'EffectiveStartDate': self.effective_date,
        # 'AddressCity': self.customer.city or '',
        # 'AddressState': self.customer.state_id.name or '',
        # 'AddressLine1': self.customer.street or '',
        # 'PhoneNumber': self.customer.phone or '',
        # 'IdentificationNumber': self.rc_number or '',
        'UserId': str(self.customer.id),
        # 'AccountNumber': self.customer.bank_ids[:1].acc_number or '',
        # 'AccountName': self.customer.bank_ids[:1].acc_holder_name or '',
      }

      _logger.info("LMS Push Data: %s", data)
      datas = json.dumps(data)
      # datas = json.loads(data)
      # req = requests.post(url, data=datas)
      try:
        response = requests.post(url, data=datas, headers=headers)
      except requests.ConnectionError as e:
          raise UserError(_("Connection failure : %s" % str(e)))
      _logger.info("LMS Push Data receiving......")
      j = json.loads(response.text)
      # j = response.text
      _logger.info("LMS Recieve data: %s", j)
      return j

    def push_lms(self):
      _logger.info("Push to LMS")
      # raise UserError(_("This feature is not yet available"))
      for rec in self:
        rec._lms_create_customer()

    def first_disbursement(self):
      _logger.info("First Disbursement")
      currency_id = self.env.ref('base.main_company').currency_id
      for rec in self:
        if not rec.journal_id:
          raise UserError(_("Enter a journal to proceed"))
        if not rec.loan_account:
          raise UserError(_("Enter a loan account to proceed"))
        if not rec.disburse_account:
          raise UserError(_("Enter a Disbursement account to proceed"))
        if not rec.total_appr_amount:
          raise UserError(_("Enter a Total approved amount to proceed"))
        # if not rec.disburse_comment:
        #   raise UserError(_("Please fill Comment for Disbursement!"))

        entry_vals = {
            # 'ref': self.application_id or '',
            'move_type': 'entry',
            'narration': rec.board_comment,
            'currency_id': currency_id.id,
            'user_id': self.env.user.id,
            # 'invoice_user_id': self.env.user.id,
            # 'team_id': self.team_id.id,
            'partner_id': rec.customer.id,
            'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
            'journal_id': rec.journal_id.id,  # company comes from the journal
            
            'company_id': self.env.user.company_id.id,

            'line_ids': [(0, 0, {
                # 'move_id': moves.id,
                'account_id': rec.loan_account.id,
                'partner_id': rec.customer.id,
                'name': 'Loan',
                'debit': rec.total_appr_amount
              }),
              (0, 0, {
                # 'move_id': moves.id,
                'account_id': rec.disburse_account.id,
                'partner_id': rec.customer.id,
                'name': 'Disbursement',
                'credit': rec.total_appr_amount
            })],
          
        }

        
        moves = self.env['account.move'].with_context(default_move_type='entry').create(entry_vals)
        if moves:
          _logger.info("Journal entry Created: %s", moves)
          if moves.line_ids:
            _logger.info("Journal lines created:")

          rec.journal_entry = moves
          rec.state = 'disburse'

    def proceed_due_dilligence(self):
      _logger.info("Due Dilligence")
      for rec in self:
        rec.state = 'dilligence'

    def proceed_mcc_two(self):
      _logger.info("MCC 2")
      for rec in self:
        rec.state = 'mcc_two'

    def proceed_board_approval(self):
      _logger.info("Board Approval")
      for rec in self:
        rec.state = 'board'

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

    def _prepare_invoice_lines(self):
      _logger.info("Preparing Lines")
      self.ensure_one()
      appraisal_acct = self.env.user.company_id.appraisal_account
      inv_lines = {
          'name': 'Appraisal Fee',
          'account_id': appraisal_acct.id,
            # 'quantity': 1,
          'price_unit': self.appraisal_amount,
        }
      _logger.info("Lines: %s", inv_lines)
      return inv_lines

    def _prepare_invoice(self):
      
        self.ensure_one()
        
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        appraisal_acct = self.env.user.company_id.appraisal_account
        currency_id = self.env.ref('base.main_company').currency_id
        _logger.info("Currency: %s", currency_id)
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
            self.env.user.company_id.name, self.env.user.company_id.id))
        
        invoice_vals = {
            'ref': self.application_id or '',
            'move_type': 'out_invoice',
            'narration': self.appraisal_comment,
            'currency_id': currency_id.id,
            'user_id': self.env.user.id,
            'invoice_user_id': self.env.user.id,
            # 'team_id': self.team_id.id,
            'partner_id': self.customer.id,
            'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            # 'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.application_id,
            'invoice_line_ids': [[0, 0, {
                # 'product_id': 15,
                # 'display_type': 'line_section',
                'name': 'Appraisal Fee',
                'account_id': appraisal_acct.id,
                'quantity': 1.0,
                'price_unit': self.appraisal_amount,
              }]],
            # 'invoice_line_ids': [],
            'company_id': self.env.user.company_id.id,
            'investment_id': self.id
        }
        return invoice_vals

    def proceed_mcc_one(self):
      _logger.info("MCC1 Review")
      for rec in self:
        rec.state = 'mcc_one'

    def process_appraisal_fee(self):
      _logger.info("Process Appraisal fee")
      for rec in self:
        # if not rec.appraisal_comment:
        #   raise UserError(_("Please fill Comment for Appraisal Fee!"))
        rec.state = 'appraisal'

    def _add_invoice(self, moves):
      _logger.info("Adding invoice to Investment")
      for rec in self:
        rec.invoice_ids = moves.id

    def _appraisal_fee_inv_generated(self):
      self.write({
          'appraisal_fee_status': 'not_paid'
        })

    def generate_appraisal_fee(self):
      _logger.info("Generate Appraisal fee")
      appraisal_acct = self.env.user.company_id.appraisal_account
      _logger.info("Appraisal Account set on config: %s", appraisal_acct.name)
      inv_vals = []
      inv_vals_lines = []
      # inv_vals_list = None
      for rec in self:
        if not rec.appraisal_amount:
          raise UserError(_("Please fill in an Appraisal amount for this record!"))
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
        self._appraisal_fee_inv_generated()
      return moves


# class FhflPartner(models.Model):
#     _inherit = 'res.partner'

#     property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
#                                                      string="Account Receivable",
#                                                      domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
#                                                      help="This account will be used instead of the default one as the receivable account for the current partner",
#                                                      required=False)
#     property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
#                                                   string="Account Payable",
#                                                   domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False), ('company_id', '=', current_company_id)]",
#                                                   help="This account will be used instead of the default one as the payable account for the current partner",
#                                                   required=False)