from datetime import timedelta

from ..utils import mail_utils as utils

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RFP(models.Model):
    _name = 'supplier.management.rfp'
    _description = 'Request for Purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # For chatter and tracking
    _rec_name = 'rfp_name'

    # Fields
    rfp_name = fields.Char(string='RFP Number', readonly=True, default='New')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed'),
        ('recommendation', 'Recommendation'),
        ('accepted', 'Accepted')
    ], string='Status', default='draft', tracking=True)
    required_date = fields.Date(string='Required Date', default=lambda self: fields.Date.today() + timedelta(days=7))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    approved_supplier = fields.Many2one('res.partner', string='Approved Supplier')
    product_lines = fields.One2many('supplier.management.rfp.product.line', 'rfp_id', string='Product Lines')
    rfq_lines = fields.One2many('purchase.order', 'rfp_id', string='RFQ Lines', domain=lambda self: self._get_rfq_lines_domain())
    approve_date = fields.Datetime(string='Approve Date')
    accept_date = fields.Datetime(string='Accept Date')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True)
    selected_product_ids = fields.Many2many('product.product', string='Selected Products', compute='_compute_selected_product_ids', store=False)

    # Computed Fields
    @api.depends('product_lines.product_id')
    def _compute_selected_product_ids(self):
        """Compute the selected product IDs based on the product lines."""
        for rfp in self:
            rfp.selected_product_ids = rfp.product_lines.mapped('product_id')

    @api.depends('product_lines', 'product_lines.subtotal_price')
    def _compute_total_amount(self):
        """Compute the total amount based on the subtotal prices of the product lines."""
        for record in self:
            record.total_amount = sum(record.product_lines.mapped('subtotal_price'))

    @api.model
    def _get_rfq_lines_domain(self):
        """Get the domain for RFQ lines based on the user's group and RFP status."""
        if self.env.user.has_group('supplier_management.group_supplier_management_approver'):
            return [('recommended', '=', True)] if self.status in ['recommendation', 'accepted'] else [('id', '=', False)]

    @api.depends('rfq_lines')
    def _compute_rfq_lines(self):
        """Sort the RFQ lines by score in descending order."""
        for rec in self:
            rec.rfq_lines = rec.rfq_lines.sorted(lambda r: r.score, reverse=True)

    @api.model
    def create(self, vals):
        """Override the create method to generate a sequence number for the RFP."""
        if vals.get('rfp_name', ('New')) == ('New'):
            seq = self.env['ir.sequence'].next_by_code('rfp.sequence')
            vals['rfp_name'] = seq or _('New')
        return super(RFP, self).create(vals)

    # Actions
    def action_submit(self):
        """Submit the RFP and send an email notification to the approvers."""
        for record in self:
            if not record.product_lines:
                raise UserError(_("You cannot submit an RFP without product lines. Please add at least one product line."))
        self.status = 'submit'
        email_values = {
            'email_to': utils.get_approvers_mail(self.env),
            'email_from': self.create_uid.email,
            'subject': 'New RFP Submitted',
        }
        context = {
            'rfp_name': self.rfp_name,
            'submission_date': self.create_date,
            'name': self.create_uid.name,
            'company_name': self.env.company.name,
        }
        template = self.env.ref('supplier_management.email_template_rfp_submission')
        template.with_context(**context).send_mail(self.id, email_values=email_values)

    def action_return_to_draft(self):
        """Return the RFP to draft status."""
        self.status = 'draft'

    def action_recommend(self):
        """Recommend the RFP and send an email notification to the approvers."""
        if not any(line.recommended for line in self.rfq_lines):
            raise UserError("At least one RFQ line must be recommended.")
        self.status = 'recommendation'
        email_values = {
            'email_to': utils.get_approvers_mail(self.env),
            'email_from': self.create_uid.email,
            'subject': 'Review The Recommended RFQs',
        }
        context = {
            'rfp_name': self.rfp_name,
            'name': self.create_uid.name,
            'company_name': self.env.company.name,
        }
        template = self.env.ref('supplier_management.email_template_rfq_finalize_approvers')
        template.with_context(**context).send_mail(self.id, email_values=email_values)

    def action_approve(self):
        """Approve the RFP, set the approval date, and send email notifications."""
        self.write({'approve_date': fields.Datetime.today()})
        self.status = 'approved'
        email_values = {
            'email_to': self.create_uid.email,
            'email_from': utils.get_sender_mail(self.env),
            'subject': 'RFP Approved',
        }
        context = {
            'rfp_name': self.rfp_name,
            'name': self.env.user.name,
            'company_name': self.env.company.name,
            'creator_name': self.create_uid.name,
            'company_mail': self.env.company.email,
        }
        template = self.env.ref('supplier_management.email_template_rfp_approved')
        template.with_context(**context).send_mail(self.id, email_values=email_values)

        # For suppliers notification
        template = self.env.ref('supplier_management.email_template_rfp_supplier_notification')
        supplier_mails = utils.get_suppliers_mail(self.env)
        email_values['subject'] = f"New RFP Available {self.rfp_name}"
        for email in supplier_mails:
            email_values['email_to'] = email
            template.with_context(**context).send_mail(self.id, email_values=email_values)

    def action_reject(self):
        """Reject the RFP and send an email notification to the creator."""
        self.status = 'rejected'
        email_values = {
            'email_to': self.create_uid.email,
            'email_from': utils.get_sender_mail(self.env),
            'subject': f'RFP Rejected {self.rfp_name}',
        }
        context = {
            'rfp_name': self.rfp_name,
            'company_name': self.env.company.name,
            'creator_name': self.create_uid.name,
            'company_mail': self.env.company.email,
        }
        template = self.env.ref('supplier_management.email_template_rfp_rejection')
        template.with_context(**context).send_mail(self.id, email_values=email_values)

    def action_close(self):
        """Close the RFP."""
        self.status = 'closed'