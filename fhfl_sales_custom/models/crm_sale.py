# -*- coding: utf-8 -*-
import calendar
import datetime
# from datetime import datetime, timedelta
from dateutil.relativedelta import *
import logging
import requests
import json
# from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class InstallmentScheme(models.Model):
    _name = 'installment.scheme'

    name = fields.Char('Description')
    num_months = fields.Integer('Number of months')

class FhflSalesLead(models.Model):
    _inherit = "crm.lead"

    desired_home = fields.Integer()
    company_name = fields.Char()
    company_address = fields.Char()
    company_state = fields.Char()
    company_lga = fields.Char()
    occupation = fields.Char()
    income = fields.Integer()
    sector = fields.Char()
    first_time_buyer = fields.Char()
    full_name = fields.Char()
    date_of_birth = fields.Date()
    gender = fields.Selection([
        ('m', 'Male'),
        ('f', 'Female')
    ], copy=False, index=True, tracking=True)
    marital_status = fields.Char(readonly=True)
    no_of_dependants = fields.Integer()
    current_address = fields.Char()
    current_state = fields.Char()
    ownership_type = fields.Char()
    years_of_residence = fields.Integer()
    # name = fields.Char()
    payment_method = fields.Char()
    sales_type = fields.Selection([
        ('outright', 'Outright'),
        ('installment', 'Installment'),
        # ('mortgage', 'Mortgage'),
        ], string='Sales Type', copy=False, index=True, tracking=True)
    product_id = fields.Many2one('product.product', string="Property")
    quantity = fields.Integer()
    is_final = fields.Boolean(compute="_compute_final_stage", store=True)
    installment_scheme = fields.Many2one('installment.scheme')
    num_months =  fields.Integer(related='installment_scheme.num_months')
    start_date = fields.Date()
    end_date = fields.Date()

    @api.depends('stage_id')
    def _compute_final_stage(self):
    	for rec in self:
    		_logger.info("Final stage")
    		rec.is_final = True if rec.stage_id.is_won else False

    def action_new_quotation(self):
        res = super(FhflSalesLead, self).action_new_quotation()
        # sale_order = self.env['sale.order']
        cre_line = {
            'product_id': self.product_id.id,
            'name': str(self.product_id.get_product_multiline_description_sale()),
            'price_unit': self.product_id.lst_price,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id
        }
        if self.sales_type == 'installment' and self.start_date:
            cre_intsall_line = []
            period = 0
            start_date = self.start_date
            for i in range(self.num_months):
                # period = 0
                date = self.start_date

                end_date = date + relativedelta(months=period)
                days_in_month = calendar. \
                    monthrange(end_date.year,
                               end_date.month)[1]
                end_date = end_date + datetime.timedelta(days=days_in_month)

                # end_date = date + relativedelta(months=period)
                # # # end_date = date.replace(day = calendar.monthrange(date.year, date.month)[1])
                # last_date = calendar.monthrange(end_date.year, end_date.month)[1]
                # end_date = end_date.replace(day=last_date)

                # next_date = end_date + datetime.timedelta(days=1)
                # _logger.info("Next start Date: %s", next_date)
                description = self.product_id.get_product_multiline_description_sale()
                amount = self.product_id.lst_price * self.quantity / self.num_months
                if i > 0:
                    period+=1
                    date = end_date
                    _logger.info("Loop Next start Date: %s", date)
                    days_in_month = calendar. \
                        monthrange(date.year,
                                   date.month)[1]
                    end_date = date + datetime.timedelta(days=days_in_month)
                    _logger.info("Loop End Date: %s", end_date)
                    # date = next_date
                    # _logger.info("Next start Date loop: %s", date)
                    # _logger.info("loop")
                    # end_date = date.replace(day = calendar.monthrange(date.year, date.month)[1])
                   

                    # date = date.replace(day=last_date)
                _logger.info("Periods: %s", period)
                _logger.info("Start Date: %s", date)
                _logger.info("End Date: %s", end_date)
                _logger.info("Description: %s", description)
                _logger.info("Amount: %s", amount)
                cre_intsall_line.append((0,0, {
                    's_n': period+1,
                    'start_date': date,
                    'end_date': end_date,
                    'amount': amount,
                    'description': description,
                    'state': 'unpaid'
                }))

            res['context']['default_install_schedule_line'] = cre_intsall_line

        if self.product_id.id:
            res['context']['default_order_line'] = [(0,0, cre_line)]
        # res['context']['default_install_schedule_line'] = cre_intsall_line
        res['context']['model_lead_id'] = self.id
        res['context']['prod_description'] = self.product_id.get_product_multiline_description_sale()
        res['context']['default_sales_type'] = self.sales_type
        return res


