# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    phone = fields.Char(related="partner_id.phone",store=True)




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
            print('partner_id')
            print(partner_id)
            print(type(partner_id))
            domain.append(('id','!=',int(partner_id)))


        return self.env['res.partner'].search_count(domain,limit=1)




class PosSession(models.Model):
    _inherit = 'pos.session'


    def _loader_params_hr_employee(self):
        res =  super(PosSession,self)._loader_params_hr_employee()
        # res['fields'].append('allow_refund')
        print("---------res-------")
        print(res)
        res['search_params']['fields'].append('allow_refund')
        print(res['search_params']['fields'])

        return res

