# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
from odoo import models, api, fields, _
from datetime import datetime
import random

# import barcode

try:
    from barcode.writer import ImageWriter
except ImportError:
    ImageWriter = None  # lint:ok
import base64
import os


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def generate_bulk_barcode(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        prouct_ids = self.browse(active_ids)
        for record in prouct_ids:
            number_random = int("%0.13d" % random.randint(0, 999999999999))
            bcode = self.env['barcode.nomenclature'].sanitize_ean("%s" % (number_random))

            if record.price_id != False:
                bcode = record.price_id.name + bcode
            if record.kind_id != False:
                bcode = record.kind_id.name + bcode
            if record.type_id != False:
                bcode = record.type_id.name + bcode

            record.write({'barcode': bcode, 'default_code': bcode})


class ProductProduct(models.Model):
    _inherit = "product.product"

    check_barcode_setting = fields.Boolean('Check Barcode Setting')
    barcode_img = fields.Binary('Barcode Image')

    @api.model
    def default_get(self, field_lst):
        res = super(ProductProduct, self).default_get(field_lst)
        if not self.env['ir.config_parameter'].sudo().get_param('bi_generate_product_ean13.gen_barcode'):
            res['check_barcode_setting'] = True
        return res

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        number_random = 0
        if res:
            if not vals.get('barcode') and self.env['ir.config_parameter'].sudo().get_param(
                    'bi_generate_product_ean13.gen_barcode'):
                if self.env['ir.config_parameter'].sudo().get_param(
                        'bi_generate_product_ean13.generate_option') == 'date':
                    barcode_str = self.env['barcode.nomenclature'].sanitize_ean(
                        "%s%s" % (res.id, datetime.now().strftime("%d%m%y%H%M")))
                else:
                    number_random = int("%0.13d" % random.randint(0, 999999999999))
                    barcode_str = self.env['barcode.nomenclature'].sanitize_ean("%s" % (number_random))

                if res.price_id != False:
                    barcode_str = res.price_id.name + barcode_str
                if res.kind_id != False:
                    barcode_str = res.kind_id.name + barcode_str
                if res.type_id != False:
                    barcode_str = res.type_id.name + barcode_str

                res.write({'barcode': barcode_str, 'default_code': barcode_str})
        return res

    def v_generate_bulk_barcode(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids')
        prouct_ids = self.browse(active_ids)
        for record in prouct_ids:
            number_random = int("%0.13d" % random.randint(0, 999999999999))
            bcode = self.env['barcode.nomenclature'].sanitize_ean("%s" % (number_random))

            if record.price_id != False:
                bcode = record.price_id.name + bcode
            if record.kind_id != False:
                bcode = record.kind_id.name + bcode
            if record.type_id != False:
                bcode = record.type_id.name + bcode

            record.write({'barcode': bcode, 'default_code': bcode})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
