# -*- coding: utf-8 -*-
import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class HelpStage(models.Model):
    """ Model for case stages. This models the main stages of a document
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "help.stage"
    _description = "Help To Own Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    is_won = fields.Boolean('Is Final Stage?')
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: Offer sent to customer). It will appear as a tooltip over the stage's name.")
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')



class HelpToOwn(models.Model):
    _name = 'help.own'
    _description = 'Help To Own'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _rec_name = 'name'

    @api.model
    def _default_value(self):
        return self.env['help.stage'].search([], limit=1)

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        # help_id = self.env.context.get('default_project_id')
        # if not help_id:
        #     return False
        return self.stage_find([('fold', '=', False)])

    @api.model
    def _default_company_id(self):
        return self.env.company

    desired_home = fields.Integer()
    company_name = fields.Char()
    company_address = fields.Char()
    company_state = fields.Char()
    company_lga = fields.Char()
    occupation = fields.Char()
    income = fields.Integer()
    sector = fields.Char()
    first_time_buyer = fields.Char()
    full_name = fields.Char()
    date_of_birth = fields.Date()
    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female')
    ], copy=False, index=True, tracking=True)
    marital_status = fields.Char(readonly=True)
    no_of_dependants = fields.Integer()
    current_address = fields.Char()
    current_state = fields.Char()
    ownership_type = fields.Char()
    years_of_residence = fields.Integer()
    name = fields.Char()
    payment_method = fields.Char()
    product_id = fields.Many2one('product.product', string="Property")
    stage_id = fields.Many2one(
        'help.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id',
        readonly=False, store=True, default=_get_default_stage_id,
        copy=False, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company', store=True, readonly=False,
        required=True, copy=True, default=_default_company_id)

    @api.depends('company_id', 'stage_id')
    def _compute_stage_id(self):
        for task in self:
            task.stage_id = task.stage_find([
                        ('fold', '=', False)])

    def stage_find(self, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - section_id: if set, stages must belong to this section or
              be a default stage; if not set, stages must be default
              stages
        """
        # collect all section_ids
        # section_ids = []
        # if section_id:
        #     section_ids.append(section_id)
        # section_ids.extend(self.mapped('project_id').ids)
        # search_domain = []
        # if section_ids:
        #     search_domain = [('|')] * (len(section_ids) - 1)
        #     for section_id in section_ids:
        #         search_domain.append(('project_ids', '=', section_id))
        # search_domain += list(domain)
        # perform search, return the first found
        return self.env['help.stage'].search(domain, order=order, limit=1).id
    




