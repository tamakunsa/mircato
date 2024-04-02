import logging
import pytz
import threading

from datetime import datetime

from odoo import models, fields, api, registry, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import format_datetime, config
from odoo.osv import expression
from odoo.addons.base.models.res_partner import _tz_get

from ..pyzk.zk import ZK
from ..pyzk.zk.user import User
from ..pyzk.zk.exception import ZKErrorResponse, ZKNetworkError, ZKConnectionUnauthorized

_logger = logging.getLogger(__name__)


class AttendanceDevice(models.Model):
    _name = 'attendance.device'
    _description = 'Attendance Machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_get_attendance_device_state_lines(self):
        attendance_device_state_line_data = []
        for state in self.env['attendance.state'].search([]):
            attendance_device_state_line_data.append(
                (0, 0, {
                    'attendance_state_id': state.id,
                    'code': state.code,
                    'type': state.type,
                    'activity_id': state.activity_id.id
                })
            )
        return attendance_device_state_line_data

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', index=True, copy=False, required=True, tracking=True,
        help="Only confirmed machines will get their data synchronized automatically.")

    name = fields.Char(string='Name', required=True, help="The name of the attendance machine", tracking=True,
                       translate=True, copy=True, default='/',
                       readonly=False, states={'confirmed': [('readonly', True)],
                                               'cancelled': [('readonly', True)]})

    firmware_version = fields.Char(string='Firmware Version', readonly=True,
                                   help="The firmware version of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")
    serialnumber = fields.Char(string='Serial Number', readonly=True,
                               help="The serial number of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")
    oem_vendor = fields.Char(string='OEM Vendor', readonly=True,
                             help="The OEM Vendor of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")
    platform = fields.Char(string='Platform', readonly=True,
                           help="The Platform of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")
    fingerprint_algorithm = fields.Char(string='Fingerprint Algorithm', readonly=True,
                                        help="The Fingerprint Algorithm (aka ZKFPVersion) of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")
    device_name = fields.Char(string='Machine Name', readonly=True,
                              help="The model of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")

    work_code = fields.Char(string='Work Code', readonly=True,
                            help="The Work Code of the machine which will be filled automatically when you hit the 'Get Machine Info' button.")

    ip = fields.Char(string='IP / Domain Name', required=True, tracking=True, copy=False, readonly=False,
                     states={'confirmed': [('readonly', True)],
                             'cancelled': [('readonly', True)]},
                     help="The accessible IP or Domain Name of the machine to get the machine's attendance data",
                     default='0.0.0.0')
    port = fields.Integer(string='Port', required=True, default=4370, tracking=True, readonly=False,
                          states={'confirmed': [('readonly', True)],
                                  'cancelled': [('readonly', True)]})
    timeout = fields.Integer(string='Timeout', default=20, required=True,
                             help="Maximum time in seconds to wait for response from the machine", tracking=True,
                             readonly=False, states={'confirmed': [('readonly', True)],
                                                     'cancelled': [('readonly', True)]})
    description = fields.Text(string='Description')
    user_id = fields.Many2one('res.users', string='Technician', tracking=True, default=lambda self: self.env.user)
    device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Machine Users',
                                      help="List of Users stored in the attendance machine")
    device_users_count = fields.Integer(string='Users Count', compute='_compute_device_users_count', store=True,
                                        tracking=True)

    mapped_employee_ids = fields.Many2many('hr.employee', 'mapped_device_employee_rel', string='Mapped Employees',
                                           compute='_compute_employees', store=True,
                                           help="List of employees that have been mapped with this machine's users")

    mapped_employees_count = fields.Integer(string='Mapped Employee Count', compute='_compute_mapped_employees_count',
                                            store=True, tracking=True)

    umapped_device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Unmapped Machine Users',
                                              domain=[('employee_id', '=', False)],
                                              help="List of Machine Users that have not been mapped with an employee")

    unmapped_employee_ids = fields.Many2many('hr.employee', 'device_employee_rel', 'device_id', 'employee_id',
                                             compute='_compute_employees', store=True, string='Unmapped Employees',
                                             help="The employees that have not been mapped with any user of this machine")

    attendance_device_state_line_ids = fields.One2many('attendance.device.state.line', 'device_id',
                                                       string='State Codes', copy=False,
                                                       default=_default_get_attendance_device_state_lines,
                                                       readonly=False, states={'confirmed': [('readonly', True)],
                                                                               'cancelled': [('readonly', True)]})
    location_id = fields.Many2one('attendance.device.location', string='Location', tracking=True,
                                  help="The location where the machine is located", required=True,
                                  readonly=False, states={'confirmed': [('readonly', True)],
                                                          'cancelled': [('readonly', True)]})

    ignore_unknown_code = fields.Boolean(string='Ignore Unknown Code', default=False, tracking=True,
                                         help="Sometimes you don't want to load attendance data with status "
                                              "codes those not declared in the table below. In such the case, check this field.",
                                         readonly=False, states={'confirmed': [('readonly', True)],
                                                                 'cancelled': [('readonly', True)]})

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
                                 readonly=False, states={'confirmed': [('readonly', True)],
                                                         'cancelled': [('readonly', True)]})

    auto_clear_attendance = fields.Boolean(string='Auto Clear Attendance Data', default=False, tracking=True,
                                           readonly=False, states={'confirmed': [('readonly', True)],
                                                                   'cancelled': [('readonly', True)]},
                                           help="Check this to clear all machine attendance data after download into Odoo")

    auto_clear_attendance_schedule = fields.Selection([
        ('on_download_complete', 'On Download Completion'),
        ('time_scheduled', 'Time Scheduled')], string='Auto Clear Schedule', required=True,
        default='on_download_complete', tracking=True,
        help="On Download Completion: Delete attendance data as soon as download finished\n"
             "Time Scheduled: Delete attendance data on the time specified below")
    auto_clear_attendance_hour = fields.Float(string='Auto Clear At', tracking=True, required=True, default=0.0,
                                              help="The time (in the attendance machine's timezone) to clear attendance data after download.")

    auto_clear_attendance_dow = fields.Selection([
        ('-1', 'Everyday'),
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'), ], string='Auto Clear On', default='6', required=True, tracking=True)

    auto_clear_attendance_error_notif = fields.Boolean(string='Auto Clear Attendance Notif.', default=True,
                                                       tracking=True,
                                                       help="Notify upon no safe found to clear attendance data")

    tz = fields.Selection(_tz_get, string='Time zone', compute='_compute_tz', store=True,
                          help="The machine's timezone, used to output proper date and time values inside attendance reports.")

    active = fields.Boolean(string='Active', default=True, tracking=True, readonly=True,
                            states={'draft': [('readonly', False)]})
    unique_uid = fields.Boolean(string='Unique UID', default=True, required=True, tracking=True,
                                readonly=False, states={'confirmed': [('readonly', True)],
                                                        'cancelled': [('readonly', True)]},
                                help="Some Bad Machines allow uid duplication. In this case, uncheck this field. But it is recommended to change your machine.")
    last_attendance_download = fields.Datetime(string='Last Sync.', readonly=True,
                                               help="The last time that the attendance data was downlowed from the machine into Odoo.")

    map_before_dl = fields.Boolean(string='Map Employee Before Download', default=True,
                                   help="Always try to map users and employees (if any new found) before downloading attendance data.")
    create_employee_during_mapping = fields.Boolean(string='Generate Employees During Mapping', default=False,
                                                    help="If checked, during mapping between Machine's Users and company's employees, unmapped machine"
                                                         " users will try to create a new employee then map accordingly.")

    download_error_notification = fields.Boolean(string='Download Error Notification', default=True,
                                                 readonly=False, states={'confirmed': [('readonly', True)],
                                                                         'cancelled': [('readonly', True)]},
                                                 help="Enable this to get notified when data download error occurs.")
    debug_message = fields.Boolean(string='Debug Message', default=False,
                                   help="If checked, debugging messages will be posted in"
                                        " OpenChatter for debugging purpose")

    user_attendance_ids = fields.One2many('user.attendance', 'device_id', string='Attendance Data', readonly=True)
    total_att_records = fields.Integer(string='Attendance Records', compute='_compute_total_attendance_records')
    finger_template_ids = fields.One2many('finger.template', 'device_id', string='Finger Template', readonly=True)
    total_finger_template_records = fields.Integer(string='Finger Templates',
                                                   compute='_compute_total_finger_template_records')
    protocol = fields.Selection([('udp', 'UDP'), ('tcp', 'TCP')], string='Protocol', required=True, default='tcp',
                                tracking=True,
                                help="Some old devices do not support TCP. In such the case, please try on switching to UDP.")
    omit_ping = fields.Boolean(string='Omit Ping', default=True,
                               help="Omit ping ip address when connecting to machine.",
                               readonly=False, states={'confirmed': [('readonly', True)],
                                                       'cancelled': [('readonly', True)]})
    password = fields.Char(string='Password', readonly=False, states={'confirmed': [('readonly', True)],
                                                                      'cancelled': [('readonly', True)]},
                           help="The password to authenticate the machine, if required")

    unaccent_user_name = fields.Boolean(string='Unaccent User Name', default=True, tracking=True,
                                        help="Some Machines support Unicode names such as the ZKTeco K50, some others do not."
                                             " In addition to this, the name field on devices is usually limited at about 24 Latin characters"
                                             " or less Unicode characters. Unaccent is sometimes a workaround for long Unicode names")
    # 65472 (0xFFc0) is the max size of TCP in the original pyzk (use in the method base.read_with_buffer as MAX_CHUNK)
    max_size_TCP = fields.Selection([('65472', '65472 bytes'),
                                     ('32768', '32768 bytes'),
                                     ('16384', '16384 bytes'),
                                     ('8192', '8192 bytes'),
                                     ('4096', '4096 bytes'),
                                     ('2048', '2048 bytes'),
                                     ('1024', '1024 bytes'),
                                     ], string='TCP Max-Size', default='65472', required=True,
                                    help="The default value (65472) works well for almost attendance machines. However, in some rare cases"
                                         " the error '[Errno 32] Broken pipe' may occur while getting data from devices. In such case, you may try on decreasing this value"
                                         " to see if it would help.\n"
                                         "Note: the smaller this value is, the slower data getting will be.")
    # 16384 is the max size of UDP in the original pyzk (use in the method base.read_with_buffer)
    max_size_UDP = fields.Selection([('65472', '65472 bytes'),
                                     ('32768', '32768 bytes'),
                                     ('16384', '16384 bytes'),
                                     ('8192', '8192 bytes'),
                                     ('4096', '4096 bytes'),
                                     ('2048', '2048 bytes'),
                                     ('1024', '1024 bytes'),
                                     ], string='UDP Max-Size', default='16384', required=True,
                                    help="The default value (16384) works well for almost attendance machines. However, in some rare cases,"
                                         " the error 'timed out' may occur while getting data from devices. In such situation, you may try on decreasing this value to see if it would help\n."
                                         "Note: the smaller this value is, the slower data getting will be.")

    zk_cache = {}

    _sql_constraints = [
        ('ip_and_port_unique',
         'UNIQUE(ip, port, location_id)',
         "You cannot have more than one machine with the same ip and port of the same location!"),
    ]

    @property
    def zk(self):
        """
        This method return a ZK object.
        If an object corresponding to the connection param was created
        and available in self.zk_cache, it will be return. To avoid it, call it with .with_context(no_zk_cache=True)
        """
        self.ensure_one()
        force_udp = self.protocol == 'udp'
        password = self.password or 0
        cached_key = (
        self.protocol, self.omit_ping, self.timeout, password, self.max_size_TCP, self.max_size_UDP, self.ip, self.port)

        if not cached_key in self.zk_cache.keys() or self.env.context.get('no_zk_cache', False):
            self.zk_cache[cached_key] = ZK(self.ip, self.port, self.timeout, password=password, force_udp=force_udp,
                                           ommit_ping=self.omit_ping,
                                           max_size_TCP=int(self.max_size_TCP), max_size_UDP=int(self.max_size_UDP))

        return self.zk_cache[cached_key]

    @api.depends('location_id.tz')
    def _compute_tz(self):
        default_tz = self.env.context.get('tz') or self.env.user.tz
        for r in self:
            if r.location_id and r.location_id.tz:
                r.tz = r.location_id.tz
            else:
                r.tz = default_tz

    def name_get(self):
        """
        name_get that supports displaying location name and model as prefix
        """
        result = []
        for r in self:
            name = r.name
            if r.oem_vendor:
                if r.device_name:
                    name = "[%s %s] %s" % (r.oem_vendor, r.device_name, name)
                else:
                    name = "[%s] %s" % (r.oem_vendor, name)
            if r.location_id:
                name = "[%s] %s" % (r.location_id.name, name)
            result.append((r.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """
        name search that supports searching by tag code
        """
        args = args or []
        domain = []
        if name:
            domain = ['|', ('location_id.name', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        state = self.search(domain + args, limit=limit)
        return state.name_get()

    @api.depends('device_user_ids', 'device_user_ids.active')
    def _compute_device_users_count(self):
        total_att_data = self.env['attendance.device.user'].read_group([('device_id', 'in', self.ids)], ['device_id'],
                                                                       ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.device_users_count = mapped_data.get(r.id, 0)

    def _compute_total_finger_template_records(self):
        total_att_data = self.env['finger.template'].read_group([('device_id', 'in', self.ids)], ['device_id'],
                                                                ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_finger_template_records = mapped_data.get(r.id, 0)

    def _compute_total_attendance_records(self):
        total_att_data = self.env['user.attendance'].read_group([('device_id', 'in', self.ids)], ['device_id'],
                                                                ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.total_att_records = mapped_data.get(r.id, 0)

    @api.depends('device_user_ids', 'device_user_ids.active', 'device_user_ids.employee_id',
                 'device_user_ids.employee_id.active')
    def _compute_employees(self):
        HrEmployee = self.env['hr.employee']
        for r in self:
            r.update({
                'unmapped_employee_ids': [(6, 0, HrEmployee.search([('company_id', '=', r.company_id.id), (
                'id', 'not in', r.device_user_ids.mapped('employee_id').ids)]).ids)],
                'mapped_employee_ids': [(6, 0, r.device_user_ids.mapped('employee_id').filtered(
                    lambda employee: employee.active == True).ids)],
            })

    @api.depends('mapped_employee_ids')
    def _compute_mapped_employees_count(self):
        for r in self:
            r.mapped_employees_count = len(r.mapped_employee_ids)

    @api.onchange('unique_uid')
    def onchange_unique_uid(self):
        if not self.unique_uid:
            message = _("This is for experiment to check if the machine contains bad data with non-unique user's uid."
                        " Turn this option off will allow mapping machine user's user_id with user's user_id in Odoo.\n"
                        "NOTE:\n"
                        "- non-latin user_id are not supportted.\n"
                        "- Do not turn this option off in production.")
            return {
                'warning': {
                    'title': "Warning!",
                    'message': message,
                },
            }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'ip' in vals:
                vals['ip'] = vals['ip'].strip() or False
        return super(AttendanceDevice, self).create(vals_list)

    def write(self, vals):
        if 'ip' in vals:
            vals['ip'] = vals['ip'].strip() or False
        return super(AttendanceDevice, self).write(vals)

    def connect(self):
        self.ensure_one()

        def post_message():
            email_template_id = self.env.ref('to_attendance_device.email_template_attendance_device')
            cr = registry(self._cr.dbname).cursor()
            self.with_env(self.env(cr=cr)).post_message(email_template_id)
            cr.commit()
            cr.close()

        error_msg = False
        try:
            return self.zk.connect()
        except ZKNetworkError as e:
            error_msg = _("Could not connect to the machine %s.\nDebugging info: %s") % (self.display_name, e)
        except ZKConnectionUnauthorized as e:
            error_msg = _("Connection Unauthorized! The machine %s may require password.") % self.display_name
        except ZKErrorResponse as e:
            error_msg = _(
                "Could not get connected to the machine %s. This is usually due to either the network error or"
                " wrong protocol selection or password authentication is required.\n"
                "Debugging info:\n%s") % (self.display_name, e)
        except Exception as e:
            error_msg = _("Could not get connected to the machine '%s'. Please check your network"
                          " configuration and machine password and/or hard restart your machine.\nDebugging info: %s") % (
                        self.display_name, e)

        if error_msg:
            post_message()
            raise ValidationError(error_msg)

    def disconnect(self):
        try:
            return self.zk.disconnect()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the machine %s disconnected. Here is the debugging information:\n%s")
                                  % (self.display_name, e))

    def disableDevice(self):
        """
        disable (lock) machine, ensure no activity when process run
        """
        try:
            return self.zk.disable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the machine %s disabled. Here is the debugging information:\n%s")
                                  % (self.display_name, e))

    def _restart(self):
        self.ensure_one()
        self.restartDevice()

    def enableDevice(self):
        """
        re-enable the connected machine
        """
        try:
            return self.zk.enable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the machine %s enabled. Here is the debugging information:\n%s")
                                  % (self.display_name, e))

    def getFirmwareVersion(self):
        '''
        return the firmware version
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_firmware_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the firmware version of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def getSerialNumber(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_serialnumber()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the serial number of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def getOEMVendor(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_oem_vendor()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the OEM Vendor of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def getFingerprintAlgorithm(self):
        '''
        return the Fingerprint Algorithm
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_fp_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the Fingerprint Algorithm of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def getPlatform(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_platform()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the platform of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def getDeviceName(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_device_name()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the Name of the machine %s. Here is the debugging information:\n%s")
                                  % (self.display_name, e))
        finally:
            self.disconnect()

    def getWorkCode(self):
        '''
        return the serial number
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_workcode()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not get the Work Code of the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.disconnect()

    def restartDevice(self):
        '''
        restart the machine
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.restart()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not restart the machine %s. Here is the debugging information:\n%s")
                                  % (self.display_name, e))

    def setUser(self, uid=None, name='', privilege=0, password='', group_id='', user_id='', card=0):
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.set_user(uid, name, privilege, password, group_id, user_id, card)
        except Exception as e:
            _logger.info(e)
            raise ValidationError(_("Could not set user into the machine %s. Here is the user information:\n"
                                    "uid: %s\n"
                                    "name: %s\n"
                                    "privilege: %s\n"
                                    "password: %s\n"
                                    "group_id: %s\n"
                                    "user_id: %s\n"
                                    "Here is the debugging information:\n%s\n")
                                  % (self.display_name, uid, name, privilege, password, group_id, user_id, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def delUser(self, uid, user_id):
        '''
        delete specific user by uid
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user(uid, user_id)
        except ZKErrorResponse as e:
            raise ZKErrorResponse(_("Could not delete the user with uid '%s', user_id '%s' from the device %s\n%s")
                                  % (uid, user_id, self.display_name, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def getUser(self):
        '''
        return a Python List of machine users in User(uid, name, privilege, password, group_id, user_id)
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_users()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("Could not get users from the machine %s\n"
                                    "If you had connected to your machine, perhaps your machine had problem. "
                                    "Some bad machines allowed duplicated uid may cause such problem. In such case, "
                                    "if you still want to load users from those bad machines, please uncheck Data "
                                    "Acknowledge field.\n"
                                    "Here is the debugging error message:\n%s") % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()

    def upload_finger_templates(self, uid, name, privilege, password, group_id, user_id, fingers):
        user = User(uid, name, privilege, password, group_id, user_id, card=0)
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.save_user_template(user, fingers)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not set finger template into the machine %s. Here are the information:\n"
                                    "user_id: %s\n"
                                    "Debugging information:\n%s")
                                  % (self.display_name, user_id, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def delFingerTemplate(self, uid, fid, user_id):
        '''
        delete finger template by uid and fid
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.delete_user_template(uid, fid, user_id)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(
                _("Could not delete finger template with fid '%s' of uid '%s' from the machine %s") % (
                fid, uid, self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getFingerTemplate(self):
        '''
        return a Python List of fingers template in Finger(uid, fid, valid, template)
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_templates()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("Could not get finger templates from the machine %s\n"
                                    "If you had connected to your machine, perhaps your machine had problem. "
                                    "Some bad machines allowed duplicated uid may cause such problem. In such case, "
                                    "if you still want to load users from those bad machines, please uncheck Data "
                                    "Acknowledge field.\n"
                                    "Here is the debugging error message:\n%s") % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()

    def get_next_uid(self):
        '''
        return max uid of users on attendance machine
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_next_uid()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("Could not get max uid from the machine %s\n"
                                    "If you had connected to your machine, perhaps your machine had problem.\n"
                                    "Here is the debugging error message:\n%s") % (self.display_name, str(e)))
        finally:
            self.enableDevice()
            self.disconnect()

    def getMachineTime(self):
        """
        Get naive machine date and time in its local timezone
        """
        try:
            self.connect()
            self.enableDevice()
            local_dt = self.zk.get_time()
            utc = self.env['to.base'].convert_local_to_utc(local_dt, force_local_tz_name=self.tz, naive=False)
            return utc.astimezone(pytz.timezone(self.tz))
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("Could not get time from the machine %s\n"
                                    "Here is the debugging error message:\n%s") % (self.display_name, str(e)))
        finally:
            self.disconnect()

    def clearData(self):
        '''
        clear all data (include: user, attendance report, finger database )
        '''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.clear_data()
        except Exception:
            raise ValidationError(_("Could not clear all data from the machine %s") % (self.display_name,))
        finally:
            self.enableDevice()
            self.disconnect()

    def getAttendance(self):
        post_err_msg = False
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.get_attendance()

        except Exception as e:
            _logger.error(str(e))
            post_err_msg = True
            raise ValidationError(_("Could not get attendance data from the machine %s") % (self.display_name,))

        finally:
            if post_err_msg and self.download_error_notification:
                email_template_id = self.env.ref('to_attendance_device.email_template_error_get_attendance')
                self.post_message(email_template_id)
            self.enableDevice()
            self.disconnect()

    def clearAttendance(self):
        '''
        clear all attendance records from the machine
        '''
        try:
            self.connect()
            self.enableDevice()
            self.disableDevice()
            return self.zk.clear_attendance()
        except Exception as e:
            raise ValidationError(
                _("Could not clear attendance data from the machine %s. Here is the debugging information:\n%s")
                % (self.display_name, e))
        finally:
            self.enableDevice()
            self.disconnect()

    def _download_users_by_uid(self):
        """
        This method download and update all machine users into model attendance.device.user using uid as key
        """
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            error_msg = ""
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            uids = []
            for device_user in device_users:
                uids.append(device_user.uid)

            existing_user_ids = []

            device_user_ids = DeviceUser.with_context(active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.uid in uids):
                existing_user_ids.append(user.uid)

            users_not_in_device = device_user_ids.filtered(lambda user: user.uid not in existing_user_ids)
            users_not_in_device.write({'not_in_device': True})

            for device_user in device_users:
                uid = device_user.uid
                vals = {
                    'uid': uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if uid not in existing_user_ids:
                    try:

                        DeviceUser.create(vals)
                    except Exception as e:
                        _logger.info(e)
                        _logger.info(vals)
                        error_msg += str(e)
                        error_msg += _("\nData that caused the error: %s") % str(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search(
                        [('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                    if existing:
                        update_data = {}
                        if existing.name != vals['name']:
                            update_data['name'] = vals['name']
                        if existing.privilege != vals['privilege']:
                            update_data['privilege'] = vals['privilege']
                        if existing.password != vals['password']:
                            update_data['password'] = vals['password']
                        if 'group_id' in vals and existing.group_id != vals['group_id']:
                            update_data['group_id'] = vals['group_id']
                        if existing.user_id != vals['user_id']:
                            update_data['user_id'] = vals['user_id']
                        if existing.device_id.id != vals['device_id']:
                            update_data['device_id'] = vals['device_id']
                        if bool(update_data):
                            try:
                                existing.write(update_data)
                            except Exception as e:
                                _logger.info(e)
                                _logger.info(vals)
                                error_msg += str(e) + "<br />"
                                error_msg += _("\nData that caused the error: %s") % str(update_data)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    def _download_users_by_user_id(self):
        """
        This method download and update all machine users into model attendance.device.user using user_id as key
        NOTE: This method is experimental as it failed on comparing user_id in unicode type from machines (unicode: string) with user_id in unicode string from Odoo (u'string')
        """
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.getUser()

            user_ids = []
            for device_user in device_users:
                user_ids.append(str(device_user.user_id))

            existing_user_ids = []
            device_user_ids = DeviceUser.with_context(active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.user_id in user_ids):
                existing_user_ids.append(str(user.user_id))

            for device_user in device_users:
                user_id = str(device_user.user_id)
                vals = {
                    'uid': device_user.uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if user_id not in existing_user_ids:
                    DeviceUser.create(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search([
                        ('user_id', '=', user_id),
                        ('device_id', '=', r.id)], limit=1)
                    if existing:
                        existing.write(vals)

    def action_show_time(self):
        """
        Show the time on the machine
        """
        self.ensure_one()
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': 'N/A',
            'title': _('Machine Time'),
            'content': _("The machine time is %s") % self.getMachineTime()
        })
        return action

    def _user_download(self):
        """
        This method download and update all machine users into model attendance.device.user
        """
        for r in self:
            if r.unique_uid:
                r._download_users_by_uid()
            else:
                r._download_users_by_user_id()

    def _user_upload(self):
        """
        This method will
        1. Download users from machine
        2. Map the users with emloyee
        3. Upload users from model attendance.device.user into the machine
        """
        ignored_employees_dict = {}
        for r in self:
            # Then we download and map all employees with users
            r._employee_map()
            # Then we create users from unmapped employee
            ignored_employees = []
            for employee in r.unmapped_employee_ids:
                if not employee.barcode:
                    ignored_employees.append(employee)
                    continue
                employee.upload_to_attendance_device(r)
            # we download and map all employees with users again
            r._employee_map()

            if len(ignored_employees) > 0:
                ignored_employees_dict[r] = ignored_employees

        if bool(ignored_employees_dict):
            message = _(
                "The following employees, who have no Badge ID defined, have not been uploaded to the corresponding machine:\n")
            for device in ignored_employees_dict.keys():
                for employee in ignored_employees_dict[device]:
                    message += device.name + ': ' + employee.name + '\n'

            return {
                'warning': {
                    'title': "Some Employees could not be uploaded!",
                    'message': message,
                },
            }

    def _employee_map(self):
        self._user_download()

        for r in self:
            for user in r.device_user_ids.filtered(lambda user: not user.employee_id):
                employee = user.smart_find_employee()
                if employee:
                    user.write({
                        'employee_id': employee.id,
                    })
            # upload users that are available in Odoo but not available in device
            for user in r.device_user_ids.filtered(lambda user: user.not_in_device):
                user.setUser()

            # upload users that are available in Odoo but not available in device
            for user in r.device_user_ids.filtered(lambda user: user.not_in_device):
                user.setUser()
                user.write({'not_in_device': False})

            if r.create_employee_during_mapping:
                users = r.device_user_ids.filtered(lambda user: not user.employee_id)
                if users:
                    users.generate_employees()

    def action_attendance_download(self):
        # TODO: remove me in master/16+
        _logger.warning("The method action_attendance_download() is deprecated and will be removed soon."
                        " Please use the `_fetch_attendance_data()` instead.")
        return self._fetch_attendance_data()

    def action_fetch_attendance_data(self):
        self._threaded_fetch_attendance_data(wait=True)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def _threaded_fetch_attendance_data(self, wait=False):

        def _fetch_attendance_data(devices):
            with self.pool.cursor() as cr:
                env = self.env(cr=cr)
                for device in devices:
                    device = device.with_env(env)
                    # Try... except... helps continue with the remain devices if one got error raised.
                    try:
                        with env.cr.savepoint():
                            device._fetch_attendance_data()
                        env.cr.commit()
                    except Exception as e:
                        _logger.error("Error fetching attendance data from the machine %s: %s", device.display_name, e)

        jobs = []
        to_process = self
        max_threads = config['db_maxconn'] // 8  # get 8 threads if db_maxconn is 64 by default
        batch_count = (len(to_process) // max_threads) if len(self) > max_threads else 1
        idx_from = 0
        while to_process:
            slices = to_process[:batch_count]
            t = threading.Thread(target=_fetch_attendance_data, args=(slices,), daemon=True)
            t.start()
            to_process -= slices
            jobs.append(t)
            idx_from += batch_count
        if wait:
            for j in jobs:
                j.join()
        return jobs

    @api.model
    def _cron_download_device_attendance(self):
        devices = self.env['attendance.device'].search([('state', '=', 'confirmed')])
        devices._threaded_fetch_attendance_data()

    def _fetch_attendance_data(self):
        DeviceUserAttendance = self.env['user.attendance']
        AttendanceUser = self.env['attendance.device.user']

        map_before_dl = self.filtered(lambda r: r.map_before_dl)
        if map_before_dl:
            map_before_dl._finger_template_download()

        for r in self:
            error_msg = ""
            attendance_states = {}
            for state_line in r.attendance_device_state_line_ids:
                attendance_states[state_line.attendance_state_id.code] = state_line.attendance_state_id.id

            attendance_data = r.getAttendance()
            for attendance in attendance_data:
                if attendance.punch not in attendance_states.keys():
                    if not r.ignore_unknown_code:
                        try:
                            email_template_id = self.env.ref(
                                'to_attendance_device.email_template_unknown_attendance_status_code')
                            cr = registry(self._cr.dbname).cursor()
                            context = {
                                'code': attendance.punch,
                                'machine_name': r.display_name,
                            }
                            r.with_env(self.env(cr=cr)).with_context(context).post_message(email_template_id)
                        finally:
                            cr.commit()
                            cr.close()
                        unknown_code_msg = _("We found attendance status code '%s' from your machine %s "
                                             "but no such code found in the machine's settings in Odoo. "
                                             "Please go to the machine %s and add this attendance code.\n"
                                             "In case you want to ignore to load attendance data with this code, "
                                             " go to the machine setting in Odoo and check 'Ignore Unknown Code'.") \
                                           % (attendance.punch, r.display_name, r.display_name)
                        _logger.warning(unknown_code_msg)
                        raise UserError(unknown_code_msg)
                    continue

                attendance_user = AttendanceUser.with_context(active_test=False).search([
                    ('user_id', '=', attendance.user_id),
                    ('device_id', '=', r.id)
                ], limit=1)
                if attendance_user:
                    utc_timestamp = r.convert_local_to_utc(attendance.timestamp, r.tz, naive=True)
                    duplicate_attend = DeviceUserAttendance.search([
                        ('device_id', '=', r.id),
                        ('user_id', '=', attendance_user.id),
                        ('timestamp', '=', utc_timestamp)
                    ], limit=1)

                    if duplicate_attend:
                        continue

                    try:
                        with r.env.cr.savepoint():
                            self._cr.execute("""SELECT id FROM user_attendance LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED""")
                            DeviceUserAttendance.create({
                                'device_id': r.id,
                                'user_id': attendance_user.id,
                                'timestamp': utc_timestamp,
                                'status': attendance.punch,
                                'attendance_state_id': attendance_states[attendance.punch]
                            })
                    except Exception as e:
                        error_msg += str(e) + "<br />"
                        error_msg += _(
                            "Error create DeviceUserAttendance record: device_id %s; user_id %s; timestamp %s; attendance_state_id %s.<br />") % (
                                         r.id,
                                         attendance_user.id,
                                         attendance.timestamp,
                                         attendance_states[attendance.punch]
                                     )
                        _logger.error(error_msg)

            r.last_attendance_download = fields.Datetime.now()
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

            if not r.auto_clear_attendance:
                continue

            if r.auto_clear_attendance_schedule == 'on_download_complete':
                r._attendance_clear()
            elif r.auto_clear_attendance_schedule == 'time_scheduled':
                # datetime in the timezone of the device
                dt_now = self.convert_utc_to_local(datetime.utcnow(), r.tz, naive=True)
                float_dt_now = self.time_to_float_hour(dt_now)

                if int(r.auto_clear_attendance_dow) == -1 or dt_now.weekday() == int(r.auto_clear_attendance_dow):
                    delta = r.auto_clear_attendance_hour - float_dt_now
                    if abs(delta) <= 0.5 or abs(delta) >= 23.5:
                        r._attendance_clear()

    def _finger_template_download(self):
        FingerTemplate = self.env['finger.template']
        self._employee_map()
        all_device_users = self.env['attendance.device.user'].search([('device_id', 'in', self.ids)])
        for r in self:
            device_users = all_device_users.filtered(lambda dev: dev.device_id.id == r.id)

            # if there is still no device users, just ignore downloading finger templates
            if not device_users:
                continue

            template_data = r.getFingerTemplate()
            template_datas = []
            for template in template_data:
                template_datas.append(str(template.uid) + '_' + str(template.fid))

            existing_finger_template_ids = []
            finger_template_ids = FingerTemplate.search([('device_id', '=', r.id)])
            for template in finger_template_ids.filtered(
                    lambda tmp: (str(tmp.uid) + '_' + str(tmp.fid)) in template_datas):
                existing_finger_template_ids.append(str(template.uid) + '_' + str(template.fid))

            for template in template_data:
                uid = template.uid
                fid = template.fid
                valid = template.valid
                tmp = template.template
                device_user_id = self.env['attendance.device.user'].search(
                    [('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                device_user_id = device_users.filtered(lambda u: u.uid == uid)
                if not device_user_id:
                    continue
                else:
                    device_user_id = device_user_id[0]
                vals = {
                    'device_user_id': device_user_id.id,
                    'fid': fid,
                    'valid': valid,
                    'template': tmp,
                }
                if device_user_id.employee_id:
                    vals['employee_id'] = device_user_id.employee_id.id

                if (str(template.uid) + '_' + str(template.fid)) not in existing_finger_template_ids:
                    FingerTemplate.create(vals)
                else:
                    existing = FingerTemplate.search([
                        ('uid', '=', uid),
                        ('fid', '=', fid),
                        ('device_id', '=', r.id),
                    ], limit=1)
                    if existing:
                        existing.write(vals)
        return

    def is_attendance_clear_safe(self):
        """
        If the data from machines has not been downloaded into Odoo, this method will return false
        """
        UserAttendance = self.env['user.attendance']
        User = self.env['attendance.device.user']

        check_statuses = self.attendance_device_state_line_ids.mapped('code')

        attendances = self.getAttendance()  # Attendance(user_id, timestamp, status)
        for att in attendances:
            if att.punch not in check_statuses:
                continue
            user = User.with_context(active_test=False).search(
                [('user_id', '=', att.user_id), ('device_id', '=', self.id)], limit=1)
            utc_dt = self.convert_time_to_utc(att.timestamp, self.tz, naive=True)
            match = UserAttendance.search([('device_id', '=', self.id),
                                           ('user_id', '=', user.id),
                                           ('status', '=', att.punch),
                                           ('timestamp', '=', utc_dt)], limit=1)
            if not match:
                return False, att
        return True, False

    def _attendance_clear(self):
        """
        Method to clear all attendance data from the machine
        """

        for r in self:
            error_msg = ""
            attendance_clear_safe, att = r.is_attendance_clear_safe()
            if attendance_clear_safe:
                r.clearAttendance()
            else:
                error_msg += _("It was not safe to clear attendance data from the machine %s.<br />") % (r.name,)
                error_msg += _("The following attendance data has not been stored in Odoo yet:<br />")
                error_msg += _("user_id: %s<br />timestamp: %s<br />status: %s<br />") % (
                att.user_id, att.timestamp, att.punch)
                _logger.warning("It was not safe to clear attendance data from the machine %s" % r.name)
                if r.auto_clear_attendance_error_notif:
                    email_template_id = self.env.ref('to_attendance_device.email_template_not_safe_to_clear_attendance')
                    cr = registry(self._cr.dbname).cursor()
                    r.with_env(self.env(cr=cr)).post_message(email_template_id)
                    cr.commit()
                    cr.close()
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)
            if error_msg:
                raise ValidationError(error_msg.replace('<br />', '\n'))

    def action_check_connection(self):
        self.ensure_one()
        if self.connect():
            self.disconnect()
            action = self._prepare_action_confirm()
            action['context'].update({
                'method': 'N/A',
                'title': _('Machine Connection'),
                'content': _("Connect to the machine %s successfully!") % (self.display_name,)
            })
            return action

    def action_device_information(self):
        dbname = self._cr.dbname
        for r in self:
            try:
                cr = registry(dbname).cursor()
                r = r.with_env(r.env(cr=cr))
                r.connect()
                r.firmware_version = r.zk.get_firmware_version()
                r.serialnumber = r.zk.get_serialnumber()
                r.platform = r.zk.get_platform()
                r.fingerprint_algorithm = r.zk.get_fp_version()
                r.device_name = r.zk.get_device_name()
                r.work_code = r.zk.get_workcode()
                r.oem_vendor = r.zk.get_oem_vendor()
            except Exception as e:
                _logger.error(e)
                raise UserError(e)
            finally:
                cr.commit()
                cr.close()

    @api.model
    def post_message(self, email_template):
        if self.user_id:
            self.message_subscribe([self.user_id.partner_id.id])
        if email_template:
            self.message_post_with_template(email_template.id)

    def action_view_users(self):
        result = self.env['ir.actions.act_window']._for_xml_id('to_attendance_device.device_user_list_action')

        # reset context
        result['context'] = {}

        # choose the view_mode accordingly
        if self.device_users_count != 1:
            result['domain'] = "[('id', 'in', %s)]" % self.with_context(active_test=False).device_user_ids.ids
        elif self.device_users_count == 1:
            res = self.env.ref('to_attendance_device.attendance_device_user_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.device_user_ids.id
        return result

    def action_view_attendance_data(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id('to_attendance_device.action_user_attendance_data')

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_att_records = self.total_att_records
        if total_att_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_att_records == 1:
            res = self.env.ref('to_attendance_device.view_attendance_data_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.user_attendance_ids.id
        return result

    def action_view_mapped_employees(self):
        result = self.env['ir.actions.act_window']._for_xml_id('hr.open_view_employee_list_my')

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.mapped_employees_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.mapped_employee_ids.ids) + ")]"
        elif self.mapped_employees_count == 1:
            res = self.env.ref('to_attendance_device.view_employee_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.mapped_employee_ids.id
        return result

    def action_view_finger_template(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id('to_attendance_device.action_finger_template')

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('to_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_template_ids.id
        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_state(self):
        for r in self:
            if r.state != 'draft':
                raise UserError(_("You cannot delete the machine '%s' while its state is not Draft.")
                                % (r.display_name,))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_not_force_delete(self):
        force_delete = self.env.context.get('force_delete', False)
        for r in self:
            if r.device_user_ids and not force_delete:
                raise UserError(_("You may not be able to delete the machine '%s' while its data is stored in Odoo."
                                  " Please remove all the related data of this machine before removing it from Odoo."
                                  " You may also consider to deactivate this machine so that you don't have to delete"
                                  " it.") % (r.display_name,))

    def _prepare_action_confirm(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Information'),
            'res_model': 'device.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'safe_confirm': False,
            }
        }

    def action_user_upload(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_user_upload',
            'title': _('Upload Users To Machine'),
            'safe_confirm': True,
            'content': _("Odoo will map the existing users with Odoo's employees."
                         " The unmapped employees will be uploaded to this machine as new users"
                         " and then download those new users into Odoo and map them again"
                         " with those unmapped employees. Do you want to proceed?")
        })
        return action

    def action_user_download(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_user_download',
            'title': _('Download Users From Machine'),
            'content': _("Odoo will connect and download all the users from your machine"
                         " (without mapping those with the existing Employees in Odoo)."
                         " Do you want to proceed?")
        })
        return action

    def action_employee_map(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_employee_map',
            'title': _('Map Employees With Users'),
            'content': _("Odoo will connect and download all the users from your machine"
                         " and try to map those with the Odoo's employees."
                         " Do you want to proceed?")
        })
        return action

    def action_finger_template_download(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_finger_template_download',
            'title': _('Download Fingerprints From Machine'),
            'content': _("Odoo will connect and download all the fingers template from your machine."
                         " Do you want to proceed?")
        })
        return action

    def action_clear_attendance_data(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_attendance_clear',
            'title': _('Clear Attendance Data'),
            'safe_confirm': True,
            'content': _("Odoo will connect and clear all the attendance data"
                         " in this machine. Are you sure about this?")
        })
        return action

    def action_restart(self):
        action = self._prepare_action_confirm()
        action['context'].update({
            'method': '_restart',
            'title': _('Restart Machine'),
            'safe_confirm': True,
            'content': _("Are you sure to restart the machine: %s?") % (self.display_name,)
        })
        return action


class AttendanceDeviceStateLine(models.Model):
    _name = 'attendance.device.state.line'
    _description = 'Attendance Machine State'

    attendance_state_id = fields.Many2one('attendance.state', string='State Code', required=True, index=True, )
    device_id = fields.Many2one('attendance.device', string='Machine', required=True, ondelete='cascade', index=True,
                                copy=False)
    code = fields.Integer(string='Code Number', related='attendance_state_id.code', store=True, readonly=True)
    type = fields.Selection(related='attendance_state_id.type', store=True)
    activity_id = fields.Many2one('attendance.activity', related='attendance_state_id.activity_id',
                                  help="Attendance activity, e.g. Normal Working, Overtime, etc", readonly=True,
                                  store=True, index=True)

    _sql_constraints = [
        ('attendance_state_id_device_id_unique',
         'UNIQUE(attendance_state_id, device_id)',
         "The Code must be unique per Machine"),
    ]
