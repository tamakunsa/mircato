from odoo import fields, models, api, _


class EmployeeSponsor(models.Model):
    _name = 'employee.sponsor'

    name = fields.Char()
