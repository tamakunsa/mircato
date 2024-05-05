# -*- coding: utf-8 -*-
{
    'name': "ERA POS Order Report",
    "version": "15.0.0.1",
    "category": "Accounting",
    'description': """
        ERA POS Order Report
    """,
    'author': "Era group",
    'email': "aqlan@era.net.sa ",
    'website': "https://era.net.sa",
    'category': 'accounting',
    'price': 0,  
    'currency': 'USD',
    'version': '0.1',
    'license': 'AGPL-3',
    'images': [],
    'depends': ['point_of_sale'],
    "data": [
        'security/ir.model.access.csv',
        'report/pos_report.xml',
        'report/action_pos_report.xml',
        'wizard/pos_details_wizard.xml',
    ],
    'qweb': [],
    "application": True,

}
