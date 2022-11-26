from odoo import api, fields, models

class KPIDeadline(models.Model):
    _name = "kpi.deadline"

    name = fields.Char(string="Deadline")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    apply_on_draft = fields.Boolean("Apply on KPI Setting")
    apply_for_appraisal = fields.Boolean("Apply on Appraisal")

    @api.onchange("start_date", "end_date")
    def set_name(self):
        if self.start_date and self.end_date:
            self.name = str(self.start_date) + " - " + str(self.end_date)