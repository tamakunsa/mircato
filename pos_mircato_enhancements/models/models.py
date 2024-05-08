# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.osv.expression import AND
from collections import defaultdict
from datetime import datetime


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

    def _loader_params_hr_employee(self):
        res =  super(PosSession,self)._loader_params_hr_employee()
        res['search_params']['fields'].append('allow_refund')

        return res

