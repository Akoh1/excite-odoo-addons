from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class SmartKPIFactor(models.Model):
    _name = "smart.kpi.factor"

    name = fields.Char(string="Performance Area")
    mea_success = fields.Char(string="Measure of Success")
    # target2 = fields.Float("Target", digits=(16, 2), store=True)
    max_score2 = fields.Float("Weight", digits=(16, 2))


class SmartKPICore(models.Model):
    _name = "employee.core.value"

    factor_id = fields.Many2one("smart.kpi.factor", string="Performance Area", copy=True)
    # name = fields.Char(string="Performance Area", related="factor_id.name", store=True)
    mea_success = fields.Char(string="Measure of Success", related="factor_id.mea_success", store=True)
    max_score2 = fields.Float(string="Weight", related="factor_id.max_score2", store=True)
    emp_score2 = fields.Float(string="Employee Score", digits=(16, 2), store=True)
    score2 = fields.Float("Manager Score", digits=(16, 2), store=True)
    evi_com = fields.Char("Evidence/Comment")
    smart_kpi_id = fields.Many2one("if.smart.kpi")
    final_score2 = fields.Float(string="Final Score", store=True, compute="_compute_total", readonly="1")

    @api.depends("max_score2", "score2")
    def _compute_total(self):
        for record in self:
            record.final_score2 = record.score2
