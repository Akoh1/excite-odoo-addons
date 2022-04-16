import logging
import requests
import json
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class FhflProjectProject(models.Model):
    _inherit = 'project.project'

    investment_id = fields.Many2one('crm.investment')