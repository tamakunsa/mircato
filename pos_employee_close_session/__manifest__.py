# -*- coding: utf-8 -*-
{
    "name": "Employee Close Point of Sale Session",
    "version": "0.0.1",
    "category": "Sales/Point of Sale",
    'summary': "Allow employees access to close session button",
    'description': "",
    "author": "Ewetoye Ibrahim, Erplify.ng",
    "website": "ibrahim.ewetoye.com",
    "auto_install": False,
    "depends": ["pos_hr"],
    'installable': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_employee_close_session/static/src/*',
        ],
    },
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
}
