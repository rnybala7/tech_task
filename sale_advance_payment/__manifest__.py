# -*- coding: utf-8 -*-
{
    "name": "Sale Advance Payment",
    'version': '18.0.1.0.0',
    'category': 'Sales Management',
    "summary": """ Adds an advance payment field to Sale Orders and automatically creates 
        journal entry upon confirmation. """,
    'description': "Advance Payment from Sale Order",
    'author': 'Rinoy',
    'depends': ['base', 'sale_management', 'account', 'accountant'],
    'data': [
        "data/account_data.xml",
        "views/res_config_settings.xml",
        "views/sale_order_view.xml"
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
