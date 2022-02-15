# -*- coding: utf-8 -*-
import logging
import secrets
import string
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _inherit = 'hr.contract'

    wage = fields.Monetary('Wage', required=False, tracking=True, help="Employee's monthly gross wage.")

class HrEmployeeSalary(models.Model):
    _inherit = "hr.employee"

    @api.model
    def create(self, vals):
        employee = super(HrEmployeeSalary, self).create(vals)
        contract = self.env['hr.contract']. \
            create({
            'name': '{} Contract'.format(employee.name),
            'employee_id': employee.id,
            'department_id': employee.department_id.id,
            'job_id': employee.job_id.id,
            'structure_type_id': employee.job_id.salary_structure.id or None,
            'date_start': datetime.date.today(),
            'first_contract_date': datetime.date.today(),
            'resource_calendar_id': vals['resource_calendar_id']
                if 'resource_calendar_id' in vals else employee.resource_calender_id.id,
            'state': 'open'
        })
        employee.contract_ids = [(6, 0, contract.id)]
        return employee

class Job(models.Model):
    _inherit = "hr.job"

    ref_num = fields.Char(string="REF NUMBER", readonly=True)
    salary_structure = fields.Many2one('hr.payroll.structure.type')
    state = fields.Selection(selection_add=[('draft', 'Draft'), ('recruit',)],
                             ondelete={'draft': 'set default'}, default='draft')

    def hr_approve(self):
        _logger.info("Hr approve here")
        self.write({'state': 'recruit'})

    @api.model
    def create(self, values):
        _logger.info("Values: %s", values)
        rand_num = ''. \
            join(secrets.choice(string.ascii_uppercase +
                                string.digits) for i in range(7))
        if 'ref_num' in values:
            _logger.info("There is Ref num")
            values['ref_num'] = rand_num
        res = super(Job, self.with_context(mail_create_nosubscribe=True)).create(values)
        return res


class Applicant(models.Model):
    _inherit = "hr.applicant"

    interview_scores = fields.Float("Interview Scores")

    def create_employee_from_applicant(self):
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.display_name
            else:
                if not applicant.partner_name:
                    raise UserError(_('You must define a Contact Name for this applicant.'))
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'type': 'private',
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                applicant.partner_id = new_partner_id
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.partner_name or contact_name:
                # contract = self.env['hr.contract'].\
                #     create
                employee_data = {
                    'default_name': applicant.partner_name or contact_name,
                    'default_job_id': applicant.job_id.id,
                    'default_job_title': applicant.job_id.name,
                    'address_home_id': address_id,
                    'default_department_id': applicant.department_id.id or False,
                    'default_address_id': applicant.company_id and applicant.company_id.partner_id
                                          and applicant.company_id.partner_id.id or False,
                    'default_work_email': applicant.department_id and applicant.department_id.company_id
                                          and applicant.department_id.company_id.email or False,
                    'default_work_phone': applicant.department_id.company_id.phone,
                    'form_view_initial_mode': 'edit',
                    'default_applicant_id': applicant.ids,
                }

                other_applicants = self.env['hr.applicant']. \
                    search([('job_id', '=',applicant.job_id.id)])
                for others in other_applicants:
                    if others.email_from is not None:
                        body = "<p>Dear %s ,<br/><br/> " % others.partner_name
                        body += "This is to inform you that we will not be proceeding with your application, "
                        body += "Thank you for your time in this process<br/> "
                        body += "and we wish you goodluck in your future endeavours<br/> "
                        body += "%s</p>" % (self.env.user.company_id.name)

                        _logger.info("Applicants emails: %s", others.email_from)
                        vals = {
                            'subject': 'Application Status',
                            'body_html': body,
                            'email_to': others.email_from,
                            # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                            # 'email_cc': [emp.work_email for emp in employees],
                            'auto_delete': False,
                            'email_from': self.env.user.company_id.email,
                        }

                        mail_id = self.env['mail.mail'].sudo().create(vals)
                        mail_id.sudo().send()

        dict_act_window = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list')
        dict_act_window['context'] = employee_data
        return dict_act_window