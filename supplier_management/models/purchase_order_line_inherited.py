from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    delivery_charges = fields.Monetary(string='Delivery Charge', currency_field='currency_id', default=0.0)
    """
    Adds a new field 'delivery_charges' to the purchase order line model.
    """

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'delivery_charges')
    def _compute_amount(self):
        """
        Compute the amounts for the purchase order line, including delivery charges.
        """
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = next(iter(tax_results['totals'].values()))
            amount_untaxed = totals['amount_untaxed']
            if line.delivery_charges:
                amount_untaxed += line.delivery_charges
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })