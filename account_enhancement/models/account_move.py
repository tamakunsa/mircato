from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    change_analytic_distribution = fields.Boolean(compute='check_confirm_bill',
                                                  default=lambda self: self.env.user.has_group(
                                                      'account_enhancement.group_control_entry_analytic_account'))

    def check_change_analytic_distribution(self):
        for rec in self:
            rec.change_analytic_distribution = False
            if self.env.user.has_group(
                    'account_enhancement.group_control_entry_analytic_account'):
                rec.change_analytic_distribution = True
