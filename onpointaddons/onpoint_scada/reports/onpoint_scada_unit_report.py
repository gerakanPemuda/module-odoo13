import base64

from odoo import models, fields, api, _
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import json
from odoo.exceptions import ValidationError
import pandas as pd


class OnpointScadaUnitReport(models.TransientModel):
    _name = 'onpoint.scada.unit.report'

    unit_id = fields.Many2one('onpoint.scada.unit',
                              required=True,
                              string='Sensor',
                              ondelete='cascade',
                              index=True)
    report_period = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    option_hour = fields.Char()
    image_url = fields.Char()
    image_base = fields.Text()
    remarks = fields.Text()
    highchart_options = fields.Text()
    show_data = fields.Boolean(string='Show Data')
    interval = fields.Char()

    def generate_pdf_report(self, with_attachment=False):
        html_data = ''
        highcart_options = json.loads(self.highchart_options)
        df = None
        for series in highcart_options['series']:
            unit_values = []
            name = series['name']
            for data in series['data']:
                unit_values.append({
                    'dates': data[0],
                    name: str(data[1]) + ' ' + series['uom'],
                })

            if series['data']:
                if df is None:
                    df = pd.DataFrame(unit_values)
                else:
                    dx = pd.DataFrame(unit_values)
                    df = pd.merge(df, dx, on='dates', how='left')

                # df['unit_date'] = pd.to_datetime(df['dates'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Jakarta')

                if self.show_data:
                    html_data = '<table width="90%">'
                    cols = df.columns.values.tolist()
                    if len(cols) > 0:
                        cell_width = 100 / len(cols)
                    else:
                        cell_width = 100
                    logger_data = df.values.tolist()
                    html_data += '<tr>'
                    html_data += '<th width="' + str(
                        cell_width) + '%" style="border: 1px solid #000;text-align: center">Dates</th>'
                    idx = 0
                    for column in df.columns:
                        if idx > 0:
                            html_data += '<th width="' + str(cell_width) + '%" style="border: 1px solid #000;text-align: center">' + column + '</th>'
                        idx += 1
                    html_data += '</tr>'

                    for i in range(len(df)):
                        html_data += '<tr>'
                        # value_dates = df.loc[i, 'dates'] + timedelta(hours=add_hours)
                        value_dates = (datetime.fromtimestamp(df.loc[i, 'dates'] / 1000) - timedelta(hours=1)).strftime('%d-%m-%Y %H:%M:%S')
                        html_data += '<td style="border: 1px solid #000">' + str(value_dates) + '</td>'
                        idx = 0
                        for column in df.columns:
                            if idx > 0:
                                html_data += '<th width="' + str(cell_width) + '%" style="border: 1px solid #000;text-align: right">' + str(df.loc[i, column]) + '</th>'
                            idx += 1
                        html_data += '</tr>'
                    html_data += '</table>'
                else:
                    html_data = ''

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'timestamp': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                'image_base': self.image_base,
                'unit': {
                    'report_period': self.report_period,
                    'unit_name': self.unit_id.name,
                    'html_data': html_data,
                    'stats': highcart_options['stats']
                }
            },
        }

        return self.env.ref('onpoint_scada.act_onpoint_scada_unit_report1').report_action(self, data=data)


class OnpointUnitRecapReport(models.AbstractModel):
    _name = 'report.onpoint_scada.onpoint_scada_unit_report_template'
    _template = 'onpoint_scada.onpoint_scada_unit_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['onpoint.scada.unit.report'].browse(docids)

        timestamp = data['form']['timestamp']
        image_base64 = data['form']['image_base']
        unit = data['form']['unit']

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': self,
            'unit': unit,
            'timestamp': timestamp,
            'image_base64': image_base64,
        }
