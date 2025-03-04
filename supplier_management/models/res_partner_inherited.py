from odoo import api, fields, models


class MySupplier(models.Model):
    _inherit = 'res.partner'
    _description = 'Supplier Registration'

    company_address = fields.Char(string='Company Registered Address')
    company_type_category = fields.Selection([
        ('LLC', 'LLC'),
        ('corporate', 'Corporation'),
        ('sole_proprietorship', 'Sole Proprietorship'),
        ('partnership', 'Partnership'),
        ('cooperative', 'Cooperative')
    ], string='Company Category')
    trade_license_number = fields.Char(string='Trade License Number')
    commencement_date = fields.Date(string='Commencement Date')
    expiry_date = fields.Date(string='Expiry Date')
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
    name_of_signatory = fields.Char(string='Name of Signatory')
    authorized_signatory = fields.Char(string='Designation of Authorized Signatory')
    company_stamp = fields.Binary(string='Company Stamp')
    submission_date = fields.Date(string='Submission Date')


