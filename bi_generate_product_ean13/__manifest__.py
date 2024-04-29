# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Generate Product Barcode (EAN13) Odoo App',
    'version': '17.0.0.1',
    'summary': "Generate automatic barcode for products Generate auto barcode for product auto ean13 barcode for product"
               " automatic barcode generation auto barcode generation automatic ean13 barcode generation auto serial "
               "generation automatic Auto Generate Product Barcode",
    'category': 'Sales',
    'description': """Generate automatic and manual barcode for products, Generate barcode for barcode, Generate Barcode in odoo
    barcode for product on odoo, barcode on product, ean13 barcode on product. 
    
This apps is used for generic barcode automatically for product
it will provide option that on configuration level that either you can allow or disable option for generate barcode.

Also on barcode generation will have two option generate with random number or it will be based on current date.

We also provide option to generate barcode easily for multiple product in single click as well as manual generate barcode for single product.

Product Barcode Generator Barcode Generator
Auto Generate EAN13 for Product Auto Set Barcode Product EAN13 Image
Auto Generate EAN13 for Product Generate Product Barcode EAN13 product barcode EAN 13
Product barcode generator Product Barcode Number & Image
Barcode Image Barcode Number Barcode label Product EAN13 Auto Generator
Generate barcode automatically for product Generate EAN13 Product Barcode generate products barcode number
Auto Generate EAN13 for Product Auto Generate Product Barcode
Auto Generate barcode on product Auto Generate ean13 barcode on Product
Auto Generate Product barcode label Auto Generate barcode label
Auto product barcodde Generator Auto barcode Generator
Auto barcode label Generator automatic Generate Product Barcode
automatic Generate barcode on product automatic Generate ean13 barcode on Product
automatic Generate Product barcode label automatic Generate barcode label
automatic product barcodde Generator automatic barcode Generator
automatic barcode label Generator Auto product sequance
automatic product sequance generate barcode for product product barcode generator Generate Product EAN13
""",
    'author': 'BrowseInfo',
    'website': 'http://www.browseinfo.in',
    'depends': ['base', 'product', 'sale', 'barcodes', 'sale_management', 'custom_barcode'],
    'data': [
        'views/generate_product_ean13_view.xml',
        'views/res_config_view.xml',
        'security/ir.model.access.csv'
    ],
    'price': 8.00,
    'currency': "EUR",
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/YmSwBcwBCvg',
    "images": ['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
