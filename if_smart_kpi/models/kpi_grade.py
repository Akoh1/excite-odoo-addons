from odoo import models, api, fields

class PerformanceGrade(models.Model):
    _name = "kpi.grade"

    name = fields.Selection([("A1+", "A1+"), ("A1", "A1"), ("A2", "A2"), ("B", "B"), ("C", "C"), ("D", "D"), ("E","E"),], string="Grade",
                            )
    rate_from = fields.Float(string="Rate From(%)")
    rate_to = fields.Float(string="Rate To(%)")
    comment = fields.Text(string="Comment")
    rating_comment = fields.Text(string="Rating Comment")

class employee_year(models.Model):
    _name = "employee.year"

    name = fields.Char("Year", size=4)
