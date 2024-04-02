from odoo.addons.to_attendance_device.tests.common import Common
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAttendanceActivity(Common):

    # Form test
    # Case 2: Tự động cập nhật số lượng Status Count trong Attendance Activity.
    def test_01_compute_status_count(self):
        status_count = self.attendance_activity.status_count
        # Thêm hoặc Attendance State trong form view của Attendance Activity
        self.attendance_state.create({
            'name': 'test',
            'activity_id': self.attendance_activity.id,
            'code': 101,
            'type': 'checkout',
        })
        self.assertEqual(self.attendance_activity.status_count, 2)
