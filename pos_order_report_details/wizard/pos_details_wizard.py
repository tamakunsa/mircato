# -*- coding: utf-8 -*-

import logging
from datetime import timedelta

import pytz
from odoo import api, fields, models, _
import xlsxwriter
from io import BytesIO

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
    def get_pos_order_details(self, date_start=False, date_stop=False, branches=False, config_ids=False, has_many_branches=False,detailed_report=False):
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
                print(date_start)
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
                            'config_name': config_name if detailed_report else 'hide',
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
        resultat = self.get_pos_order_details(self.start_date, self.end_date, self.company_ids.ids, self.pos_config_ids.ids, self.has_many_branches,self.detailed_report)
        return resultat

    def generate_report(self):
        return self.env.ref('pos_order_report_details.template_point_of_sale_report_saledetails_new').report_action(self)



    def print_excel_report(self):
        url = {
            'type': 'ir.actions.act_url',
            'target': 'new',
        }
        url.update({
                'url': '/pos/report/detail/excel_report?date_start=%(date_from)s&date_stop=%(date_stop)s&branches=%(branches)s&config_ids=%(config_ids)s&has_many_branches=%(has_many_branches)s&detailed_report=%(detailed_report)s' % {
                    'date_from':self.start_date,
                    'date_stop':self.end_date,
                    'branches':','.join(str(company_id) for company_id in self.company_ids.ids),
                    'config_ids':','.join(str(pos_config_id) for pos_config_id in self.pos_config_ids.ids),
                    'has_many_branches':self.has_many_branches,
                    'detailed_report':self.detailed_report,
                }
        })

        return url


    def generate_excel_report(self, **kwargs):
        # Fetch data using the get_resultat_pos_order_details() function
        data = self.get_pos_order_details(**kwargs)

        # data = self.get_resultat_pos_order_details()

        # Create a new XLSX workbook and add a worksheet
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Define formats for headers and data
        bold_format = workbook.add_format({'bold': True})
        number_format = workbook.add_format({'num_format': '#,##0.00'})
        number_totals_format = workbook.add_format({'num_format': '#,##0.00','bg_color': '#888888'})
        number_sub_total_format = workbook.add_format({'num_format': '#,##0.00','bg_color':'#EEEEEE'})

        # Write headers
        headers = ["", "مبيعات", "مردودات", "صافي المبيعات", "ضريبة مبيعات", "ضريبة مردودات", "صافي الضريبة", "النقدية", "ماستر كارد", "الاجمالي", "الكاشير"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold_format)

        row = 1
        for res in data:
            worksheet.set_column(row, 0, 35)
            if res['config_name'] == "Totals":
                worksheet.write(row, 0, res.get("config_name", ""),number_totals_format)
                worksheet.write(row, 1, res.get("sale_order_amount", ""), number_totals_format)
                worksheet.write(row, 2, res.get("returns_order_amount", ""), number_totals_format)
                worksheet.write(row, 3, res.get("net_sales_amount", ""), number_totals_format)
                worksheet.write(row, 4, res.get("sale_order_tax", ""), number_totals_format)
                worksheet.write(row, 5, res.get("returns_order_tax", ""), number_totals_format)
                worksheet.write(row, 6, res.get("net_tax_amount", ""), number_totals_format)
                worksheet.write(row, 7, res.get("cash_payment", ""), number_totals_format)
                worksheet.write(row, 8, res.get("master_cart_payment", ""), number_totals_format)
                worksheet.write(row, 9, res.get("total_payment", ""), number_totals_format)
                row += 1
                
            if res["config_name"] != "sub_totals" and res["config_name"] != "hide" and res["config_name"] != "Totals":
                worksheet.write(row, 0, res.get("config_name", ""))
                worksheet.write(row, 1, res.get("sale_order_amount", ""), number_format)
                worksheet.write(row, 2, res.get("returns_order_amount", ""), number_format)
                worksheet.write(row, 3, res.get("net_sales_amount", ""), number_format)
                worksheet.write(row, 4, res.get("sale_order_tax", ""), number_format)
                worksheet.write(row, 5, res.get("returns_order_tax", ""), number_format)
                worksheet.write(row, 6, res.get("net_tax_amount", ""), number_format)
                worksheet.write(row, 7, res.get("cash_payment", ""), number_format)
                worksheet.write(row, 8, res.get("master_cart_payment", ""), number_format)
                worksheet.write(row, 9, res.get("total_payment", ""), number_format)
                cashiers = ", ".join(res.get("cashier_ids", []))
                worksheet.write(row, 10, cashiers)
                row += 1

            if res["config_name"] == "sub_totals":
                worksheet.write(row, 0, res.get("branch_name", ""),number_sub_total_format)
                worksheet.write(row, 1, res.get("sale_order_amount", ""), number_sub_total_format)
                worksheet.write(row, 2, res.get("returns_order_amount", ""), number_sub_total_format)
                worksheet.write(row, 3, res.get("net_sales_amount", ""), number_sub_total_format)
                worksheet.write(row, 4, res.get("sale_order_tax", ""), number_sub_total_format)
                worksheet.write(row, 5, res.get("returns_order_tax", ""), number_sub_total_format)
                worksheet.write(row, 6, res.get("net_tax_amount", ""), number_sub_total_format)
                worksheet.write(row, 7, res.get("cash_payment", ""), number_sub_total_format)
                worksheet.write(row, 8, res.get("master_cart_payment", ""), number_sub_total_format)
                worksheet.write(row, 9, res.get("total_payment", ""), number_sub_total_format)
                cashiers = ", ".join(res.get("cashier_ids", []))
                worksheet.write(row, 10, cashiers,number_sub_total_format)
                row += 1

            # if  res["config_name"] != "Totals":

        # Close the workbook
        workbook.close()
        output.seek(0)
        return output

