from odoo import fields, models, api, _
from datetime import datetime, date
import datetime as dt


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_pos_sale_details(self, session_ids=False,date_from=False,date_to=False):
        pos_session = self.env['pos.session'].search([('id', 'in', session_ids)])

        orders_domain = [('session_id', 'in', pos_session.ids),('amount_total', '>', 0.0)]
        # Get total sales data
        if date_from and date_to:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            orders_domain.append(("date_order",'>=',date_from_obj))
            orders_domain.append(("date_order",'<=',date_to_obj))
                            
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

        # Get total Returns data
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

        res = {
            'company_id': self.env.company,
            'date_start': min(pos_session.mapped('start_at')),
            'date_stop': fields.Datetime.now(),
            'branch': pos_session.config_id.name,
            'cahier': ", ".join(pos_session.mapped('user_id').mapped("name")) if len(pos_session.mapped('user_id')) > 1 else pos_session.user_id.name,
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

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        # initialize data keys with their value if provided, else None
        data.update({
            'session_ids': data.get('session_ids') or docids,
        })
        if data.get("config_ids") and not data.get("session_ids"):
            data.update({
                'session_ids':self.env['pos.session'].search([('config_id', 'in', data.get("config_ids"))]).ids
            })

        data.update(self.get_pos_sale_details(data['session_ids'],data.get('date_start'),data.get('date_stop')))
        return data
