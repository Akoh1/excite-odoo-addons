# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MilestonePayment(models.Model):
    _name = 'milestone.payment'
    _description = 'Milestone Payment'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    milestone = fields.Many2one('project.milestone')
    project_id = fields.Many2one(related="milestone.project_id")
    date = fields.Date()
    amount = fields.Float()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'To Approve'),
        ('approved', 'Approved'),

    ], string='State', tracking=True,
        copy=False, default='draft')
    analytic_account = fields.Many2one('account.analytic.account')

    def action_submit(self):
        for rec in self:
            rec.state = 'submit'

    def action_approve(self):
        _logger.info("Action Approve")
        # for rec in self:
        #     rec.state = 'approved'


class ProjectMilestone(models.Model):
    _name = 'project.milestone'
    _description = 'Project Milestone'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    name = fields.Char()
    project_id = fields.Many2one('project.project')
    start_date = fields.Date()
    end_date = fields.Date()
    next_mile = fields.Many2one('project.milestone', 
                                string='Next Milestone',
                                domain="[('id', '!=', id),('id', '>', id)]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Completed'),

    ], string='State', tracking=True,
        copy=False, default='draft')

    def action_running(self):
        _logger.info("Running")
        for rec in self:
            rec.state = 'running'

    def action_done(self):
        _logger.info("Completed")
        for rec in self:
            rec.state = 'done'


class ProjectProject(models.Model):
    _inherit = 'project.project'

    miles_count = fields.Integer(compute='_compute_miles_count',
                                 string='Milestone Count')

    def _compute_miles_count(self):
        for rec in self:
            all_milestones = self.env['project.milestone'].\
                search([('project_id', '=', rec.id)])
            rec.miles_count = len(all_milestones)

    def action_view_milestones(self):
        action = {
            'name': _('Milestones'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.milestone',
            'target': 'current',
        }
        all_milestones = self.env['project.milestone'].\
            search([('project_id', '=', self.id)])
        if all_milestones.ids:
            action['res_id'] = all_milestones.ids
            action['view_mode'] = 'tree'
        # else:
        #     action['view_mode'] = 'tree,form'
        #     action['domain'] = [('id', 'in', sale_order_ids)]
        return action


class ProjectTask(models.Model):
    _inherit = 'project.task'

    milestone = fields.Many2one('project.milestone',
                                domain="[('project_id', '=', project_id)]")


    # @api.onchange('milestone')
    # def _onchange_milestone(self):
    #     for rec in self:
    def write(self, vals):
        _logger.info("Vals: %s", vals)
        if 'milestone' in vals:
            _logger.info("last milestone: %s", self.milestone)
            _logger.info("Current milestone: %s", vals['milestone'])
            if vals['milestone'] > self.milestone.id:
                last_mile_state = self.milestone.state
                if last_mile_state != 'done':
                    raise UserError(_("You cannot move to the next "
                                      "milestone, if current milestone "
                                      "is not completed"))
        res = super(ProjectTask, self).write(vals)
        return res





