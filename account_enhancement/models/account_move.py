from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    change_analytic_distribution = fields.Boolean(compute='check_change_analytic_distribution',
                                                  default=lambda self: self.env.user.has_group(
                                                      'account_enhancement.group_control_entry_analytic_account'))

    def check_change_analytic_distribution(self):
        for rec in self:
            rec.change_analytic_distribution = False
            if self.env.user.has_group(
                    'account_enhancement.group_control_entry_analytic_account'):
                rec.change_analytic_distribution = True

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            company = m.company_id or self.env.company
            m.suitable_journal_ids = self.env['account.journal'].search([
                *self.env['account.journal']._check_company_domain(company),
                ('type', '=', journal_type),
            ])
            if m.move_type == 'entry':
                journal_types = 'sale', 'purchase', 'bank', 'cash', 'general'
                m.suitable_journal_ids = self.env['account.journal'].search([
                    *self.env['account.journal']._check_company_domain(company),
                    ('type', 'in', journal_types),
                ])
