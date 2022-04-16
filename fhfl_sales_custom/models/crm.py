# -*- coding: utf-8 -*-
import logging
import requests
import json
import decimal
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


# class vendorPartner(models.Model):
#   _inherit = 'res.partner'

#   vat = fields.Char(string='Tax ID',
#                     index=True, r
#                     help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")


class FhflAppraisalFeeConfig(models.Model):
    _name = 'appraisal.fee.config'
    _description = 'Appraisal Fee'

    income_account = fields.Many2one('account.account')


class InvestmentConditionsConfig(models.Model):
    _name = 'investment.condition'
    _description = 'Condition Precedents'

    name = fields.Char()
    mandatory = fields.Boolean()


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
            record.investment_id.state = '9_refuse'
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
    checklist = fields.Many2many('investment.condition')
    priority = fields.Selection(
        AVAILABLE_PRIORITIES, string='Rating', index=True,
        default=AVAILABLE_PRIORITIES[0][0])
    customer = fields.Many2one('res.partner')
    customer_name = fields.Char(related='customer.name')
    customer_num = fields.Char()
    date = fields.Date(default=datetime.today())
    appraisal_amount = fields.Float()
    invest_type = fields.Selection([
        ('affordable', 'Affordable Housing'),
        ('mortgage', 'Mortgage'),
    ], string='Investment Type', copy=False, index=True, tracking=True)
    state = fields.Selection([
        ('1_new', 'New'),
        ('2_mcc_one', 'MCC1 Review'),
        ('3_appraisal', 'Appraisal Fee'),
        ('4_dilligence', 'Due Dilligence'),
        ('5_mcc_two', 'MCC 2'),
        ('6_board', 'Board Approval'),
        ('7_disburse', 'Disbursement'),
        ('8_done', 'Done'),
        ('9_refuse', 'Refuse'),
        # ('10_park', 'Park'),
    ], string='Status', copy=False, index=True, tracking=True, default='1_new')
    appraisal_fee_status = fields.Selection([
        ('draft', 'Draft'),
        ('not_paid', 'Generated'),
        ('paid', 'Paid'),
    ], string='Appraisal fee status', copy=False, index=True, tracking=True, default='draft')
    park = fields.Boolean(default=False, readonly=True)
    mcc_one_comment = fields.Text()
    mcc_one_back_comment = fields.Text('MCC1 – Re-Present')
    appraisal_comment = fields.Text('Comment for Appraisal fee')
    appraisal_back_comment = fields.Text('Appraisal fee - Re-Present')
    dilligence_comment = fields.Text('Comment for Due Dilligence')
    dilligence_back_comment = fields.Text('Due Dilligence Re-Present')
    mcc_two_comment = fields.Text('Comment for MCC 2')
    mcc_two_back_comment = fields.Text('MCC 2 Re-Present')
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
    total_appr_amount = fields.Float('Total Approved Amount', required=True)
    # first_dis_amount = fields.Float('First Disbursement Amount')
    application_date = fields.Date()
    effective_date = fields.Date()
    credit_purpose = fields.Char()
    intrest_rate = fields.Float('Interest Rate')
    journal_id = fields.Many2one('account.journal', string='Journal')
    loan_account = fields.Many2one('account.account')
    disburse_account = fields.Many2one('account.account', string="Disbursement Account",
                                       domain=domain_bank_cash_account)
    # remain_amount = fields.Float('Remaining Amount', compute="_compute_rem_amount")
    journal_entry = fields.Many2one('account.move')
    files_url = fields.Char()
    company_website = fields.Char()
    application_no = fields.Char('Loan ID')
    # account_number = fields.Char()
    project_id = fields.Many2one('project.project', string='Project')
    loan_id = fields.Char()
    # prev_data = fields.One2many('crm.investment', string="Previous Records")

    def action_park(self):
      _logger.info("Park")
      for rec in self:
        rec.park = True

    def action_unpark(self):
      _logger.info("UnPark")
      for rec in self:
        rec.park = False

    # @api.depends('total_appr_amount', 'first_dis_amount')
    # def _compute_rem_amount(self):
    #   _logger.info("Calculate Remaining Amount")
    #   for rec in self:
    #     rec.remain_amount = rec.total_appr_amount - rec.first_dis_amount

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
    def _check_lms_customer(self):
      self.ensure_one()
      test_ip = '51.145.88.82'
      test_port = '8080'
      url = 'http://%s:%s/neptune/rest/customerExist' % (test_ip, test_port)

      headers = {
          "content-type": "application/json"
      }

      data = {
        'user_id': self.customer.id,
      }

      _logger.info("LMS Data: %s", data)
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
      _logger.info("LMS check user: %s", j)
      return j

    def _lms_create_customer(self):
      self.ensure_one()
      test_ip = '51.145.88.82'
      test_port = '8080'
      url = 'http://%s:%s/neptune/rest/createNewCustomer' % (test_ip, test_port)
      headers = {
          "content-type": "application/json"
      }
      # url = 'http://%s:%s/FamilyHomes/services/FamilyHomesPort?WSDL' %\
      #   (test_ip, test_port)

      data = {
        'name': self.customer_name,
        'email': self.customer.email,
        'mobile': self.customer.mobile,
        'phone': self.customer.phone,
        'user_id': self.customer.id,
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
      if j['customerNo'] is not None:
        self.write({
            'customer_num': j['customerNo']
          })
        # self.customer_num = j['customerNo']
      _logger.info("LMS Recieve data: %s", j)
      return j

    def _lms_credit_application(self):
      self.ensure_one()
      test_ip = '51.145.88.82'
      test_port = '8080'
      url = 'http://%s:%s/neptune/rest/createCreditApplication' % (test_ip, test_port)
      headers = {
          "content-type": "application/json"
      }
      # url = 'http://%s:%s/FamilyHomes/services/FamilyHomesPort?WSDL' %\
      #   (test_ip, test_port)

      data = {
        'totalApprovedAmount': float(self.total_appr_amount),
        # 'firstDisbursementAmount': self.first_dis_amount,
        # 'totalDisbursedAmount': 
        'applicationDate': self.date.strftime('%Y-%m-%d') or None,
        # 'effectiveDate': self.effective_date.strftime('%Y-%m-%d') or None,
        'creditPurpose': self.credit_purpose,
        'application_id': self.application_id,
        'interestRate': self.intrest_rate,
        'user_id': self.customer.id
      }

      _logger.info("LMS Credit Data: %s", data)
      datas = json.dumps(data)
      # datas = json.loads(data)
      # req = requests.post(url, data=datas)
      try:
        response = requests.post(url, data=datas, headers=headers)
      except requests.ConnectionError as e:
          raise UserError(_("Connection failure : %s" % str(e)))
      _logger.info("LMS Push Credit Data receiving......")
      j = json.loads(response.text)
      _logger.info("LMS Recieve Credit data: %s", j)
      if j['applicationNo'] is None:
        raise UserError(_("Could not generate Credit Application"))
      
      # self.application_no = j['applicationNo']
      self.write({
          'state': '7_disburse',
          'application_no': j['applicationNo']
        })

      # j = response.text
      
      return j

    def first_disbursement(self):
      checklist_model = self.env['investment.condition'].\
        search([('mandatory', '=', True)])
      checklists = [i.id for i in checklist_model]
      _logger.info("Mandatory checklists: %s", checklist_model)

      checked_list = []
      for rec in self.checklist:
        # for checks in rec.checklist:
        _logger.info("Checked checklist: %s", rec)
        checked_list.append(rec)
      
      get_checks = [i.id for i in checklist_model if i in checked_list]
      _logger.info("Checklist that are mandatory in model: %s", get_checks)

      if not checklists == get_checks:
        raise UserError(_("Mandatory checklist set in configuration "
                          "must be selected here!"))

      for rec in self:
        check_customer = rec._check_lms_customer()
        # Check if Customer exists
        if check_customer['customerNo'] == None:
          _logger.info("No customer")
          # Create customer if None exists
          create_customer = rec._lms_create_customer()
          if create_customer['customerNo'] is not None:
            _logger.info("Create credit application")
            rec._lms_credit_application()

        else:
          _logger.info("Customer exists")
          rec._lms_credit_application()

    def generate_project(self):
      _logger.info("Generate Project")
      for rec in self:
        project = self.env['project.project'].\
          create({
              'name': rec.application_no,
              'investment_id': rec.id,
            })
        _logger.info("project Investment id: %s", project.investment_id)
        rec.project_id = project.id
        rec.state = '8_done'

    # def first_disbursement(self):
    #   _logger.info("First Disbursement")
    #   currency_id = self.env.ref('base.main_company').currency_id
    #   for rec in self:
    #     if not rec.journal_id:
    #       raise UserError(_("Enter a journal to proceed"))
    #     if not rec.loan_account:
    #       raise UserError(_("Enter a loan account to proceed"))
    #     if not rec.disburse_account:
    #       raise UserError(_("Enter a Disbursement account to proceed"))
    #     if not rec.total_appr_amount:
    #       raise UserError(_("Enter a Total approved amount to proceed"))
    #     # if not rec.disburse_comment:
    #     #   raise UserError(_("Please fill Comment for Disbursement!"))

    #     entry_vals = {
    #         # 'ref': self.application_id or '',
    #         'move_type': 'entry',
    #         'narration': rec.board_comment,
    #         'currency_id': currency_id.id,
    #         'user_id': self.env.user.id,
    #         # 'invoice_user_id': self.env.user.id,
    #         # 'team_id': self.team_id.id,
    #         'partner_id': rec.customer.id,
    #         'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
    #         'journal_id': rec.journal_id.id,  # company comes from the journal
            
    #         'company_id': self.env.user.company_id.id,

    #         'line_ids': [(0, 0, {
    #             # 'move_id': moves.id,
    #             'account_id': rec.loan_account.id,
    #             'partner_id': rec.customer.id,
    #             'name': 'Loan',
    #             'debit': rec.total_appr_amount
    #           }),
    #           (0, 0, {
    #             # 'move_id': moves.id,
    #             'account_id': rec.disburse_account.id,
    #             'partner_id': rec.customer.id,
    #             'name': 'Disbursement',
    #             'credit': rec.total_appr_amount
    #         })],
          
    #     }

        
    #     moves = self.env['account.move'].with_context(default_move_type='entry').create(entry_vals)
    #     if moves:
    #       _logger.info("Journal entry Created: %s", moves)
    #       if moves.line_ids:
    #         _logger.info("Journal lines created:")

    #       rec.journal_entry = moves
    #       rec.state = '7_disburse'

    def waive_appraisal(self):
      _logger.info("Waive Appraisal")
      self.write({'state': '4_dilligence'})

    def proceed_due_dilligence(self):
      _logger.info("Due Dilligence")
      for rec in self:
        rec.state = '4_dilligence'

    def proceed_mcc_two(self):
      _logger.info("MCC 2")
      for rec in self:
        rec.state = '5_mcc_two'

    def proceed_board_approval(self):
      _logger.info("Board Approval")
      for rec in self:
        rec.state = '6_board'

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

    def action_back(self):
      _logger.info("Back to prev state")
      for rec in self:
        if rec.state == '3_appraisal':
          if not rec.mcc_one_back_comment:
            raise UserError(_("Please fill MCC1 Re-Present Comment"))
          rec.state = '2_mcc_one'

        if rec.state == '4_dilligence':
          if not rec.appraisal_back_comment:
            raise UserError(_("Please fill Appraisal Fee Re-Present Comment"))
          rec.state = '3_appraisal'
          rec.appraisal_fee_status = 'draft'

        if rec.state == '5_mcc_two':
          if not rec.dilligence_back_comment:
            raise UserError(_("Please fill Due Dilligence Re-Present Comment"))
          rec.state = '4_dilligence'

        if rec.state == '6_board':
          if not rec.mcc_two_back_comment:
            raise UserError(_("Please fill MCC2 Re-Present Comment"))
          rec.state = '5_mcc_two'

    def proceed_mcc_one(self):
      _logger.info("MCC1 Review")
      for rec in self:
        rec.state = '2_mcc_one'

    def process_appraisal_fee(self):
      _logger.info("Process Appraisal fee")
      for rec in self:
        # if not rec.appraisal_comment:
        #   raise UserError(_("Please fill Comment for Appraisal Fee!"))
        rec.state = '3_appraisal'

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

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(FhflInvestment, self).create(vals_list)
    #     _logger.info("LMS Journal values: %s", vals_list)
    #     journal_id = self.env.company.lms_journal
    #     res.journal_id = journal_id.id
    #     _logger.info('company journal: %s', journal_id)
    #     res.create_journal_entry()
    #     # for vals in vals_list:
    #     #     vals['journal_id'] = journal_id.id or None
    #     return res