# -*- coding: utf-8 -*-
import logging
import base64
import datetime
from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, format_date, get_lang

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # @api.model
    def get_email_from(self):
        _logger.info("Current user mail: %s", self.env.user.email)
        return self.env.user.email

    # def print_onboard_form(self):
    #     ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
    #     self.ensure_one()
    #     _logger.info("Enter print form")
    #     ir_model_data = self.env['ir.model.data']
    #     # template_id = self._find_mail_template()
    #     template = self.env.ref('employee_onboarding.email_onboarding_missing_fields', raise_if_not_found=False)
    #     _logger.info("Template: %s", template)
    #     # lang = False
    #     # if template:
    #     #     lang = template._render_lang(self.ids)[self.id]
    #     # if not lang:
    #     #     lang = get_lang(self.env).code
    #     # compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
    #     ctx = dict(
    #         default_model='hr.employee',
    #         default_res_id=self.id,
    #         # For the sake of consistency we need a default_res_model if
    #         # default_res_id is set. Not renaming default_model as it can
    #         # create many side-effects.
    #         default_res_model='hr.employee',
    #         default_use_template=bool(template),
    #         default_template_id=template and template.id or False,
    #         default_composition_mode='comment',
    #         mark_hr_as_sent=True,
    #         custom_layout="mail.mail_notification_paynow",
    #         model_description=_("Employee"),
    #         force_email=True
    #     )
    #     # ctx['model_description'] = _('Employee')
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }

    def print_onboard_form(self):
        self.ensure_one()
        _logger.info("Print form")
        # data = {
        #     'test': ['Testing', 'Testing 1'],
        #     'model_id': self.id,
        # }
        # # data = ['Testing', 'Testing 1']
        # docids = self.env['hr.employee'].search([]).ids
        # test_report = self.env.ref('employee_onboarding.action_onboard_missing_form').\
        #     report_action(None, data=data)
        # _logger.info("Test Report template id: %s", test_report)
        report_template_id = self.env.ref(
            'employee_onboarding.action_onboard_missing_form')._render_qweb_pdf(self.id)
        _logger.info("Report template id: %s", report_template_id[0])
        # ir_model_data = self.env['ir.model.data']
        # template_id = None
        # try:
        #     template_id = ir_model_data.get_object_reference('employee_onboarding',
        #                                                      'email_onboarding_missing_fields')[1]
        # except ValueError:
        #     template_id = False
        #     _logger.info("Template Id: %s", template_id)
        # data_record = base64.b64encode(template_id)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Employee Onboarding form",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        _logger.info("Data id: %s", data_id)
        # template = self.env['mail.template']
        template_id = self.env.ref('employee_onboarding.email_onboarding_missing_fields').id
        template = self.env['mail.template'].browse(template_id)
        _logger.info("Self template: %s", template)
        template.attachment_ids = [(6, 0, [data_id.id])]
        template.send_mail(self.id, force_send=True)
        # email_values = {'email_to': self.work_email,
        #                 'email_from': self.env.user.email}
        email_values = {}
        for rec in self:
            email_values['email_to'] = rec.work_email
            email_values['email_from'] = self.env.user.email
        _logger.info("email vals: %s", email_values)
        # template.send_mail(self.id, email_values=email_values, force_send=True)
        _logger.info("Attempt Send")
        template.attachment_ids = [(3, data_id.id)]
        _logger.info("End of print form fnc")
        return True

    @api.model
    def create(self, vals):
        # if vals.get('user_id'):
        #     user = self.env['res.users'].browse(vals['user_id'])
        #     vals.update(self._sync_user(user, vals.get('image_1920') == self._default_image()))
        #     vals['name'] = vals.get('name', user.name)
        employee = super(HrEmployee, self).create(vals)
        today = datetime.date.today()
        future_day = today.day
        future_month = (today.month + 6) % 12
        future_year = today.year + ((today.month + 6) // 12)
        six_months_later = datetime.date(future_year, future_month, future_day)
        _logger.info("6 months: %s", six_months_later)
        # _logger.info("Last Appr: %s", vals['last_appraisal_date'])
        # vals['next_appraisal_date'] = six_months_later
        employee.next_appraisal_date = six_months_later
        return employee

class EmployeeOnboadingReport(models.AbstractModel):
    _name = 'report.employee_onboarding.report_onboarding_form'
    _description = "Employee Onboarding Missing Fields"

    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.info("Report Values Docids: %s", docids)
        docs = self.env['hr.employee'].browse(docids)
        emp_model = self.env['hr.employee']
        # docs = self.env['hr.employee'].browse(data['model_id'])
        _logger.info("Report Values Docs: %s", docs)
        # data = {
        #     'test': [1,2,3],
        #
        # }
        datas = []
        test = {}
        if not docs.address_home_id:
            _logger.info("Field inside: %s", emp_model._fields['address_home_id'].string)
            str_add = emp_model._fields['address_home_id'].string
            test["1"] = str_add
            datas.append(str_add)
            
        if not docs.private_email:
            str_pemail = emp_model._fields['private_email'].string
            test["2"] = str_pemail
            datas.append(str_pemail)

        if not docs.km_home_work:
            str_hm_wk = emp_model._fields['km_home_work'].string
            test["3"] = str_hm_wk
            datas.append(str_hm_wk)
        if not docs.emergency_contact:
            str_em_contact = emp_model._fields['emergency_contact'].string
            test["4"] = str_em_contact
            datas.append(str_em_contact)

        if not docs.emergency_phone:
            str_em_contact = emp_model._fields['emergency_phone'].string
            test["5"] = str_em_contact
            datas.append(str_em_contact)

        if not docs.study_field:
            str_add = emp_model._fields['study_field'].string
            test["6"] = str_add
            datas.append(str_add)
        if not docs.country_id:
            str_add = emp_model._fields['country_id'].string
            test["7"] = str_add
            datas.append(str_add)

        if not docs.identification_id:
            str_add = emp_model._fields['identification_id'].string
            test["8"] = str_add
            datas.append(str_add)

        if not docs.passport_id:
            str_add = emp_model._fields['passport_id'].string
            test["9"] = str_add
            datas.append(str_add)

        if not docs.gender:
            str_add = emp_model._fields['gender'].string
            test["10"] = str_add
            datas.append(str_add)

        if not docs.birthday:
            str_add = emp_model._fields['birthday'].string
            test["11"] = str_add
            datas.append(str_add)

        if not docs.country_of_birth:
            str_add = emp_model._fields['country_of_birth'].string
            test["12"] = str_add
            datas.append(str_add)

        if not docs.place_of_birth:
            str_add = emp_model._fields['place_of_birth'].string
            # test["12"] = str_add
            datas.append(str_add)

        if not docs.children:
            str_add = emp_model._fields['children'].string
            # test["12"] = str_add
            datas.append(str_add)
        if not docs.visa_no:
            str_add = emp_model._fields['visa_no'].string
            # test["12"] = str_add
            datas.append(str_add)

        if not docs.permit_no:
            str_add = emp_model._fields['permit_no'].string
            # test["12"] = str_add
            datas.append(str_add)

        if not docs.visa_expire:
            str_add = emp_model._fields['visa_expire'].string
            # test["12"] = str_add
            datas.append(str_add)
        _logger.info("Report Data: %s", data)
        return {
              'doc_ids': docids,
              'doc_model': 'hr.employee',
              'docs': docs,
              'datas': datas,
            'test': test,
            #   'proforma': True
        }


# class MailComposeMessage(models.TransientModel):
#     _inherit = 'mail.compose.message'

#     def send_mail(self, auto_commit=False):
#         if self.env.context.get('mark_hr_as_sent') and self.model == 'hr.employee':
#             get_emp = self.env['hr.employee'].\
#                 search([('id', '=', self.env.context.get('active_id'))
#                         ], limit=1)
#             _logger.info("I am employee")
#             self = self.with_context(
#                 mail_notify_author=self.env.user.partner_id in self.partner_ids)
#         return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)