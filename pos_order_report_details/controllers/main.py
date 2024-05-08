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
        # print(post)
        post['branches'] = [int(s) for s in post['branches'].split(',')]
        post['date_start'] = datetime_object = datetime.strptime(post['date_start'], "%Y-%m-%d").date()
        post['date_stop'] = datetime_object = datetime.strptime(post['date_stop'], "%Y-%m-%d").date()
        # ids = [int(s) for s in list_ids.split(',')]
        # print(post)

        # if date_start and date_stop:
        output = request.env['pos.order.report.wizard'].generate_excel_report(**post)
        # else:
        #     output = request.env['pos.order.report.wizard'].generate_excel_report(ids)

        response.stream.write(output.read())
        output.close()
        return response