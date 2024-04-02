from odoo.addons.to_attendance_device.tests.common import Common
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestFingerTemplate(Common):

    # Form test
    # Case 10: Tại tree view Finger Template, thông tin Employee của mỗi bản ghi được tự cập nhật mỗi khi có sự thay đổi liên quan đến Device User của bản ghi đó
    def test_01_compute_employee_id(self):
        # gán trường device_user_id của finger_template này một giá trị mới.
        # thông tin employee_id của finger_template tự động cập nhật
        self.finger_template.device_user_id = self.attendance_device_user.id
        self.assertEqual(self.finger_template.employee_id, self.attendance_device_user.employee_id)
