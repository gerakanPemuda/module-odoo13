import base64

from odoo import models, fields, api, _
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import pandas as pd


class OnpointLoggerReport(models.TransientModel):
    _name = 'onpoint.logger.report'
    _inherit = 'onpoint.monitor'

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    report_period = fields.Char()
    start_date = fields.Date()
    end_date = fields.Date()
    option_hour = fields.Char()
    image_url = fields.Char()
    image_base64 = fields.Text()
    power_image = fields.Char()
    power_value = fields.Char()
    signal_image = fields.Char()
    signal_value = fields.Char()
    temperature_image = fields.Char()
    temperature_value = fields.Char()
    is_flow = fields.Boolean(default=False)
    channel_id = fields.Many2one('onpoint.logger.channel', index=True)
    remarks = fields.Text()
    show_data = fields.Boolean(string='Show Data')
    interval = fields.Char()

    def generate_pdf_report(self, with_attachment=False):

        add_hours = self.logger_id.get_time_zone(self.logger_id.id)
        report_period = self.report_period.split(' - ')

        start_hour = int(self.option_hour)
        if start_hour == 0:
            end_hour = 23
        else:
            end_hour = start_hour - 1

        start_hours = f'{start_hour:02}'
        end_hours = f'{end_hour:02}'

        start_date = (
                    datetime.strptime(report_period[0] + ' ' + start_hours + ':00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
                hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(report_period[1] + ' ' + end_hours + ':59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        channels = []
        rows = []
        counter = 0
        channel_data = []
        df_logger = []
        df = None
        col = 0
        for channel in self.logger_id.channel_ids:
            if channel.display_on_chart:
                logger_values = []
                data = self.env['onpoint.logger.value'].get_data(channel.id, start_date, end_date)
                if not channel_data:
                    for value in data['values']:
                        channel_row = {
                            'dates': value.dates
                        }
                        channel_data.append(channel_row)

                for value in data['values']:
                    logger_row = {
                        'dates': value.dates,
                        channel.name: value.channel_value
                    }
                    logger_values.append(logger_row)

                if df is None:
                    df = pd.DataFrame(logger_values)
                else:
                    dx = pd.DataFrame(logger_values)
                    df = pd.merge(df, dx, on='dates', how='left')

                for value in data['values']:
                    res = [idx for idx, val in enumerate(channel_data) if val['dates'] == value.dates]
                    channel_value = {
                        channel.name: value.channel_value
                    }

                if not data['min_date']:
                    min_date = ''
                else:
                    min_date = self.convert_to_localtime(self.logger_id.id, data['min_date'])

                if not data['max_date']:
                    max_date = ''
                else:
                    max_date = self.convert_to_localtime(self.logger_id.id, data['max_date'])

                if not data['last_date']:
                    last_date = ''
                else:
                    last_date = self.convert_to_localtime(self.logger_id.id, data['last_date'])

                val = {
                    'name': channel.name,
                    'value_type_name': channel.value_type_name,
                    'value_unit_name': channel.value_unit_name,
                    'color': channel.color,
                    'last_date': last_date,
                    'last_value': data['last_value'],
                    'min_date': min_date,
                    'min_value': data['min_value'],
                    'max_date': max_date,
                    'max_value': data['max_value']
                }
                rows.append(val)
                counter += 1

            if counter == 3:
                counter = 0
                channels.append(rows)
                rows = []
        channels.append(rows)

        channel_data = self.env['onpoint.logger.channel'].search([('id', '=', self.channel_id.id)])
        has_totalizer_point_id = False
        channel_totalizer = False
        if 'totalizer_point_id' in channel_data._fields:
            has_totalizer_point_id = True
            if channel_data.totalizer_point_id:
                channel_totalizer = self.env['onpoint.logger.channel'].search([('logger_id', '=', self.logger_id.id),
                                                                               ('point_id', '=',
                                                                                channel_data.totalizer_point_id.id)])

        consumption_datas = self.env['onpoint.logger'].get_data_consumption(logger_id=self.logger_id.id,
                                                                            channel_id=self.channel_id.id,
                                                                            range_date=self.report_period,
                                                                            option_hour=self.option_hour,
                                                                            interval=self.interval)
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
            for channel in channels[0]:
                html_data += '<th width="' + str(cell_width) + '%" style="border: 1px solid #000;text-align: center">' + channel['name'] + '</th>'
            html_data += '</tr>'

            for i in range(len(df)):
                html_data += '<tr>'
                value_dates = df.loc[i, 'dates'] + timedelta(hours=add_hours)
                html_data += '<td style="border: 1px solid #000">' + str(value_dates) + '</td>'
                for channel in channels[0]:
                    html_data += '<th width="' + str(
                        cell_width) + '%" style="border: 1px solid #000;text-align: right">' + str(df.loc[i, channel['name']]) + ' ' + channel['value_unit_name'] + '</th>'
                html_data += '</tr>'
            html_data += '</table>'
        else:
            html_data = ''

        logger = {
            'id': self.logger_id.id,
            'report_period': self.report_period,
            'name': self.logger_id.name,
            'identifier': self.logger_id.identifier,
            'brand': self.logger_id.brand_id.name,
            'logger_type': self.logger_id.logger_type_id.name,
            'department': self.logger_id.department_id.name,
            'wtp': self.logger_id.wtp_id.name,
            'zone': self.logger_id.zone_id.name,
            'dma': self.logger_id.dma_id.name,
            'simcard': self.logger_id.simcard,
            'nosal': self.logger_id.nosal,
            'address': self.logger_id.address,
            'meter_type': self.logger_id.meter_type_id.name,
            'meter_brand': self.logger_id.meter_brand_id.name,
            'meter_size': self.logger_id.meter_size_id.name,
            'pipe_material': self.logger_id.pipe_material_id.name,
            'pipe_size': self.logger_id.pipe_size_id.name,
            'valve_control': self.logger_id.valve_control_id.name,
            'power_image': self.power_image,
            'power_value': self.power_value,
            'signal_image': self.signal_image,
            'signal_value': self.signal_value,
            'temperature_image': self.temperature_image,
            'temperature_value': self.temperature_value,
            'channels': channels,
            'is_flow': self.is_flow,
            'show_data': self.show_data,
            'flow_data': flow_data,
            'html_data': html_data,
            'consumption_last_value': consumption_datas['last_value'],
            'consumption_last_date': consumption_datas['last_date'],
            'consumption_min_value': consumption_datas['min_value'],
            'consumption_min_date': consumption_datas['min_date'],
            'consumption_max_value': consumption_datas['max_value'],
            'consumption_max_date': consumption_datas['max_date'],
            'consumption_meter_index': consumption_datas['last_totalizer'],
            'remarks': self.remarks if self.remarks else '',
            'print_date': datetime.now().strftime('%Y-%m-%d')
        }

        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'timestamp': (datetime.now() + relativedelta(hours=7)).strftime('%d/%m/%Y %H:%M:%S'),
                'image_url': self.image_base64,
                'logger': logger
            },
        }

        if with_attachment:
            pdf = self.env.ref('onpoint_monitor.act_onpoint_logger_report').render_qweb_pdf(self, data=data)
            b64_pdf = base64.b64encode(pdf[0])

            name = 'Onpoint Report ' + self.logger_id.name
            try:
                attachment = self.env['ir.attachment'].create({
                    'name': name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'store_fname': name,
                    'res_model': self._name,
                    'res_id': self.id,
                    'mimetype': 'application/pdf',
                    'public': True
                })
                return attachment
            except Exception as e:
                raise ValidationError(e)
        else:
            return self.env.ref('onpoint_monitor.act_onpoint_logger_report').report_action(self, data=data)


class OnpointLoggerRecapReport(models.AbstractModel):
    _name = 'report.onpoint_monitor.onpoint_logger_report_template'
    _template = 'onpoint_monitor.onpoint_logger_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['onpoint.logger.report'].browse(docids)

        timestamp = data['form']['timestamp']
        image_url = data['form']['image_url']
        logger = data['form']['logger']

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': self,
            'timestamp': timestamp,
            'image_url': image_url,
            'logger': logger
        }
