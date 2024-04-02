from odoo import models, fields, api

from ..pyzk.zk.finger import Finger


class FingerTemplate(models.Model):
    _name = 'finger.template'
    _description = 'Fingers Template'

    device_user_id = fields.Many2one('attendance.device.user', string='Machine User',
                                     help="The device user who is owner of this finger template")
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help="The employee who is owner of this finger template", ondelete='cascade',
                                  compute='_compute_employee_id', store=True, readonly=False)
    uid = fields.Integer(string='UId', help="The ID (technical field) of the user/employee in the machine storage",
                         related='device_user_id.uid', store=True)
    device_id = fields.Many2one('attendance.device', string='Attendance Machine',
                                related='device_user_id.device_id', store=True)
    fid = fields.Integer(string='Finger Id', help="The ID of this finger template in the attendance machine.")
    valid = fields.Integer(string='Valid')
    # we don't want to store template as attachement since its format may not match any mimetype and will raise
    # "binascii.Error: Incorrect padding"
    template = fields.Binary(string='Template', attachment=False)

    # we use compute attribute to define the active value to employee_id.active
    # if we use related attribute, we'll mean employee_id.active = active. Then, if this template is archived,
    # the employee_id will be archived accordingly.
    active = fields.Boolean(string='Active', compute='_compute_active', default=True, store=True, readonly=False)

    @api.depends('device_id', 'device_id.active', 'employee_id', 'employee_id.active')
    def _compute_active(self):
        for r in self:
            if r.employee_id:
                r.active = r.device_id.active and r.employee_id.active
            else:
                r.active = r.device_id.active

    @api.depends('device_user_id', 'device_user_id.employee_id')
    def _compute_employee_id(self):
        for r in self:
            if r.device_user_id and r.device_user_id.employee_id:
                r.employee_id = r.device_user_id.employee_id.id
            else:
                self._cr.execute('''SELECT employee_id FROM finger_template WHERE id = %s''', (r.id,))
                res = self._cr.fetchone()
                r.employee_id = res and res[0] or False

    def upload_to_device(self, devices=None):
        devices = devices or self.mapped('device_id')
        device_users = self.mapped('device_user_id')
        for device in devices:
            for user in device_users.filtered(lambda u: u.device_id == device):
                fingers = []
                for template in self.filtered(lambda t: t.device_user_id == user and t.device_id == device):
                    fingers.append(Finger(template.uid, template.fid, template.valid, template.template))
                if fingers:
                    device.upload_finger_templates(user.uid, user.name, user.privilege, user.password, user.group_id,
                                                   user.user_id, fingers)
