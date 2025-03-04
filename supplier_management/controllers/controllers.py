# -*- coding: utf-8 -*-
from odoo import http


class SupplierManagement(http.Controller):
    @http.route('/supplier_management/supplier_management', auth='public')
    def index(self, **kw):
        return "Hello, world"

    # @http.route('/supplier_management/supplier_management/objects', auth='public')
    # def list(self, **kw):
    #     return http.request.render('supplier_management.listing', {
    #         'root': '/supplier_management/supplier_management',
    #         'objects': http.request.env['supplier_management.supplier_management'].search([]),
    #     })
    #
    # @http.route('/supplier_management/supplier_management/objects/<model("supplier_management.supplier_management"):obj>', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('supplier_management.object', {
    #         'object': obj
    #     })

