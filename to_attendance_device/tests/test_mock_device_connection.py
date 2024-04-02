from unittest.mock import patch

from odoo.exceptions import ValidationError, UserError
from odoo.tests import TransactionCase
from odoo.tests import tagged

from ..pyzk.zk.base import ZK
from ..pyzk.zk.exception import ZKConnectionUnauthorized, ZKNetworkError

def _disconnect(*arg, **kargs):
    pass

def _enable_device(*arg, **kargs):
    return True

def _disable_device(*arg, **kargs):
    return True

def _connect_wrong_password(*arg, **kargs):
    raise ZKConnectionUnauthorized("Unauthenticated")

def _connect_wrong_ip(*arg, **kargs):
    raise ZKNetworkError("can't reach device (ping)")

def _connect_wrong_port(*arg, **kargs):
    raise ZKNetworkError("can't open port")

def _connect_wrong_protocol(*arg, **kargs):
    raise ZKNetworkError("wrong protocol")

def _connect_successfully(*arg, **kargs):
    return True

@tagged('post_install', '-at_install')
@patch.object(ZK, 'disconnect', _disconnect)
@patch.object(ZK, 'enable_device', _enable_device)
@patch.object(ZK, 'disable_device', _disable_device)
class TestAttendanceDeviceConnection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry.enter_test_mode(cls.cr)
        cls.attendance_device_location = cls.env['attendance.device.location'].create({
            'name': 'test_attendance_device_location',
            'hr_work_location_id': cls.env.ref('hr.work_location_1').id,
            })
        cls.attendance_device = cls.env['attendance.device'].create({
            'name': 'test_attendance_device',
            'ip': 'ip_test',
            'port': 1111,
            'timeout': 20,
            'password':'1234',
            'location_id': cls.attendance_device_location.id,
            })

    @classmethod
    def tearDownClass(cls):
        cls.registry.leave_test_mode()
        super().tearDownClass()

    # ============ Test functional: ============
    # 1. Check connection - Sai password hoặc chưa nhập password kết nối máy chấm công
    @patch.object(ZK, 'connect', _connect_wrong_password)
    def test_01_connect_wrong_password(self):
        with self.assertRaises(ValidationError, msg = "test_connect_wrong_password failed"):
            self.attendance_device.action_check_connection()

    # 2. Check connection - Sai ip address kết nối máy chấm công
    # 5. Check connection: Không có kết nối mạng với thiết bị chấm công
    @patch.object(ZK, 'connect', _connect_wrong_ip)
    def test_02_connect_wrong_ip(self):
        with self.assertRaises(ValidationError, msg = "test_connect_wrong_ip failed"):
            self.attendance_device.action_check_connection()

    # 3. Check connection - Sai port kết nối máy chấm công
    @patch.object(ZK, 'connect', _connect_wrong_port)
    def test_03_connect_wrong_port(self):
        with self.assertRaises(ValidationError, msg = "test_connect_wrong_port failed"):
            self.attendance_device.action_check_connection()

    # 4. Check connection: Sai giao thức kết nối UDC/TCP
    @patch.object(ZK, 'connect', _connect_wrong_protocol)
    def test_04_connect_wrong_protocol(self):
        with self.assertRaises(ValidationError, msg = "test_connect_wrong_protocol failed"):
            self.attendance_device.action_check_connection()

    # 6. Check connection: Thông tin kết nối thiết bị chấm công hợp lệ
    @patch.object(ZK, 'connect', _connect_successfully)
    def test_05_connect_successfully(self):
        action = self.attendance_device._prepare_action_confirm()
        action['context'].update({
            'method': 'N/A',
            'title': 'Machine Connection',
            'content': "Connect to the machine %s successfully!" % (self.attendance_device.display_name,)
        })
        self.assertEqual(self.attendance_device.action_check_connection(), action)
