from datetime import date, datetime
from odoo.http import (
    content_disposition,
    request,
    route,
    Controller
)

import base64
import xlsxwriter
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)

class PosReportDetailsController(Controller):
    @route(["/pos/report/detail/excel_report"], type='http', auth='user')
    def get_pos_report_detail(self,**post):
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('pos_details_report'+ time + '.xlsx'))
            ]
        )
        post['branches'] = [int(s) for s in post['branches'].split(',')]
        post['config_ids'] = [int(s) for s in post['config_ids'].split(',')]
        post['date_start'] = datetime.strptime(post['date_start'], "%Y-%m-%d").date()
        post['date_stop']  = datetime.strptime(post['date_stop'], "%Y-%m-%d").date()
        post['detailed_report'] = True if post['detailed_report']=='True' else False
        post['has_many_branches'] = True if post['has_many_branches']=='True' else False
        output = request.env['pos.order.report.wizard'].generate_excel_report(**post)

        response.stream.write(output.read())
        output.close()
        return response