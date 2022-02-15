# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EmployeeAppraisal(models.Model):
    _name = "employee.appraisal"
    _description = "Employee Appraisal Template"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.render.mixin']
    _rec_name = 'employee'

    employee = fields.Many2one('hr.employee')
    employee_feedback_template = fields.Html(readonly=False)
    manager_feedback_template = fields.Html(readonly=False)

class CustomHrAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    appr_strt_date = fields.Date('Appraisal Start Date')
    # emp_template = fields.Many2one('employee.appraisal', string='Employee Appraisal template')
    emp_appraisal = fields.Many2one("employee.appraisal", string='Set Employee Appraisal Template')

    @api.depends('employee_id.job_id', 'emp_appraisal')
    def _compute_feedback_templates(self):
        for appraisal in self:
            appraisal.employee_feedback_template = appraisal.emp_appraisal.employee_feedback_template \
                if appraisal.emp_appraisal.id else appraisal.job_id.employee_feedback_template \
                    or appraisal.company_id.appraisal_employee_feedback_template
            appraisal.manager_feedback_template = appraisal.emp_appraisal.manager_feedback_template \
                if appraisal.emp_appraisal.id else appraisal.job_id.manager_feedback_template \
                    or appraisal.company_id.appraisal_manager_feedback_template

    @api.onchange('appr_strt_date')
    def _onchange_start_date(self):
        for rec in self:
            rec.employee_id.sudo().write({
                'next_appraisal_date': rec.appr_strt_date,
            })

    @api.model
    def get_email_to(self):
        return self.employee_id.work_email

    @api.model
    def get_name_of_user(self):

        return self.employee_id.name

    @api.model
    def send_mail_template(self):
        _logger.info("Send mail function")
        templ = self.env.ref('appraisal_custom.appraisal_reminder_email_template')
        start_templ = self.env.ref('appraisal_custom.appraisal_start_email_template')
        _logger.info("Mail template: %s", templ)
        days = datetime.timedelta(days=14)
        today = datetime.date.today()
        _logger.info("Testing code block")

        appr_model = self.env['hr.appraisal']. \
            search([('appr_strt_date', '!=', False)])
        _logger.info("APpr model: %s", appr_model)
        for rec in appr_model:
            _logger.info("Loop self")
            #subtract 14 days from appraisal start date
            two_weeks = rec.appr_strt_date - days

            if today == two_weeks:
                self.env['mail.template'].browse(templ.id). \
                        send_mail(rec.id, force_send=True, raise_exception=True)
            if today == rec.appr_strt_date:
                self.env['mail.template'].browse(start_templ.id). \
                        send_mail(rec.id, force_send=True, raise_exception=True)
            # else:
            #     raise UserError(_("The date is not yet 2 weeks before"))


# class HrEmployee(models.Model):
#     _inherit = "hr.employee"



