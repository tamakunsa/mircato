# -*- coding: utf-8 -*-
{
    'name': "HR Enhancement",
    'summary': """ This Module customize for hr. """,
    'author': "Omnya Rashwan (ECO-Tech)",
    'category': 'HR',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_holidays', 'hr_contract', 'hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/employee_request_document_security.xml',
        'data/send_notification_mail.xml',
        'data/send_email_delegation_template.xml',
        'views/hr_employee_inh_view.xml',
        'views/hr_leave_inh_view.xml',
        'views/hr_contract_inh_view.xml',
        'views/hr_probation_period_view.xml',
        'wizard/back_to_work_wiz_vew.xml',
        'reports/employee_request_document_report.xml',
        'views/employee_sponsor_view.xml',
    ],
}
