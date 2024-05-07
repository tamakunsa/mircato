# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND
from collections import defaultdict
from datetime import datetime


class PosOrder(models.Model):
    _inherit = 'pos.order'

    phone = fields.Char(related="partner_id.phone",store=True)

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """Search for 'paid' orders that satisfy the given domain, limit and offset."""
        default_domain = [('state', '!=', 'draft'), ('state', '!=', 'cancel')]
        # if domain == []:
        #     real_domain = AND([[['config_id', '=', config_id]], default_domain])
        # else:
        print('---------domain-------')
        # print(self)
        print(limit)
        print(offset)
        print(domain)
        print('---------default_domain-------')
        print(default_domain)
        real_domain = AND([domain, default_domain])
        # orders = self.search(real_domain, limit=limit, offset=offset)
        orders = self.search(real_domain, limit=limit)
        print("self.search([])")
        print(self.env['pos.order'].search([]))
        print("-------real_domain----------")
        print(real_domain)
        print(orders)
        # We clean here the orders that does not have the same currency.
        # As we cannot use currency_id in the domain (because it is not a stored field),
        # we must do it after the search.
        # pos_config = self.env['pos.config'].browse(config_id)
        # orders = orders.filtered(lambda order: order.currency_id == pos_config.currency_id)
        # orderlines = self.env['pos.order.line'].search(['|', ('refunded_orderline_id.order_id', 'in', orders.ids), ('order_id', 'in', orders.ids)])
        orderlines = self.env['pos.order.line'].search(['|', ('refunded_orderline_id.order_id', 'in', orders.ids), ('order_id', 'in', orders.ids)])

        # We will return to the frontend the ids and the date of their last modification
        # so that it can compare to the last time it fetched the orders and can ask to fetch
        # orders that are not up-to-date.
        # The date of their last modification is either the last time one of its orderline has changed,
        # or the last time a refunded orderline related to it has changed.
        orders_info = defaultdict(lambda: datetime.min)
        for orderline in orderlines:
            key_order = orderline.order_id.id if orderline.order_id in orders \
                            else orderline.refunded_orderline_id.order_id.id
            if orders_info[key_order] < orderline.write_date:
                orders_info[key_order] = orderline.write_date
        totalCount = self.search_count(real_domain)
        return {'ordersInfo': list(orders_info.items())[::-1], 'totalCount': totalCount}



class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"
    allow_refund  = fields.Boolean()


class PosEmployee(models.Model):
    _inherit = 'hr.employee'
    allow_refund  = fields.Boolean()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('mobile')
    def _check_mobile_unique(self):
        """
        this function give a non-humanly error in pos
        """
        for partner in self:
            if self.env['res.partner'].search_count([('mobile','=',partner.mobile)]) >1:
                raise ValidationError("Mobile must be unique")

    
    @api.model
    def search_mobile_existance(self,mobile,partner_id=None):
        domain = [('mobile','=',mobile)]
        if partner_id:
            domain.append(('id','!=',int(partner_id)))


        return self.env['res.partner'].search_count(domain,limit=1)




class PosSession(models.Model):
    _inherit = 'pos.session'


    def _loader_params_hr_employee(self):
        res =  super(PosSession,self)._loader_params_hr_employee()
        res['search_params']['fields'].append('allow_refund')

        return res

