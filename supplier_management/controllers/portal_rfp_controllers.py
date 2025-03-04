from datetime import timedelta, datetime
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import pager as portal_pager
from ..utils import mail_utils as utils
from odoo.tools import groupby as groupbyelem
from operator import itemgetter


class RFPPortal(http.Controller):

    @http.route(['/my/rfps', '/my/rfps/page/<int:page>'], type='http', auth='user', website=True)
    def portal_rfp_list(self, page=1, sortby=None, search=None, search_in=None, groupby='status', **kw):
        limit = 7

        # Define sorting options
        searchbar_sortings = {
            'rfp_name': {'label': _('RFP Number'), 'order': 'rfp_name'},
            'required_date': {'label': _('Required Date'), 'order': 'required_date'},
        }

        # Define grouping options
        groupby_list = {
            'required_date': {'input': 'required_date', 'label': _('Required Date')},
            'status': {'input': 'status', 'label': _('Status')},
        }
        group_by_rfp = groupby_list.get(groupby, {})

        # Default search field is 'name'
        if not search_in:
            search_in = 'rfp_name'

        # Get the sort order
        order = searchbar_sortings[sortby]['order'] if sortby else 'rfp_name'
        if not sortby:
            sortby = 'rfp_name'

        # Define search filters
        search_list = {
            'all': {'label': _('All'), 'input': 'all', 'domain': []},
            'rfp_name': {'label': _('RFP Number'), 'input': 'rfp_name', 'domain': [('rfp_name', 'ilike', search)]},
            'status': {'label': _('Status'), 'input': 'status', 'domain': [('status', '=', search)]},
        }

        # Build the search domain based on the provided search term
        search_domain = [('status', '=', 'approved')]
        if search:
            search_domain += search_list[search_in]['domain']

        # Count the number of RFP records matching the domain
        rfp_count = request.env['supplier.management.rfp'].sudo().search_count(search_domain)
        # Setup pagination
        pager = portal_pager(
            url='/my/rfps',
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search},
            total=rfp_count,
            page=page,
            step=limit,
        )

        # Search for RFP records based on the domain, pagination, and order
        rfps = request.env['supplier.management.rfp'].sudo().search(
            search_domain, limit=limit, offset=pager['offset'], order=order
        )

        # Group the RFPs according to the selected grouping option
        if groupby_list.get(groupby) and groupby_list[groupby]['input']:
            rfp_group_list = [
                {
                    'group_name': key.rfp_name if hasattr(key, 'rfp_name') else key,
                    'rfps': list(group)
                }
                for key, group in groupbyelem(rfps, key=lambda r: getattr(r, group_by_rfp['input']))
            ]
        else:
            rfp_group_list = [{'group_name': _('All RFPs'), 'rfps': rfps}]

        # Render the portal view template with the prepared values
        return request.render('supplier_management.rfp_portal_list_view', {
            'page_name': 'rfp_list',
            'pager': pager,
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': search_list,
            'search_in': search_in,
            'search': search,
            'rfp_groups': rfp_group_list,
            'default_url': '/my/rfps',
            'groupby': groupby,
            'searchbar_groupby': groupby_list,
        })

    @http.route(['/my/rfps/<int:rfp_id>'], type='http', auth='user', website=True)
    def portal_rfp_detail(self, rfp_id, **kw):
        # Get all RFP record IDs
        rfp_ids = request.env['supplier.management.rfp'].sudo().search([('status', '=', 'approved')]).ids
        # Ensure rfp_id is valid
        if rfp_id not in rfp_ids:
            return request.not_found()

        rfp_index = rfp_ids.index(rfp_id)
        rfp_count = len(rfp_ids)

        # Determine next and previous record IDs
        next_index = rfp_ids[rfp_index + 1] if rfp_index < rfp_count - 1 else False
        prev_index = rfp_ids[rfp_index - 1] if rfp_index > 0 else False

        # Fetch the RFP record
        rfp = request.env['supplier.management.rfp'].sudo().browse(rfp_id)
        if not rfp.exists():
            return request.not_found()

        return request.render('supplier_management.rfp_portal_form_view', {
            'rfp': rfp,
            'page_name': 'rfp_details',
            'current_rfp_id': rfp.id,
            'prev_record': f'/my/rfps/{prev_index}' if prev_index else False,
            'next_record': f'/my/rfps/{next_index}' if next_index else False,
        })

    # Controller (Python)
    @http.route(['/my/rfp/<int:rfp_id>/submit'], type='http', methods=['POST'], auth='user', website=True)
    def rfp_submit(self, rfp_id, **kw):
        if not rfp_id:
            return request.redirect('/my')

        partner_id = request.env.user.partner_id.id
        rfp = request.env['supplier.management.rfp'].sudo().browse(rfp_id)
        if not rfp.exists():
            return request.redirect('/my')

        # Get currency from RFP or fallback to company currency
        currency = rfp.currency_id or request.env.company.currency_id

        # Validate date_planned
        date_planned = kw.get('date_planned')
        if date_planned:
            try:
                date_planned_obj = datetime.strptime(date_planned, '%Y-%m-%d').date()
                today = datetime.now().date()
                if date_planned_obj <= today:
                    return request.render(
                        "supplier_management.error_template",
                        {
                            'error_message': 'Expected Arrival must be a future date.',
                            'rfp_id': rfp_id,
                        }
                    )
            except ValueError:
                return request.render(
                    "supplier_management.error_template",
                    {
                        'error_message': 'Invalid date format for Expected Arrival.',
                        'rfp_id': rfp_id,
                    }
                )
        else:
            return request.render(
                "supplier_management.error_template",
                {
                    'error_message': 'Expected Arrival date is required.',
                    'rfp_id': rfp_id,
                }
            )

        rfq_vals = {
            'date_order': kw.get('required_date'),
            'warranty_period': kw.get('warranty_period'),
            'notes': kw.get('notes'),
            'rfp_id': rfp.id,
            'partner_id': partner_id,
            'user_id': rfp.create_uid.id,
            'date_planned': date_planned,
            'currency_id': currency.id,
        }

        rfq = request.env['purchase.order'].sudo().create(rfq_vals)

        for line in rfp.product_lines:
            unit_price_key = "order_line_unit_price_%s" % line.id
            delivery_charges_key = "order_line_delivery_charges_%s" % line.id
            line_vals = {
                'order_id': rfq.id,
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.name,
                'price_unit': float(kw.get(unit_price_key, 0)),
                'delivery_charges': float(kw.get(delivery_charges_key, 0)),
                'product_qty': line.quantity,
                'date_planned': date_planned,
            }
            request.env['purchase.order.line'].sudo().create(line_vals)

        email_values = {
            'subject': 'RFQ Submitted',
            'email_to': rfp.create_uid.login,
            'email_from': utils.get_sender_mail(request.env),
        }
        context = {
            'rfq_name': rfq.name,
            'rfp_name': rfp.rfp_name,
            'name': request.env.user.partner_id.name,
            'company_name': rfq.company_id.name,
        }
        template = request.env.ref('supplier_management.email_template_rfq_submitted_reviewers')
        template.with_context(**context).sudo().send_mail(rfq.id, email_values=email_values)

        return request.render("supplier_management.rfq_confirmation_template", {
            'rfq': rfq,
            'currency_symbol': currency.symbol,
        })

    @http.route(['/my/supplier/rfq/', '/my/supplier/rfq/page/<int:page>'], type='http', auth='user', website=True)
    def rfq_list(self, page=1, search=None, search_in=None, groupby='state', **kw):
        limit = 3  # Max RFQs per page

        groupby_list = {
            'state': {'input': 'state', 'label': _('Status')},
            'rfp_id': {'input': 'rfp_id', 'label': _('RFP Number')},
            'date_planned': {'input': 'date_planned', 'label': _('Expected Arrival')},
        }
        group_by_rfq = groupby_list.get(groupby, {})

        if not search_in:
            search_in = 'rfp_id'

        search_list = {
            'rfp_id': {'label': _('RFP Number'), 'input': 'rfp_id', 'domain': [('rfp_id.rfp_name', 'ilike', search)]},
            'state': {'label': _('Status'), 'input': 'state', 'domain': [('state', 'ilike', search)]},
        }

        search_domain = [('partner_id', '=', request.env.user.partner_id.id)]
        if search:
            search_domain += search_list[search_in]['domain']

        # Fetch all RFQs (no sorting specified)
        all_rfqs = request.env['purchase.order'].sudo().search(search_domain)

        # Group all RFQs BEFORE pagination
        if group_by_rfq:
            grouped_rfqs = groupbyelem(all_rfqs, itemgetter(group_by_rfq['input']))
            rfq_group_list = [{group_by_rfq['input']: key, 'rfqs': list(group)} for key, group in grouped_rfqs]
        else:
            rfq_group_list = [{'rfqs': all_rfqs}]

        # Flatten grouped RFQs while enforcing pagination limits
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        overall_count = 0
        paginated_rfqs = []
        paginated_groups = []
        for group in rfq_group_list:
            group_rfqs = group['rfqs']
            group_len = len(group_rfqs)
            if overall_count + group_len <= start_idx:
                overall_count += group_len
                continue

            start_in_group = max(0, start_idx - overall_count)
            end_in_group = min(group_len, end_idx - overall_count)
            group_page_rfqs = group_rfqs[start_in_group:end_in_group]

            paginated_rfqs.extend(group_page_rfqs)
            paginated_groups.append({
                'group_name': group.get(group_by_rfq['input'], _('Uncategorized')),
                'rfqs': group_page_rfqs,
            })
            overall_count += group_len
            if overall_count >= end_idx:
                break

        # Setup the pager without sortby
        rfq_count = len(all_rfqs)
        pager = portal_pager(
            url='/my/supplier/rfq',
            total=rfq_count,
            page=page,
            step=limit,
            url_args={'search_in': search_in, 'search': search, 'groupby': groupby}
        )

        return request.render("supplier_management.rfq_list_template", {
            'rfqs': paginated_rfqs,
            'page_name': 'rfq_list',
            'pager': pager,
            'searchbar_inputs': search_list,
            'search_in': search_in,
            'search': search,
            'rfq_groups': paginated_groups,
            'default_url': '/my/supplier/rfq',
            'groupby': groupby,
            'searchbar_groupby': groupby_list,
        })

    @http.route(['/my/suppliers/rfq/<int:rfq_id>'], type='http', auth='user', website=True)
    def rfq_detail(self, rfq_id, **kw):
        # Get all RFQ record IDs for the current user
        rfq_ids = request.env['purchase.order'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ]).ids

        # Ensure rfq_id is valid
        if rfq_id not in rfq_ids:
            return request.not_found()

        rfq_index = rfq_ids.index(rfq_id)
        rfq_count = len(rfq_ids)

        # Determine next and previous record IDs
        next_index = rfq_ids[rfq_index - 1] if rfq_index > 0 else False
        prev_index = rfq_ids[rfq_index + 1] if rfq_index < rfq_count - 1 else False

        # Fetch the RFQ record
        rfq = request.env['purchase.order'].sudo().browse(rfq_id)
        if not rfq.exists():
            return request.not_found()

        # Get currency symbol (assuming rfq has a currency_id field)
        currency_symbol = rfq.currency_id.symbol if rfq.currency_id else ''

        return request.render("supplier_management.rfq_detail_template", {
            'rfq': rfq,
            'page_name': 'rfq_details',
            'current_rfq_id': rfq.id,
            'prev_record': f'/my/suppliers/rfq/{prev_index}' if prev_index else False,
            'next_record': f'/my/suppliers/rfq/{next_index}' if next_index else False,
            'currency_symbol': currency_symbol,
        })
