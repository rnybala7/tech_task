# -*- coding: utf-8 -*-
{
    "name": "Sale Discount Rules",
    'version': '18.0.1.0.0',
    'category': 'Sales Management',
    "summary": "Dynamic discount rules for Sales Orders",
    'description': "Dynamic discount rules for Sales Orders",
    'author': 'Rinoy',
    'depends': ['base', 'sales_team', 'sale_management'],
    'data': [
        "security/ir.model.access.csv",
        "views/sale_discount_rule.xml",
        "views/sale_order_views.xml"
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
