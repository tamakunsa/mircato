from odoo import models, fields, api
import time


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_id = fields.Many2one(
        'vendor.code',
        string='Vendor',
        required=True,
        help='Select the vendor associated with this product.'
    )

    type_id = fields.Many2one(
        'type.code',
        string='Type',
        required=True,
        help='Select the type associated with this product.'
    )

    kind_id = fields.Many2one(
        'kind.code',
        string='kind',
        required=True,
        help='Select the kind associated with this product.'
    )

    price_id = fields.Many2one(
        'price.code',
        string='Price',
        required=True,
        help='Select the price associated with this product.'
    )

    status = fields.Selection([
        ('draft', 'Draft'),
        ('generated', 'Barcode Generated'),
    ], string='Status', default='draft')

    def generate_barcode(self):
        sequence_parameter_prefix = 'product.barcode.sequence.'
        for record in self:
            base_barcode = '{}{}{}{}'.format(
                record.type_id.code or '',
                record.vendor_id.code or '',
                record.kind_id.code or '',
                record.price_id.code or ''
            )

            sequence_key = sequence_parameter_prefix + base_barcode

            sequence = int(self.env['ir.config_parameter'].sudo().get_param(sequence_key, default=1))

            record.barcode = '{}{:d}'.format(base_barcode, sequence)

            self.env['ir.config_parameter'].sudo().set_param(sequence_key, sequence + 1)
            record.status = 'generated'
