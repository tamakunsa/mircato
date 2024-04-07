# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    transit_location_id = fields.Many2one(string="Transit Location", related="company_id.transit_location_id",
                                          readonly=False)
