# -*- coding: utf-8 -*-
# Part of Browseinfo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import api, fields, models, _
import datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class exit_request(models.Model):
	_name = "exit.request"
	_description = 'Exit Request'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'mail.render.mixin']
	

	name = fields.Char(string ="Name",related="employee_id.name",readonly=True)
	employee_id =  fields.Many2one('hr.employee',string="Employee" ,required=True)
	req_date = fields.Date(string="Request Date",required=True)
	last_date = fields.Date(string="Last Day Of Work",required=True)
	partner_id= fields.Many2one('res.partner',string="Contact",required=True)
	department_manager_id = fields.Many2one('res.users',string="Department Manager")
	department_id = fields.Many2one('hr.department',string="Department")
	job_title_id = fields.Many2one('hr.job',string="Job Title",required=True)
	user_id = fields.Many2one('res.users',string="User",required=True)
	state = fields.Selection([('draft','Draft'),
							  ('confirm','Confirmed'),
							  ('approved_dept','Approved By Dept Manager'),
							  ('approved_hr','Approved By HR Manager'),
							  ('approved_gen','Approved By General Manager'),
							  ('done','Done')],
							  string='State',default='draft', tracking=True)
	confirmed_by_id = fields.Many2one('res.users',string="Confirmed By",readonly=True)
	approved_by_dept_manager_id = fields.Many2one('res.users',string="Approved By Department Manager",readonly=True)
	approved_by_hr_manager_id = fields.Many2one('res.users',string="Approved By HR Manager",readonly=True)
	approved_by_hr_genral_id = fields.Many2one('res.users',string="Approved By General Manager",readonly=True)
	confirm_date = fields.Date(string="Confirm Date(Employee)",readonly=True)
	approve_date_dept_manager = fields.Date(string="Approved Date(Department Manager)",readonly=True)
	approve_date_hr_manager = fields.Date(string="Approved Date(HR Manager)",readonly=True)
	approve_date_gen_manager = fields.Date(string="Approved Date(General Manager)",readonly=True)
	checklist_ids = fields.Many2many('checklist.information','rel_exit_request_id',string="Checklist",domain=[('state','=','approved')])
	reasone = fields.Text(string="Reason For Exit")
	notes = fields.Text(string="Notes")
	email = fields.Char(string="Email")
	phone = fields.Char(string="Phone")
	survey_id = fields.Many2one('survey.survey', related='job_title_id.survey_id', string="Interview")
	response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
	company_id = fields.Many2one('res.company', 'Company',
    							 default=lambda self: self.env.user.company_id)


	@api.constrains('req_date','last_date')
	def check_end_date(self):
		if self.last_date < self.req_date :
			raise ValidationError(_('Last Day Of Work must be after the Request Date!!'))


	@api.onchange('employee_id')
	def onchange_employee(self):

		self.department_id = self.employee_id.department_id.id
		self.job_title_id = self.employee_id.job_id.id
		

	def action_makeMeeting(self):
		""" This opens Meeting's calendar view to schedule meeting on current applicant
			@return: Dictionary value for created Meeting view
		"""
		self.ensure_one()
		partners = self.partner_id | self.user_id.partner_id | self.department_id.manager_id.user_id.partner_id

		category = self.env.ref('hr_recruitment.categ_meet_interview')
		res = self.env['ir.actions.act_window']._for_xml_id('calendar.action_calendar_event')
		res['context'] = {
			'search_default_partner_ids': self.partner_id.name,
			'default_partner_ids': partners.ids,
			'default_user_id': self.env.uid,
			'default_name': self.name,
			'default_categ_ids': category and [category.id] or False,
		}
		return res


	def action_start_survey(self):
		self.ensure_one()
		# create a response and link it to this applicant
		if not self.response_id:
			response = self.env['survey.user_input'].create({'survey_id': self.survey_id.id, 'partner_id': self.partner_id.id})
			self.response_id = response.id
		else:
			response = self.response_id
		# grab the token of the response and start surveying
		return self.survey_id.action_start_survey(answer=response)

	def action_print_survey(self):
		""" If response is available then print this response otherwise print survey form (print template of the survey) """
		self.ensure_one()
		if not self.response_id:
			return self.survey_id.action_print_survey(answer=self.response_id)
		else:
			response = self.response_id
			return self.survey_id.action_print_survey(answer=response)

	def action_confirm(self):
		self.write({'state': 'confirm'})
		self.confirm_date = datetime.datetime.now().date()
		self.confirmed_by_id = self.env.user.id
		return

	def action_approve_dept(self):
		self.write({'state': 'approved_dept'})
		self.approve_date_dept_manager = datetime.datetime.now().date()
		self.approved_by_dept_manager_id = self.env.user.id
		return

	# def toggle_active(self):
    #     res = super(HrEmployeePrivate, self).toggle_active()
    #     unarchived_employees = self.filtered(lambda employee: employee.active)
    #     unarchived_employees.write({
    #         'departure_reason': False,
    #         'departure_description': False,
    #         'departure_date': False
    #     })
    #     archived_addresses = unarchived_employees.mapped('address_home_id').filtered(lambda addr: not addr.active)
    #     archived_addresses.toggle_active()
    #     if len(self) == 1 and not self.active:
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': _('Register Departure'),
    #             'res_model': 'hr.departure.wizard',
    #             'view_mode': 'form',
    #             'target': 'new',
    #             'context': {'active_id': self.id},
    #             'views': [[False, 'form']]
    #         }
    #     return res

	def action_approve_hr(self):
		self.write({'state': 'approved_hr'})
		self.approve_date_hr_manager = datetime.datetime.now().date()
		self.approved_by_hr_manager_id = self.env.user.id
		# self.employee_id.toggle_active()
		return {
                'type': 'ir.actions.act_window',
                'name': _('Employee Exit'),
                'res_model': 'hr.exit.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
					'active_id': self.id,
					'active_model': 'exit.request',
					'employee_id': self.employee_id.id,
					},
                'views': [[False, 'form']]
            }

	def action_approve_gen(self):
		self.write({'state': 'approved_gen'})
		self.approve_date_gen_manager = datetime.datetime.now().date()
		self.approved_by_hr_genral_id = self.env.user.id
		return

	def action_done(self):
		self.write({'state': 'done'})
		employees = self.env['hr.employee']. \
			search([('active', '=', True),
					('work_email', '!=', False),
					# ('id', '!=', self.employee_id.id)
					])
		_logger.info("Employees: %s", employees)
		body = "<p>Dear All ,<br/><br/> "
		body += "This is to inform you that %s is exiting the organization, " % (self.name)
		body +=  "we wish him goodluck in his future endeavours<br/> "
		body +=  "%s</p>" % (self.company_id.name)
		receipt_list = [emp.work_email for emp in employees]
		_logger.info("Employee work emails: %s", receipt_list)
		vals = {
				'subject': 'Employee Exit',
				'body_html': body,
				'email_to': ",".join(receipt_list),
				# 'email_to': ";".join(map(lambda x: x, receipt_list)),
				# 'email_cc': [emp.work_email for emp in employees],
				'auto_delete': False,
				'email_from': self.company_id.email,
			}

		mail_id = self.env['mail.mail'].sudo().create(vals)
		mail_id.sudo().send()
		return

class exit_checklist(models.Model):
	_name = "checklist.information"
	_description = 'Checklist Information'
	_rec_name = "checklist_id"

	checklist_id = fields.Many2one('exit.checklist',string="Checklist")
	responsible_user_id = fields.Many2one('res.users',string="Responsible User")
	remarks = fields.Char('Remarks')
	exit_request_id = fields.Many2one('exit.request')
	
	state = fields.Selection([('new','New'),('confirm','Confirmed'),('approved','Approved')],string='State',default='new')
	checklist_line_ids = fields.One2many('exit.checklist.line','checklist_info_id',string="Checklist Line")

	@api.onchange('checklist_id')
	def onchange_checklist_id(self):
		
		self.responsible_user_id = self.checklist_id.responsible_user_id.id
		self.remarks = self.checklist_id.notes
		self.checklist_line_ids = self.checklist_id.checklist_line_ids.ids
		return

	def action_confirm(self) :
		self.write({'state': 'confirm'})
		return

	def action_approve(self) :
		self.write({'state': 'approved'})
		return

class employee_exit_checklist(models.Model):
	_name = "exit.checklist"
	_description = 'Exit Checklist'

	name = fields.Char(string = "Checklist")
	responsible_user_id = fields.Many2one('res.users',string="Responsible User")
	notes = fields.Char('Notes')
	
	checklist_line_ids = fields.One2many('exit.checklist.line','checklist_id',string="Checklist")

class checklist_lines(models.Model):
	_name = "exit.checklist.line"
	_description = 'Exit Checklist Line'

	name = fields.Char(string="Name")
	checklist_id = fields.Many2one('exit.checklist')
	checklist_info_id = fields.Many2one('checklist.information')


class HrExitWizard(models.TransientModel):
    _name = 'hr.exit.wizard'
    _description = 'Employee Exit Wizard'

    name = fields.Many2one('hr.employee', string="Employee", required=True,
						   readonly=True,
						   default=lambda self: self.env.context.get('employee_id', None),)

    def deactivate_employee(self):
        today = datetime.date.today()
        self.name.write({
			'active': False,
			'departure_date': today,
		})
        return
