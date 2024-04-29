from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError


@tagged('post_install', '-at_install')
class TestPosUser(TransactionCase):

    def setUp(self):
        super(TestPosUser, self).setUp()
        self.user_pos = self.env.ref('pos_user_restrict.user_pos')
        self.user_demo = self.env.ref('base.user_demo')
        self.user_admin = self.env.ref('base.user_demo')
        self.pos_1 = self.env.ref('point_of_sale.pos_config_main')
        self.pos_2 = self.env.ref('pos_user_restrict.pos_config_second')

    def test_01_no_allowed_pos(self):
        with self.assertRaises(AccessError):
            self.pos_1.with_user(self.user_pos).read(['name'])
        with self.assertRaises(AccessError):
            self.pos_2.with_user(self.user_pos).read(['name'])

    def test_02_pos_1_allowed(self):
        self.user_pos.pos_config_ids = [Command.link(self.pos_1.id)]
        # Check the access to POS 1
        self.pos_1.with_user(self.user_pos).read(['name'])
        # Check the access to POS 2
        with self.assertRaises(AccessError):
            self.pos_2.with_user(self.user_pos).read(['name'])
