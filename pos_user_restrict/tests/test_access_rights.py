from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError
from odoo.addons.base.tests.common import BaseUsersCommon


@tagged('post_install', '-at_install')
class TestPosUser(BaseUsersCommon, TransactionCase):

    def setUp(self):
        super(TestPosUser, self).setUp()
        self.pos_1 = self.env.ref('point_of_sale.pos_config_main')
        self.pos_2 = self.env.ref('pos_user_restrict.pos_config_second')
        self.user_internal.groups_id = [(4, self.env.ref('point_of_sale.group_pos_user').id)]

    def test_01_no_allowed_pos(self):
        with self.assertRaises(AccessError):
            self.pos_1.with_user(self.user_internal).read(['name'])
        with self.assertRaises(AccessError):
            self.pos_2.with_user(self.user_internal).read(['name'])

    def test_02_pos_1_allowed(self):
        self.user_internal.pos_config_ids = [Command.link(self.pos_1.id)]
        # Check the access to POS 1
        self.pos_1.with_user(self.user_internal).read(['name'])
        # Check the access to POS 2
        with self.assertRaises(AccessError):
            self.pos_2.with_user(self.user_internal).read(['name'])

        # Remove access
        self.user_internal.pos_config_ids = [Command.unlink(self.pos_1.id)]
        # Check the access to POS 1
        with self.assertRaises(AccessError):
            self.pos_1.with_user(self.user_internal).read(['name'])
