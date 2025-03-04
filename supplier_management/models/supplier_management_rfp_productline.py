from odoo import models, fields, api

class RFPProductLine(models.Model):
    _name = 'supplier.management.rfp.product.line'
    _description = 'RFP Product Lines'

    rfp_id = fields.Many2one('supplier.management.rfp', string='RFP')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_name = fields.Char(related='product_id.name', string='Product Name', store=False, readonly=True)
    product_image = fields.Binary(related='product_id.image_1920', string='Product Image', store=False, readonly=True)
    description = fields.Text(string='Description')
    quantity = fields.Integer(string='Quantity', default=1)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    unit_price = fields.Monetary(string='Unit Price', currency_field='currency_id')
    subtotal_price = fields.Monetary(string='Subtotal Price', compute='_compute_subtotal', store=True)
    delivery_charges = fields.Monetary(string='Delivery Charges', currency_field='currency_id')

    @api.depends('quantity', 'unit_price', 'delivery_charges')
    def _compute_subtotal(self):
        """
        Compute the subtotal price for the product line.
        The subtotal price is calculated as the product of the quantity and unit price,
        plus any delivery charges.
        """
        for line in self:
            line.subtotal_price = (line.quantity * line.unit_price) + line.delivery_charges