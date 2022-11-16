# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TravelRequest(models.Model):
    _name = 'travel.request'
    _description = 'Travel Request'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    @api.model
    def _default_logged_employee(self):
        return self.env['hr.employee']. \
            search([('user_id', '=', self.env.user.id)], limit=1)

    name = fields.Char('Subject')
    employee_id = fields.Many2one('hr.employee',
                                  default=_default_logged_employee)
    department_id = fields.Many2one(related='employee_id.department_id')
    job_position = fields.Many2one(related='employee_id.job_id')
    manager = fields.Many2one(related='employee_id.parent_id')
    request_date = fields.Date(default=datetime.datetime.today())
    take_off = fields.Char()
    destination = fields.Char()
    arrival_date = fields.Datetime()
    departure_date = fields.Datetime()
    travel_mode = fields.Selection([
        ('air', 'Air'),
        ('road', 'Road'),
        ('train', 'Train'),
    ], 'Mode of Travel', copy=False, index=True, tracking=True)
    reason = fields.Char('Reason for Travel', required=True)
    duration = fields.Integer('Duration of stay(days)')
    num_days = fields.Integer('Number of Days')
    amount = fields.Float('Amount(Accommodation)')
    cash_accommodate = fields.Float('Cash in lieu of Accommodation')
    station_amount = fields.Float('Per Diem/Out of Station Allowance (Per Day)')
    total = fields.Float(compute="_compute_total")
    state = fields.Selection([
        ('draft', 'draft'),
        ('submit', 'Submitted'),
        ('1_approve', 'Manager Approved'),
        ('2_approve', 'HR Approved'),
        ('cfo_approve', 'CFO Approved'),
        ('paid', 'Paid'),
        ('modify', 'Modification'),
        ('reject', 'Rejected'),
    ], 'Status', default='draft', copy=False, index=True, tracking=True)
    check_manager = fields.Boolean(compute='_compute_check_manager')
    check_hr_manager = fields.Boolean(compute='_compute_hr_manager')
    journal_id = fields.Many2one('account.journal',
                                 domain="['|', ('type', '=', 'cash'), ('type', '=', 'bank')]")
    staff_account = fields.Many2one('account.account', string='Staff Expense Account')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 index=True, default=lambda self: self.env.company,
                                 help="Company related to this record")
    move_ids = fields.Many2one('account.move',
                                   string='Journal Entry', copy=False, readonly=True)

    move_count = fields.Integer(compute='_compute_move_count',
                                   string='Journal Entry')


    @api.depends('move_ids')
    def _compute_move_count(self):
        for trans in self:
            trans.move_count = len(trans.move_ids)

    def action_view_moves(self):
        action = {
            'name': _('Journal Entries(s)'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
        }
        move_ids = self.move_ids.id
        if move_ids:
            action['res_id'] = move_ids
            action['view_mode'] = 'form'
        # else:
        #     action['view_mode'] = 'tree,form'
        #     action['domain'] = [('id', 'in', sale_order_ids)]
        return action

    @api.depends('num_days', 'amount', 'cash_accommodate', 'station_amount')
    def _compute_total(self):
        _logger.info("Compute total")
        for rec in self:
            rec.total = (rec.amount + rec.cash_accommodate +
                         rec.station_amount) * rec.num_days

    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    def action_reject(self):
        for rec in self:
            rec.state = 'reject'

    def action_modify(self):
        for rec in self:
            rec.state = 'draft'

    @api.depends('employee_id')
    def _compute_check_manager(self):
        _logger.info("Check for Emp Manager")
        for rec in self:
            _logger.info("Manager: %s", rec.manager)
            curr_manager = self.env.user
            rec.check_manager = curr_manager.id is rec.manager.user_id.id

    def action_approve_one(self):
        _logger.info("Approve ")
        for rec in self:
            rec.state = '1_approve'

    @api.depends('company_id')
    def _compute_hr_manager(self):
        _logger.info("Check for Emp Manager")
        for rec in self:
            hr_manager = self.env.user.has_group('hr.group_hr_manager')
            rec.check_hr_manager = hr_manager

    def action_approve_two(self):
        _logger.info("Approve 2")
        for rec in self:
            rec.state = '2_approve'

    def action_cfo_approve(self):
        _logger.info("Approve 2")
        for rec in self:
            rec.state = 'cfo_approve'

    def _create_journal_entry(self):
        self.ensure_one()
        _logger.info("Create Journal Entry")
        currency_id = self.env.ref('base.main_company').currency_id
        journal_account = self.journal_id.default_account_id

        entry_vals = {
            'ref': self.name or '',
            'move_type': 'entry',
            'currency_id': currency_id.id,
            'user_id': self.env.user.id,
                
            # 'partner_id': rec.customer_id.id or None,
            'partner_bank_id': self.env.user.company_id.partner_id.bank_ids[:1].id,
            'journal_id': self.journal_id.id,  # company comes from the journal
            'date': self.request_date,
            'company_id': self.company_id.id,

            'line_ids': [(0, 0, {
                    # 'move_id': moves.id,
                    'account_id': self.staff_account.id,
                    # 'partner_id': rec.customer_id.id or None,
                    'name': 'Travel Request',
                    'debit': self.total
                }),
                (0, 0, {
                    # 'move_id': moves.id,
                    'account_id': journal_account.id,
                    # 'partner_id': rec.customer_id.id or None,
                    'name': 'Travel Request',
                    'credit': self.total
            })],
              
        }
        _logger.info("After entry vals: %s", entry_vals)

        return entry_vals

    def _add_move(self, moves):
      _logger.info("Adding Moves")
      for rec in self:
        rec.move_ids = moves.id

    def action_pay(self):
        _logger.info("Pay")
        entry_vals = []
        for rec in self:
            if rec.total == 0:
                raise UserError(_("You cannot Pay for amount of 0."))
            entry_vals_list = rec._create_journal_entry()
            entry_vals.append(entry_vals_list)
        moves = self.env['account.move'].with_context(default_move_type='entry').create(entry_vals)
        if moves:
            _logger.info("Journal entry Created: %s", moves)
            if moves.line_ids:
                _logger.info("Journal lines created:")
                rec.state = 'paid'
                self._add_move(moves)

        return moves










