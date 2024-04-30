# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from . import pos_order
import xlsxwriter
from io import BytesIO
from datetime import datetime, date
import datetime as dt
from odoo.exceptions import ValidationError



class PosDailyReport(models.TransientModel):
    _inherit = 'pos.daily.sales.reports.wizard'
    # 99
    date_start = fields.Date()
    date_stop = fields.Date()
    branch_id = fields.Many2one('pos.config')

    pos_session_domain = fields.Char(compute='_compute_pos_session_domain', store=True)
    pos_session_id = fields.Many2many('pos.session')

    @api.depends('branch_id')
    def _compute_pos_session_domain(self):
        if self.branch_id:
            self.pos_session_domain = "[('config_id','in',%s)]" % self.branch_id.ids
        else:
            self.pos_session_domain = "[]"

    def generate_report(self):
        if not self.pos_session_id and not self.branch_id:
            raise ValidationError("Please Select A session or a branch")
        elif self.branch_id and not self.pos_session_id:
            sessions_exist = self.env['pos.session'].search_count([('config_id','in',self.branch_id.ids)])
            if sessions_exist == 0:
                raise ValidationError("There are No sessions for the provided branch")

        data = {
            'date_start': self.date_start, 
            'date_stop': self.date_stop,
            'config_ids': self.pos_session_id.config_id.ids or self.branch_id.ids, 
            'session_ids': self.pos_session_id.ids
        }
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)

    def print_excel_report(self):
        records = self.pos_session_id

        if not self.pos_session_id and not self.branch_id:
            raise ValidationError("Please Select A session or a branch")
        elif self.branch_id and not self.pos_session_id:
            records = self.env['pos.session'].search([('config_id','in',self.branch_id.ids)])
            if len(records) == 0:
                raise ValidationError("There are No sessions for the provided branch")

        url = {
            'type': 'ir.actions.act_url',
            'url': '/pos/session/excel_report?list_ids=%(list_ids)s' % {
                'list_ids': ','.join(str(x) for x in records.ids)},
            'target': 'new',
        }
        if self.date_start and self.date_stop:
            url.update({
                'url': '/pos/session/excel_report?list_ids=%(list_ids)s&date_start=%(date_from)s&date_stop=%(date_to)s' % {
                    'list_ids': ','.join(str(x) for x in records.ids),
                    'date_from':self.date_start,
                    'date_to':self.date_stop,
                }
            })

        return url

    def get_pos_sale_details(self, session_ids=False,date_from=False,date_to=False):
        pos_session = self.env['pos.session'].search([('id', 'in', session_ids)])
        orders_domain = [('session_id', 'in', pos_session.ids),('amount_total', '>', 0.0)]
        # Get total sales data
        if date_from and date_to:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders_domain.append(("date_order",'>=',date_from_obj))
            orders_domain.append(("date_order",'<=',date_to_obj))

        # Get total sales data
        session_pos_orders = self.env['pos.order'].search(orders_domain)

        total_sales = 0.0
        if session_pos_orders:
            for record in session_pos_orders.mapped('lines'):
                if record.price_unit > 0.0:
                    total_sales += record.price_subtotal_incl

        total_discount = 0.0
        for line in session_pos_orders.mapped('lines'):
            if 'Discount' in line.full_product_name or 'discount' in line.full_product_name:
                total_discount += round(abs(line.price_subtotal_incl), 3)
            if line.discount:
                total_discount += (line.qty * line.price_unit) * line.discount / 100

        count_related_invoice = len(session_pos_orders)
        net_sales = total_sales - total_discount

        return_orders_domain = [('amount_total', '<', 0.0), ('session_id', 'in', pos_session.ids)]
        if date_from and date_to:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            return_orders_domain.append(("date_order",'>=',date_from_obj))
            return_orders_domain.append(("date_order",'<=',date_to_obj))


        returns_pos_orders = self.env['pos.order'].search(return_orders_domain)

        total_return = sum(returns_pos_orders.mapped('amount_total')) if returns_pos_orders else 0.0

        total_return_discount = 0.0
        for line in returns_pos_orders.mapped('lines'):
            if 'Discount' in line.full_product_name or 'discount' in line.full_product_name:
                total_return_discount += round(abs(line.price_subtotal_incl), 3)
            if line.discount:
                total_return_discount += (line.qty * line.price_unit) * line.discount / 100

        net_return = abs(total_return) - total_return_discount

        # pos_payment_methods
        payment_methods, return_payment_methods = [], []
        payment_sales_values, payment_discount_values, payment_count = {}, {}, {}
        payment_return_values, payment_returns_count = {}, {}
        t_total_sales_value, t_total_discount_value, t_net_values = {}, {}, {}
        sales_value, return_value = 0.0, 0.0

        for pay in session_pos_orders.mapped('payment_ids'):
            discount = 0.000
            if pay.payment_method_id.name not in payment_methods:
                payment_methods.append(str(pay.payment_method_id.name))
                payment_count[pay.payment_method_id.name] = 1
                for line in session_pos_orders.mapped('lines'):
                    for rec in line.order_id.payment_ids:
                        if rec.payment_method_id.name == pay.payment_method_id.name:
                            if 'Discount' in line.full_product_name or 'discount' in line.full_product_name:
                                discount += round(abs(line.price_subtotal_incl), 3)
                            if line.discount:
                                discount += (line.qty * line.price_unit) * line.discount / 100

                            t_total_discount_value[pay.payment_method_id.name] = discount
                sales_value = pay.amount
                payment_sales_values[pay.payment_method_id.name] = pay.amount
                t_total_sales_value[pay.payment_method_id.name] = pay.amount + discount
                payment_discount_values[pay.payment_method_id.name] = discount
                t_net_values[pay.payment_method_id.name] = pay.amount
            else:
                if pay.payment_method_id.name in payment_sales_values:
                    if 'Cash' in pay.payment_method_id.name: # == 'Cash كاش'
                        sales_value += pay.amount
                    else:
                        t_total_discount_value[pay.payment_method_id.name] = discount

                    payment_sales_values[pay.payment_method_id.name] += pay.amount
                    payment_count[pay.payment_method_id.name] += 1
                    t_total_sales_value[pay.payment_method_id.name] += pay.amount
                    t_net_values[pay.payment_method_id.name] += pay.amount

        for pay in returns_pos_orders.mapped('payment_ids'):
            if pay.payment_method_id.name not in return_payment_methods:
                return_payment_methods.append(pay.payment_method_id.name)
                payment_return_values[pay.payment_method_id.name] = round(abs(pay.amount), 3) or 0.000
                payment_returns_count[pay.payment_method_id.name] = 1
                if 'Cash' in pay.payment_method_id.name: # == 'Cash كاش'
                    return_value = abs(pay.amount)
                else:
                    t_total_sales_value[pay.payment_method_id.name] = round(pay.amount, 3)
                    t_total_discount_value[pay.payment_method_id.name] = 0.000
                    t_net_values[pay.payment_method_id.name] = round(pay.amount, 3)

            else:
                if pay.payment_method_id.name in payment_return_values:
                    payment_return_values[pay.payment_method_id.name] += round(abs(pay.amount), 3) or 0.000
                    payment_returns_count[pay.payment_method_id.name] += 1
                    if 'Cash' in pay.payment_method_id.name: # == 'Cash كاش'
                        return_value += abs(pay.amount)
                    else:
                        t_total_sales_value[pay.payment_method_id.name] += round(pay.amount, 3)
                        t_total_discount_value[pay.payment_method_id.name] = 0.000
                        t_net_values[pay.payment_method_id.name] += round(pay.amount, 3)
        
        for r_key, r_value in payment_return_values.items():
            for key, value in payment_sales_values.items():
                if r_key == key:
                    value -= r_value
                    payment_sales_values[key] = value
            for key, value in t_total_sales_value.items():
                if r_key == key:
                    if value > 0.0:
                        value -= r_value
                        t_total_sales_value[key] = value
            for key, value in t_net_values.items():
                if r_key == key:
                    if value > 0.0:
                        value -= r_value
                        t_net_values[key] = value

        t_total_sales = total_sales - abs(total_return)
        total_payment_methods = []

        for method in payment_methods:
            if method not in total_payment_methods:
                total_payment_methods.append(method)
        for r_method in return_payment_methods:
            if r_method not in total_payment_methods:
                total_payment_methods.append(r_method)


        res =  {
            'company_id': self.env.company,
            'date_start': min(pos_session.mapped('start_at')),
            'date_stop': fields.Datetime.now(),
            'branch': pos_session.config_id.name,
            # 'cahier': pos_session.user_id.name,
            'cashier': ', '.join(set(session_pos_orders.mapped("employee_id").mapped('name'))),
            'total_sales': total_sales,
            'total_discount': total_discount,
            'net_sales': net_sales,
            'invoice_count': count_related_invoice,
            'cancel_orders': session_pos_orders.search_count([('state', '=', 'cancel')]),
            'total_return': abs(total_return),
            'total_return_discount': abs(total_return_discount),
            'net_return': abs(net_return),
            'returns_count': len(returns_pos_orders),
            'total_net': (net_sales - abs(total_return)) if total_return_discount > 0.0 else net_sales - abs(
                net_return),
            'payment_methods': payment_methods,
            'return_payment_methods': return_payment_methods,
            'total_payment_methods': total_payment_methods,
            'payment_sales_values': payment_sales_values,
            'payment_discount_values': payment_discount_values,
            'payment_count': payment_count,
            'payment_return_values': payment_return_values,
            'payment_returns_count': payment_returns_count,
            't_total_sales_value': t_total_sales_value,
            't_total_discount_value': t_total_discount_value,
            't_net_values': t_net_values,
            'petty_cash': min(pos_session.mapped("cash_register_balance_start")),
            't_total_sales': t_total_sales,
            't_total_discount': total_discount,
            't_total_nets': t_total_sales - total_discount,
            'drawer_cash': sales_value - return_value
        }
        if date_from and date_to:
            res.update({
                'date_start': date_from,
                'date_stop': date_to,
            })
        return res

    def generate_excel_report(self, records,date_from=False,date_to=False):
        data = self.get_pos_sale_details(records,date_from,date_to)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Define cell formats
        bold = workbook.add_format({'bold': True})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd HH:MM'})
        currency_format = workbook.add_format({'num_format': '#,##0.00'})

        # Write headers
        worksheet.write('B2', 'Date', bold)
        worksheet.write('C2', 'X OUT STATUS REPORT', bold)
        worksheet.write('B4', 'Branch', bold)
        worksheet.write('C4', data.get('branch', ''), bold)
        worksheet.write('B5', 'Cashier', bold)
        worksheet.write('C5', data.get('cashier', ''), bold)
        worksheet.write('B6', 'From', bold)
        worksheet.write('C6', data.get('from_date'), date_format)
        worksheet.write('B7', 'To', bold)
        worksheet.write('C7', data.get('to_date'), date_format)

        # Write sales section
        sales_start_row = 9
        worksheet.write('D' + str(sales_start_row), 'SALES', bold)
        sales_start_row+=1

        worksheet.write('B' + str(sales_start_row), 'Total Sales', bold)
        worksheet.write('C' + str(sales_start_row), data.get('total_sales', 0))
        sales_start_row+=1
        worksheet.write('B' + str(sales_start_row), 'Total Discount', bold)
        worksheet.write('C' + str(sales_start_row), data.get('total_discount', 0))
        sales_start_row+=1
        worksheet.write('B' + str(sales_start_row), 'Net Sales', bold)
        worksheet.write('C' + str(sales_start_row), data.get('total_discount', 0))
        sales_start_row+=1
        worksheet.write('B' + str(sales_start_row), 'Invoice Counts', bold)
        worksheet.write('C' + str(sales_start_row), data.get('invoice_count', 0))
        sales_start_row+=1
        worksheet.write('B' + str(sales_start_row), 'Cancel Order', bold)
        worksheet.write('C' + str(sales_start_row), data.get('cancel_orders', 0))

        # Write returns section
        returns_start_row= sales_start_row+4
        worksheet.write('D' + str(returns_start_row), 'Returns', bold)
        returns_start_row+=1

        worksheet.write('B' + str(returns_start_row), 'Total Returns', bold)
        worksheet.write('C' + str(returns_start_row), data.get('total_returns', 0))
        returns_start_row+=1
        worksheet.write('B' + str(returns_start_row), 'Total Discount', bold)
        worksheet.write('C' + str(returns_start_row), data.get('total_return_discount', 0))
        returns_start_row+=1
        worksheet.write('B' + str(returns_start_row), 'Net Returns', bold)
        worksheet.write('C' + str(returns_start_row), data.get('net_return', 0))
        returns_start_row+=1
        worksheet.write('B' + str(returns_start_row), 'Return Counts', bold)
        worksheet.write('C' + str(returns_start_row), data.get('returns_count', 0))


        # Write summary section
        summary_start_row = returns_start_row+4
        worksheet.write('D' + str(summary_start_row), 'Summary', bold)
        summary_start_row+=1

        worksheet.write('B' + str(summary_start_row), 'Total Net', bold)
        worksheet.write('C' + str(summary_start_row), data.get('total_net', 0))


        total_sales_payment_start_row =summary_start_row+6
        worksheet.write('E' + str(total_sales_payment_start_row), 'Total Sales Payment', bold)
        worksheet.write('B' + str(total_sales_payment_start_row + 1), 'Payment', bold)
        worksheet.write('C' + str(total_sales_payment_start_row + 1), 'Sales', bold)
        worksheet.write('D' + str(total_sales_payment_start_row + 1), 'Disc', bold)
        worksheet.write('E' + str(total_sales_payment_start_row + 1), 'Count', bold)
        payment_methods = data.get('payment_methods', {})
        payment_sales_values = data.get('payment_sales_values', {})
        payment_discount_values = data.get('payment_discount_values', {})
        payment_count = data.get('payment_count', {})
        row = total_sales_payment_start_row + 2
        for pm, sales_value in payment_sales_values.items():
            worksheet.write('B' + str(row), pm)
            worksheet.write('C' + str(row), sales_value, currency_format)
            worksheet.write('D' + str(row), payment_discount_values.get(pm, 0), currency_format)
            worksheet.write('E' + str(row), payment_count.get(pm, 0))
            row += 1

        # Write Total Returns Payment section
        total_returns_payment_start_row = row + 2
        worksheet.write('E' + str(total_returns_payment_start_row), 'Total Returns Payment', bold)
        worksheet.write('B' + str(total_returns_payment_start_row + 1), 'Payment', bold)
        worksheet.write('C' + str(total_returns_payment_start_row + 1), 'Returns', bold)
        worksheet.write('D' + str(total_returns_payment_start_row + 1), 'Count', bold)
        return_payment_methods = data.get('return_payment_methods', {})
        payment_return_values = data.get('payment_return_values', {})
        payment_returns_count = data.get('payment_returns_count', {})
        row = total_returns_payment_start_row + 2
        for rpm, return_value in payment_return_values.items():
            worksheet.write('B' + str(row), rpm)
            worksheet.write('C' + str(row), return_value, currency_format)
            worksheet.write('D' + str(row), payment_returns_count.get(rpm, 0))
            row += 1

        # Write Transaction Summary section
        transaction_summary_start_row = row + 2
        worksheet.write('E' + str(transaction_summary_start_row), 'Transaction Summary', bold)
        worksheet.write('B' + str(transaction_summary_start_row + 1), 'Payment', bold)
        worksheet.write('C' + str(transaction_summary_start_row + 1), 'Sales', bold)
        worksheet.write('D' + str(transaction_summary_start_row + 1), 'Disc', bold)
        worksheet.write('E' + str(transaction_summary_start_row + 1), 'Net', bold)
        total_payment_methods = data.get('total_payment_methods', {})
        t_total_sales_value = data.get('t_total_sales_value', {})
        t_total_discount_value = data.get('t_total_discount_value', {})
        t_net_values = data.get('t_net_values', {})
        row = transaction_summary_start_row + 2
        total_calc_sales = 0
        total_calc_disc = 0
        total_calc_net = 0

        for tpm, total_sale_value in t_total_sales_value.items():
            total_calc_sales+=total_sale_value
            total_calc_disc+=t_total_discount_value.get(tpm, 0)
            total_calc_net+=t_net_values.get(tpm, 0)

            worksheet.write('B' + str(row), tpm)
            worksheet.write('C' + str(row), total_sale_value, currency_format)
            worksheet.write('D' + str(row), t_total_discount_value.get(tpm, 0), currency_format)
            worksheet.write('E' + str(row), t_net_values.get(tpm, 0), currency_format)
            row += 1

        # Write Total row in Transaction Summary section
        worksheet.write('B' + str(row), 'TOTAL:', bold)
        worksheet.write_formula('C' + str(row), '=SUM(C{}:C{})'.format(transaction_summary_start_row + 2, row - 1), currency_format)
        worksheet.write_formula('D' + str(row), '=SUM(D{}:D{})'.format(transaction_summary_start_row + 2, row - 1), currency_format)
        worksheet.write_formula('E' + str(row), '=SUM(E{}:E{})'.format(transaction_summary_start_row + 2, row - 1), currency_format)


        worksheet.write('C' + str(row), total_calc_sales, currency_format)
        worksheet.write('D' + str(row), total_calc_disc, currency_format)
        worksheet.write('E' + str(row), total_calc_net, currency_format)


        workbook.close()
        output.seek(0)
        return output
