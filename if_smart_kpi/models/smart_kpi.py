from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from urllib.parse import urljoin, urlencode
import base64
from datetime import datetime

class SmartKpi(models.Model):
    _name = "if.smart.kpi"
    _inherit = ["mail.thread"]
    _description = 'Smart KPI'
    _order = "draft_start_date desc, id desc"


    def _get_employee_id(self):
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.uid)])
        if employee:
            return employee.id
        return False


    name = fields.Selection(
        selection=[('1', "January"),
                   ('2', "February"),
                   ('3', "March"),
                   ('4', "April"),
                   ('5', 'May'),
                   ('6', 'June'),
                   ('7', 'July'),
                   ('8', 'August'),
                   ('9', 'September'),
                   ('10', 'October'),
                   ('11', 'November'),
                   ('12', 'December'),
                   ],string="Review Period", required=True)
    year = fields.Many2one("employee.year", string="Year")
    ref_no = fields.Char("Reference Number", readonly=True, default="New KPI")
    period = fields.Selection([('1', "First Half"), ('2', "Second Half")], "Period")
    employee_id = fields.Many2one("hr.employee", "Employee", default=_get_employee_id)
    department_id = fields.Many2one("hr.department", string="Department", related="employee_id.department_id",
                                    readonly=True, store=True)
    job_id = fields.Many2one("hr.job", string="Job Position", related="employee_id.job_id", readonly=True)
    user_id = fields.Many2one("res.users", related="employee_id.user_id")
    user_id_id = fields.Many2one("res.users")
    logged_user_id = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)
    appraiser = fields.Many2one("hr.employee", related="employee_id.parent_id", store=True)
    appraiser_user_id = fields.Many2one("res.users", related="appraiser.user_id")
    kpi_goals_ids = fields.One2many(
        "smart.kpi.goals",
        "smart_kpi_id",
        "Employee Goals",
        store=True,
        copy=True
    )
    kpi_factor_ids = fields.One2many("employee.core.value", "smart_kpi_id", "Factors", copy=True)
    kpi_biz_ids = fields.One2many("employee.biz.value", "smart_kpi_id", "Business Processes", copy=True)
    kpi_goal_score = fields.Float(string="Section A", store=True, readonly=True, compute="_kpi_goal_score")
    kpi_factor_score = fields.Float(string="Section B", store=True, readonly=True, compute="_kpi_goal_score")
    kpi_biz_score = fields.Float(string="Section C", store=True, readonly=True, compute="_kpi_goal_score")
    total_score = fields.Float(string="Total (100%)", store=True, readonly=True, compute="_kpi_goal_score")
    kpi_score = fields.Float(string="Total Score KPI", compute="_total_kpi", store=True)
    kpi_core = fields.Float(string="Total Core Value", compute="_total_core", store=True)
    kpi_score_biz = fields.Float(string="Total Business Score", compute="_total_biz", store=True)
    kra_comment = fields.Text(string="Comment", compute="get_performance", store=True)

    super_comment = fields.Text("Competency Gaps Identified", store=True)
    super_perf = fields.Text("Performance Improvement Plans", store=True)
    super_recommend = fields.Text("Appraisers Recommendation", store=True)

    appraisee_comment = fields.Text("Appraisee's Comment", store=True)
    hr_comment = fields.Text("HR's Comment & Recommendation", store=True)


    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "Review by Manager"),
            ("kpi_set", "KPI Agreed"),
            ("self", "Self-Appraisal"),
            ("mgr", "Manager to appraise"),
            ("emp_comment", "Employee to Comment"),
            ("appraised", "Appraised"),
            ("done", "Done"),
            ('cancel', "Cancelled"),

        ],
        "State", track_visibility="onchange", default="draft",
    )

    draft_deadline = fields.Many2one(
        "kpi.deadline",
        string="Deadline ID",
        default=lambda self: self.env["kpi.deadline"].search([("apply_on_draft", "=", True)], limit=1, order="end_date desc"),
    )
    draft_start_date = fields.Date(string="KPI Start Date", related="draft_deadline.start_date", readonly=1)
    draft_end_date = fields.Date(string="KPI End Date", related="draft_deadline.end_date", readonly=1)

    appraisal_deadline = fields.Many2one(
        "kpi.deadline",
        string="Appraisal Deadline",
        default=lambda self: self.env["kpi.deadline"].search([("apply_for_appraisal", "=", True)], limit=1, order="end_date desc"),
    )
    appraisal_start_date = fields.Date(string="Appraisal Start Date", related="appraisal_deadline.start_date", readonly=1)
    appraisal_end_date = fields.Date(string="Appraisal End Date", related="appraisal_deadline.end_date", readonly=1)

    @api.depends("kpi_goals_ids.final_score", "kpi_factor_ids.final_score2", "kpi_goals_ids.max_score", "kpi_factor_ids.max_score2",
                 "kpi_biz_ids.final_score3", "kpi_biz_ids.max_score3")
    def _kpi_goal_score(self):
        for order in self:
            goals_final_score = sum([line.final_score for line in order.kpi_goals_ids])
            goals_max_score = sum([line.max_score for line in order.kpi_goals_ids])
            factor_final_score = sum([line.final_score2 for line in order.kpi_factor_ids])
            factor_max_score2 = sum([line.max_score2 for line in order.kpi_factor_ids])
            biz_final_score = sum([line.final_score3 for line in order.kpi_biz_ids])
            biz_max_score3 = sum([line.max_score3 for line in order.kpi_biz_ids])


            if goals_max_score > 100:
                raise ValidationError(_("Max Score total cannot be more than 100"))
            if factor_max_score2 > 100:
                raise ValidationError(_("Core Value total cannot be more than 100"))
            if biz_max_score3 > 100:
                raise ValidationError(_("Business Process total value cannot be more than 100"))



            try:

                order.update(
                    {
                        "kpi_goal_score": (goals_final_score / goals_max_score) * 70
                        if goals_max_score > 0
                        else 0,
                        "kpi_factor_score": (factor_final_score / factor_max_score2) * 20
                        if factor_final_score > 0
                        else 0,
                        "kpi_biz_score": (biz_final_score / biz_max_score3) * 10
                        if biz_final_score > 0
                        else 0,
                        "total_score": ((goals_final_score / goals_max_score) * 70)
                                       + ((factor_final_score / factor_max_score2) * 20)
                                       + ((biz_final_score / biz_max_score3) * 10),
                    }
                )
            except ArithmeticError as e:
                pass

    @api.depends("total_score")
    def get_performance(self):
        grade_review = self.env["kpi.grade"].search([])
        for record in grade_review:
            for xxx in record:
                if (self.total_score <= xxx.rate_to) and (self.total_score >= xxx.rate_from):
                    self.kra_comment = xxx.rating_comment



    def button_review(self):
        self.kpi_validation()
        url = self.build_url()
        manager = self.appraiser or self.employee_id.department_id.manager_id
        mail_template = self.env.ref("if_smart_kpi.kpi_submit")
        mail_template.with_context(recipient=manager).send_mail(self.id, force_send=True)
        self.ref_no = self.env['ir.sequence'].next_by_code('if.smart.kpi')
        self.state = "review"

    def button_agree(self):
        if self.employee_id.user_id.id == self.env.uid:
            raise ValidationError(_("Only Your Manager can do this for you"))
        appraisee = self.employee_id
        mail_template = self.env.ref("if_smart_kpi.kpi_approve")
        mail_template.with_context(recipient=appraisee).send_mail(self.id, force_send=True)
        self.state = "kpi_set"

    def button_return(self):
        self.state = "draft"

    def button_appraise(self):
        self.appraisal_validation()
        self.state = "self"

    def button_complete(self):
        self._check_score()
        if self.employee_id.user_id.id == self.env.uid:
            raise ValidationError(_("You cannot appraise yourself"))
        if self.kpi_goal_score == 0:
            raise ValidationError(_("Employee has no Goal Score"))
        if self.kpi_factor_score == 0:
            raise ValidationError(_("Employee has no Core Value Score"))
        if self.kpi_biz_score == 0:
            raise ValidationError(_("Employee has no Business Process Value"))
        appraisee = self.employee_id
        mail_template = self.env.ref("if_smart_kpi.appraisal_submit_employee")
        mail_template.with_context(recipient=appraisee).send_mail(self.id, force_send=True)
        self.state = "emp_comment"

    def button_emp_comment(self):
        if self.employee_id.user_id.id != self.env.uid:
            raise ValidationError(_("You are not the Appraisee"))
        ca = self.env.ref("hr.group_hr_manager").users
        if ca:
            mail_template = self.env.ref("if_smart_kpi.appraisal_completed")
            hr_users_employees = self.env['hr.employee'].sudo().search([('user_id', 'in', ca.ids)])
            for employee in hr_users_employees:
                if employee.work_email:
                    mail_template.with_context(recipient=employee).send_mail(self.id, force_send=True)
        self.state = "appraised"


        # if self.employee_id.user_id.id != self.env.uid:
        #     raise ValidationError(_("You are not the Appraisee"))
        # hr_manager_group = self.env.ref("hr.group_hr_manager")
        # hr_users = hr_manager_group.users
        # hr_users_employees = self.env['hr.employee'].search([('user_id', 'in', hr_users.ids)])
        # mail_template = self.env.ref("if_smart_kpi.appraisal_completed")
        # mail_template.with_context(recipient=hr_users_employees).send_mail(self.id, force_send=True)
        # self.state = "appraised"


    def button_manager(self):
        if self.employee_id.user_id.id != self.env.uid:
            raise ValidationError(_("You are not the Appraisee"))
        manager = self.appraiser or self.employee_id.department_id.manager_id
        mail_template = self.env.ref("if_smart_kpi.appraisal_submit")
        mail_template.with_context(recipient=manager).send_mail(self.id, force_send=True)
        self.state = "mgr"

    def button_hr_comment(self):
        self.state = "done"
    #
    # def button_done(self):
    #     self.state = "done"

    #goals_final_score = sum([line.final_score for line in order.kpi_goals_ids])
    @api.depends('kpi_goals_ids')
    def _total_kpi(self):
        for order in self:
            total = 0.0
            for line in order.kpi_goals_ids:
                total += line.final_score
            order.update({'kpi_score': total})

    @api.depends('kpi_biz_ids')
    def _total_biz(self):
        for order in self:
            total = 0.0
            for line in order.kpi_biz_ids:
                total += line.final_score3
            order.update({'kpi_score_biz': total})

    @api.depends("kpi_factor_ids")
    def _total_core(self):
        for order in self:
            total = 0.0
            for line in order.kpi_factor_ids:
                total += line.final_score2
            order.update({'kpi_core': total})


    def kpi_validation(self):
        today_date = datetime.today()
        if not self.draft_start_date:
            raise UserError(_("Contact HR to set a Deadline Date for the Objectives Setting"))
        start_date = datetime.strptime(str(self.draft_start_date), "%Y-%m-%d")
        end_date = datetime.strptime(str(self.draft_end_date), "%Y-%m-%d")
        goals_max_scoree = sum([line.max_score for line in self.kpi_goals_ids])
        factor_max_scoree2 = sum([line.max_score2 for line in self.kpi_factor_ids])
        biz_max_scoree3 = sum([line.max_score3 for line in self.kpi_biz_ids])
        if start_date > today_date:
            raise UserError(_("Kindly hold on, review starts " + str(start_date)))
        elif today_date > end_date:
            raise UserError(_("Sorry you cannot perform operation, review period ended " + str(end_date)))
        if goals_max_scoree < 100:
            raise UserError(_("Check your KPI and make it 100"))
        if factor_max_scoree2 < 100:
            raise UserError(_("Check your Core Value and make it 100"))
        if biz_max_scoree3 < 100:
            raise UserError(_("Check your Process Section and make it 100"))

    def appraisal_validation(self):
        today_date = datetime.today()
        if not self.appraisal_start_date:
            raise UserError(_("Contact HR to set Appraisal Deadline Date"))
        start_date = datetime.strptime(str(self.appraisal_start_date), "%Y-%m-%d")
        end_date = datetime.strptime(str(self.appraisal_end_date), "%Y-%m-%d")
        if self.state in ("kpi_set", "appraised", "md_comment"):
            if start_date > today_date:
                raise UserError(_("Kindly hold on, appraisal starts " + str(start_date)))
            elif today_date > end_date:
                raise UserError(_("Sorry you cannot perform operation, appraisal ended " + str(end_date)))



    def build_url(self):
        fragment = {}
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        action_id = self.env["ir.model.data"].get_object_reference("if_smart_kpi", "menu_kpi")[1]
        menu_id = self.env["ir.model.data"].get_object_reference("if_smart_kpi", "kpi_menu")[1]
        fragment["view_type"] = "form"
        fragment["menu_id"] = menu_id
        fragment["model"] = "if.smart.kpi"
        fragment["id"] = self.id
        fragment["action"] = action_id
        query = {"db": self._cr.dbname}
        res = urljoin(base_url + "/web", "?%s#%s" % (urlencode(query), urlencode(fragment)))
        return res

    def send_mail(self, body, email):
        mails = self.env["mail.mail"]

        pdf = self.env.ref("if_smart_kpi.report_kra_employee").render_qweb_pdf([self.id])

        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": "KPI Report - " + str(self.employee_id.name),
                    "type": "binary",
                    "datas": base64.b64encode(pdf[0]),
                    "datas_fname": "KPI Report.pdf",
                    "res_model": "if.kpi.smart",
                    "res_id": self.id,
                    "mimetype": "application/x-pdf",
                }
            )
        )

        if not email:
            raise UserError(_("User Does not have an Email. Kindly check User Profile"))

        if email:
            vals = {
                "reply_to": "noreply@domain.com",
                "email_to": email,
                "subject": "KPI Review - " + str(self.employee_id.name),
                "body_html": body,
                "notification": True,
            }
            if self.state == "supervisor" or "appraised":
                vals.update({"attachment_ids": [(4, attachment.id)]})
            mail = self.env["mail.mail"].create(vals)
            mails |= mail
        mails.send()

    @api.depends('kpi_goals_ids','kpi_factor_ids', 'kpi_biz_ids')
    def _check_score(self):
        for record in self:
            for line in record.kpi_goals_ids:
                if line.score > line.max_score:
                    raise ValidationError(_("Manager Score should not be more than Set Weight"))
            for line in record.kpi_factor_ids:
                if line.score2 > line.max_score2:
                    raise ValidationError(_("Manager Score should not be more than Weight in Core Value"))
            for line in record.kpi_biz_ids:
                if line.score3 > line.max_score3:
                    raise ValidationError(_("Check Business Process - Manager Score cannot be more than Weight"))







