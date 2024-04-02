from odoo import models, fields

from odoo.addons.base.models.res_partner import _tz_get


class AttendanceDeviceLocation(models.Model):
    _name = 'attendance.device.location'
    _description = 'Machine Position'

    name = fields.Char(string='Name', required=True, translate=True,
                       help="The position where the machine is equipped. E.g. Front Door, Back Door, etc")
    hr_work_location_id = fields.Many2one('hr.work.location', string='Work Location', required=True,
                                          help="The work location to where this machine position belongs.")
    tz = fields.Selection(_tz_get, string='Time zone',
                          default=lambda self: self.env.context.get('tz') or self.env.user.tz,
                          help="The device's timezone, used to output proper date and time values "
                               "inside attendance reports. It is important to set a value for this field.")
