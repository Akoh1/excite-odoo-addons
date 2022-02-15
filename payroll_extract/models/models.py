# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class PayrollWizard(models.TransientModel):
    _name = 'payroll.extract.wizard'
    _description = 'Wizard for Employee Payroll Extract'

    start_date = fields.Date()
    end_date = fields.Date()

    def download_excel(self):
        _logger.info("Downloading document")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def render_extract_wizard(self):
        return {
            'name': _('Employee Payroll Extract Wizard'),
            'res_model': 'payroll.extract.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'hr.payslip',
                'active_ids': self.ids,
                # 'rave_pay': True,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
