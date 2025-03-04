from odoo import models, fields, api
from .. utils import mail_utils as utils
class SupplierRejectWizard(models.TransientModel):
    _name = 'supplier.reject.wizard'
    _description = 'Supplier Reject Wizard'

    reason = fields.Text(string="Reason")
    registration_id = fields.Many2one('supplier.registration', string="Registration")

    def action_reject_supplier(self):
        """Reject the supplier registration"""
        if self.registration_id:
            self.registration_id.write({'state': 'rejected', 'feedback': self.reason})
        email_values = {
            'email_from': utils.get_sender_mail(self.env),
            'email_to': self.registration_id.email,
            'subject': 'Supplier Registration Rejected',
        }
        context = {
            'your_name': self.registration_id.company_name,
            'name' : self.env.company.name,
            'reason': self.reason,
            'company_mail' : utils.get_sender_mail(self.env),
        }
        template = self.env.ref('supplier_management.email_template_supplier_rejection')
        template.with_context(**context).send_mail(self.registration_id.id, email_values=email_values)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.registration',
            'view_mode': 'form',
            'res_id': self.registration_id.id,
        }