from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import Common


@tagged('post_install', '-at_install', 'access_rights')
class TestMultiCompany(Common):

    def setUp(self):
        super(TestMultiCompany, self).setUp()
        self.new_company = self.env['res.company'].create({
            'name': 'New Company'
            })
        self.new_company_user = self.env['res.users'].with_context(no_reset_password=True, tracking_disable=True).create({
            'name': 'Attendance Machine Manager',
            'login': 'att_device_manager@example.viindoo.com',
            'groups_id': [(6, 0, [self.env.ref('to_attendance_device.group_attendance_devices_manager').id])],
            'company_id': self.new_company.id,
            'company_ids': [(6, 0, [self.new_company.id])]
            })

        self.new_company_emp = self.env['hr.employee'].create({
            'name': 'emp cpn2',
            'company_id': self.new_company.id
            })

        self.new_company_device = self.env['attendance.device'].create({
            'company_id': self.new_company.id,
            'location_id': self.attendance_device_location.id
        })

    def test_01_multi_company(self):
        attendance_id = self.env['user.attendance'].create({
            'device_id': self.attendance_device.id,
            'user_id': self.attendance_device_user.id,
            'timestamp': fields.datetime.now(),
            'status': 100,
            'attendance_state_id': self.attendance_state.id
            })
        # same company, user should be able to read
        self.attendance_device.read()
        self.attendance_device_user.read()
        attendance_id.read()

        # Switch to another user of another company's.
        # AccessError should raise when reading the same records
        with self.assertRaises(AccessError):
            self.attendance_device.with_user(self.new_company_user).read()
        with self.assertRaises(AccessError):
            self.attendance_device_user.with_user(self.new_company_user).read()
        with self.assertRaises(AccessError):
            attendance_id.with_user(self.new_company_user).read()

    def test_open_wz_upload_emp_to_machine_multi_company(self):
        self.env.company = self.new_company
        try:
            self.env['employee.upload.wizard'].create({
                'employee_ids': [(6, 0, self.new_company_emp.ids)]
            })
        except Exception:
            self.fail("Fail when open wizard upload employee to machine")
