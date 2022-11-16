# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class SmartAppraisal(models.Model):
    _name = 'smart.appraisal'
    _description = 'Smart Appraisal'

    name = fields.Many2one('hr.employee')
    position = fields.Many2one(related='name.job_id')
    department_id = fields.Many2one(related='name.department_id')
    manager_id = fields.Many2one(related='name.parent_id',
    							 string='Name of Primary Reviewer')
    manager_position = fields.Many2one(related='name.parent_id.job_id',
    								   string='Position of Primary Reviewer ')
    review_from = fields.Date()
    review_tp = fields.Date()
    

