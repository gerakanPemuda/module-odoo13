from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
_logger = logging.getLogger(__name__)


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _inherit = ['onpoint.logger', 'onpoint.seba']

    is_realtime = fields.Boolean(string='Realtime', default=False)

    def read_ftp_seba(self):

        ftp_seba_host = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_host')
        ftp_seba_port = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_port')
        ftp_seba_username = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_username')
        ftp_seba_password = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_password')
        ftp_seba_folder = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_folder')

        ftp = FTP()
        ftp.connect(ftp_seba_host, int(ftp_seba_port))
        ftp.login(ftp_seba_username, ftp_seba_password)
        data = []
        ftp.cwd(ftp_seba_folder)

        folder_name = str(self.identifier).zfill(8)

        if folder_name in ftp.nlst():
            ftp.cwd(folder_name)

            files = ftp.nlst()
            if 'archives' not in files:
                ftp.mkd('archives')

            value_ids = []

            for file_name in files:
                check_file_name = 'measdata_' in file_name
                if check_file_name:
                    temp_file = io.BytesIO()

                    ftp.retrbinary('RETR ' + file_name, temp_file.write)
                    temp_file.seek(0)

                    stream_data = temp_file.read()

                    buffer = temp_file.getbuffer()

                    if len(buffer) > 0:
                        try:
                            data = self._process_block1(buffer)

                            channel_values = self._process_block7(buffer, data)

                            for channel in self.channel_ids:
                                realtime_values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel.id),
                                                                                          ('value_type', '=', 'realtime')])
                                realtime_values.sudo().unlink()

                                idx = 0
                                for channel_value in channel_values:
                                    value_date = datetime.strptime(channel_value['dates'], '%Y-%m-%d %H:%M:%S')
                                    value_vals = {
                                        'channel_id': channel.id,
                                        'dates': value_date,
                                        'channel_value': channel_value[channel.point_id.code],
                                        'value_type': 'trending'
                                    }

                                    row_value = (0, 0, value_vals)
                                    value_ids.append(row_value)
                        except Exception as e:
                            continue

                    ftp.rename(file_name, 'archives/' + file_name)

            logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

            logger.sudo().update({
                'value_ids': value_ids
            })

        ftp.quit()

    def act_read_realtime(self):
        channel_ids = []
        for channel in self.channel_ids:
            channel_ids.append(channel.id)

        ftp_seba_host = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_host')
        ftp_seba_port = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_port')
        ftp_seba_username = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_username')
        ftp_seba_password = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_password')
        ftp_seba_folder = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_folder')

        ftp = FTP()
        ftp.connect(ftp_seba_host, int(ftp_seba_port))
        ftp.login(ftp_seba_username, ftp_seba_password)
        ftp.cwd(ftp_seba_folder)

        folder_name = str(self.identifier).zfill(8)

        if folder_name in ftp.nlst():
            ftp.cwd(folder_name)

            files = ftp.nlst()
            value_ids = []

            for file_name in files:
                check_file_name = 'data.txt' in file_name
                if check_file_name:
                    lines = []
                    ftp.retrlines('RETR ' + file_name, lines.append)

                    line_number = 1
                    line_channel_number = 3

                    start_date = int(lines[1]) - 90000
                    number_of_channels = int(lines[2])

                    idx_start = 3 + number_of_channels
                    idx_end = idx_start + (number_of_channels - 1)
                    idx_interval = idx_end + 1

                    intervals = str(lines[idx_interval]).split('=')
                    interval = int(intervals[1])

                    idx_now = idx_start
                    yAxis_count = 0
                    idx = 0

                    while idx_now <= idx_end:
                        channel = self.env['onpoint.logger.channel'].search([('id', '=', channel_ids[idx])])
                        realtime_values = str(lines[idx_now]).split(',')

                        channel_values = []
                        # value_date = start_date * 1000
                        value_date = start_date

                        last_date = ''
                        last_value = 0

                        for realtime_value in realtime_values:
                            realtime_timestamp = datetime.fromtimestamp(value_date)
                            if channel.last_date < realtime_timestamp:
                                realtime_date = datetime.fromtimestamp(value_date).strftime('%Y-%m-%d %H:%M:%S')

                                data_val = [value_date, float(realtime_value)]
                                channel_values.append(data_val)

                                value_vals = {
                                    'logger_id': self.id,
                                    'channel_id': channel_ids[idx],
                                    'dates': realtime_date,
                                    'channel_value': float(realtime_value),
                                    'value_type': 'realtime'
                                }

                                # row_value = (0, 0, value_vals)
                                value_ids.append(value_vals)

                            value_date = value_date + interval

                        idx_now = idx_now + 1
                        idx = idx + 1

            self.env['onpoint.logger.value'].sudo().create(value_ids)
            self.env.cr.commit()

        ftp.quit()

        return True

    # @api.model
    # def get_realtime_data(self, logger_id):
    #
    #     yAxis = []
    #     series = []
    #     events = []
    #     yAxis_count = 0
    #     opposite = False
    #
    #     logger_data = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)
    #
    #     channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id)])
    #
    #     channel_params = {}
    #     value_units = []
    #
    #     idx = 0
    #     for channel in channels:
    #
    #         last_date = ''
    #         last_value = 0
    #
    #         value_units.append(channel.value_unit_id.name)
    #
    #         channel_params[idx] = {
    #             'value_type_name': channel.value_type_id.name,
    #             'color': channel.color,
    #             'value_unit_name': channel.value_unit_id.name
    #         }
    #
    #         yAxis_data = self._set_yAxis(channel, opposite)
    #
    #         other_index = value_units.index(channel.value_unit_id.name)
    #         if other_index != idx:
    #             yAxis_data.update({
    #                 'linkedTo': other_index
    #             })
    #
    #         yAxis.append(yAxis_data)
    #
    #         if opposite:
    #             opposite = False
    #         else:
    #             opposite = True
    #
    #         idx = idx + 1
    #
    #     _logger.debug('Value Units  %s ', value_units)
    #
    #     ftp_seba_host = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_host')
    #     ftp_seba_port = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_port')
    #     ftp_seba_username = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_username')
    #     ftp_seba_password = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_password')
    #     ftp_seba_folder = self.env['ir.config_parameter'].sudo().get_param('onpoint_seba.ftp_seba_folder')
    #
    #     ftp = FTP()
    #     ftp.connect(ftp_seba_host, int(ftp_seba_port))
    #     ftp.login(ftp_seba_username, ftp_seba_password)
    #     ftp.cwd(ftp_seba_folder)
    #
    #     folder_name = str(self.identifier).zfill(8)
    #
    #     if folder_name in ftp.nlst():
    #         ftp.cwd(folder_name)
    #
    #         files = ftp.nlst()
    #         value_ids = []
    #
    #         for file_name in files:
    #             check_file_name = 'data.txt' in file_name
    #             if check_file_name:
    #                 lines = []
    #                 ftp.retrlines('RETR ' + file_name, lines.append)
    #
    #                 line_number = 1
    #                 line_channel_number = 3
    #
    #                 start_date = int(lines[1])
    #                 number_of_channels = int(lines[2])
    #
    #                 idx_start = 3 + number_of_channels
    #                 idx_end = idx_start + (number_of_channels - 1)
    #                 idx_interval = idx_end + 1
    #
    #                 intervals = str(lines[idx_interval]).split('=')
    #                 interval = int(intervals[1])
    #
    #                 idx_now = idx_start
    #                 yAxis_count = 0
    #                 idx = 0
    #
    #                 while idx_now <= idx_end:
    #                     realtime_values = str(lines[idx_now]).split(',')
    #
    #                     channel_values = []
    #                     value_date = start_date * 1000
    #
    #                     last_date = ''
    #                     last_value = 0
    #
    #                     for realtime_value in realtime_values:
    #                         data_val = [value_date, float(realtime_value)]
    #                         channel_values.append(data_val)
    #
    #                         last_date = value_date
    #                         last_value = float(realtime_value)
    #
    #                         value_date = value_date + interval
    #
    #                     series_data = self._set_series(channel_params[idx]['value_type_name'], yAxis_count,
    #                                                    channel_params[idx]['color'], channel_values,
    #                                                    channel_params[idx]['value_unit_name'])
    #                     series.append(series_data)
    #
    #                     data_event = {
    #                         'name': channel_params[idx]['value_type_name'],
    #                         'unit_name': channel_params[idx]['value_unit_name'],
    #                         'last_date': last_date,
    #                         'last_value': last_value,
    #                     }
    #                     events.append(data_event)
    #
    #                     idx_now = idx_now + 1
    #                     idx = idx + 1
    #
    #     ftp.quit()
    #
    #     data = {
    #         'id': logger_data.id,
    #         'name': logger_data.name,
    #         'yAxis': yAxis,
    #         'series': series,
    #         'events': events
    #     }
    #
    #     return data


class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    _inherit = ['onpoint.logger.channel']

    last_value_type = fields.Selection([
        ('trending', 'Trending'),
        ('alarm', 'Alarm'),
        ('realtime', 'Realtime')
    ], compute='_compute_last_value', store=True)


class OnpointLoggerValue(models.Model):
    _name = 'onpoint.logger.value'
    _inherit = ['onpoint.logger.value']

    value_type = fields.Selection([
        ('trending', 'Trending'),
        ('alarm', 'Alarm'),
        ('realtime', 'Realtime')
    ], default='trending', index=True)
