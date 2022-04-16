# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class EmployeeResCompany(models.Model):
    _inherit = "res.company"

    set_days_mail = fields.Integer(readonly=False,
                                string="Number of Days before Confirmation to send mail")


class AutoBankResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    set_days_mail = fields.Integer(related="company_id.set_days_mail", readonly=False,
                                string="Number of Days before Confirmation to send mail")

class Pension(models.Model):
    _name = 'hr.pension'
    _description = 'Pension Administrator'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    name = fields.Char()
    # pin = fields.Char()
    # _sql_constraints = [
    #     ('pin_unique', 'unique(pin)',
    #      'Cannot have duplicate Pension PIN!')
    # ]


class HMO(models.Model):
    _name = 'hr.hmo'
    _description = 'HMO Administrator'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    name = fields.Char()
    # hmo_id = fields.Char('HMO ID')
    # _sql_constraints = [
    #     ('hmo_id_unique', 'unique(hmo_id)',
    #      'Cannot have duplicate HMO ID!')
    # ]


# class PublicHoliday(models.Model):
#     _name = 'public.holiday'
#     _description = 'Public Holiday'
#     _inherit = ['mail.thread.cc', 'mail.activity.mixin']

#     name = fields.Char('Description')
#     date = fields.Date()


class HrSalaryGrade(models.Model):
    _name = 'hr.salary.grade'
    _description = 'Salary Grade'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']

    name = fields.Char(string="Subject Name")
    # parameters = fields.One2many('hr.salary.parameter', 'grade_id')
    gross_salary = fields.Float(string="Wage")
    basic_trans = fields.Float('Basic Transport')
    housing = fields.Float('Housing')
    leave_allowance = fields.Float()
    utility = fields.Float()
    meal = fields.Float()
    trans = fields.Float('Transport')
    wardrobe = fields.Float()
    ent = fields.Float('Entertainment')
    education = fields.Float()
    th_month = fields.Float('13th Month')
    other = fields.Float()
    other_two = fields.Float('Other 2')

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100

# class HrSalaryGradeParameters(models.Model):
#     _name = 'hr.salary.parameter'
#     _description = 'Salary Grade Parameters'
#
#     name = fields.Char()
#     grade_id = fields.Many2one('hr.salary.grade')
#     amount = fields.Float()

class Contract(models.Model):
    _inherit = 'hr.contract'

    salary_grade = fields.Many2one('hr.salary.grade')
    manager_status = fields.Selection([
        ('manager', 'Manager'),
        ('not_manager', 'Non Manager'),

    ], string='Manager Status', tracking=True,
        copy=False)
    gross_salary = fields.Float(compute="_compute_salary_params", store=True)
    basic_trans = fields.Float('Basic Transport', compute="_compute_salary_params",
                               store=True)
    housing = fields.Float('Housing', compute="_compute_salary_params",
                           store=True)
    leave_allowance = fields.Float(compute="_compute_salary_params",
                                   store=True)
    utility = fields.Float(compute="_compute_salary_params", store=True)
    meal = fields.Float(compute="_compute_salary_params", store=True)
    trans = fields.Float('Transport', compute="_compute_salary_params", store=True)
    wardrobe = fields.Float(compute="_compute_salary_params", store=True)
    ent = fields.Float('Entertainment', compute="_compute_salary_params", store=True)
    education = fields.Float(compute="_compute_salary_params", store=True)
    th_month = fields.Float('13th Month', compute="_compute_salary_params", store=True)
    other = fields.Float(compute="_compute_salary_params", store=True)
    other_two = fields.Float('Other 2', compute="_compute_salary_params", store=True)
    check_wage_readonly = fields.Boolean(default=False)

    @api.depends('salary_grade')
    def _compute_salary_params(self):
        for rec in self:
            rec.gross_salary = rec.salary_grade.gross_salary
            rec.basic_trans = rec.salary_grade.basic_trans
            rec.housing = rec.salary_grade.housing
            rec.leave_allowance = rec.salary_grade.leave_allowance
            rec.utility = rec.salary_grade.utility
            rec.meal = rec.salary_grade.meal
            rec.trans = rec.salary_grade.trans
            rec.wardrobe = rec.salary_grade.wardrobe
            rec.ent = rec.salary_grade.ent
            rec.education = rec.salary_grade.education
            rec.th_month = rec.salary_grade.th_month
            rec.other = rec.salary_grade.other
            rec.other_two = rec.salary_grade.other_two
            rec.wage = rec.salary_grade.gross_salary

    @api.onchange('salary_grade')
    def _check_wage_readonly(self):
        for rec in self:
            rec.check_wage_readonly = True if rec.salary_grade.id else False
            # if rec.salary_grade.id:
            #     rec.check_wage_readonly = True

class Employee(models.Model):
    _inherit = 'hr.employee'

    states = fields.Many2one('res.country.state', string="State Of origin",
                             domain="[('country_id', '=', country_id)]")
    geo_zone = fields.Selection([
        ('ne', 'North East'),
        ('sw', 'South West'),
        ('nc', 'North Central'),
        ('se', 'South East'),
        ('nw', 'North West'),
        ('ss', 'South South'),
    ], string='Geopolitical Zone', tracking=True,
        copy=False)
    emp_status = fields.Selection([
        ('full', 'Full Employment'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('consult', 'Consulting'),
        ('others', 'Others'),
    ], string='Employment Status', tracking=True,
        copy=False)
    emp_date = fields.Date('Employment Date')
    start_date = fields.Date()
    prob_days = fields.Integer("Probation Days")
    confirm_date = fields.Date('Suggested Confirmation Date', compute="_compute_confirm_date",
                               store=True)
    date_confirm = fields.Date('Date Confirmed')
    confirm_status = fields.Selection([
        ('confirm', 'Confirmed'),
        ('not_confirm', 'Not Confirmed'),

    ], string='Confirmation Status', tracking=True,
        copy=False, default='not_confirm')
    emg_rel = fields.Selection([
        ('husband', 'Husband'),
        ('wife', 'Wife'),
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('brother', 'Brother'),
        ('sister', 'Sister'),
        ('daughter', 'Daughter'),
        ('son', 'Son'),
        ('aunt', 'Aunt'),
        ('uncle', 'Uncle'),
        ('others', 'Others'),
    ], string='Emergency Relationship', tracking=True,
        copy=False)
    pension_admin = fields.Many2one('hr.pension', string="Pension Administrator")
    pension_pin = fields.Char(string="Pension PIN")
    hmo_admin = fields.Many2one('hr.hmo', string="HMO Administrator")
    hmo_id = fields.Char( string="HMO ID")
    paye_state = fields.Char(string='PAYE State')
    _sql_constraints = [
        ('pin_unique', 'unique(pension_pin)',
         'Cannot have duplicate Pension PIN!'),
        ('hmo_id_unique', 'unique(hmo_id)',
         'Cannot have duplicate HMO ID!')
    ]

    def confirm_employee(self):
        self.write({
            'confirm_status': 'confirm',
            'date_confirm': datetime.date.today(),
        })

    @api.depends('prob_days', 'emp_date')
    def _compute_confirm_date(self):
        for rec in self:
            _logger.info("Confirm Date")
            today = datetime.date.today()
            num_days_after = rec.emp_date + datetime.timedelta(days=rec.prob_days) \
                if rec.emp_date else None
            _logger.info("6 months: %s", num_days_after)
            rec.confirm_date = num_days_after

    @api.model
    def _send_mail_before_confirmation(self):
        """
        This Function is called as a cron job to send mails to Hr managers
        of pending confirmation number of days set in Employee settingd
        before confirmation date.

        """

        employees = self.env['hr.employee']. \
            search([])
        emp_filter = employees.filtered(lambda l: l.user_id.id and
                                                  self.env.ref("hr.group_hr_manager").id in l.user_id.groups_id.ids)

        _logger.info("Hr users: %s", emp_filter)
        managers_email = [e.work_email for e in emp_filter]
        get_days = self.env.user.company_id.set_days_mail
        _logger.info("Company: %s", self.env.user.company_id.name)
        _logger.info("Hr users manager emails: %s", managers_email)

        for rec in employees.filtered(lambda l: l.confirm_date is not False):

            body = "<p>Dear All ,<br/><br/> "
            body += "This is to inform you of %s confirmation, <br/> " % (rec.name)
            body += "coming uo on %s <br/> " % (rec.confirm_date)
            body += "%s</p>" % (self.company_id.name)

            vals = {
                'subject': 'Employee Confirmation',
                'body_html': body,
                'email_to': ",".join(managers_email),
                # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                # 'email_cc': [emp.work_email for emp in employees],
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }
            # get_days = self.company_id.set_days_mail
            # _logger.info("Company: %s", self.company_id.name)
            days = datetime.timedelta(days=get_days)
            _logger.info("Number of days set in settings: %s", get_days)
            days_before = rec.confirm_date - days
            today = datetime.date.today()
            if today == days_before:
                _logger.info("Sent confirmation mail successfully")
                mail_id = self.env['mail.mail'].sudo().create(vals)
                mail_id.sudo().send()
            else:
                _logger.info("Not amount of days before confirmation")

        _logger.info("Sent email for confirmation")