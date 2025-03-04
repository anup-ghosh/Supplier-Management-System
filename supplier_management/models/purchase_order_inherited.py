from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rfp_id = fields.Many2one('supplier.management.rfp', string='RFP', index=True)
    warranty_period = fields.Integer(string='Warranty Period (Months)')
    score = fields.Integer(string='Score')
    recommended = fields.Boolean(string='Recommended')
    rfp_status = fields.Selection(related='rfp_id.status', string='RFP Status')

    def action_accept(self):
        """
        Accept the purchase order, update the RFP status to 'accepted', and confirm the order.
        Also, update the product lines in the RFP to reflect the accepted supplier and cancel other RFQs.
        """
        self.rfp_id.write({'status': 'accepted', 'approved_supplier': self.partner_id.id, 'accept_date': fields.Datetime.today()})
        self.button_confirm()

        # Update the product lines in the RFP to reflect the accepted supplier
        for line in self.rfp_id.product_lines:
            rfq_product_line = self.order_line.filtered(lambda x: x.product_id == line.product_id)
            line.write({'unit_price': rfq_product_line.price_unit, 'delivery_charges': rfq_product_line.delivery_charges})

        # Cancel other RFQs related to the same RFP
        other_rfq = self.env['purchase.order'].search([
            ('rfp_id', '=', self.rfp_id.id),
            ('id', '!=', self.id)
        ])
        other_rfq.button_cancel()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.management.rfp',
            'view_mode': 'form',
            'res_id': self.rfp_id.id,
            'target': 'current',
        }

    @api.constrains('partner_id', 'recommended')
    def _constrains_recommendation(self):
        """
        Ensure that a supplier is not recommended in more than one RFQ for the same RFP.
        Raise a ValidationError if the supplier is already recommended in another RFQ.
        """
        for order in self:
            if order.recommended and order.partner_id:
                existing_recommended = self.env['purchase.order'].search([
                    ('partner_id', '=', order.partner_id.id),
                    ('recommended', '=', True),
                    ('rfp_id', '=', order.rfp_id.id),
                    ('id', '!=', order.id)
                ])

                if existing_recommended:
                    raise ValidationError(_("Supplier has already been recommended in another RFQ."))

    @api.depends_context('lang')
    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed', 'order_line.delivery_charges')
    def _compute_tax_totals(self):
        """
        Override the server code for adding delivery charge in tax calculation.
        Compute the tax totals for the order, including delivery charges in the tax base.
        """
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            # Prepare lines for tax calculation, including delivery charges
            line_dicts = []
            for line in order_lines:
                line_dict = line._convert_to_tax_base_line_dict()
                # Include delivery charge in the tax base
                line_dict['price_unit'] += line.delivery_charges / line.product_qty if line.product_qty else line.delivery_charges
                line_dicts.append(line_dict)
            order.tax_totals = self.env['account.tax']._prepare_tax_totals(
                line_dicts,
                order.currency_id or order.company_id.currency_id,
            )