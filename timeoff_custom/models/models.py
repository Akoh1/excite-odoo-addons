# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class TimeOffCustom(models.Model):
    _inherit = 'hr.leave'

    stand_in = fields.Many2one('hr.employee')
    state = fields.Selection(selection_add=[('validate',), ('resume', 'Resumed')],
                                # ondelete={'resume': 'set default'}
                             )
    resume_date = fields.Date()
    resume_days = fields.Float()

    def action_resume(self):
        today = datetime.date.today()
        # employees = self.env['hr.employee'].\
        #     search([('user_id.groups_id', '=', self.env.ref("hr.group_hr_manager").id)])
        employees = self.env['hr.employee']. \
            search([])
        emp_filter = employees.filtered(lambda l: l.user_id.id and
                                        self.env.ref("hr.group_hr_manager").id in l.user_id.groups_id.ids
                                        )
        # hr_users_model = self.env['res.users'].\
        #     search([('groups_id', '=', self.env.ref("hr.group_hr_manager").id)])
        _logger.info("Hr users: %s", emp_filter)
        managers_email = [e.work_email for e in emp_filter]

        _logger.info("Hr users manager emails: %s", managers_email)
        for rec in self:
            # cur_emp = employees.filtered(lambda l: l.user_id.id == self.env.user.id)
            if rec.employee_id.parent_id:
                _logger.info("new managers: %s", rec.employee_id.parent_id)
                managers_email.append(rec.employee_id.parent_id.work_email)
                _logger.info("new managers mail: %s", managers_email)
            # hr_user = self.env.user. \
            #     has_group("hr.group_hr_user")
            # hr_admin = self.env.user. \
            #     has_group("	hr.group_hr_manager")

            diff = today - rec.request_date_from
            diff_days = diff.days
            _logger.info("Diff Days: %s", diff_days)
            rec.resume_days = diff_days
            rec.resume_date = today
            rec.request_date_to = today
            body = "<p>Dear All ,<br/><br/> "
            body += "This is to inform you that %s has resumed, " % (rec.employee_id.name)
            # body += "we wish him goodluck in his future endeavours<br/> "
            body += "%s</p>" % (self.env.user.company_id.name)

            vals = {
                'subject': 'Employee Resumption',
                'body_html': body,
                'email_to': ",".join(managers_email),
                # 'email_to': ";".join(map(lambda x: x, receipt_list)),
                # 'email_cc': [emp.work_email for emp in employees],
                'auto_delete': False,
                'email_from': self.env.user.company_id.email,
            }

            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()
            rec.state = 'resume'
        _logger.info("Resume")

    @api.depends('date_from', 'date_to', 'employee_id', 'resume_date')
    def _compute_number_of_days(self):
        # res = super(TimeOffCustom, self)._compute_number_of_days()
        # return res
        today = datetime.date.today()
        for holiday in self:
            if not holiday.resume_date:

                if holiday.date_from and holiday.date_to:
                    holiday.number_of_days = \
                    holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
                # elif holiday.resume_date:
                #     holiday.number_of_days = holiday.resume_days
                    # holiday.request_date_to = holiday.resume_date
                else:
                    holiday.number_of_days = 0
            else:
                holiday.number_of_days = holiday.resume_days

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1', 'resume'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))
        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').write({'active': False})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()

        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Your %(leave_type)s planned on %(date)s has been refused',
                           leave_type=holiday.holiday_status_id.display_name, date=holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self._remove_resource_leave()
        self.activity_update()
        return True

    @api.constrains('date_from', 'date_to', 'employee_id', 'resume_date')
    def _check_date_state(self):
        if self.env.context.get('leave_skip_state_check'):
            return
        for holiday in self:
            if holiday.resume_date:
                return
            if holiday.state in ['cancel', 'refuse', 'validate1', 'validate']:
                raise ValidationError(_("This modification is not allowed in the current state."))

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        for holiday in self:
            val_type = holiday.validation_type

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee and not self.resume_date:
                        raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (
                            state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                        if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                            raise UserError(
                                _('You must be either %s\'s manager or Time off Manager to approve this leave') % (
                                    holiday.employee_id.name))
