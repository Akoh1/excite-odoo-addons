import logging
import time
import datetime
from odoo import api, fields, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class hr_salary_rule(models.Model):
    _inherit = "hr.salary.rule"
    _order = "sequence"

class payroll_register_report(models.AbstractModel):
    _name = "report.ng_hr_payroll.payroll_register_report"

    mnths = []
    mnths_total = []
    rules = []
    rules_data = []

    total = 0.0

    def get_periods(self, form):
        #       Get start year-month-date and end year-month-date
        #        first_year = int(form['start_date'][0:4])
        #        last_year = int(form['end_date'][0:4])
        #
        #        first_month = int(form['start_date'][5:7])
        #        last_month = int(form['end_date'][5:7])
        #        no_months = (last_year-first_year) * 12 + last_month - first_month + 1
        #        current_month = first_month
        #        current_year = first_year
        #
        # Get name of the months from integer
        #        mnth_name = []
        #        for count in range(0, no_months):
        #            m = datetime.date(current_year, current_month, 1).strftime('%b')
        #            mnth_name.append(m)
        #            self.mnths.append(str(current_month) + '-' + str(current_year))
        #            if current_month == 12:
        #                current_month = 0
        #                current_year = last_year
        #            current_month = current_month + 1
        #        for c in range(0, (12-no_months)):
        #            mnth_name.append('None')
        #            self.mnths.append('None')
        #

        mnth_name = []
        rules = []
        self.rules.clear()
        #        category_id = form.get('category_id', [])
        #        category_id = category_id and category_id[0] or False
        #        rule_ids = self.env['hr.salary.rule'].search(self.cr, self.uid, [('category_id', '=', category_id)])
        rule_ids = form.get("rule_ids", [])
        if rule_ids:
            for r in self.env["hr.salary.rule"].browse(rule_ids):
                mnth_name.append(r.name)
                _logger.info("Rule name: %s", r.name)
                rules.append(r.id)
                # self.rules.append(r.id)
                self.rules_data.append(r.name)
        _logger.info("Rules: %s", rules)
        # _logger.info("Self Rules: %s", self.rules)
        # self.rules.clear()
        self.rules.extend(rules)
        _logger.info("Self Rules: %s", self.rules)
        # self.rules_data = mnth_name
        return [mnth_name]

    def get_salary(self, form, emp_id, emp_salary, total_mnths):
        #        category_id = form.get('category_id', [])
        #        category_id = category_id and category_id[0] or False

        #        self.cr.execute("select to_char(date_to,'mm-yyyy') as to_date ,sum(pl.total) \
        #                             from hr_payslip_line as pl \
        #                             left join hr_payslip as p on pl.slip_id = p.id \
        #                             left join hr_employee as emp on emp.id = p.employee_id \
        #                             left join resource_resource as r on r.id = emp.resource_id  \
        #                            where p.state = 'done' and p.employee_id = %s and pl.category_id = %s \
        #                            group by r.name, p.date_to,emp.id",(emp_id, category_id,))
        #
        #        sal = self.cr.fetchall()
        #        salary = dict(sal)
        #        total = 0.0
        #        cnt = 1
        #        for month in self.mnths:
        #            if month <> 'None':
        #                if len(month) != 7:
        #                    month = '0' + str(month)
        #                if month in salary and salary[month]:
        #                    emp_salary.append(salary[month])
        #                    total += salary[month]
        #                    total_mnths[cnt] = total_mnths[cnt] + salary[month]
        #                else:
        #                    emp_salary.append(0.00)
        #            else:
        #                emp_salary.append('')
        #                total_mnths[cnt] = ''
        #            cnt = cnt + 1
        #

        #        emp_obj = self.env['hr.employee']
        #        eid = emp_obj.browse(self.cr, self.uid, emp_id)
        #        emp_salary.append(eid.name)
        total = 0.0
        cnt = 0
        flag = 0
        #        for r in self.rules:
        for r in self.env["hr.salary.rule"].browse(self.rules):
            #            self.cr.execute("select pl.name as name ,pl.total \
            #                                 from hr_payslip_line as pl \
            #                                 left join hr_payslip as p on pl.slip_id = p.id \
            #                                 left join hr_payslip_run as pr on pr.id = p.payslip_run_id \
            #                                 left join hr_employee as emp on emp.id = p.employee_id \
            #                                 left join resource_resource as r on r.id = emp.resource_id  \
            #                                where p.employee_id = %s and pl.salary_rule_id = %s \
            #                                and (p.date_from >= %s) AND (p.date_to <= %s) \
            #                                and (pr.state != 'cancel')\
            #                                group by pl.total,r.name, pl.name,emp.id",(emp_id, r, form.get('start_date', False), form.get('end_date', False),))
            self._cr.execute(
                "select pl.name as name ,pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id",
                (emp_id, r.id, form.get("start_date", False), form.get("end_date", False),),
            )
            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1
            if flag > 8:
                continue
            if r.name in salary:
                emp_salary.append(salary[r.name])
                total += salary[r.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[r.name]
            else:
                emp_salary.append("")
        #                total_mnths[cnt] = 0.0
        #            total = 0.0
        #            cnt = 1
        #            for month in self.rules_data:
        #                if month <> 'None':
        #                    if len(month) != 7:
        #                        month = '0' + str(month)
        #                    if month in salary and salary[month]:
        #                        emp_salary.append(salary[month])
        #                        total += salary[month]
        #                        total_mnths[cnt] = total_mnths[cnt] + salary[month]
        #                    else:
        #                        emp_salary.append(0.00)
        #                else:
        #                    emp_salary.append('')
        #                    total_mnths[cnt] = ''
        #                cnt = cnt + 1

        if len(self.rules) < 8:
            diff = 8 - len(self.rules)
            for x in range(0, diff):
                emp_salary.append("")
        return emp_salary, total, total_mnths

    def get_salary1(self, form, emp_id, emp_salary, total_mnths):
        #        category_id = form.get('category_id', [])
        #        category_id = category_id and category_id[0] or False

        #        self.cr.execute("select to_char(date_to,'mm-yyyy') as to_date ,sum(pl.total) \
        #                             from hr_payslip_line as pl \
        #                             left join hr_payslip as p on pl.slip_id = p.id \
        #                             left join hr_employee as emp on emp.id = p.employee_id \
        #                             left join resource_resource as r on r.id = emp.resource_id  \
        #                            where p.state = 'done' and p.employee_id = %s and pl.category_id = %s \
        #                            group by r.name, p.date_to,emp.id",(emp_id, category_id,))
        #
        #        sal = self.cr.fetchall()
        #        salary = dict(sal)
        #        total = 0.0
        #        cnt = 1
        #        for month in self.mnths:
        #            if month <> 'None':
        #                if len(month) != 7:
        #                    month = '0' + str(month)
        #                if month in salary and salary[month]:
        #                    emp_salary.append(salary[month])
        #                    total += salary[month]
        #                    total_mnths[cnt] = total_mnths[cnt] + salary[month]
        #                else:
        #                    emp_salary.append(0.00)
        #            else:
        #                emp_salary.append('')
        #                total_mnths[cnt] = ''
        #            cnt = cnt + 1
        #

        #        emp_obj = self.env['hr.employee']
        #        eid = emp_obj.browse(self.cr, self.uid, emp_id)
        #        emp_salary.append(eid.name)
        total = 0.0
        cnt = 0
        flag = 0
        for r in self.env["hr.salary.rule"].browse(self.rules):
            #        for r in self.rules:
            #            rname = self.env['hr.salary.rule'].browse(self.cr, self.uid, r)
            #            self.cr.execute("select pl.name as name ,pl.total \
            #                                 from hr_payslip_line as pl \
            #                                 left join hr_payslip as p on pl.slip_id = p.id \
            #                                 left join hr_payslip_run as pr on pr.id = p.payslip_run_id \
            #                                 left join hr_employee as emp on emp.id = p.employee_id \
            #                                 left join resource_resource as r on r.id = emp.resource_id  \
            #                                where p.employee_id = %s and pl.salary_rule_id = %s \
            #                                and (p.date_from >= %s) AND (p.date_to <= %s) \
            #                                and (pr.state != 'cancel')\
            #                                group by pl.total,r.name, pl.name,emp.id",(emp_id, r, form.get('start_date', False), form.get('end_date', False),))
            self._cr.execute(
                "select pl.name as name ,pl.total \
                                 from hr_payslip_line as pl \
                                 left join hr_payslip as p on pl.slip_id = p.id \
                                 left join hr_employee as emp on emp.id = p.employee_id \
                                 left join resource_resource as r on r.id = emp.resource_id  \
                                where p.employee_id = %s and pl.salary_rule_id = %s \
                                and (p.date_from >= %s) AND (p.date_to <= %s) \
                                group by pl.total,r.name, pl.name,emp.id",
                (emp_id, r.id, form.get("start_date", False), form.get("end_date", False),),
            )

            sal = self._cr.fetchall()
            salary = dict(sal)
            cnt += 1
            flag += 1
            #            if flag > 8:
            #                continue
            if r.name in salary:
                emp_salary.append(salary[r.name])
                total += salary[r.name]
                total_mnths[cnt] = total_mnths[cnt] + salary[r.name]
            else:
                emp_salary.append("")
        #                total_mnths[cnt] = 0.0
        #            total = 0.0
        #            cnt = 1
        #            for month in self.rules_data:
        #                if month <> 'None':
        #                    if len(month) != 7:
        #                        month = '0' + str(month)
        #                    if month in salary and salary[month]:
        #                        emp_salary.append(salary[month])
        #                        total += salary[month]
        #                        total_mnths[cnt] = total_mnths[cnt] + salary[month]
        #                    else:
        #                        emp_salary.append(0.00)
        #                else:
        #                    emp_salary.append('')
        #                    total_mnths[cnt] = ''
        #                cnt = cnt + 1

        #        if len(self.rules) < 8:
        #            diff = 8 - len(self.rules)
        #            for x in range(0,diff):
        #                emp_salary.append('')
        return emp_salary, total, total_mnths

    def get_employee(self, form, excel=False):
        emp_salary = []
        salary_list = []
        total_mnths = ["Total", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # only for pdf report!
        emp_obj = self.env["hr.employee"]
        emp_ids = form.get("employee_ids", [])
        sum_total = 0

        total_excel_months = [
            "Total",
        ]  # for excel report
        for r in range(0, len(self.rules)):
            total_excel_months.append(0)
        employees = emp_obj.browse(emp_ids)
        for emp_id in employees:
            # state_domain = ('state', 'in', 'open')
            # contract = self.env['hr.contract'].search([('employee_id', '=', emp_id.id),
            #                     ('state', '=', 'open')])
            emp_salary.append(emp_id.job_title)
            emp_salary.append(emp_id.registration_number)
            # emp_salary.append(emp_id.contract_id.salary_grade.name)
            emp_salary.append(emp_id.emp_status)
            emp_salary.append(emp_id.emp_date)
            # emp_salary.append(emp_id.paye_state)
            emp_salary.append(emp_id.bank_account_id.bank_id.name)
            emp_salary.append(emp_id.bank_account_id.acc_number)
            emp_salary.append(emp_id.name)
            total = 0.0
            if excel:
                emp_salary, total, total_mnths = self.get_salary1(
                    form, emp_id.id, emp_salary, total_mnths=total_excel_months
                )
            else:
                emp_salary, total, total_mnths = self.get_salary(form, emp_id.id, emp_salary, total_mnths)
            _logger.info("Emp salary: %s", emp_salary)
            _logger.info("get emp total: %s", total)
            _logger.info("get emp total_mnths: %s", total_mnths)
            _logger.info("Emp salary: %s", emp_salary)
            sum_total += total
            emp_salary.append(total)
            salary_list.append(emp_salary)
            emp_salary = []
        total_mnths.append(sum_total)
        self.mnths_total.append(total_mnths)
        return salary_list

    def get_months_tol(self):
        return self.mnths_total

    def get_total(self):
        for item in self.mnths_total:
            for count in range(1, len(item)):
                if item[count] == "":
                    continue
                self.total += item[count]
        return self.total

    @api.model
    def render_html(self, docids, data=None):
        docs = self.env["hr.employee"].browse(data["form"]["employee_ids"])
        docargs = {
            "time": time,
            "get_employee": self.get_employee,
            "get_periods": self.get_periods,
            "get_months_tol": self.get_months_tol,
            "get_total": self.get_total,
            "doc_ids": data["form"]["employee_ids"],
            "doc_model": "hr.employee",
            "docs": docs,
            "data": data,
            "company": self.env.user.company_id,
        }
        return self.env["report"].render("ng_hr_payroll.payroll_register_report", values=docargs)
