from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.models import NewId


class EmployeeUploadLine(models.TransientModel):
    _name = 'employee.upload.line'
    _description = 'Employee Upload Details'

    wizard_id = fields.Many2one('employee.upload.wizard', required=True, ondelete='cascade')

    device_id = fields.Many2one('attendance.device', string='Device', required=True, ondelete='cascade')

    employee_id = fields.Many2one('hr.employee', string='Employees to upload', required=True, ondelete='cascade')

    def upload_employees(self):
        devices = self.mapped('device_id')
        error_msg = ""
        for device in devices:
            employees = self.filtered(lambda line: line.device_id.id == device.id).mapped('employee_id')
            with self.pool.cursor() as cr:
                error_msg += employees.with_env(self.env(cr=cr)).upload_to_attendance_device(device)
        if error_msg:
            raise ValidationError(error_msg)


class EmployeeUploadWizard(models.TransientModel):
    _name = 'employee.upload.wizard'
    _description = 'Employee Upload Wizard'

    @api.model
    def _default_get_employee_ids(self):
        return self.env['hr.employee'].search([('id', 'in', self.env.context.get('active_ids', []))])

    device_ids = fields.Many2many('attendance.device', 'employee_upload_wizard_attendance_device_rel', 'wizard_id',
                                  'device_id',
                                  string='Devices', required=True,
                                  compute='_compute_devices', store=True, readonly=False)

    employee_ids = fields.Many2many('hr.employee', 'employee_upload_wizard_hr_employee_rel', 'wizard_id', 'employee_id',
                                    string='Employees to upload', default=_default_get_employee_ids, required=True)

    line_ids = fields.One2many('employee.upload.line', 'wizard_id', string='Upload Details',
                               compute='_compute_line_ids',
                               store=True, readonly=False)

    @api.depends('employee_ids')
    def _compute_devices(self):
        for r in self:
            device_ids = r.employee_ids.mapped('unamapped_attendance_device_ids').filtered(
                lambda device: device.state != 'cancelled')
            r.device_ids = [(6, 0, device_ids.ids)]

    def _prepare_lines(self):
        data = []
        for employee in self.employee_ids:
            # Since Odoo 13, employee.id will return an instance of NewId stead of id in integer,
            # even the employee record already exists
            employee_id = isinstance(employee.id, NewId) and employee.id.origin or employee.id
            for device in self.device_ids:
                device_id = isinstance(device.id, NewId) and device.id.origin or device.id
                new_line = (0, 0, {
                    'employee_id': employee_id,
                    'device_id': device_id,
                })
                data.append(new_line)
        return data

    @api.depends('employee_ids', 'device_ids')
    def _compute_line_ids(self):
        for r in self:
            r.line_ids = [(5,)] + r._prepare_lines()

    def action_employee_upload(self):
        line_ids = self.mapped('line_ids')
        line_ids.upload_employees()
