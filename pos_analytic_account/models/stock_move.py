from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Project')

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id,
                                       credit_account_id, svl_id, description):
        self.ensure_one()
        # analytic_acc = {}
        # if 'Product' not in description:
        #     if 'POS' in description.split('/')[1]:
        #         pos_order = self.env['pos.order'].search([('account_analytic_id', '!=', False)], limit=1)
        #         print(pos_order)
        #         analytic_acc = {str(pos_order.account_analytic_id.id): 100}
        #
        #     if len(description.split('/')) > 2:
        #         if 'IN' in description.split('/')[2]:
        #             po_line = self.env['purchase.order.line'].search([('order_id.name', '=', self.picking_id.origin),
        #                                                               ('product_id', '=', self.product_id.id)], limit=1)
        #             analytic_acc = po_line.analytic_distribution
        #         elif 'OUT' in description.split('/')[2]:
        #             so_line = self.env['sale.order.line'].search([('order_id.name', '=', self.picking_id.origin),
        #                                                           ('product_id', '=', self.product_id.id)], limit=1)
        #             analytic_acc = so_line.analytic_distribution
        #     elif '/' == description.split(' - ')[0]:
        #         account_move_line = self.env['account.move.line'].search([('product_id', '=', self.product_id.id)],
        #                                                                  limit=1)
        #         analytic_acc = account_move_line.analytic_distribution

        debit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
            'analytic_distribution': False
        }

        credit_line_vals = {
            'name': description,
            'product_id': self.product_id.id,
            'quantity': qty,
            'product_uom_id': self.product_id.uom_id.id,
            'ref': description,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
            'analytic_distribution': False
        }

        rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
        if credit_value != debit_value:
            # for supplier returns of product in average costing method, in anglo saxon mode
            diff_amount = debit_value - credit_value
            price_diff_account = self.product_id.property_account_creditor_price_difference

            if not price_diff_account:
                price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
            if not price_diff_account:
                raise UserError(
                    _('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))

            rslt['price_diff_line_vals'] = {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'credit': diff_amount > 0 and diff_amount or 0,
                'debit': diff_amount < 0 and -diff_amount or 0,
                'account_id': price_diff_account.id,
            }
        return rslt

# class StockMoveLine(models.Model):
#     _inherit = 'stock.move.line'
#
#     analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Project')
