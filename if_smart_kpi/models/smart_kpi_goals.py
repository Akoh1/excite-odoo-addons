from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SmartKPIGoals(models.Model):
    _name = "smart.kpi.goals"

    name = fields.Text("KPI Details")
    sequence = fields.Integer("Sr.No")
    perf_area = fields.Selection([("1", "Business"), ("2", "Functional")])
    smart_kpi_id = fields.Many2one("if.smart.kpi")
    max_score = fields.Float("Weight", digits=(16, 2))
    emp_score = fields.Float("Employee Score", digits=(16, 2), store=True)
    score = fields.Float("Manager Score", digits=(16, 2), store=True)
    comment = fields.Char("Comment")
    final_score = fields.Float(string="Final Score", store=True, compute="_compute_total", readonly="1")
    state = fields.Char(string="State", compute="_set_state", default="False")
    no_delete = fields.Boolean(string="Delete", compute="_set_no_delete_")


    @api.depends("state")
    def _set_no_delete_(self):
        for rec in self:
            rec.no_delete = False
            if rec.state not in ['draft', 'review']:
                rec.no_delete = True
    #         if rec.state not in ["draft", "review"]:
    #             rec.no_delete = True

    @api.depends("smart_kpi_id.state")
    def _set_state(self):
        for record in self:
            record.state = record.smart_kpi_id.state

    def unlink(self):
        res = self.env['smart.kpi.goals']
        if self.no_delete:
            raise UserError(_('Ugh! Stop deleting the KPIs'))
        return res



    @api.depends("max_score", "score")
    def _compute_total(self):
        for record in self:
            record.final_score = record.score


    # @api.depends("max_score")
    # def _check_score(self):
    #     for record in self:
    #         for line in record.kpi_goals_ids:
    #             if line.score > line.max_score:
    #                 raise UserError(_("check your input"))
