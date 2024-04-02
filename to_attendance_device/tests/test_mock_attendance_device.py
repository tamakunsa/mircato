import datetime, pytz
from unittest.mock import patch
from psycopg2 import IntegrityError

from odoo import fields
from odoo.tools import mute_logger
from odoo.tests import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError, UserError

from ..pyzk.zk.base import Attendance, Finger, ZK
from ..pyzk.zk.user import User
from ..pyzk.zk.exception import ZKErrorConnection, ZKConnectionUnauthorized, ZKErrorResponse, ZKNetworkError

class ZkDeviceMock():
    users = [User(uid=1, name='test', user_id=1, privilege=1)]
    attendances = [Attendance(user_id=1, timestamp=fields.Datetime.now(), status=1, punch=0, uid=1)]
    fingers = [Finger(uid=1, fid=1, valid=1, template=b"J\xc7SS21\x00")]

    @classmethod
    def _connect(cls, *arg, **kargs):
        return True

    @classmethod
    def _disconnect(cls, *arg, **kargs):
        pass

    @classmethod
    def _enable_device(cls, *arg, **kargs):
        return True

    @classmethod
    def _disable_device(cls, *arg, **kargs):
        return True

    @classmethod
    def _get_firmware_version(cls, *arg, **kargs):
        return 'mock_firmware'

    @classmethod
    def _get_serialnumber(cls, *arg, **kargs):
        return 'mock_serialnumber'

    @classmethod
    def _get_platform(cls, *arg, **kargs):
        return 'mock_platform'

    @classmethod
    def _get_fp_version(cls, *arg, **kargs):
        return 'mock_fp_version'

    @classmethod
    def _get_device_name(cls, *arg, **kargs):
        return 'mock_device_name'

    @classmethod
    def _get_workcode(cls, *arg, **kargs):
        return 'mock_workcode'

    @classmethod
    def _get_oem_vendor(cls, *arg, **kargs):
        return 'mock_oem_vender'

    @classmethod
    def _get_time(cls, *arg):
        return datetime.datetime(year=1970, month=1, day=1, hour=11, minute=59, second=59)

    @classmethod
    def _get_users(cls, *arg):
        return cls.users

    @classmethod
    def _set_user(cls, uid=None, name='', privilege=0, password='', group_id='', user_id='', card=0, *arg, **kargs):
        cls.users.append(User(uid=uid, name=name, user_id=user_id, privilege=privilege))

    @classmethod
    def _delete_user(cls, uid, user_id, *arg, **kargs):
        for user in cls.users:
            if user.uid == uid and user.user_id == user_id:
                cls.users.remove(user)
                break

    @classmethod
    def _save_user_template(cls, user, fingers, *arg, **kargs):
        user_existing = False
        for u in cls.users:
            if user.uid == u.uid and user.user_id == u.user_id:
                user_existing = True
                break
        if not user_existing:
            cls.users.append(user)
        for finger in fingers:
            finger_existing = False
            for f in cls.fingers:
                if finger.uid == f.uid and finger.fid == f.fid:
                    finger_existing = True
                    break
            if not finger_existing:
                cls.fingers.append(finger)

    @classmethod
    def _get_templates(cls, *arg, **kargs):
        return cls.fingers

    @classmethod
    def _get_attendance(cls, *arg, **kargs):
        return cls.attendances

    @classmethod
    def _clear_attendance(cls, *arg, **kargs):
        cls.attendances.clear()

    @classmethod
    def _get_next_uid(cls, *arg, **kargs):
        max_uid = 0
        for user in cls.users:
            if user.uid > max_uid: max_uid = user.uid
        return max_uid + 1

    @classmethod
    def _restart(cls, *arg, **kargs):
        raise ZKErrorConnection("instance are not connected.")

    @classmethod
    def _clear_data(cls, *arg, **kargs):
        raise ZKErrorConnection("instance are not connected.")

@tagged('post_install', '-at_install')
@patch.object(ZK, 'connect', ZkDeviceMock._connect)
@patch.object(ZK, 'disconnect', ZkDeviceMock._disconnect)
@patch.object(ZK, 'enable_device', ZkDeviceMock._enable_device)
@patch.object(ZK, 'disable_device', ZkDeviceMock._disable_device)
@patch.object(ZK, 'get_users', ZkDeviceMock._get_users)
@patch.object(ZK, 'set_user', ZkDeviceMock._set_user)
@patch.object(ZK, 'delete_user', ZkDeviceMock._delete_user)
@patch.object(ZK, 'save_user_template', ZkDeviceMock._save_user_template)
@patch.object(ZK, 'get_templates', ZkDeviceMock._get_templates)
@patch.object(ZK, 'get_attendance', ZkDeviceMock._get_attendance)
@patch.object(ZK, 'clear_attendance', ZkDeviceMock._clear_attendance)
@patch.object(ZK, 'get_next_uid', ZkDeviceMock._get_next_uid)
class TestAttendanceDeviceMock(TransactionCase):

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

    # =================Test functional==================
    # 7 Lấy thông tin thiết bị - Các thông tin kết nối hợp lệ
    @patch.object(ZK, 'get_firmware_version', ZkDeviceMock._get_firmware_version)
    @patch.object(ZK, 'get_serialnumber', ZkDeviceMock._get_serialnumber)
    @patch.object(ZK, 'get_platform', ZkDeviceMock._get_platform)
    @patch.object(ZK, 'get_fp_version', ZkDeviceMock._get_fp_version)
    @patch.object(ZK, 'get_device_name', ZkDeviceMock._get_device_name)
    @patch.object(ZK, 'get_workcode', ZkDeviceMock._get_workcode)
    @patch.object(ZK, 'get_oem_vendor', ZkDeviceMock._get_oem_vendor)
    def test_01_action_device_information(self):
        cr = self.registry.cursor()
        device = self.attendance_device.with_env(self.attendance_device.env(cr=cr))
        device.action_device_information()
        cr.commit()
        self.assertRecordValues(
            device,
            [
                {
                    'firmware_version': ZkDeviceMock._get_firmware_version(),
                    'serialnumber': ZkDeviceMock._get_serialnumber(),
                    'platform': ZkDeviceMock._get_platform(),
                    'fingerprint_algorithm': ZkDeviceMock._get_fp_version(),
                    'device_name': ZkDeviceMock._get_device_name(),
                    'work_code': ZkDeviceMock._get_workcode(),
                    'oem_vendor': ZkDeviceMock._get_oem_vendor(),
                    }
                ]
            )
        cr.rollback()
        cr.close()

    # 9. Hiển thị datetime của máy chấm công
    @patch.object(ZK, 'get_time', ZkDeviceMock._get_time)
    def test_02_action_show_time(self):
        local_dt = ZkDeviceMock._get_time()
        utc = self.env['to.base'].convert_local_to_utc(local_dt, force_local_tz_name=self.attendance_device.tz, naive=False)
        action = self.attendance_device._prepare_action_confirm()
        action['context'].update({
            'method': 'N/A',
            'title': 'Machine Time',
            'content': "The machine time is %s" % utc.astimezone(pytz.timezone(self.attendance_device.tz))
        })
        self.assertEqual(self.attendance_device.action_show_time(), action)

    # 10. Restart máy chấm công từ xa
    @patch.object(ZK, 'restart', ZkDeviceMock._restart)
    @mute_logger('odoo.addons.to_attendance_device.models.attendance_device', 'ZKErrorConnection')
    def test_03_action_restart(self):
        with self.assertRaises(ValidationError, msg = "test_action_restart failed"):
            self.attendance_device._restart()

    # 12. Download user
    def test_05_user_download(self):
        self.attendance_device._user_download()
        self.assertEqual(self.attendance_device.device_users_count, 1, "test_05_user_download failed")

    # 12. Upload users
    def test_06_user_upload(self):
        self.attendance_device._user_upload()
        self.assertEqual(len(ZkDeviceMock.users), 3, "test_06_user_upload failed")

    # 13. Map employee
    def test_07_action_employee_map(self):
        self.hr_employee = self.env['hr.employee'].create({
            'name': 'Test',
            })
        self.attendance_device._employee_map()
        self.assertEqual(self.attendance_device.mapped_employees_count, 3, "test_action_employee_map failed")

    # 14. Download fingers template
    def test_08_action_finger_template_download(self):
        self.attendance_device._finger_template_download()
        self.attendance_device._compute_total_finger_template_records()
        self.assertEqual(self.attendance_device.total_finger_template_records, 1, "test_action_finger_template_download failed")

    # 15. Download attendances
    def test_09_action_attendance_download(self):
        self.attendance_device._fetch_attendance_data()
        self.attendance_device._compute_total_attendance_records()
        self.assertEqual(self.attendance_device.total_att_records, 1, "test_action_attendance_download failed")

    # 20. Upload nhân viên lên thiết bị chấm công:
    def test_10_action_employee_upload_to_device(self):
        employee_to_upload = self.env.ref('hr.employee_chs')
        employee_upload_wizard = self.env['employee.upload.wizard'].create({
            'device_ids': (self.attendance_device.id,),
            'employee_ids': (employee_to_upload.id,)
            })
        employee_upload_wizard.action_employee_upload()
        self.attendance_device._compute_device_users_count()
        self.assertEqual(self.attendance_device.device_users_count, 1, "test_action_employee_upload passed failed")

        with self.assertRaises(ValidationError), mute_logger('odoo.sql_db'):
            employee_upload_wizard.action_employee_upload()

    # 16. Synchronize attendance
    def test_11_sync_attendance(self):
        self.attendance_device.create_employee_during_mapping = True
        self.attendance_device._fetch_attendance_data()
        self.env['user.attendance']._cron_synch_hr_attendance()
        self.assertEqual(self.env['hr.attendance'].search_count([]), 13, "test_sync_attendance failed")

    # ============ Tester bổ sung testcase: ============
    # 14. Tạo mới 1 thiết bị chấm công có cùng thông tin IP, Port nhưng khác địa điểm với 1 thiết bị chấm công đang sử dụng
    def test_12_new_device_dupplicate_ip_port_location(self):
        new_att_device_location = self.env['attendance.device.location'].create({
            'name': 'new_att_device_location',
            'hr_work_location_id': self.env.ref('hr.work_location_1').id,
            })
        new_att_device = self.env['attendance.device'].create({
            'name': 'new_att_device',
            'ip': self.attendance_device.ip,
            'port': self.attendance_device.port,
            'timeout': 20,
            'password':'1234',
            'location_id': new_att_device_location.id,
            })
        self.assertEqual(self.env['attendance.device'].search_count([]), 2, "test_new_device_dupplicate_ip_port_location failed")

    # 15. Xóa 1 thiết bị không ở trạng thái draft: Confirm/cancelled
    def test_13_delete_device_not_in_draft(self):
        with self.assertRaises(UserError, msg = "test_delete_device_not_in_draft failed"):
            self.attendance_device.state = 'confirmed'
            self.attendance_device.unlink()

    # 16. Xóa 1 thiết bị ở trạng thái draft và chưa có dữ liệu chấm công
    def test_14_delete_device_in_draft_no_attendance_data(self):
        new_att_device = self.env['attendance.device'].create({
            'name': 'new_att_device',
            'ip': 'new_ip',
            'port': 122,
            'timeout': 20,
            'password':'1234',
            'location_id': self.attendance_device_location.id,
            })
        new_att_device.unlink()
        self.assertEqual(self.env['attendance.device'].search_count([]), 1, "test_delete_device_in_draft_no_attendance_data failed")

    # 17. Xóa thiết bị ở trạng thái Draft và đã có dữ liệu chấm công
    def test_15_delete_device_in_draft_has_attendance_data(self):
        with self.assertRaises(UserError, msg = "test_delete_device_in_draft_has_attendance_data failed"):
            new_att_device = self.env['attendance.device'].create({
                'name': 'new_att_device',
                'ip': 'new_ip',
                'port': 122,
                'timeout': 20,
                'password':'1234',
                'location_id': self.attendance_device_location.id,
                })
            new_att_device_user = self.env['attendance.device.user'].create({
                'name': 'new user',
                'device_id': new_att_device.id,
                'user_id': 123,
                'uid': 123,
                })
            self.user_attendance = self.env['user.attendance'].create({
                'device_id': new_att_device.id,
                'user_id': new_att_device_user.id,
                'timestamp': fields.datetime.now(),
                'status': 1,
                'attendance_state_id': self.env['attendance.state'].search([])[1].id,
                })
            new_att_device.unlink()

    # Form test
    # Case 5: Time zone của máy chấm công tự cập nhật theo time zone của location
    def test_16_compute_tz(self):
        self.attendance_device.location_id.tz = 'Asia/Ho_Chi_Minh'
        self.assertEqual(self.attendance_device.tz, 'Asia/Ho_Chi_Minh')

   # Form test
    # Case 6: Sau khi thực hiện Download Users (tại form view của Device Manager), số lượng Users sẽ được tự cập nhật theo số lượng users có trong máy chấm công
    def test_17_compute_device_users_count(self):
        self.env['attendance.device.user'].create({
            'name': 'test_attendance_device_user',
            'device_id': self.attendance_device.id,
            'user_id': 2
            })
        self.assertEqual(self.attendance_device.device_users_count, 1)

    # Form test
    # Case 7: Số lượng Employee trên hệ thống đã được map với Device users trong máy chấm công được tự động cập nhật sau thao tác “Map Employee"
    def test_18_compute_mapped_employees_count(self):
        new_employee = self.env['hr.employee'].create({
            'name': 'Van A',
            })
        new_user = self.env['attendance.device.user'].create({
            'name': 'new_test_user',
            'device_id': self.attendance_device.id,
            'user_id': 2,
            'employee_id': new_employee.id,
            })
        self.assertEqual(self.attendance_device.mapped_employees_count, 1)
        pass

    # Form test
    # Case 8: Số lượng vân tay có trong máy chấm công tại form view Device Manager tự cập nhật sau thao tác Download Fingers Template (nếu máy chấm công có sự thay đổi số lượng vân tay)
    def test_19_compute_total_finger_template_records(self):
        self.test_08_action_finger_template_download()
        self.env['finger.template'].create({
            'uid': 2,
            'fid': 2,
            'device_user_id': self.attendance_device.device_user_ids.search([('name','=','test')], limit=1).id,
            'device_id': self.attendance_device.id,
            })
        self.attendance_device._compute_total_finger_template_records()
        self.assertEqual(self.attendance_device.total_finger_template_records, 2, "test_compute_total_finger_template_records failed")

    # Form test
    # Case 9: Số lượng bản ghi thông tin chấm công (Attendance Records) tự cập nhật sau khi thực hiện Download Attendance
    def test_20_compute_total_attendance_records(self):
        self.attendance_device._fetch_attendance_data()
        self.env['user.attendance'].create({
            'device_id': self.attendance_device.id,
            'user_id': self.attendance_device.device_user_ids.search([('name','=','test')], limit=1).id,
            'timestamp': fields.datetime.now(),
            'status': 1,
            'attendance_state_id': self.env['attendance.state'].search([('code','=',1)], limit=1).id,
            })
        self.attendance_device._compute_total_attendance_records()
        self.assertEqual(self.attendance_device.total_att_records, 2, "test_compute_total_attendance_records failed")

    # Tư vấn bổ sung testcases
    # 17. Một Attendance status không có cùng một loại Attendance type
    def test_21_attendance_status_type_unique(self):
        #create a new attendance activity
        self.attendance_activity = self.env['attendance.activity'].create({
            'name': 'new_test_attendance_activity'
            })
        #create a new attendance status with the type = checkin
        self.env['attendance.state'].create({
            'name': 'new_test_attendance_state',
            'activity_id': self.env['attendance.activity'].search([('name','=','new_test_attendance_activity')], limit=1).id,
            'code': 222,
            'type': 'checkin'
            })
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            #create a new attendance status with the same type = checkin, same activity but another code
            self.env['attendance.state'].create({
                'name': 'new_test_attendance_state',
                'activity_id': self.env['attendance.activity'].search([('name','=','new_test_attendance_activity')], limit=1).id,
                'code': 223,
                'type': 'checkin'
                })

    # 18. Code number của Attendance status là duy nhất
    def test_22_attendance_status_code_unique(self):
        #create a new attendance activity
        self.attendance_activity = self.env['attendance.activity'].create({
            'name': 'new_test_attendance_activity'
            })
        #create a new attendance status with the code = 222
        self.env['attendance.state'].create({
            'name': 'new_test_attendance_state',
            'activity_id': self.env['attendance.activity'].search([('name','=','new_test_attendance_activity')], limit=1).id,
            'code': 222,
            'type': 'checkin'
            })
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            #create a new attendance status with the same code = 222, same activity but another type
            self.env['attendance.state'].create({
                'name': 'new_test_attendance_state',
                'activity_id': self.env['attendance.activity'].search([('name','=','new_test_attendance_activity')], limit=1).id,
                'code': 222,
                'type': 'checkout'
                })

    # 19. Tự động tạo nhân viên với những device user chưa được map với nhân viên
    def test_23_attendance_device_generate_employee(self):
        # ZkDevice has an user named "test"
        # when Generate Emloyees is enabled, _employee_map() will create an employee named "test"
        self.attendance_device.create_employee_during_mapping = True
        self.attendance_device._employee_map()
        self.assertTrue(self.env['hr.employee'].search([('name','=','test')]))

    # Download attendances from many devices simultaneously
    def test_24_action_attendance_download_devices(self):
        self.attendance_device_2 = self.env['attendance.device'].create({
            'name': 'test_attendance_device',
            'ip': 'ip_test',
            'port': 1112,
            'timeout': 20,
            'password':'1234',
            'location_id': self.attendance_device_location.id,
            })
        self.attendance_device_3 = self.env['attendance.device'].create({
            'name': 'test_attendance_device',
            'ip': 'ip_test',
            'port': 1113,
            'timeout': 20,
            'password':'1234',
            'location_id': self.attendance_device_location.id,
            })
        attendance_devices = self.env['attendance.device'].search([])
        attendance_devices.action_fetch_attendance_data()
        self.assertEqual(self.attendance_device.total_att_records, 1)
        self.assertEqual(self.attendance_device_2.total_att_records, 1)
        self.assertEqual(self.attendance_device_3.total_att_records, 1)
