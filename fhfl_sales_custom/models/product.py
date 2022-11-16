# -*- coding: utf-8 -*-

import logging
import secrets
import string
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class FhflStockQuant(models.Model):
    _inherit = 'stock.quant'

    inventory_quantity = fields.Float(
        'Inventoried Quantity', compute='_compute_inventory_quantity',
        inverse='_set_inventory_quantity', groups='stock.group_stock_manager', store=True)

class ProductEstate(models.Model):
    _name = "product.estate"
    _description = "Estate"

    name = fields.Char()
    address = fields.Char()

class PropertyType(models.Model):
    _name = "property.type"
    _description = "Estate"

    name = fields.Char()
    # address = fields.Char()

# class ProductPropertyType(models.Model):
#     _name = "product.property.type"
#     _description = "Property Type"
#
#     name = fields.Char()

class FhflProductTemplate(models.Model):
    _inherit = "product.template"

    is_property = fields.Boolean(default=False)
    estate_id = fields.Many2one('product.estate', string='Estate')
    property_type = fields.Selection([
        ('two_bed_flat', '2 Bedroom flat'),
        ('three_bed_flat', '3 Bedroom flat'),
        ('bungalow', 'Bungalow'),
        # ('se', 'South East'),
        # ('nw', 'North West'),
        # ('ss', 'South South'),
    ], string='Property Type', tracking=True,
        copy=True)
    property_types = fields.Many2one('property.type')
    prod_ref_id = fields.Char('Product Ref ID', readonly=True)
    sqm_unit = fields.Float(string='Sqm/Unit')
    _sql_constraints = [
        ('prod_ref_id_unique', 'unique(prod_ref_id)',
         'Cannot have duplicate Product Reference ID!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        res = super(FhflProductTemplate, self).create(vals_list)
        rand_num = 'PROP_' + ''. \
            join(secrets.choice(string.ascii_uppercase +
                                string.digits) for i in range(7))

        for vals in vals_list:
            if 'is_property' in vals and vals.get('is_property') is True:
                res.prod_ref_id = rand_num
        return res

    def action_create_sales_order(self):
        _logger.info("Create product sales order")
        action = self.env["ir.actions.actions"]._for_xml_id("fhfl_sales_custom.products_sale_action_quotations_new")
        # _logger.info("Products: %s", self.ids)
        prod_prods = [self.env['product.product'].search([('product_tmpl_id', '=', i)], limit=1) for i in self.ids]
        _logger.info("Products: %s", prod_prods)
        order_line = []

        for prod in prod_prods:
            order_line.append((0,0, {
                'product_id': prod.id,
                'name': str(prod.get_product_multiline_description_sale()),
                'price_unit': prod.lst_price,
                'product_uom_qty': 1,
                'product_uom': prod.uom_id.id
            }))

        action['context'] = {
            'default_order_line': order_line
        }
        
        # action['context'] = {
        #     'search_default_opportunity_id': self.id,
        #     'default_opportunity_id': self.id,
        #     'search_default_partner_id': self.partner_id.id,
        #     'default_partner_id': self.partner_id.id,
        #     'default_campaign_id': self.campaign_id.id,
        #     'default_medium_id': self.medium_id.id,
        #     'default_origin': self.name,
        #     'default_source_id': self.source_id.id,
        #     'default_company_id': self.company_id.id or self.env.company.id,
        #     'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        # }
        return action


class FhflProductProduct(models.Model):
    _inherit = "product.product"

    is_property = fields.Boolean(related='product_tmpl_id.is_property', store=True)
    estate_id = fields.Many2one(related='product_tmpl_id.estate_id', store=True)
    property_type = fields.Selection(related='product_tmpl_id.property_type', store=True)
    property_types = fields.Many2one(related='product_tmpl_id.property_types', store=True)
    prod_ref_id = fields.Char(related='product_tmpl_id.prod_ref_id', store=True)
    sqm_unit = fields.Float(related='product_tmpl_id.sqm_unit', store=True)
    lst_price = fields.Float(
        'Public Price', compute='_compute_product_lst_price',
        digits='Product Price', inverse='_set_product_lst_price',
        help="The sale price is managed from the product template. Click on the 'Configure Variants' button to set the extra attribute prices.",
        store=True)
    qty_available = fields.Float(
        'Quantity On Hand', compute='_compute_quantities', search='_search_qty_available',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Current quantity of products.\n"
             "In a context with a single Stock Location, this includes "
             "goods stored at this Location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "stored in the Stock Location of the Warehouse of this Shop, "
             "or any of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.", store=True)
    # is_property = fields.Boolean(default=False)
    # estate_id = fields.Many2one('product.estate', string='Estate')
    # property_type = fields.Selection([
    #     ('two_bed_flat', '2 Bedroom flat'),
    #     ('three_bed_flat', '3 Bedroom flat'),
    #     ('bungalow', 'Bungalow'),
      
    # ], string='Property Type', tracking=True,
    #     copy=True)
    # prod_ref_id = fields.Char('Product Ref ID', readonly=True)
    # sqm_unit = fields.Float(string='Sqm/Unit')
    _sql_constraints = [
        ('prod_ref_id_unique', 'unique(prod_ref_id)',
         'Cannot have duplicate Product Reference ID!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        res = super(FhflProductProduct, self).create(vals_list)
        rand_num = 'PROP_' + ''. \
            join(secrets.choice(string.ascii_uppercase +
                                string.digits) for i in range(7))
        
        for vals in vals_list:
            if 'is_property' in vals and vals.get('is_property') is True:
                res.prod_ref_id = rand_num
        return res







