from odoo import models, fields, api, tools
from datetime import datetime, timezone, timedelta
import xlsxwriter
import base64
from io import StringIO, BytesIO
from odoo.exceptions import ValidationError
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointConsumptionReport(models.AbstractModel):
    _name = 'report.onpoint_wtclite.consumption_report'
    _inherit = 'report.odoo_report_xlsx.abstract'

    def generate_xlsx_report(self, logger_id, channel_id):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)

        now = datetime.now()
        current_date = now.strftime('%d/%m/%Y')
        previous = now - timedelta(days=30)
        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '7d'

        consumption_datas = self.env['onpoint.logger'].get_data_consumption(logger_id=int(logger_id),
                                                                            channel_id=int(channel_id),
                                                                            range_date=range_date,
                                                                            option_hour='00')
        flow_data = []
        idx = 0
        for value in consumption_datas['tabular_data']:
            if idx > 0:
                flow_data.append({
                    'dates': value[0],
                    'channel_value': value[1],
                    'totalizer_value': value[2]
                })
            idx += 1

        sheet = workbook.add_worksheet('Tess')
        bold = workbook.add_format({'bold': True})
        sheet.write(0, 0, 'Consumption', bold)
