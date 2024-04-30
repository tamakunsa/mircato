# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosSession(models.Model):
    _inherit="pos.session"
    bank_payments_ids = fields.One2many("pos.session.bank.payment.line",'pos_session_id')


    def save_bank_payments(self, payment_methods=None):

        line_vals = []
        for bank_payment_method in payment_methods:
            line_vals.append((0,0,{
                'pos_session_id':self.id,
                'payment_method_id':bank_payment_method.get("id"),
                'counted':bank_payment_method.get("amount"),
            }))
        self.bank_payments_ids = line_vals


class PosSessionBankPaymentLine(models.Model):
    _name="pos.session.bank.payment.line"

    currency_id = fields.Many2one('res.currency', related='pos_session_id.config_id.currency_id', string="Currency", readonly=False)
    pos_session_id = fields.Many2one("pos.session")
    payment_method_id = fields.Many2one("pos.payment.method")
    counted = fields.Monetary(string="Counted(Real Ending Balance)",readonly=False)