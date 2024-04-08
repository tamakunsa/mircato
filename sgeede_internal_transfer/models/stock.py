# -*- coding: utf-8 -*-

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def do_internal_transfer_details(self):
        context = dict(self._context or {})
        picking = [picking]
        context.update({
            'active_model': self._name,
            'active_ids': picking,
            'active_id': len(picking) and picking[0] or False
        })

        return True

    transfer_id = fields.Many2one('stock.internal.transfer', 'Transfer')


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    user_ids = fields.Many2many('res.users', 'company_user_rel', 'company_id', 'user_id', 'Owner user')
