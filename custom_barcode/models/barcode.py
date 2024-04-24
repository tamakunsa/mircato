from odoo import models, fields, api


class VendorBarcode(models.Model):
    _name = 'vendor.code'
    _description = 'Custom Barcode'

    name = fields.Many2one('res.partner', string='Name', required=True)
    code = fields.Char(string='Code', size=4)




class TypeBarcode(models.Model):
    _name = 'type.code'
    _description = 'Type Barcode'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=4)




class KindBarcode(models.Model):
    _name = 'kind.code'
    _description = 'kind Barcode'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=3)




class Pricearcode(models.Model):
    _name = 'price.code'
    _description = 'Price Barcode'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', size=6)


