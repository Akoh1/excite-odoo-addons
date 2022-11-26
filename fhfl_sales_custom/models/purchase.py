# -*- coding: utf-8 -*-
import logging
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
}

class fhflPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, states=READONLY_STATES, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")

    # state = fields.Selection(selection_add=[('cfo_approve', 'CFO Approval'), ('purchase',)],
    #                          ondelete={'draft': 'set default'}, default='draft')

    # def button_cfo_approve(self):
    #     _logger.info("CFO approve")
    #     for rec in self:
    #         rec.state = 'cfo_approve'

    # def button_confirm(self):
    #     res = super(fhflPurchaseOrder, self).button_confirm()
    #     for rec in self:
    #         if rec.state == 'cfo_approve':
    #             rec.state = 'purchase'
    #     return res


class fhflPurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    description = fields.Html()
    title = fields.Char()
    company_name = fields.Char()
    company_email = fields.Char()
    contact_name = fields.Char()
    contact_phone = fields.Char()
    files_url = fields.Text()

    def action_in_progress(self):
        self.ensure_one()
        # if not self.line_ids:
        #     raise UserError(_("You cannot confirm agreement '%s' because there is no product line.", self.name))
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without price.'))
                if requisition_line.product_qty <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
            self.write({'state': 'ongoing'})
        else:
            self.write({'state': 'in_progress'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            if self.is_quantity_copy != 'none':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            else:
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')

    def write(self, vals):
        res = super(fhflPurchaseRequisition, self).write(vals)
        # if 'price_unit' in vals:
        #     if vals['price_unit'] <= 0.0 and any(
        #             requisition.state not in ['draft', 'cancel', 'done'] and
        #             requisition.is_quantity_copy == 'none' for requisition in self.mapped('requisition_id')):
        #         raise UserError(_('You cannot confirm the blanket order without price.'))
        #     # If the price is updated, we have to update the related SupplierInfo
        #     self.supplier_info_ids.write({'price': vals['price_unit']})
        if 'company_email' in vals:
            try:
                _logger.info("Send mail function")
                templ = self.env.ref('fhfl_sales_custom.tender_email_template')
                _logger.info("Mail template: %s", templ)
    
                _logger.info("Testing code block")

                modelObjData = self.env['purchase.requisition'].search([('company_email', '=', vals.get('company_email'))])
                _logger.info("Model to send mail: %s", modelObjData)
          
                for rec in modelObjData:
                    _logger.info("Loop self: %s", rec)

                    self.env['mail.template'].browse(templ.id). \
                        send_mail(rec.id, force_send=True, raise_exception=True)
            except UserError as e:
                raise "Error: %r, %r" % (e, "Cannot send mail to applicant")
        return res






