from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    confirm_bill = fields.Boolean(compute='check_confirm_bill',
                                  default=lambda self: self.env.user.has_group(
                                      'po_access_right.group_control_bill_confirmation'))

    def check_confirm_bill(self):
        for rec in self:
            rec.confirm_bill = self.env.user.has_group('po_access_right.group_control_bill_confirmation')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if not rec.confirm_bill and rec.move_type == 'in_invoice':
                raise ValidationError(_('Sorry, You can not confirm this bill. Please contact your administrator.'))
        return res
