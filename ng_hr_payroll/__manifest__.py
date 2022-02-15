{
    "name": "Payroll Extract",
    "category": "Localization",
    # "" "author": "Mattobell",
    # "website": "http://www.mattobell.net",
    "depends": ["hr", "hr_payroll", "crm", "hr_holidays", "base", "mail",
                "employee_custom"],
    # "depends": ["hr", "hr_payroll_community", "crm", "hr_holidays",],
    "version": "1.0",
    "description": """
        To enable Employee Payroll Extract
    """,
    "active": False,
    "data": [
        "security/hr_security.xml",
        "security/ir.model.access.csv",
        "views/payslip_batch.xml",
        # "views/ng_hr_view.xml",
        # 'views/ng_hr_salary_view.xml',
        # "views/hr_employee_view.xml",
        # "views/ng_hr_overtime_view.xml",
        # "views/salary_structure.xml",
        # 'views/ng_hr_payroll_view.xml',
        # "views/ng_hr_union_view.xml",
        # "views/ng_hr_terminal_view.xml",
        # "views/ng_hr_payroll_sequence.xml",
        # "views/ng_hr_payroll_report.xml",
        # "views/hr_leave.xml",
        # "data/ng_hr_payroll_data.xml",
        # "wizard/hr_salary_employee_bymonth_view.xml",
        # "wizard/hr_yearly_salary_detail_view.xml",
        # "wizard/hr_yearly_carry_fw_view.xml",
        # "wizard/ng_hr_payroll_13_view.xml",
        # "wizard/contrib_reg_employee.xml",
        "wizard/payroll_register_view.xml",
        # "wizard/account_xls_output_wiz.xml",
        # "report/payment_advice_report_view.xml",
        # "report/payslip_report_view.xml",
        # "report/report_reg.xml",
        # "report/hr_payroll_advise_report.xml",
        # "report/hr_salary_employee_bymonth_ng_report_view.xml",
        # "report/hr_yearly_salary_detail_report.xml",
        # "report/contribution_register_emp_report_view.xml",
        # "report/contribution_register_mod_report_view.xml",
        "report/payroll_register_report_view.xml",
    ],
    # "demo": ["views/ng_hr_payroll_demo.xml"],
    "js": ["static/src/js/view_form.js"],
    "installable": True,
    "auto_install": False,
    "application": False,
}