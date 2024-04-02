from odoo import fields
from odoo.addons.to_attendance_device.tests.common import Common
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAttendancedDeviceUser(Common):

    # Form test
    # Case 3: Tại form view của Devices Users, dữ liệu chấm công (Attendance Data) gần nhất được tự động cập nhật.
    def test_01_compute_current_attendance(self):
        attendance_id = self.env['user.attendance'].create({
            'device_id': self.attendance_device.id,
            'user_id': self.attendance_device_user.id,
            'timestamp': fields.datetime.now(),
            'status': 100,
            'attendance_state_id': self.attendance_state.id
            })
        self.assertEqual(self.attendance_device_user.attendance_id, attendance_id)

    # Form test
    # Case 4: Số lượng Finger Templates (tại form view Devices Users) tự cập nhật theo số lượng vân tay mà Device user đã đăng ký
    def test_02_compute_total_finger_template_records(self):
        self.env['finger.template'].create({
            'uid': 2,
            'fid': 2,
            'device_user_id': self.attendance_device_user.id,
            'device_id': self.attendance_device.id,
            })
        self.assertEqual(self.attendance_device_user.total_finger_template_records, 2)

    # Form test
    # Trạng thái active của user tự động thay đổi theo trạng thái active của employee_id và device_id
    # Giao diện không hiển thị trạng thái active của employee_id và device_id
    def test_03_get_active(self):
        # Active của user được gán theo active thiết bị nếu thiết bị đã được lưu trữ
        self.attendance_device_user.employee_id.active = False
        self.attendance_device_user.device_id.active = False
        self.assertFalse(self.attendance_device_user.active)
        # Active của user được gán theo active của employee nếu thiết bị đang hoạt động
        self.attendance_device_user.device_id.active = True
        self.assertFalse(self.attendance_device_user.active)
