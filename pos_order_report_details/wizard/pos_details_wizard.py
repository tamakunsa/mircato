# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

import pytz
from odoo import api, fields, models, _

from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class PosOrderReportWizard(models.TransientModel):
    _name = 'pos.order.report.wizard'
    _description = 'Point of Sale Order Report'

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    company_ids = fields.Many2many('res.company',string="Branches")
    pos_config_ids = fields.Many2many('pos.config')
    detailed_report = fields.Boolean(string=_('Detailed Report'), default=False)
    has_many_branches = fields.Boolean(default=False)



    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    @api.onchange('company_ids')
    def on_change_company_ids(self):
        res = {}
        pos_config_ids = self.env['pos.config']
        if self.company_ids:
            if len(self.company_ids) == 1:
                self.has_many_branches = False
                pos_config_ids = self.env['pos.config'].search([('company_id', '=', self.company_ids.ids[0])])
                res['domain'] = {
                    'pos_config_ids': [('company_id', '=', self.company_ids.ids[0])],
                }
            elif len(self.company_ids) > 1:
                self.has_many_branches = True
                self.pos_config_ids = False
            self.pos_config_ids = pos_config_ids
        else:
            self.pos_config_ids = False
        return res

    @api.model
    def get_pos_order_details(self, date_start=False, date_stop=False, branches=False, config_ids=False, has_many_branches=False):
        res = []
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        # branches_ids = []
        orders = self.env['pos.order'].search(domain)

        if has_many_branches:
            branches_ids = self.env['res.company'].browse(branches)

            for branch in branches_ids:
                total_sale_order_amount = total_returns_order_amount = total_net_sales_amount = 0
                total_sale_order_tax = total_returns_order_tax = total_net_tax_amount = 0
                total_cash_payment = total_master_cart_payment = total_total_payment = 0

                config_ids = self.env['pos.config'].search([('company_id', '=', branch.id)])

                for config_id in config_ids:
                    config_name = self.env['pos.config'].search([('id', '=', config_id.id)]).name
                    orders_ids = orders.search([('config_id', '=', config_id.id)]).filtered(
                        lambda o: o.date_order.date() >= date_start and o.date_order.date() <= date_stop)
                    cashiers = []
                    if orders_ids:
                        cashier_ids = orders_ids.mapped('user_id')
                        for cashier in cashier_ids:
                            cashiers.append(cashier.name)
                        cashiers = set(cashiers)

                        sales_order_ids = orders_ids.filtered(lambda s: len(s.refunded_order_ids) == 0)
                        sale_amount_with_tax = sum(sales_order_ids.mapped('amount_total'))

                        # ضريبة المبيعات
                        sale_order_tax = sum(sales_order_ids.mapped('amount_tax'))
                        # المبيعات
                        sale_order_amount = sale_amount_with_tax - sale_order_tax

                        returns_order_ids = orders_ids.filtered(lambda s: len(s.refunded_order_ids) != 0)
                        returns_amount_with_tax = sum(returns_order_ids.mapped('amount_total'))

                        # ضريبة المردودات
                        returns_order_tax = sum(returns_order_ids.mapped('amount_tax'))
                        # المردودات
                        returns_order_amount = returns_amount_with_tax - returns_order_tax

                        # صافي المبيعات
                        net_sales_amount = sale_order_amount + returns_order_amount
                        # صافي الضريبة
                        net_tax_amount = sale_order_tax + returns_order_tax

                        payment_ids = orders_ids.mapped('payment_ids')

                        # النقدية
                        cash_payment = sum(payment_ids.filtered(
                            lambda payment: payment.payment_method_id.journal_id.type == "cash").mapped('amount'))
                        # ماستر كارد
                        master_cart_payment = sum(payment_ids.filtered(
                            lambda payment: payment.payment_method_id.journal_id.type == "bank").mapped('amount'))
                        # الإجمالي
                        total_payment = cash_payment + master_cart_payment

                        total_sale_order_amount += sale_order_amount
                        total_returns_order_amount += returns_order_amount
                        total_net_sales_amount += net_sales_amount
                        total_sale_order_tax += sale_order_tax
                        total_returns_order_tax += returns_order_tax
                        total_net_tax_amount += net_tax_amount
                        total_cash_payment += cash_payment
                        total_master_cart_payment += master_cart_payment
                        total_total_payment += total_payment

                        vals = {
                            'cashier_ids': cashiers,
                            'branch': branch.name,
                            'config_name': config_name if self.detailed_report else 'hide',
                            'sale_order_amount': sale_order_amount,
                            'returns_order_amount': returns_order_amount,
                            'net_sales_amount': net_sales_amount,
                            'sale_order_tax': sale_order_tax,
                            'returns_order_tax': returns_order_tax,
                            'net_tax_amount': net_tax_amount,
                            'cash_payment': cash_payment,
                            'master_cart_payment': master_cart_payment,
                            'total_payment': total_payment,
                        }
                        res.append(vals)




                if res:
                    vals = {
                        'cashier_ids': cashiers,
                        'branch_name': branch.name,
                        'config_name': 'sub_totals',
                        'sale_order_amount': total_sale_order_amount,
                        'returns_order_amount': total_returns_order_amount,
                        'net_sales_amount': total_net_sales_amount,
                        'sale_order_tax': total_sale_order_tax,
                        'returns_order_tax': total_returns_order_tax,
                        'net_tax_amount': total_net_tax_amount,
                        'cash_payment': total_cash_payment,
                        'master_cart_payment': total_master_cart_payment,
                        'total_payment': total_total_payment,
                    }
                    res.append(vals)

        else:
            for config_id in config_ids:
                config_name = self.env['pos.config'].search([('id', '=', config_id)]).name
                orders_ids = orders.search([('config_id', '=', config_id)]).filtered(lambda o: o.date_order.date() >= date_start and o.date_order.date() <= date_stop)
                cashiers = []
                if orders_ids:
                    cashier_ids = orders_ids.mapped('user_id')
                    for cashier in cashier_ids:
                        cashiers.append(cashier.name)
                    cashiers = set(cashiers)


                    sales_order_ids = orders_ids.filtered(lambda s: len(s.refunded_order_ids) == 0)
                    sale_amount_with_tax = sum(sales_order_ids.mapped('amount_total'))

                    # ضريبة المبيعات
                    sale_order_tax = sum(sales_order_ids.mapped('amount_tax'))
                    # المبيعات
                    sale_order_amount = sale_amount_with_tax - sale_order_tax

                    returns_order_ids = orders_ids.filtered(lambda s: len(s.refunded_order_ids) != 0)
                    returns_amount_with_tax = sum(returns_order_ids.mapped('amount_total'))

                    # ضريبة المردودات
                    returns_order_tax = sum(returns_order_ids.mapped('amount_tax'))
                    # المردودات
                    returns_order_amount = returns_amount_with_tax - returns_order_tax

                    # صافي المبيعات
                    net_sales_amount = sale_order_amount + returns_order_amount
                    # صافي الضريبة
                    net_tax_amount = sale_order_tax + returns_order_tax

                    payment_ids = orders_ids.mapped('payment_ids')

                    # النقدية
                    cash_payment = sum(payment_ids.filtered(
                        lambda payment: payment.payment_method_id.journal_id.type == "cash").mapped('amount'))
                    # ماستر كارد
                    master_cart_payment = sum(payment_ids.filtered(
                        lambda payment: payment.payment_method_id.journal_id.type == "bank").mapped('amount'))
                    # الإجمالي
                    total_payment = cash_payment + master_cart_payment

                    vals = {
                        # 'branch': config_id.company_id.name,
                        'cashier_ids': cashiers,
                        'config_name': config_name,
                        'sale_order_amount': sale_order_amount,
                        'returns_order_amount': returns_order_amount,
                        'net_sales_amount': net_sales_amount,
                        'sale_order_tax': sale_order_tax,
                        'returns_order_tax': returns_order_tax,
                        'net_tax_amount': net_tax_amount,
                        'cash_payment': cash_payment,
                        'master_cart_payment': master_cart_payment,
                        'total_payment': total_payment,
                    }
                    res.append(vals)

        if res:
            total_sale_order_amount = total_returns_order_amount = total_net_sales_amount = 0
            total_sale_order_tax = total_returns_order_tax = total_net_tax_amount = 0
            total_cash_payment = total_master_cart_payment = total_total_payment = 0

            for rec in res:
                if rec['config_name'] != 'sub_totals':
                    total_sale_order_amount += rec['sale_order_amount']
                    total_returns_order_amount += rec['returns_order_amount']
                    total_net_sales_amount += rec['net_sales_amount']
                    total_sale_order_tax += rec['sale_order_tax']
                    total_returns_order_tax += rec['returns_order_tax']
                    total_net_tax_amount += rec['net_tax_amount']
                    total_cash_payment += rec['cash_payment']
                    total_master_cart_payment += rec['master_cart_payment']
                    total_total_payment += rec['total_payment']

            vals = {
                # 'branch': '',
                'config_name': 'Totals',
                'sale_order_amount': total_sale_order_amount,
                'returns_order_amount': total_returns_order_amount,
                'net_sales_amount': total_net_sales_amount,
                'sale_order_tax': total_sale_order_tax,
                'returns_order_tax': total_returns_order_tax,
                'net_tax_amount': total_net_tax_amount,
                'cash_payment': total_cash_payment,
                'master_cart_payment': total_master_cart_payment,
                'total_payment': total_total_payment,
            }
            res.append(vals)

        return res

    # generate branches and pos config date for the title of the video
    def get_title_date(self):
        result = []
        if not self.company_ids:
            for pos_config in self.pos_config_ids:
                result.append('pos_config')
                result.append(pos_config.name)
        else:
            result.append('branch')
            for branch in self.company_ids:
                result.append(branch.name)
        return result


    def get_resultat_pos_order_details(self):
        resultat = self.get_pos_order_details(self.start_date, self.end_date, self.company_ids.ids, self.pos_config_ids.ids, self.has_many_branches)
        return resultat

    def generate_report(self):
        return self.env.ref('pos_order_report_details.template_point_of_sale_report_saledetails_new').report_action(self)


