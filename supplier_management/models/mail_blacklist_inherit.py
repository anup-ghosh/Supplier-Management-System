from odoo import models, fields, api

class MailBlacklist(models.Model):
    _inherit = 'mail.blacklist'

    reason = fields.Text(string="Reason")
    """
        This class extends the 'mail.blacklist' model to include an additional field 'reason'.
    """
