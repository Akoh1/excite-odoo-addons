# -*- coding:utf-8 -*-
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class HrPayslipRun(models.Model):
    _name =  'hr.payslip.run'
    # _inherit = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(selection_add=[
                                            ('submit', 'Submit'),
                                            ('approved_hr', 'HR Approved'),
                                            ('approve_cfo', 'CFO Approved'),
                                            ('approve', 'Approved'),
                                            ('close',),
                                            ('reject', 'Rejected'),
                                            ], ondelete={'draft': 'set default'},
                                            tracking=True)

    def action_submit(self):
        _logger.info("Submit to Head HR")
        employees = self.env['hr.employee']. \
            search([])
        managing_dir = employees.filtered(lambda l: l.user_id.id and
                                                  self.env.ref("ng_hr_payroll.ng_head_hr").id in
                                                  l.user_id.groups_id.ids)
        _logger.info("Managing Dir: %s", managing_dir)
        body = "<b> Dear %s </br>" % managing_dir.name
        body += "This payslip has been submitted to you "
        body += "for your approval"
        body += "</b>"
        self.message_post(body=body)
        self.write({'state': 'submit'})
        # body = "<p>Dear All ,<br/><br/> "
        # body += "This is to inform you of %s confirmation, <br/> " % (rec.name)
        # body += "coming uo on %s <br/> " % (rec.confirm_date)
        # body += "%s</p>" % (self.company_id.name)
        #
        # vals = {
        #     'subject': 'Employee Confirmation',
        #     'body_html': body,
        #     'email_to': ",".join(managers_email),
        #     # 'email_to': ";".join(map(lambda x: x, receipt_list)),
        #     # 'email_cc': [emp.work_email for emp in employees],
        #     'auto_delete': False,
        #     'email_from': self.env.user.company_id.email,
        # }
        #
        # _logger.info("Sent confirmation mail successfully")
        # mail_id = self.env['mail.mail'].sudo().create(vals)
        # mail_id.sudo().send()

    def action_approve(self):
        _logger.info("Approved")
        self.write({'state': 'approve'})

    def action_approve_hr(self):
        self.write({'state': 'approved_hr'})

    def action_approve_cfo(self):
        self.write({'state': 'approve_cfo'})

    def action_reject(self):
        _logger.info("Approved")
        self.write({'state': 'reject'})

