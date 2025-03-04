from odoo import models, fields, api
import random
import datetime


class EmailVerification(models.Model):
    _name = 'supplier.email.verification'
    _description = 'Email Verification for Supplier Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Ensures email functionality

    email = fields.Char('Email Address', required=True)
    otp = fields.Char('OTP', required=True)
    otp_sent_time = fields.Datetime('OTP Sent Time')
    is_verified = fields.Boolean('Verified', default=False)

