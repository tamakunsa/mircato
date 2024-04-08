# See LICENSE file for full copyright and licensing details

from collections import OrderedDict
from operator import itemgetter
from odoo import fields
from odoo import http
from odoo.http import request
from odoo.tools import date_utils, groupby as groupbyelem
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.translate import _


class WebsiteAccount(CustomerPortal):

    def get_domain_my_loan(self, user):
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return [('employee_id', '=', emp and emp.id or False)]

    def _prepare_portal_layout_values(self):
        values = super(WebsiteAccount, self)._prepare_portal_layout_values()
        loans_count = request.env['employee.loan'].sudo().search_count(self.get_domain_my_loan(request.env.user))
        values.update({'loans_count': loans_count})
        return values

    @http.route(['/my/loans', '/my/loans/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_loans(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, groupby='none', **kw):
        values = self._prepare_portal_layout_values()
        HrLoans = request.env['employee.loan'].sudo()
        Loans_sudo = request.env['employee.loan'].sudo()
        domain = self.get_domain_my_loan(request.env.user)

        loans_domain = ([('loan_term', '>', 0)])
        holiday_type_ids = request.env['employee.loan.type'].sudo().search(loans_domain)
        user = request.env.user
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)],
                                                       limit=1)
        values.update({
            'loan_types': holiday_type_ids.sudo().with_context({'employee_id': emp and emp.id or False}).name_get()})
        # fileter  By
        searchbar_filters = {
            'all': {'label': _('All'),
                    'domain': [('state', 'in', ('draft', 'request', 'dep_approval', 'hr_approval', 'done', 'paid'))]},
            'request': {'label': _('Request'), 'domain': [('state', '=', 'request')]},
            'approval': {'label': _('HR&Dep Approval'), 'domain': [('state', 'in', ('dep_approval', 'hr_approval'))]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            'paid': {'label': _('Paid'), 'domain': [('state', '=', 'paid')]},
        }
        # sort By
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Name'), 'order': 'name'},
        }
        # group By
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('None')},
            'loans': {'input': 'loans', 'label': _('Loans Type')},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # pager
        loans_count = HrLoans.search_count(domain)
        pager = request.website.pager(
            url="/my/loans",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=loans_count,
            page=page,
            step=self._items_per_page
        )
        # default groupby
        if groupby == 'loans':
            order = "loan_type_id, %s" % order
        # content according to pager and archive selected
        loans = HrLoans.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        if groupby == 'none':
            grouped_loans = []
            if loans:
                grouped_loans = [loans]
        else:
            grouped_loans = [Loans_sudo.concat(*g) for k, g in groupbyelem(loans, itemgetter('loan_type_id'))]
        values.update({
            'date': date_begin,
            'loans': loans,
            'grouped_loans': grouped_loans,
            'page_name': 'loans',
            'default_url': '/my/loans',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_groupby': searchbar_groupby,
            'sortby': sortby,
            'groupby': groupby,
            'filterby': filterby,
        })
        return request.render("dev_hr_loan.portal_my_loans_details", values)

    @http.route(['''/my/loans/<model('employee.loan'):loans>'''], type='http', auth="user", website=True)
    def portal_my_loans_type(self, loans, **kw):
        user = request.env.user
        emp = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)],
                                                       limit=1)
        loans_domain = ([('loan_term', '>', 0)])
        loan_type_ids = request.env['employee.loan.type'].sudo().search(loans_domain)
        return request.render(
            "dev_hr_loan.portal_my_loans_types", {
                'loans': loans,
                'loan_types': loan_type_ids.sudo().with_context({'employee_id': emp and emp.id or False}).name_get(),
                'emp_id': emp and emp.id or False
            })
