# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils import mail_utils as utils

class SupplierClient(models.Model):
    _name = 'supplier.client'
    _description = 'Supplier Client'

    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    address = fields.Char(string='Address')

class SupplierRegistration(models.TransientModel):
    _name = 'supplier.registration'
    _description = 'Supplier Registration'
    _rec_name = 'company_name'
    _order = 'create_date desc'
    _transient_max_hours = 720 # 30 days will be the max time for the transient model to be alive
    _log_access = True

    company_name = fields.Char(string='Company Name')
    email = fields.Char(string='Company Email')
    phone = fields.Char(string='Company Phone')
    company_address = fields.Char(string='Company Registered Address')
    image_1920 = fields.Binary(string='Company Logo')
    company_type_category = fields.Selection([
        ('LLC', 'LLC'),
        ('corporate', 'Corporation'),
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('cooperative', 'Cooperative')
    ], string='Company Category')
    trade_license_number = fields.Char(string='Trade License Number')
    tax_identification_number = fields.Char(string='Tax Identification Number')
    commencement_date = fields.Date(string='Commencement Date')
    expiry_date = fields.Date(string='Expiry Date')
    contact_person_name = fields.Char(string='Contact Person Name')
    contact_email = fields.Char(string='Contact Email')
    contact_phone = fields.Char(string='Contact Phone')
    contact_address = fields.Char(string='Contact Address')
    finance_contact_name = fields.Char(string='Finance Contact Name')
    finance_contact_email = fields.Char(string='Finance Contact Email')
    finance_contact_phone = fields.Char(string='Finance Contact Phone')
    finance_contact_address = fields.Char(string='Finance Contact Address')
    authorized_person_name = fields.Char(string='Authorized Person Name')
    authorized_person_email = fields.Char(string='Authorized Person Email')
    authorized_person_phone = fields.Char(string='Authorized Person Phone')
    authorized_person_address = fields.Char(string='Authorized Person Address')
    bank_name = fields.Char(string='Bank Name')
    bank_address = fields.Char(string='Bank Address')
    bank_swift_code = fields.Char(string='Bank Swift Code')
    account_name = fields.Char(string='Account Name')
    account_number = fields.Char(string='Account Number')
    iban = fields.Char(string='IBAN')
    company_address_as_per_bank = fields.Char(string='Company Address as per Bank')
    client_ids = fields.Many2many('supplier.client',  string='Clients')
    certification = fields.Char(string='Certification')
    certificate_number = fields.Char(string='Certificate Number')
    certifying_body = fields.Char(string='Certifying Body')
    award_date = fields.Date(string='Award Date')
    certificate_expiry_date = fields.Date(string='Certificate Expiry Date')
    trade_license_business_registration = fields.Binary(string='Trade License/Business Registration')
    certificate_of_incorporation = fields.Binary(string='Certificate of Incorporation')
    certificate_of_good_standing = fields.Binary(string='Certificate of Good Standing')
    establishment_card = fields.Binary(string='Establishment Card')
    vat_tax_certificate = fields.Binary(string='VAT/TAX Certificate')
    memorandum_of_association = fields.Binary(string='Memorandum of Association')
    identification_document_for_authorized_person = fields.Binary(string='Identification Document for Authorized Person')
    bank_letter_indicating_bank_account = fields.Binary(string='Bank Letter indicating Bank Account')
    past_2_years_audited_financial_statements = fields.Binary(string='Past 2 Years Audited Financial Statements')
    other_certifications = fields.Binary(string='Other Certifications')
    feedback = fields.Text(string="Feedback", tracking=True)
    name_of_signatory = fields.Char(string='Name of Signatory')
    authorized_signatory = fields.Char(string='Authorized Signatory')
    company_stamp = fields.Binary(string='Company Stamp')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('final review', 'Final Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('blacklist', 'Blacklisted'),
         ],
        string='State', default='draft')

    def action_review(self):
        """
        Change the state of the supplier registration to 'final review'.
        """
        self.state = 'final review'

    def action_blacklist(self):
        """
        Create a wizard to blacklist the supplier's email and return an action to open the wizard.

        Returns:
            dict: An action to open the blacklist wizard.
        """
        wizard = self.env['mail.blacklist.wizard'].create({'email': self.email, 'registration_id': self.id})
        return {
            'name': 'Blacklist Email',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.blacklist.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }

    def action_approve(self):
        """
        Approve the supplier registration, create a new supplier record, and send a confirmation email.
        """
        vals = {
            'name': self.company_name or 'N/A',
            'email': self.email or 'N/A',
            'phone': self.phone or 'N/A',
            'street': self.company_address or 'N/A',
            'company_type_category': self.company_type_category or 'N/A',
            'trade_license_number': self.trade_license_number or 'N/A',
            'vat': self.tax_identification_number or 'N/A',
            'commencement_date': self.commencement_date or fields.Date.today(),
            'expiry_date': self.expiry_date or fields.Date.today(),
            'certification': self.certification or 'N/A',
            'certificate_number': self.certificate_number or 'N/A',
            'certifying_body': self.certifying_body or 'N/A',
            'award_date': self.award_date or 'N/A',
            'certificate_expiry_date': self.certificate_expiry_date or 'N/A',
            'supplier_rank': 1,
            'company_type': 'company',
            'submission_date' : self.create_date,
            'name_of_signatory' : self.name_of_signatory,
            'authorized_signatory' : self.authorized_signatory,
        }
        vals = {k: v for k, v in vals.items() if v != 'N/A'}
        vals['child_ids'] = []
        vals['bank_ids'] = []
        if self.contact_person_name:
            vals['child_ids'].append((0, 0, {
                'name': self.contact_person_name,
                'email': self.contact_email,
                'phone': self.contact_phone,
                'street': self.contact_address,
                'function':'Primary Contact',
                'type': 'contact',
            }))
        if self.authorized_person_name:
            vals['child_ids'].append((0, 0, {
                'name': self.authorized_person_name,
                'email': self.authorized_person_email,
                'phone': self.authorized_person_phone,
                'street': self.authorized_person_address,
                'function': 'Authorized Contact',
                'type': 'contact',
            }))
        if self.finance_contact_name:
            vals['child_ids'].append((0, 0, {
                'name': self.finance_contact_name,
                'email': self.finance_contact_email,
                'phone': self.finance_contact_phone,
                'street': self.finance_contact_address,
                'function': 'Finance Contact',
                'type': 'contact',
            }))
        for client in self.client_ids:
            vals['child_ids'].append((0, 0, {
                'name': client.name,
                'email': client.email,
                'phone': client.phone,
                'street': client.address,
                'type': 'contact',
            }))

        if self.bank_name:
            bank_id = self.env['res.bank'].create({
                'name': self.bank_name,
                'street': self.bank_address,
                'bank_swift_code': self.bank_swift_code,
                'iban': self.iban,
            })
            vals['bank_ids'].append((0, 0, {
                'bank_id': bank_id.id,
                'acc_number': self.account_number,
                'acc_holder_name': self.account_name,
                'address': self.company_address_as_per_bank,
             }))
            # Check for file fields and add them to vals if present
        file_fields = [
            'trade_license_business_registration',
            'certificate_of_incorporation',
            'certificate_of_good_standing',
            'establishment_card',
            'vat_tax_certificate',
            'memorandum_of_association',
            'identification_document_for_authorized_person',
            'bank_letter_indicating_bank_account',
            'past_2_years_audited_financial_statements',
            'other_certifications',
            'image_1920',
            'company_stamp',
        ]
        for field in file_fields:
            if getattr(self, field):
                vals[field] = getattr(self, field)
        new_supplier = self.env['res.partner'].create(vals)
        new_user = self.env['res.users'].create({
            'login': self.email,
            'password': self.email,
            'partner_id': new_supplier.id,
            'company_id': self.env.company.id,
            'groups_id': [(6, 0, self.env.ref('base.group_portal').ids)]
        })
        email_values = {
            'email_from' : utils.get_sender_mail(self.env),
            'email_to' : self.email,
            'subject' : 'Supplier Registration Approved',
        }
        context = {
            'name' : self.company_name,
            'email' : self.email,
            'password' : self.email,
            'company_name' : self.env.company.name,
        }
        template = self.env.ref('supplier_management.vendor_registration_confirmation')
        template.with_context(**context).send_mail(new_supplier.id,email_values=email_values)
        self.state = 'approved'

    def action_reject(self):
        """
        Create a wizard to reject the supplier registration and return an action to open the wizard.

        Returns:
            dict: An action to open the reject wizard.
        """
        wizard = self.env['supplier.reject.wizard'].create({'registration_id': self.id})
        return {
            'name': 'Reject Supplier',
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wizard.id,
        }

    def action_submit(self):
        """
        Change the state of the supplier registration to 'submitted'.
        """
        self.state = 'submitted'
