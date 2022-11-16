# -*- coding: utf-8 -*-
import logging
import secrets
import string
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class JobLocation(models.Model):
    _name = "job.location"
    _description = "Job Location"

    name = fields.Char()

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
    job_location = fields.Many2one('job.location', string="Job location")
    job_type = fields.Selection([
        ('full_time', 'Full time'),
        ('contract', 'Contract'),
        ('internship', 'Internship')
    ], copy=False, index=True, tracking=True)

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
    resume = fields.Binary(string='Resume/CV')
    resume_id = fields.Many2one('ir.attachment', string="Resume Attachment", required=True)

    # @api.onchange('stage_id')
    # def _onchange_stage(self):
    #     _logger.info("Change recruit stage")
    #     for rec in self:
    #         # tmp_stage = rec.stage_id
    #         stage_ids = self.env['hr.recruitment.stage'].search([])
    #         _logger.info("Recruit stages: %s", stage_ids)
    #         _logger.info("Last stage: %s", rec.last_stage_id)
    #         _logger.info("Stage id: %s", rec.stage_id)

    # @api.depends('job_id')
    # def _compute_stage(self):
    #     _logger.info("Change recruitment stage")
    #     for applicant in self:
    #         if applicant.job_id:
    #             if not applicant.stage_id:
    #                 stage_ids = self.env['hr.recruitment.stage'].search([
    #                     '|',
    #                     ('job_ids', '=', False),
    #                     ('job_ids', '=', applicant.job_id.id),
    #                     ('fold', '=', False)
    #                 ], order='sequence asc', limit=1).ids
    #                 applicant.stage_id = stage_ids[0] if stage_ids else False
    #         else:
    #             applicant.stage_id = False

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

    def write(self, vals):
        # user_id change: update date_open
        # if vals.get('user_id'):
        #     vals['date_open'] = fields.Datetime.now()
        # if vals.get('email_from'):
        #     vals['email_from'] = vals['email_from'].strip()
        # # stage_id: track last stage before update
        # if 'stage_id' in vals:
        #     vals['date_last_stage_update'] = fields.Datetime.now()
        #     if 'kanban_state' not in vals:
        #         vals['kanban_state'] = 'normal'
        #     for applicant in self:
        #         vals['last_stage_id'] = applicant.stage_id.id
        #         res = super(Applicant, self).write(vals)
        # else:
        # _logger.info("Write last stage: %s", self.stage_id)
        # _logger.info("Write Current stage: %s", vals['stage_id'])
        if 'stage_id' in vals and vals['stage_id'] > self.stage_id.id and vals['stage_id'] - self.stage_id.id > 1:
            raise UserError(_("You must proceed to the next stage first"))
        elif 'stage_id' in vals and  vals['stage_id'] < self.stage_id.id and self.stage_id.id - vals['stage_id'] > 1:
            raise UserError(_("You must proceed to the next stage first"))
        res = super(Applicant, self).write(vals)
        return res
