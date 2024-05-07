{
    'name': 'Custom Barcode',
    'version': '16.0',
    'summary': 'Custom barcode module for Odoo',
    'description': 'This module adds custom barcode functionality to Odoo.',
    'category': 'Custom',
    'author': 'M Sohaib',
    'website': '',
    'depends': ['base', 'stock', 'product'],
    'data': [
        'views/price_barcode_view.xml',
        'views/kind_barcode_view.xml',
        'views/type_barcode_view.xml',
        # 'views/vendor_barcode_view.xml',
        'views/product_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}