import base64
from ..utils import mail_utils as utils
from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.account.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo import http, _
from odoo.http import request, route
from odoo import fields
import random
import datetime
import json
from werkzeug.datastructures import FileStorage


class SupplierPortal(CustomerPortal):

    @http.route('/my/supplier_registration', type='http', auth="public", website=True)
    def supplier_registration_page(self):
        return request.render('supplier_management.supplier_registration_form')

    # Endpoint for email verification
    @http.route('/api/verify_email', type='json', auth='public', methods=['POST'])
    def verify_email(self, **kw):
        data = request.httprequest.data.decode('utf-8')
        # Parse the JSON content
        json_data = json.loads(data)
        email = json_data.get('email')

        # Check blacklist
        blacklist = request.env['mail.blacklist'].sudo().search([('email', '=', email)], limit=1)
        if blacklist:
            return {'status': 'error', 'message': 'Email is blacklisted. Contact the administrator.'}

        # Check if the email is already registered or blacklisted
        existing_partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        already_applied = request.env['supplier.registration'].sudo().search([('email', '=', email)], limit=1)
        if already_applied:
            return {'status': 'error', 'message': 'Email already applied for registration.'}
        if existing_partner:
            return {'status': 'error', 'message': 'Email already registered.'}





        # Create OTP and send to email
        otp = random.randint(100000, 999999)
        otp_record = request.env['supplier.email.verification'].sudo().create({
            'email': email,
            'otp': str(otp),
            'otp_sent_time': datetime.datetime.now(),
        })
        company_name = utils.get_my_company(request.env)
        email_values = {
            'email_from': 'info@bjitacademy.com',
            'email_to': email,
            'subject': 'Your One-Time Password (OTP)',
        }

        context = {
            'otp': otp,
            'company_name': company_name
        }

        template = request.env.ref('supplier_management.otp_email_template')
        template.with_context(**context).sudo().send_mail(otp_record.id, email_values=email_values, force_send=True)

        # Return success message
        return {'status': 'success', 'message': 'OTP sent to your email.'}

    # Endpoint for OTP verification
    @http.route('/api/verify_otp', type='json', auth='public', methods=['POST'])
    def verify_otp(self, **kw):
        # Verify OTP
        data = request.httprequest.data.decode('utf-8')
        json_data = json.loads(data)
        email = json_data.get('email')
        otp = json_data.get('otp')
        verification = request.env['supplier.email.verification'].sudo().search(
            [('email', '=', email), ('otp', '=', otp)],
            limit=1)
        if not verification:
            return {'status': 'error', 'message': 'Invalid OTP. Please try again.'}

        # Check if OTP is within the validity time (e.g., 5 minutes)
        if (datetime.datetime.now() - verification.otp_sent_time).seconds > 300:
            return {'status': 'error', 'message': 'OTP expired. Please request a new one.'}

        # Mark OTP as verified
        verification.is_verified = True

        # Set session variable to indicate successful verification
        request.session['email_verified'] = True
        request.session['verified_email'] = email  # Store the verified email for later use

        return {'status': 'success', 'message': 'OTP verified. Proceeding to registration.',
                'redirect_url': '/my/create/supplier'}

    @http.route(["/my/create/supplier"], type="http", methods=['POST', 'GET'], auth="public", website=True, csrf=True)
    def register_supplier(self, **kw):
        if not request.session.get('email_verified'):
            return request.redirect('/my/supplier_registration')

        verified_email = request.session.get('verified_email')
        error_list = []
        success_list = []

        def generate_supplier_review_link(registration_id):
            # Get the action ID for reviewer
            action = request.env.ref('supplier_management.action_supplier_registration_reviewr')
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            params = {
                'id': registration_id,
                'model': 'supplier.registration',
                'action': action.id,
                'view_type': 'form',
                'cids': request.env.company.id,
            }

            query_string = '&'.join(f"{key}={value}" for key, value in params.items() if value)
            return f"{base_url}/web#{query_string}"

        if request.httprequest.method == 'POST':
            vals = {}
            keys = [
                'company_name', 'email', 'phone', 'company_address', 'image_1920',
                'company_type_category', 'company_type', 'trade_license_number',
                'tax_identification_number', 'commencement_date', 'expiry_date',
                'contact_person_name', 'contact_email', 'contact_phone', 'contact_address',
                'finance_contact_name', 'finance_contact_email', 'finance_contact_phone', 'finance_contact_address',
                'authorized_person_name', 'authorized_person_email', 'authorized_person_phone',
                'authorized_person_address',
                'bank_name', 'bank_address', 'bank_swift_code', 'account_name',
                'account_number', 'iban', 'company_address_as_per_bank', 'certification', 'certificate_number',
                'certifying_body', 'award_date', 'certificate_expiry_date', 'name_of_signatory', 'authorized_signatory'
            ]

            for key in keys:
                if kw.get(key):
                    vals[key] = kw.get(key)

            clients = []
            for i in range(0, 5):
                if any(kw.get(f'client_{i + 1}_{field}') for field in ['name', 'address', 'email', 'phone']):
                    client_data = {
                        'name': kw.get(f'client_{i + 1}_name'),
                        'address': kw.get(f'client_{i + 1}_address'),
                        'email': kw.get(f'client_{i + 1}_email'),
                        'phone': kw.get(f'client_{i + 1}_phone'),
                    }
                    clients.append((0, 0, client_data))

            vals['email'] = verified_email
            vals.update({'client_ids': clients})

            # Validation checks
            if kw.get('tax_identification_number') and (len(kw.get('tax_identification_number')) != 16 or not kw.get(
                    'tax_identification_number').isdigit()):
                error_list.append("Tax Identification Number Should Be Of 15 Digits And All Digits")
            if kw.get('trade_license_number') and (not kw.get('trade_license_number').isalnum() or not (
                    8 <= len(kw.get('trade_license_number')) <= 20)):
                error_list.append("Trade License Number Should Be Of 8-20 Digits And Alphanumeric")
            if kw.get('expiry_date') and fields.Date.to_date(kw.get('expiry_date')) <= fields.date.today():
                error_list.append("Expiry Date Should Be Greater Than Today")
            if not kw.get('company_name'):
                error_list.append("Company Name is mandatory")

            file_fields = [
                'trade_license_business_registration', 'certificate_of_incorporation', 'certificate_of_good_standing',
                'establishment_card', 'vat_tax_certificate', 'memorandum_of_association',
                'identification_document_for_authorized_person', 'bank_letter_indicating_bank_account',
                'past_2_years_audited_financial_statements', 'other_certifications'
            ]

            if image_1920 := kw.get('image_1920'):
                vals['image_1920'] = base64.b64encode(image_1920.read())
            if company_stamp := kw.get('company_stamp'):
                vals['company_stamp'] = base64.b64encode(company_stamp.read())

            file_vals = {}
            for field in file_fields:
                if field in kw and kw[field]:
                    file_vals[field] = base64.b64encode(kw[field].read())

            vals['state'] = 'submitted'

            if not error_list:
                new_supplier = request.env['supplier.registration'].sudo().create(vals)
                if new_supplier:
                    success_list.append("Supplier Registered Successfully")
                    if file_vals:
                        new_supplier.write(file_vals)

                    # Generate the review link
                    review_link = generate_supplier_review_link(new_supplier.id)

                    email_values = {
                        'email_from': utils.get_sender_mail(request.env),
                        'email_to': utils.get_reviewers_mail(request.env),
                        'subject': 'Review New Supplier Registration',
                    }
                    context = {
                        'your_name': vals['company_name'],
                        'submission_date': fields.Date.today(),
                        'name': request.env.company.name,
                        'review_link': review_link,  # Add the dynamic link to context
                    }
                    template = request.env.ref('supplier_management.email_template_supplier_submission')
                    template.with_context(**context).sudo().send_mail(new_supplier.id, email_values=email_values)
                    return request.render("supplier_management.supplier_registration_success")

        return request.render("supplier_management.new_supplier_registration_form_view_portal",
                              {'page_name': 'supplier_registration',
                               'error_list': error_list,
                               'success_list': success_list,
                               'email': verified_email})
