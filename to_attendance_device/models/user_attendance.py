import logging

from odoo import models, fields, api, _
from odoo import tools

_logger = logging.getLogger(__name__)


class UserAttendance(models.Model):
    _name = 'user.attendance'
    _description = 'User Attendance'
    _order = 'timestamp DESC, user_id, status, attendance_state_id, device_id'

    device_id = fields.Many2one('attendance.device', string='Attendance Machine', required=True, ondelete='restrict',
                                index=True)
    user_id = fields.Many2one('attendance.device.user', string='Machine User', required=True, ondelete='cascade',
                              index=True)
    timestamp = fields.Datetime(
        string='Timestamp', required=True, index=True,
        help="The date and time at which the employee took a check in/out action at the attendance machine")
    status = fields.Integer(string='Machine Attendance State', required=True,
                            help="The state which is the unique number stored in the machine to"
                                 " indicate type of attendance (e.g. 0: Checkin, 1: Checkout, etc)")
    attendance_state_id = fields.Many2one('attendance.state', string='Software Attendance State',
                                          help="This technical field is to map the attendance"
                                               " status stored in the machine and the attendance status in Odoo",
                                          required=True, index=True)
    activity_id = fields.Many2one('attendance.activity', related='attendance_state_id.activity_id', store=True,
                                  index=True)
    hr_attendance_id = fields.Many2one(
        'hr.attendance', string='HR Attendance', ondelete='set null',
        help="The technical field to link Machine Attendance Data with Odoo Attendance Data",
        index=True)

    type = fields.Selection(string='Activity Type', related='attendance_state_id.type', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', related='user_id.employee_id', store=True,
                                  index=True)

    _sql_constraints = [
        ('unique_user_id_device_id_timestamp',
         'UNIQUE(user_id, device_id, timestamp)',
         "The Timestamp and User must be unique per machine"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super(UserAttendance, self).create(vals_list)
        return attendances

    @api.constrains('status', 'attendance_state_id')
    def constrains_status_attendance_state_id(self):
        for r in self:
            if r.status != r.attendance_state_id.code:
                raise (
                    _("Attendance Status conflict! The status number from machine must match the attendance status defined in Odoo."))

    def _prepare_last_hr_attendance_domain(self):
        self.ensure_one()
        return [
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '<=', self.timestamp),
            '|', ('activity_id', '=', False), ('activity_id', '=', self.activity_id.id),
        ]

    def _get_last_hr_attendance(self, user_attendance, hr_attendances):
        last_hr_attendance = hr_attendances.filtered(
            lambda hr_att: hr_att.employee_id == user_attendance.employee_id
                           and hr_att.check_in <= user_attendance.timestamp
                           and (hr_att.activity_id == user_attendance.activity_id
                                or not hr_att.activity_id)).sorted('check_in')
        return last_hr_attendance and last_hr_attendance[-1:] or False

    def _prepare_hr_attendance_vals(self):
        return {
            'employee_id': self.employee_id.id,
            'check_in': self.timestamp,
            'checkin_device_id': self.device_id.id,
            'activity_id': self.activity_id.id,
        }

    def _create_hr_attendance(self):
        vals_list = []
        for r in self:
            vals_list.append(r._prepare_hr_attendance_vals())
        return self.env['hr.attendance'].create(vals_list)

    def _sync_attendance(self):
        """
        This method synchronizes `user.attendance` data into `hr.attendance` data
        """
        error_msg = {}
        hr_attendances = self.env['hr.attendance'].search([])
        for attendance_activity in self.env['attendance.activity'].search([]):
            for employee in self.employee_id:
                unsync_user_attendances = self.filtered(
                    lambda uatt: uatt.employee_id == employee \
                                 and uatt.activity_id == attendance_activity
                ).sorted('timestamp')
                for uatt in unsync_user_attendances:
                    # Do flush manually to avoid magical user error:
                    # https://github.com/Viindoo/tvtmaaddons/pull/4053
                    with self.env.cr.savepoint(flush=False), tools.mute_logger('odoo.sql_db'):
                        last_hr_attendance = self._get_last_hr_attendance(uatt, hr_attendances)
                        try:
                            uatt_update = False
                            if uatt.type == 'checkin':
                                if not last_hr_attendance or (
                                        last_hr_attendance.check_out and uatt.timestamp > last_hr_attendance.check_out):
                                    last_hr_attendance = uatt._create_hr_attendance()
                                    uatt_update = True
                            else:
                                if last_hr_attendance and not last_hr_attendance.check_out and uatt.timestamp >= last_hr_attendance.check_in:
                                    last_hr_attendance.with_context(not_manual_check_out_modification=True).write({
                                        'check_out': uatt.timestamp,
                                        'checkout_device_id': uatt.device_id.id
                                    })
                                    uatt_update = True
                            if uatt_update:
                                if last_hr_attendance not in hr_attendances:
                                    hr_attendances += last_hr_attendance
                                uatt.write({
                                    'hr_attendance_id': last_hr_attendance.id
                                })
                            self.flush()
                        except Exception as e:
                            hr_attendances = self.env['hr.attendance'].search([])
                            error_msg.setdefault(uatt.device_id, [])
                            msg = str(e)
                            if msg not in error_msg[uatt.device_id]:
                                error_msg[uatt.device_id].append(str(e))
        if bool(error_msg):
            for device, msg_list in error_msg.items():
                device.message_post(body="<ol>%s</ol>" % "".join(["<li>%s</li>" % msg for msg in msg_list]))

    def action_sync_attendance(self):
        self._sync_attendance()

    @api.model
    def _prepare_unsynch_data_domain(self):
        return [
            ('hr_attendance_id', '=', False),
            ('employee_id', '!=', False)
        ]

    @api.model
    def _cron_synch_hr_attendance(self):
        unsync_data = self.env['user.attendance'].search(self._prepare_unsynch_data_domain())
        unsync_data._sync_attendance()
