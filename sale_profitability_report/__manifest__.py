# -*- coding: utf-8 -*-
{
    "name": "Sale Profitability Report",
    'version': '18.0.1.0.0',
    'category': 'Sales/Reporting',
    "summary": """ Order-wise revenue, cost, and margin for sales orders """,
    'description': """ This module provides a wizard to analyze sales profitability by:
                        - Date range  
                        - Product category  
                        - Customer """,
    'author': 'Rinoy',
    'depends': ['base', 'sales_team', 'sale_management', 'account', 'stock'],
    'data': [
        "security/ir.model.access.csv",
        "wizards/sale_profitability_wizard.xml",
        "report/report_sale_profitability.xml"
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
