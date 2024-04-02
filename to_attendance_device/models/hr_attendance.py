from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    checkin_device_id = fields.Many2one('attendance.device', string='Checkin Device', readonly=True, index=True,
                                        help="The device with which user took check in action")
    checkout_device_id = fields.Many2one('attendance.device', string='Checkout Device', readonly=True, index=True,
                                         help="The device with which user took check out action")
    activity_id = fields.Many2one('attendance.activity', string='Attendance Activity',
                                  help="This field is to group attendance into multiple Activity"
                                       " (e.g. Overtime, Normal Working, etc)")
