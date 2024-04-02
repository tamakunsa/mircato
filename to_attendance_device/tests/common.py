from odoo import fields
from odoo.tests import TransactionCase

class Common(TransactionCase):

    def setUp(self):
        super(Common, self).setUp()
        self.attendance_activity = self.env['attendance.activity'].create({
            'name': 'test_attendance_activity'
            })
        self.attendance_device_location = self.env['attendance.device.location'].create({
            'name': 'test_attendance_device_location',
            'hr_work_location_id': self.env.ref('hr.work_location_1').id,
            })
        self.hr_employee = self.env.ref('hr.employee_fme')
        self.attendance_device = self.env['attendance.device'].create({
            'name': 'test_attendance_device',
            'ip': 'ip_test',
            'port': 4355,
            'timeout': 5,
            'password':'0',
            'location_id': self.attendance_device_location.id
            })
        self.attendance_device_user = self.env['attendance.device.user'].create({
            'name': 'test_attendance_device_user',
            'device_id': self.attendance_device.id,
            'user_id': 1,
            'employee_id': self.hr_employee.id,
            })
        self.attendance_state = self.env['attendance.state'].create({
            'name': 'test_attendance_state',
            'activity_id': self.attendance_activity.id,
            'code': 100,
            'type': 'checkin'
            })
        self.finger_template = self.env['finger.template'].create({
            'uid': 1,
            'fid': 1,
            'device_user_id': self.attendance_device_user.id,
            'device_id': self.attendance_device.id,
            })
        self.hr_attendance = self.env['hr.attendance']
        self.user_attendance = self.env['user.attendance'].create({
            'device_id': self.attendance_device.id,
            'user_id': self.attendance_device_user.id,
            'timestamp': fields.datetime.now(),
            'status': 100,
            'attendance_state_id': self.attendance_state.id
            })
