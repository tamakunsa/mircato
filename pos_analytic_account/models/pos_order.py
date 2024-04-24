from odoo import models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account', copy=False, string='Analytic Account')

    def _prepare_invoice_line(self, order_line):
        res = super(PosOrder, self)._prepare_invoice_line(order_line)
        if self.session_id.config_id.account_analytic_id:
            res['analytic_distribution'] = {self.session_id.config_id.account_analytic_id.id: 100}
        return res

    def write(self, vals):
        for order in self:
            if order.session_id.config_id.account_analytic_id.id and not order.account_analytic_id:
                vals['account_analytic_id'] = order.session_id.config_id.account_analytic_id.id
        return super(PosOrder, self).write(vals)
