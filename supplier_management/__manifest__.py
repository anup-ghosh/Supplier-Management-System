# -*- coding: utf-8 -*-
{
    'name': "Supplier Management",

    'summary': "Vendor Management System",

    'description': """
    Vendor Management System
    """,

    'author': "Anup Ghosh",
    'website': "https://github.com/anup-ghosh-bjit",

    'category': 'Procurement Management',
    'version': '0.1',

    # necessary for this one to work correctly
    'depends': ['portal', 'purchase', 'account', 'contacts', 'website'],

    # always loaded
    'data': [
        'security/supplier_management_security.xml',
        'security/ir.model.access.csv',
        'views/supplier_application_views.xml',
        'views/res_partner_bank_inherit_views.xml',
        'views/bank_views_extended.xml',
        'views/res_partner_extended.xml',
        'views/email_template_views.xml',
        'views/mail_blacklist_views_inherited.xml',
        'views/supplier_registration_portal_views.xml',
        'views/supplier_registration_views.xml',
        'wizard/mail_blacklist_wizard_views.xml',
        'wizard/supplier_reject_views.xml',
        'views/ir_sequence.xml',
        'views/supplier_management_rfp_views.xml',
        'views/supplier_management_menus.xml',
        'views/dashboard_action_views.xml',
        'views/rfp_portal_views.xml',
        'views/purchase_order_extended_view.xml',
        'wizard/rfp_report_views.xml',
        'wizard/rfp_html_preview_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/user_demo.xml',
        'demo/supplier_management_registration_demo.xml',
        'demo/supplier.management.rfp.csv',
        'demo/supplier.management.rfp.product.line.csv',
        'demo/purchase.order.csv',
        'demo/purchase.order.line.csv',
    ],

    "assets": {
        "web.assets_backend": [
            "supplier_management/static/src/components/dashboard.js",
            "supplier_management/static/src/components/dashboard.xml",
            "supplier_management/static/src/components/dashboard.scss",
        ],

    },

}
