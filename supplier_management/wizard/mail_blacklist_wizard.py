from odoo import models, fields, api

class MailBlacklistWizard(models.TransientModel):
    _name = 'mail.blacklist.wizard'
    _description = 'Mail Blacklist Wizard'

    email = fields.Char(string="Email Address", required=True)
    reason = fields.Text(string="Reason")
    registration_id = fields.Many2one('supplier.registration', string="Registration")


    def action_blacklist_email(self):
        """Add the email to the mail.blacklist model"""
        if self.email:
            blacklist = self.env['mail.blacklist'].search([('email', '=', self.email)])
            if not blacklist:
                self.env['mail.blacklist'].create({'email': self.email, 'reason': self.reason})
        if self.registration_id:
            self.registration_id.write({'state': 'blacklist'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.registration',
            'view_mode': 'form',
            'res_id': self.registration_id.id,
        }