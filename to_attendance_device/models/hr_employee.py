from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    unamapped_attendance_device_ids = fields.Many2many(
        'attendance.device', 'device_employee_rel', 'employee_id',
        'device_id',
        string='Unmapped Machines',
        help="The devices that have not store this employee as an user yet."
             " When you map employee with a user of a device, the device will disappear from this list.")
    created_from_attendance_device = fields.Boolean(
        string='Created from Device', readonly=True,
        groups="hr.group_hr_user",
        help="This field indicates that the employee was created from the data of an attendance machine")
    finger_templates_ids = fields.One2many('finger.template', 'employee_id',
                                           string='Finger Template', readonly=True)
    total_finger_template_records = fields.Integer(string='Finger Templates',
                                                   compute='_compute_total_finger_template_records')
    device_user_ids = fields.One2many('attendance.device.user', 'employee_id', string='Mapped Device Users')

    def _compute_total_finger_template_records(self):
        for r in self:
            r.total_finger_template_records = len(r.finger_templates_ids)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HrEmployee, self).create(vals_list)
        for company in employees.company_id:
            unmapped_attendance_devices = self.env['attendance.device'].sudo().with_context(active_test=False).search(
                [('company_id', '=', company.id)])
            employees.filtered(lambda emp: emp.company_id == company).write(
                {'unamapped_attendance_device_ids': [(6, 0, unmapped_attendance_devices.ids)]})
        return employees

    def write(self, vals):
        if 'barcode' in vals:
            DeviceUser = self.env['attendance.device.user'].sudo()
            for r in self.filtered(lambda emp: emp.barcode):
                if DeviceUser.search([('employee_id', '=', r.id)], limit=1):
                    raise ValidationError(_("The employee '%s' is currently referred by an attendance machine user."
                                            " Hence, you can not change the Badge ID of the employee") % (r.name,))
        return super(HrEmployee, self).write(vals)

    def _get_unaccent_name(self):
        return self.env['to.base'].strip_accents(self.name)

    def _prepare_device_user_data(self, device):
        return {
            'uid': device.get_next_uid(),
            'name': self._get_unaccent_name() if device.unaccent_user_name else self.name,
            'password': '',
            'privilege': 0,
            'group_id': '0',
            'user_id': self.barcode,
            'employee_id': self.id,
            'device_id': device.id,
        }

    def create_device_user_if_not_exist(self, device):
        data = self._prepare_device_user_data(device)
        domain = [('device_id', '=', device.id)]
        if device.unique_uid:
            domain += [('uid', '=', int(data['uid']))]
        else:
            domain += [('user_id', '=', str(data['user_id']))]
        user = self.env['attendance.device.user'].search(domain, limit=1)
        if not user:
            user = self.env['attendance.device.user'].create(data)
        else:
            update_vals = {
                'employee_id': self.id,
            }
            if device.unique_uid:
                update_vals.update({
                    'user_id': self.barcode
                })
            else:
                update_vals.update({
                    'uid': int(data['uid'])
                })
            user.write(update_vals)
        return user

    def upload_to_attendance_device(self, device):
        error_msg = ""
        for r in self:
            try:
                with r.env.cr.savepoint():
                    if not r.barcode:
                        r.generate_random_barcode()
                    device_user = r.create_device_user_if_not_exist(device)
                    device_user.setUser()
            except Exception as e:
                error_msg += _("Fail to upload the employee: %s to the machine: %s. %s\n") % (r.name, device.name, e)
        return error_msg

    def action_view_finger_template(self):
        result = self.env['ir.actions.act_window']._for_xml_id('to_attendance_device.action_finger_template')

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_finger_template_records = self.total_finger_template_records
        if total_finger_template_records != 1:
            result['domain'] = "[('employee_id', 'in', " + str(self.ids) + ")]"
        elif total_finger_template_records == 1:
            res = self.env.ref('to_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_templates_ids.id
        return result
