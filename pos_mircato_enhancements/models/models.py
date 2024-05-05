# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    phone = fields.Char(related="partner_id.phone",store=True)


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

    # def get_closing_control_data(self):
    #     res = super().get_closing_control_data()
    #     orders = self._get_closed_orders()
    #     #this function is responsable for getting cash control data
    #     cash_payment_method_ids = self.payment_method_ids.filtered(lambda pm: pm.type == 'cash')
    #     default_cash_payment_method_id = cash_payment_method_ids[0] if cash_payment_method_ids else None
    #     other_payment_method_ids = self.payment_method_ids - default_cash_payment_method_id if default_cash_payment_method_id else self.payment_method_ids
    #     print("-----res before----")
    #     print(res)
    #     res['other_payment_methods'] =  [{
    #             'name': pm.name,
    #             # 'amount':0,
    #             'amount': sum(orders.payment_ids.filtered(lambda p: p.payment_method_id == pm).mapped('amount')),
    #             'number': len(orders.payment_ids.filtered(lambda p: p.payment_method_id == pm)),
    #             'id': pm.id,
    #             'type': pm.type,
    #         } for pm in other_payment_method_ids],
    #     print("-----res after----")

    #     print(res)

    #     return res

    def _loader_params_hr_employee(self):
        res =  super(PosSession,self)._loader_params_hr_employee()
        # res['fields'].append('allow_refund')
        res['search_params']['fields'].append('allow_refund')

        return res

