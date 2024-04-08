# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    transit_location_id = fields.Many2one('stock.location', 'Transit Location')
