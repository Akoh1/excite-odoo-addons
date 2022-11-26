from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

class SmartKPIBiz(models.Model):
    _name = "smart.kpi.biz"

    name = fields.Char(string="Business Process")
    mea_success3 = fields.Char(string="Measure of Success")
    max_score3 = fields.Float("Weight", digits=(16, 2))


class SmartKPICoreBiz(models.Model):
    _name = "employee.biz.value"

    biz_id = fields.Many2one("smart.kpi.biz", string="Business Process", copy=True)
    # name = fields.Char(string="Performance Area", related="factor_id.name", store=True)
    mea_success = fields.Char(string="Measure of Success", related="biz_id.mea_success3", store=True)
    max_score3 = fields.Float(string="Weight", related="biz_id.max_score3", store=True)
    emp_score3 = fields.Float(string="Employee Score", digits=(16, 2), store=True)
    score3 = fields.Float("Manager Score", digits=(16, 2), store=True)
    evi_com = fields.Char("Evidence/Comment")
    smart_kpi_id = fields.Many2one("if.smart.kpi")
    final_score3 = fields.Float(string="Final Score", store=True, compute="_compute_total", readonly="1")

    @api.depends("max_score3", "score3")
    def _compute_total(self):
        for record in self:
            record.final_score3 = record.score3
