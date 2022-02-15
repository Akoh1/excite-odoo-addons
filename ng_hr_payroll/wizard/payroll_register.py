##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Mattobell (<http://www.mattobell.com>)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
import logging
import time
import xlwt
from io import StringIO, BytesIO
import base64
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)

class payroll_reg(models.TransientModel):

    _name = "payroll.register"
    _description = "Payroll Register"

    name = fields.Char(string="Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    employee_ids = fields.Many2many(
        "hr.employee", "payroll_register_rel", "payroll_year_id", "employee_id", string="Employees", required=True
    )
    rule_ids = fields.Many2many(
        "hr.salary.rule", "payroll_register_rel_salary", "reg_id", "rule_id", string="Salary Rules", required=True
    )
    xls_output = fields.Boolean(string="Excel Output", help="Tick if you want to output of report in excel sheet")

    def print_report(self):
        _logger.info("Print report")
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: return report
        """
        context = self._context or {}
        datas = {"ids": context.get("active_ids", [])}

        res = self.read()
        res = res and res[0] or {}
        datas.update({"form": res})
        if datas["form"].get("xls_output", False):
            obj_pr = self.env["report.ng_hr_payroll.payroll_register_report"]
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet("Payroll Register")
            sheet.row(0).height = 256 * 3
            title_style = xlwt.easyxf("font: name Times New Roman,bold on, italic on, height 600")
            title_style1 = xlwt.easyxf("font: name Times New Roman,bold on")
            al = xlwt.Alignment()
            al.horz = xlwt.Alignment.HORZ_CENTER
            title_style.alignment = al
            sheet.write_merge(0, 0, 5, 9, "Payroll Register", title_style)
            sheet.write(1, 6, datas["form"]["name"], title_style1)
            sheet.write(2, 4, "From", title_style1)
            sheet.write(2, 5, datas["form"]["start_date"], title_style1)
            sheet.write(2, 6, "To", title_style1)
            sheet.write(2, 7, datas["form"]["end_date"], title_style1)
            main_header = obj_pr.get_periods(datas["form"])
            _logger.info("Main header: %s", main_header)
            row = self.render_header(sheet, ["Job Title"] + ["Staff Number"] +
                                     ['Grade'] + ['Employment Status'] + ['Date Employed'] +
                                     ['PAYE State'] + ['Bank Name'] + ['Account Number'] +
                                     ["Name"] + main_header[0] + ["Total"], first_row=5)
            _logger.info("Row: %s", row)
            emp_datas = obj_pr.get_employee(datas["form"], excel=True)
            _logger.info("Emp Data: %s", emp_datas)
            value_style = xlwt.easyxf("font: name Helvetica,bold on", num_format_str="#,##0.00")
            cell_count = 0
            for value in emp_datas:
                for v in value:
                    sheet.write(row, cell_count, v, value_style)
                    cell_count += 1
                row += 1
                cell_count = 0
            sheet.write(row + 1, 0, "Total", value_style)
            total_datas = obj_pr.get_months_tol()
            cell_count = 1
            row += 1
            for record in total_datas[-1][1:]:
                sheet.write(row, cell_count, record, value_style)
                cell_count += 1

            stream = BytesIO()
            workbook.save(stream)
            ctx = {"default_xls_output": base64.encodebytes(stream.getvalue())}
            ir_attachment = (
                self.env["ir.attachment"]
                .create({"name": self.name + ".xls", "datas": base64.encodebytes(stream.getvalue()),})
                .id
            )
            actid = self.env.ref("base.action_attachment")[0]
            myres = actid.read()[0]
            myres["domain"] = "[('id','in',[" + ",".join(map(str, [ir_attachment])) + "])]"
            return myres
        return self.env["report"].get_action(self, "ng_hr_payroll.payroll_register_report", data=datas)

    def render_header(self, ws, fields, first_row=0):
        header_style = xlwt.easyxf("font: name Helvetica,bold on")
        col = 0
        for hdr in fields:
            ws.write(first_row, col, hdr, header_style)
            col += 1
        return first_row + 2


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
