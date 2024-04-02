# -*- coding: utf-8 -*-

{
    'name': "Biometric Attendance Machines Integration",
    'name_vi_VN': "Tích hợp Máy chấm công Sinh trắc học",

    'summary': """
Integrate all kinds of ZKTeco based attendance machines with Odoo""",
    'summary_vi_VN': """
Tích hợp tất cả các loại máy chấm công nền tảng ZKTeco với Odoo""",

    'description': """
Key Features
============

* Support both UDP and TCP for large attendance data (tested with a real machine that store more than 90 thousand attendance records)
* Support connection with either domain name or IP
* Authenticate machines with password.
* Multiple machines for multiple locations
* Multiple machine time zones at multiple locations
* Multiple Attendance Status support (e.g. Check-in, Check-out, Start Overtime, End Overtime, etc)
* Store fingerprint templates in employee profiles to quickly set up new a machine (Added since version 1.1.0)
* Delete Machine's Users from Odoo
* Upload new users into the machines from Odoo's Employee database
* Auto Map Machine Users with Odoo employee base on Badge ID mapping, or name search mapping if no Badge ID match found
* Store Machine Attendance data permanently
* Manual/Automatic download attendance data from all your machines into Odoo (using scheduled actions)
* Manual/Automatic synchronize machine attendance data with HR Attendance so that you can access them in your salary rules for payslip computation
* Automatically Clear Attendance Data from the machines periodically, which is configurable.
* Designed to work with all attendance machines that based on ZKTeco platform.

  * Fully TESTED with the following machines:

    * RONALD JACK B3-C
    * ZKTeco K50
    * ZKTeco MA300
    * ZKTeco U580
    * ZKTeco T4C
    * ZKTeco G3
    * RONALD JACK iClock260
    * ZKTeco K14
    * iFace702
    * ZKTeco H5L
    * Uface 800 (worked with finger and face)

  * Reported by clients that the module has worked great with the following machines

    * ZKTeco K40
    * ZKTeco U580
    * iFace402/ID
    * ZKTeco MB20
    * ZKteco IN0A-1
    * ZKTeco H5L
    * Uface 800
    * ... (please advise us your machines. Tks!)

Credit
======
Tons of thanks to fananimi for his pyzk library @ https://github.com/fananimi/pyzk

We got inspired from that and customize it for more features (machine information, Python 3 support,
TCP/IP support, etc) then we integrated into Odoo by this great Attendance Machine application

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,
    'author': "T.V.T Marine Automation (aka TVTMA),Viindoo",
    'live_test_url': "https://v15demo-int.viindoo.com",
    'live_test_url_vi_VN': "https://v15demo-vn.viindoo.com",
    'website': 'https://viindoo.com/apps/app/15.0/to_attendance_device',
    'support': 'apps.support@viindoo.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '1.1.3',

    # any module necessary for this one to work correctly
    'depends': ['hr_attendance'],

    # always loaded
    'data': [
        'data/scheduler_data.xml',
        'data/attendance_state_data.xml',
        'data/mail_template_data.xml',
        'security/module_security.xml',
        'security/ir.model.access.csv',
        'views/menu_view.xml',
        'views/attendance_device_views.xml',
        'views/attendance_state_views.xml',
        'views/device_user_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_employee_views.xml',
        'views/user_attendance_views.xml',
        'views/attendance_activity_views.xml',
        'views/finger_template_views.xml',
        'wizard/employee_upload_wizard.xml',
        'wizard/device_confirm_wizard.xml',

    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 198.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
