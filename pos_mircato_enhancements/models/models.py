# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    phone = fields.Char(related="partner_id.phone",store=True)
