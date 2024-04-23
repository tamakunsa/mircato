from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PosSession(models.Model):
    _inherit = 'pos.session'

    account_analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account',
                                          copy=False)

    def _prepare_line(self, order_line):
        res = super(PosSession, self)._prepare_line(order_line)
        res['analytic_distribution'] = {self.config_id.account_analytic_id.id: 100} or False
        return res

    def _get_sale_vals(self, key, amount, amount_converted):
        res = super(PosSession, self)._get_sale_vals(key, amount, amount_converted)
        res['analytic_distribution'] = {self.config_id.account_analytic_id.id: 100} or False
        return res

    def _get_stock_output_vals(self, out_account, amount, amount_converted):
        partial_args = {'account_id': out_account.id, 'move_id': self.move_id.id,
                        'analytic_distribution': False}
        return self._credit_amounts(partial_args, amount, amount_converted, force_company_currency=True)

    def _get_stock_expense_vals(self, exp_account, amount, amount_converted):
        partial_args = {'account_id': exp_account.id, 'move_id': self.move_id.id,
                        'analytic_distribution': {self.config_id.account_analytic_id.id: 100} or False}
        return self._debit_amounts(partial_args, amount, amount_converted, force_company_currency=True)

    def write(self, vals):
        for session in self:
            if not session.account_analytic_id:
                vals['account_analytic_id'] = session.config_id.account_analytic_id or False
        return super(PosSession, self).write(vals)

    def _reconcile_account_move_lines(self, data):
        # reconcile cash receivable lines
        split_cash_statement_lines = data.get('split_cash_statement_lines')
        combine_cash_statement_lines = data.get('combine_cash_statement_lines')
        split_cash_receivable_lines = data.get('split_cash_receivable_lines')
        combine_cash_receivable_lines = data.get('combine_cash_receivable_lines')
        combine_inv_payment_receivable_lines = data.get('combine_inv_payment_receivable_lines')
        split_inv_payment_receivable_lines = data.get('split_inv_payment_receivable_lines')
        combine_invoice_receivable_lines = data.get('combine_invoice_receivable_lines')
        split_invoice_receivable_lines = data.get('split_invoice_receivable_lines')
        stock_output_lines = data.get('stock_output_lines')
        payment_method_to_receivable_lines = data.get('payment_method_to_receivable_lines')
        payment_to_receivable_lines = data.get('payment_to_receivable_lines')

        all_lines = (
                split_cash_statement_lines
                | combine_cash_statement_lines
                | split_cash_receivable_lines
                | combine_cash_receivable_lines
        )

        for line in all_lines:
            for rec in line.move_id.line_ids:
                if rec.account_id.account_type not in ('income', 'expense_direct_cost', 'expense'):
                    rec.update({'analytic_distribution': False})
                else:
                    rec.update({'analytic_distribution': {self.config_id.account_analytic_id.id: 100}})
        all_lines.filtered(lambda line: line.move_id.state != 'posted').move_id._post(soft=False)

        accounts = all_lines.mapped('account_id')
        lines_by_account = [all_lines.filtered(lambda l: l.account_id == account and not l.reconciled) for account in
                            accounts if account.reconcile]
        for lines in lines_by_account:
            lines.reconcile()

        for payment_method, lines in payment_method_to_receivable_lines.items():
            receivable_account = self._get_receivable_account(payment_method)
            for pay_m_line in lines:
                for rec in pay_m_line.move_id.line_ids:
                    if rec.account_id.account_type not in ('income', 'expense_direct_cost', 'expense'):
                        rec.update({'analytic_distribution': False})
                    else:
                        rec.update({'analytic_distribution': {self.config_id.account_analytic_id.id: 100}})
            if receivable_account.reconcile:
                lines.filtered(lambda line: not line.reconciled).reconcile()

        for payment, lines in payment_to_receivable_lines.items():
            for pay_line in lines:
                for rec in pay_line.move_id.line_ids:
                    if rec.account_id.account_type not in ('income', 'expense_direct_cost', 'expense'):
                        rec.update({'analytic_distribution': False})
                    else:
                        rec.update({'analytic_distribution': {self.config_id.account_analytic_id.id: 100}})
            if payment.partner_id.property_account_receivable_id.reconcile:
                lines.filtered(lambda line: not line.reconciled).reconcile()

        # Reconcile invoice payments' receivable lines. But we only do when the account is reconcilable.
        # Though `account_default_pos_receivable_account_id` should be of type receivable, there is currently
        # no constraint for it. Therefore, it is possible to put set a non-reconcilable account to it.
        if self.company_id.account_default_pos_receivable_account_id.reconcile:
            for payment_method in combine_inv_payment_receivable_lines:
                lines = combine_inv_payment_receivable_lines[payment_method] | combine_invoice_receivable_lines.get(
                    payment_method, self.env['account.move.line'])
                for line in lines:
                    for rec in line.move_id.line_ids:
                        if rec.account_id.account_type not in ('income', 'expense_direct_cost', 'expense'):
                            rec.update({'analytic_distribution': False})
                        else:
                            rec.update({'analytic_distribution': {self.config_id.account_analytic_id.id: 100}})
                lines.filtered(lambda line: not line.reconciled).reconcile()

            for payment in split_inv_payment_receivable_lines:
                lines = split_inv_payment_receivable_lines[payment] | \
                        split_invoice_receivable_lines.get(payment, self.env['account.move.line'])
                for line in lines:
                    for rec in line.move_id.line_ids:
                        if rec.account_id.account_type not in ('income', 'expense_direct_cost', 'expense'):
                            rec.update({'analytic_distribution': False})
                        else:
                            rec.update({'analytic_distribution': {self.config_id.account_analytic_id.id: 100}})
                lines.filtered(lambda line: not line.reconciled).reconcile()

        # reconcile stock output lines
        pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
        pickings |= self.order_ids.filtered(lambda o: not o.is_invoiced).mapped('picking_ids')
        stock_moves = self.env['stock.move'].search([('picking_id', 'in', pickings.ids)])
        stock_account_move_lines = self.env['account.move'].search([('stock_move_id', 'in', stock_moves.ids)]).mapped(
            'line_ids')
        for account_id in stock_output_lines:
            (stock_output_lines[account_id]
             | stock_account_move_lines.filtered(lambda aml: aml.account_id == account_id)
             ).filtered(lambda aml: not aml.reconciled).reconcile()
        return data

    def _post_statement_difference(self, amount, is_opening):
        if amount:
            if self.config_id.cash_control:
                st_line_vals = {
                    'journal_id': self.cash_journal_id.id,
                    'amount': amount,
                    'date': self.statement_line_ids.sorted()[-1:].date or fields.Date.context_today(self),
                    'pos_session_id': self.id,
                }

            if amount < 0.0:
                if not self.cash_journal_id.loss_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Loss Account. This account will be used to record cash difference.',
                          self.cash_journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Loss)") + (
                    _(' - opening') if is_opening else _(' - closing'))
                if not is_opening:
                    st_line_vals['counterpart_account_id'] = self.cash_journal_id.loss_account_id.id
            else:
                # self.cash_register_difference  > 0.0
                if not self.cash_journal_id.profit_account_id:
                    raise UserError(
                        _('Please go on the %s journal and define a Profit Account. This account will be used to record cash difference.',
                          self.cash_journal_id.name))

                st_line_vals['payment_ref'] = _("Cash difference observed during the counting (Profit)") + (
                    _(' - opening') if is_opening else _(' - closing'))
                if not is_opening:
                    st_line_vals['counterpart_account_id'] = self.cash_journal_id.profit_account_id.id

            statement = self.env['account.bank.statement.line'].create(st_line_vals)
            for line in statement.move_id.line_ids:
                if line.analytic_distribution:
                    line.update({'analytic_distribution': False})

    def try_cash_in_out(self, _type, amount, reason, extras):
        sign = 1 if _type == 'in' else -1
        sessions = self.filtered('cash_journal_id')
        if not sessions:
            raise UserError(_("There is no cash payment method for this PoS Session"))

        account_bank_statement_line = self.env['account.bank.statement.line'].create([
            {
                'pos_session_id': session.id,
                'journal_id': session.cash_journal_id.id,
                'amount': sign * amount,
                'date': fields.Date.context_today(self),
                'payment_ref': '-'.join([session.name, extras['translatedType'], reason]),
            }
            for session in sessions
        ])
        for line in account_bank_statement_line.move_id.line_ids:
            if line.analytic_distribution:
                line.update({'analytic_distribution': False})

        message_content = [f"Cash {extras['translatedType']}", f'- Amount: {extras["formattedAmount"]}']
        if reason:
            message_content.append(f'- Reason: {reason}')
        self.message_post(body='<br/>\n'.join(message_content))
