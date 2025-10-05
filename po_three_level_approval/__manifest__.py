# -*- coding: utf-8 -*-
{
    "name": "Purchase Order Approval",
    'version': '18.0.1.0.0',
    'category': 'Purchase',
    "summary": "Three Level Purchase Order Approval",
    'description': "Three Levels of Approval in Purchase work flow",
    'author': 'Rinoy',
    'depends': ['base', 'purchase', 'purchase_stock'],
    'data': [
        "security/security.xml",
        "data/approval_mail.xml",
        "views/purchase_order.xml",
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
