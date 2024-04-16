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


class PosReportController(Controller):
    @route(["/pos/session/excel_report"], type='http', auth='user')
    def get_pos_session_report(self, list_ids='',date_start='',date_stop='' ,**post):
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('pos_session_report'+ time + '.xlsx'))
            ]
        )
        ids = [int(s) for s in list_ids.split(',')]
        if date_start and date_stop:
            output = request.env['pos.daily.sales.reports.wizard'].generate_excel_report(ids,date_start,date_stop)
        else:
            output = request.env['pos.daily.sales.reports.wizard'].generate_excel_report(ids)

        response.stream.write(output.read())
        output.close()
        return response