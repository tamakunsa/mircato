from odoo import SUPERUSER_ID, api


def replace_partner_email_template(env):
    templates = env.ref('to_attendance_device.email_template_attendance_device', raise_if_not_found=False) or env['mail.template']
    templates |= env.ref('to_attendance_device.email_template_not_safe_to_clear_attendance', raise_if_not_found=False) or env['mail.template']
    templates |= env.ref('to_attendance_device.email_template_error_get_attendance', raise_if_not_found=False) or env['mail.template']
    templates.write({'partner_to': '${object.user_id.partner_id.id}'})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    replace_partner_email_template(env)
