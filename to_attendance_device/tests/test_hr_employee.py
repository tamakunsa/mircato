from odoo.addons.to_attendance_device.tests.common import Common
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestHrEmployee(Common):

    # Form test
    # Case 11: Số lượng mẫu vân tay của mỗi nhân viên sẽ được tính lại mỗi khi mở bản ghi của nhân viên đóó
    def test_01_compute_total_finger_template_records(self):
        # Thêm mới 1 bản ghi vào db finger.template
        self.env['finger.template'].create({
            'fid': 111,
            'valid': 111,
            'employee_id': self.hr_employee.id,
            })
        self.hr_employee._compute_total_finger_template_records()
        self.assertEqual(self.hr_employee.total_finger_template_records, 2)
