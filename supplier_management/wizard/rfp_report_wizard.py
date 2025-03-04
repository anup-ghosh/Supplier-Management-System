import base64
import tempfile

from odoo import models, fields, api
from odoo.exceptions import UserError
import xlsxwriter
from io import BytesIO
from datetime import datetime
from base64 import b64encode


class RFPReport(models.TransientModel):
    _name = 'rfp.report'
    _description = 'RFP Report Generator'
    _rec_name = 'display_name'

    supplier_id = fields.Many2one('res.partner', string='Supplier', required=True, domain="[('supplier_rank', '>', 0)]")
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    excel_report = fields.Binary(string='Excel Report')
    company_logo = fields.Image(string='Company Logo', max_width=200, max_height=200)
    html_report = fields.Html(string='HTML Report')

    def _compute_display_name(self):
        """
        Compute the display name for the RFP report.
        The display name is set to 'RFP Report for {supplier name}' if a supplier is selected,
        otherwise it is set to 'RFP Report'.
        """
        for record in self:
            if record.supplier_id:
                record.display_name = f'RFP Report for {record.supplier_id.name}'
            else:
                record.display_name = 'RFP Report'

    def prepare_rfp_data(self):
        """
        Prepare the RFP data for the report.
        Searches for accepted RFPs for the selected supplier within the specified date range.
        Raises a UserError if no accepted RFPs are found.
        Returns:(recordset) The RFPs that match the search criteria.
        """
        rfps = self.env['supplier.management.rfp'].search([
            ('approved_supplier', '=', self.supplier_id.id),
            ('status', '=', 'accepted'),
            ('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date)
        ])
        if not rfps:
            raise UserError('No accepted RFPs found for this supplier within the specified date range.')
        return rfps

    def prepare_vendor_data(self):
        """
        Prepare the vendor data for the report.
        Retrieves the supplier's bank account information and other details.
        Sets the company logo.
        Returns:(list) A list of tuples containing the supplier's information.
        """
        bank_account = self.supplier_id.bank_ids[0] if self.supplier_id.bank_ids else None
        bank = bank_account.bank_id if bank_account else None
        supplier_info = [
            ('Email', self.supplier_id.email or ' '),
            ('Phone', self.supplier_id.phone or ' '),
            ('Address', self.supplier_id.street or ' '),
            ('TIN', self.supplier_id.vat or ' '),
            ('Bank', bank.name if bank else ' '),
            ('Account Name', bank_account.acc_holder_name if bank_account else ' '),
            ('Account Number', bank_account.acc_number if bank_account else ' '),
            ('IBAN', bank.iban if bank else ' '),
            ('SWIFT', bank.bank_swift_code if bank else ' ')
        ]
        self.company_logo = self.env.company.logo
        return supplier_info

    def action_generate_qweb_preview(self):
        """
        Generate a QWeb preview of the RFP report.
        Ensures the start date is less than or equal to the end date.
        Prepares the RFP and vendor data, and renders the HTML content using a QWeb template.
        Sets the HTML report content and returns an action to open the report form.
        Returns:(dict)An action to open the RFP report form.
        """
        self.ensure_one()
        if self.start_date > datetime.now().date():
            raise UserError('Start date must be less than or equal to today.')

        if self.start_date > self.end_date:
            raise UserError('Start date must be less than or equal to end date.')

        self.company_logo = self.env.company.logo
        if not self.company_logo:
            raise UserError('Please add a logo for the company.')

        rfps = self.prepare_rfp_data()
        supplier_info = self.prepare_vendor_data()

        # Get currency symbol from the first RFP
        currency_symbol = rfps[0].currency_id.symbol if rfps else ''

        # Grouping products by RFP reference
        grouped_products = {}
        for rfp in rfps:
            for line in rfp.product_lines:
                rfp_key = rfp.rfp_name
                if rfp_key not in grouped_products:
                    grouped_products[rfp_key] = []
                grouped_products[rfp_key].append({
                    'product': line.product_id.name,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'delivery_charges': line.delivery_charges or 0,
                    'subtotal': line.subtotal_price
                })

        # Calculate total amount for RFPs and products
        total_amount = sum(rfp.total_amount for rfp in rfps)
        product_total_amount = sum(
            sum(product['subtotal'] for product in products)
            for products in grouped_products.values()
        )

        # Render the template
        template = self.env.ref('supplier_management.rfp_report_html_preview')
        html_content = self.env['ir.qweb']._render(template.id, {
            'object': self,
            'rfps': rfps,
            'grouped_products': grouped_products,
            'total_amount': total_amount,
            'product_total_amount': product_total_amount,
            'supplier_info': supplier_info,
            'currency_symbol': currency_symbol,
        })

        self.write({'html_report': html_content})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'rfp.report',
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }

    def action_generate_excel_report(self):
        """
        Generate an Excel report of the RFP data.
        Ensures the start date is less than or equal to the end date.
        Prepares the RFP and vendor data, and creates an Excel file with the report content.
        Sets the Excel report content and returns an action to download the report.
        Returns:(dict) An action to download the Excel report.
        """
        if self.start_date > datetime.now().date():
            raise UserError('Start date must be less than or equal to today.')

        if self.start_date > self.end_date:
            raise UserError('Start date must be less than or equal to end date.')

        rfps = self.prepare_rfp_data()
        supplier_info = self.prepare_vendor_data()
        company = self.env.company

        # Get currency symbol from the first RFP
        currency_symbol = rfps[0].currency_id.symbol if rfps else ''

        if not self.company_logo:
            raise UserError('Please add a logo for the company.')

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('RFP Report')

        # Set Column Widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 25)

        # Define Styles without currency symbol in data
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                             'fg_color': '#604058', 'font_color': 'white', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center',
                                            'valign': 'vcenter', 'border': 1})
        subheader_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        regular_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        number_format = workbook.add_format(
            {'align': 'center', 'valign': 'vcenter', 'num_format': '#,##0.00', 'border': 1})  # No currency symbol
        total_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                            'num_format': '#,##0.00', 'border': 1})  # No currency symbol
        alternate_row_format = workbook.add_format({'align': 'center', 'valign': 'vcenter',
                                                    'num_format': '#,##0.00', 'border': 1, 'bg_color': '#F2F2F2'})  # No currency symbol

        # Insert Company Logo
        logo_data = base64.b64decode(self.company_logo)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp:
            temp.write(logo_data)
            worksheet.insert_image('A1', temp.name, {'x_scale': 0.5, 'y_scale': 0.5})

        # Section-1: Supplier Info
        row = 2
        worksheet.merge_range('F3:G3', self.supplier_id.name, title_format)
        row += 1
        for label, value in supplier_info:
            worksheet.write(row, 5, label, subheader_format)
            worksheet.write(row, 6, value, regular_format)
            row += 1

        # Section-2: RFP Table
        row += 2
        worksheet.merge_range(f'B{row}:E{row}', 'Accepted RFPs', title_format)
        headers = ['RFP Number', 'Date', 'Required Date', f'Total Amount ({currency_symbol})']  # Symbol in header
        for col, header in enumerate(headers):
            worksheet.write(row, col + 1, header, header_format)

        row += 1
        amount_total = 0
        for index, rfp in enumerate(rfps):
            worksheet.write(row, 1, rfp.rfp_name, regular_format)
            worksheet.write(row, 2, rfp.create_date.strftime('%d/%m/%Y'), regular_format)
            worksheet.write(row, 3, rfp.required_date.strftime('%d/%m/%Y'), regular_format)
            amount = rfp.total_amount
            worksheet.write(row, 4, amount, number_format)  # No symbol here
            amount_total += amount
            row += 1
        worksheet.write(row, 3, 'Net Total', total_format)
        worksheet.write(row, 4, amount_total, total_format)  # No symbol here

        # Section-3: Product Lines (Grouped by RFP)
        row += 3
        worksheet.merge_range(f'B{row}:G{row}', 'Product Information', title_format)
        headers = ['RFP Number', 'Product', 'Quantity', f'Unit Price ({currency_symbol})',
                   f'Delivery Charge ({currency_symbol})', f'Subtotal ({currency_symbol})']  # Symbol in headers
        for col, header in enumerate(headers):
            worksheet.write(row, col + 1, header, header_format)

        row += 1

        # Grouping products by RFP reference
        grouped_products = {}
        for rfp in rfps:
            for line in rfp.product_lines:
                rfp_key = rfp.rfp_name
                if rfp_key not in grouped_products:
                    grouped_products[rfp_key] = []
                grouped_products[rfp_key].append({
                    'product': line.product_id.name,
                    'quantity': line.quantity,
                    'unit_price': line.unit_price,
                    'delivery_charges': line.delivery_charges or 0,
                    'subtotal': line.subtotal_price
                })

        # Writing grouped product lines with RFP row span
        for rfp_key, product_list in grouped_products.items():
            start_row = row
            for index, data in enumerate(product_list):
                worksheet.write(row, 2, data['product'], regular_format)
                worksheet.write(row, 3, data['quantity'], number_format)
                worksheet.write(row, 4, data['unit_price'], number_format)  # No symbol here
                worksheet.write(row, 5, data['delivery_charges'], number_format)  # No symbol here
                worksheet.write(row, 6, data['subtotal'], number_format)  # No symbol here
                row += 1

            worksheet.merge_range(start_row, 1, row - 1, 1, rfp_key, regular_format)

        # Add Net Total Row
        worksheet.write(row, 5, 'Net Total', total_format)
        worksheet.write(row, 6, amount_total, total_format)  # No symbol here

        # Section-4: Company Info
        row += 3
        worksheet.merge_range(f'B{row}:C{row}', company.name, title_format)
        company_info = [
            ('Email', company.email),
            ('Phone', company.phone),
            ('Address', company.street)
        ]
        for label, value in company_info:
            worksheet.write(row, 1, label, subheader_format)
            worksheet.write(row, 2, value, regular_format)
            row += 1

        workbook.close()
        output.seek(0)

        self.excel_report = base64.b64encode(output.getvalue()).decode('utf-8')
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s/%s/%s?download=true' % (self._name, self.id, 'excel_report'),
            'target': 'self',
        }