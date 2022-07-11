from odoo import models, fields, tools, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timezone, timedelta
from ftplib import FTP
import csv
import pandas as pd
import chardet
import math
import io
import logging

_logger = logging.getLogger(__name__)


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _inherit = ['onpoint.logger', 'onpoint.pointorange']

    # is_modbus = fields.Boolean(string='Use Modbus', default=False)
    modbus = fields.Selection([
        ('unavailable', 'Unavailable'),
        ('other', 'Other'),
        ('adam', 'Serial'),
    ], default='unavailable')
    count_logger_alarm = fields.Integer(compute='_count_logger_alarm')
    alarm_ids = fields.One2many('onpoint.logger.alarm', 'logger_id')
    employee_ids = fields.One2many('onpoint.logger.employee', 'logger_id')
    employee_ids = fields.Many2many('hr.employee', column1='logger_id', column2='employee_id', string='PIC')
    additional_ids = fields.One2many('onpoint.logger.additional', 'logger_id')

    def _count_logger_alarm(self):
        self.count_logger_alarm = self.env['onpoint.logger.alarm'].search_count([('logger_id', '=', self.id)])

    def _set_series(self, loggers, value_unit_ids, start_date, end_date):
        series, totalizers, events, is_totalizer = super(OnpointLogger, self)._set_series(loggers, value_unit_ids,
                                                                                          start_date, end_date)

        for event in events:
            if event["need_totalizer"]:
                channel = self.env['onpoint.logger.channel'].search([('id', '=', event['channel_id'])])
                if channel.totalizer_point_id:
                    totalizer_channel = self.env['onpoint.logger.channel'].search(
                        [('logger_id', '=', channel.logger_id.id),
                         ('point_id', '=', channel.totalizer_point_id.id)])
                    totalizer_value = self.env['onpoint.logger.value'].search(
                        [('channel_id', '=', totalizer_channel.id),
                         ('dates', '>=', start_date),
                         ('dates', '<=', end_date)],
                        order='dates desc',
                        limit=1)
                    event['last_totalizer'] = totalizer_value.channel_value

        return series, totalizers, events, is_totalizer

    # def read_ftp_pointorange(self):
    #
    #     points = self.env['onpoint.logger.point'].search([('owner', '=', 'pointorange')])
    #     channels = self.channel_ids
    #     value_ids = []
    #
    #     ftp = self.set_ftp_connection()
    #
    #     files = ftp.nlst()
    #
    #     logger_file = self.env['onpoint.logger.file'].search([('logger_id', '=', self.id)])
    #     logger_file.sudo().unlink()
    #
    #     for file_name in files:
    #         value_ids = []
    #         check_trending_file = self.identifier + '_T_' in file_name
    #         check_alarm_file = self.identifier + '_A_' in file_name
    #
    #         if check_trending_file:
    #             temp_file = io.StringIO()
    #             temp_filename = '/opt/odoo13/odoo-custom-addons/onpoint_pointorange/temps/temp.csv'
    #
    #             with open(temp_filename, 'wb') as f:
    #                 ftp.retrbinary('RETR ' + file_name, f.write)
    #
    #             df = pd.read_csv(temp_filename, engine='python')
    #             df = df.drop(df.columns[df.columns.str.contains('unnamed', case=False)], axis=1)
    #
    #             # Import to Database
    #             logger_file = self.import_to_database(points, file_name, df)
    #             ftp.rename(file_name, 'archives/' + file_name)
    #
    #     ftp.quit()
    #
    #     logger_files = self.env['onpoint.logger.file'].search([('logger_id', '=', self.id)])
    #
    #     for logger_file in logger_files:
    #         # Process Data in Temporary Table
    #         value_ids, channels = self.process_data(logger_file, channels, value_ids)
    #
    #         if read_ftp:
    #             temp_file.close()
    #             ftp.rename(file_name, 'archives/' + file_name)
    #
    #         # logger = self.env['onpoint.logger'].search([('id', '=', self.id)])
    #         # if value_ids:
    #         #     for value_id in value_ids:
    #         #         data = value_id[2]
    #         #         self.env['onpoint.logger.value'].create({
    #         #             'logger_id': logger.id,
    #         #             'channel_id': data.channel_id.id,
    #         #
    #         #         })
    #
    #             # logger.sudo().update({
    #             #     'value_ids': value_ids
    #             # })
    #
    #             # for channel in logger.channel_ids:
    #             #     if channel.value_type_id.need_totalizer and not channel.totalizer_point_id:
    #             #         channel.calculate_totalizer()

    def read_ftp_pointorange(self):

        points = self.env['onpoint.logger.point'].search([('owner', '=', 'pointorange')])

        ftp = self.set_ftp_connection()

        files = ftp.nlst()

        for file_name in files:
            value_ids = []
            channels = self.channel_ids
            check_trending_file = self.identifier + '_T_' in file_name
            check_alarm_file = self.identifier + '_A_' in file_name

            if check_trending_file:
                temp_file = io.StringIO()
                temp_filename = '/opt/odoo13/odoo-custom-addons/onpoint_pointorange/temps/temp.csv'

                size = ftp.size(file_name)
                if size > 0:
                    with open(temp_filename, 'wb') as f:
                        ftp.retrbinary('RETR ' + file_name, f.write)

                    df = pd.read_csv(temp_filename, engine='python', encoding='ISO-8859-1')
                    df = df.drop(df.columns[df.columns.str.contains('unnamed', case=False)], axis=1)

                    # Import to Database
                    logger_file = self.import_to_database(points, file_name, df)

                    # Process Data in Temporary Table
                    value_ids, channels = self.process_data(logger_file, channels, value_ids)

                    temp_file.close()
                    archive_file_name = file_name
                else:
                    now = datetime.now()
                    time = now.strftime("%H%M%S")
                    split_file_names = file_name.split(".")
                    archive_file_name = split_file_names[0] + '_' + time + '.' + split_file_names[1]

                ftp.rename(file_name, 'archives/' + archive_file_name)

            if value_ids:
                logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

                # logger.sudo().update({
                #     'value_ids': value_ids
                # })

                for channel in logger.channel_ids:
                    if channel.value_type_id.need_totalizer and not channel.totalizer_point_id:
                        channel.calculate_totalizer()

        ftp.quit()

    def read_ftp_archives_pointorange(self, target_file=None):

        points = self.env['onpoint.logger.point'].search([('owner', '=', 'pointorange')])
        ftp = self.set_ftp_connection()


        ftp.cwd('archives')

        files = ftp.nlst()

        for file_name in files:
            value_ids = []
            channels = self.channel_ids
            if not target_file:
                check_trending_file = self.identifier + '_T_' in file_name
                check_alarm_file = self.identifier + '_A_' in file_name
            else:
                check_trending_file = target_file in file_name

            if check_trending_file:
                temp_file = io.StringIO()
                temp_filename = '/opt/odoo13/odoo-custom-addons/onpoint_pointorange/temps/temp.csv'

                with open(temp_filename, 'wb') as f:
                    ftp.retrbinary('RETR ' + file_name, f.write)

                # ftp.retrbinary('RETR ' + file_name, temp_file.write)
                # temp_file.seek(0)
                # with open(temp_filename, 'r') as fr:
                #     coding = chardet.detect(fr).get('encoding')

                df = pd.read_csv(temp_filename, engine='python')
                df = df.drop(df.columns[df.columns.str.contains('unnamed', case=False)], axis=1)

                # csv_file = csv.DictReader(io.TextIOWrapper(temp_file, newline=None), delimiter=',')

                # Read from trending file csv
                # value_ids, channels = self.read_trending_file(df, points, value_ids, channels)

                # Import to Database
                logger_file = self.import_to_database(points, file_name, df)

                # Process Data in Temporary Table
                value_ids, channels = self.process_data(logger_file, channels, value_ids)

                temp_file.close()

            if value_ids:
                logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

                logger.sudo().update({
                    'value_ids': value_ids
                })

                for channel in logger.channel_ids:
                    if channel.value_type_id.need_totalizer and not channel.totalizer_point_id:
                        channel.calculate_totalizer()

        ftp.quit()

    def testing_ftp_connection(self):
        ftp_pointorange_host = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_host')
        ftp_pointorange_port = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_port')
        ftp_pointorange_username = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_username')
        ftp_pointorange_password = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_password')
        ftp_pointorange_folder = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_folder')

        ftp = FTP()
        ftp.connect(ftp_pointorange_host, int(ftp_pointorange_port))
        result = ftp.login(ftp_pointorange_username, ftp_pointorange_password)

        return result

    def set_ftp_connection(self):
        ftp_pointorange_host = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_host')
        ftp_pointorange_port = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_port')
        ftp_pointorange_username = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_username')
        ftp_pointorange_password = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_password')
        ftp_pointorange_folder = self.env['ir.config_parameter'].sudo().get_param(
            'onpoint_pointorange.ftp_pointorange_folder')

        ftp = FTP()
        ftp.connect(ftp_pointorange_host, int(ftp_pointorange_port))
        ftp.login(ftp_pointorange_username, ftp_pointorange_password)
        ftp.cwd(ftp_pointorange_folder)

        return ftp

    def import_to_database(self, points, file_name, df):
        logger_file = self.env['onpoint.logger.file'].sudo().create({
            'name': file_name,
            'logger_id': self.id
        })

        line_rows = []

        for key in df.keys():
            try:
                if key != 'Date & Time':
                    key_point = key[0:4]
                    point_id = points.filtered(lambda p: p.code_alt == key_point)

                    if point_id:
                        detail_rows = []
                        previous_value = False
                        previous_date = False
                        for index, row in df.iterrows():
                            logger_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                            logger_value = float(row[key])

                            if not math.isnan(logger_value):
                                if previous_value:
                                    logger_value_diff = logger_value - previous_value
                                    date_difference = logger_date - previous_date
                                    logger_date_diff = date_difference.total_seconds()
                                else:
                                    logger_value_diff = False
                                    logger_date_diff = False
                                previous_value = logger_value
                                previous_date = logger_date

                                detail_row = (0, 0, {
                                    'logger_date': logger_date,
                                    'logger_value': logger_value,
                                    'logger_value_diff': logger_value_diff,
                                    'logger_date_diff': logger_date_diff
                                })
                                detail_rows.append(detail_row)

                        line_row = (0, 0, {
                            'point_code': key_point,
                            'point_id': point_id.id,
                            'detail_ids': detail_rows
                        })
                        line_rows.append(line_row)
            except Exception as e:
                x = 1
                continue

        try:
            logger_file.sudo().update({
                'line_ids': line_rows
            })

            self.update_detail_date_diff(logger_file)
            self.update_detail_first_row(logger_file)

            logger_file = self.env['onpoint.logger.file'].search([('id', '=', logger_file.id)])

            return logger_file
        except Exception as e:
            x = 1
            return False

    def update_detail_date_diff(self, logger_file):
        line_ids = logger_file.line_ids
        for line in line_ids:
            detail = self.env['onpoint.logger.file.detail'].search([('logger_file_line_id', '=', line.id),
                                                                    ('logger_date_diff', '=', 0)])
            if detail:
                date_diff = self.env['onpoint.logger.file.detail'].search([('logger_file_line_id', '=', line.id),
                                                                           ('logger_date_diff', '>', 0)],
                                                                          order='id asc',
                                                                          limit=1)
                if date_diff:
                    detail.sudo().update({
                        'logger_date_diff': date_diff.logger_date_diff
                    })

    def update_detail_first_row(self, logger_file):
        line_ids = logger_file.line_ids
        for line in line_ids:
            if line.point_id.code_source:
                if line.point_id.code != line.point_id.code_source:
                    point_source = line_ids.filtered(lambda p: p.point_code == line.point_id.code_source_alt)

                    first_id = 0
                    for detail in line.detail_ids:
                        first_id = detail.id
                        break

                    index = 0
                    second_value = 0
                    for detail in point_source.detail_ids:
                        if index == 1:
                            second_value = detail.logger_value

                        index = index + 1
                        if index > 1:
                            break

                    first_row = self.env['onpoint.logger.file.detail'].search([('id', '=', first_id)])
                    first_row.update({
                        'logger_value_diff': second_value
                    })

    def process_data(self, logger_file, channels, value_ids):
        for line in logger_file.line_ids:
            channel = channels.filtered(lambda c: c.point_id.id == line.point_id.id)

            # If channel / points hasn't been created
            if not channel:
                channel = self.env['onpoint.logger.channel'].sudo().create({
                    'logger_id': self.id,
                    'brand_owner': 'pointorange',
                    'point_id': line.point_id.id,
                    'name': line.point_id.name,
                    'display_on_chart': False,
                    'show_channel': False
                })
                channels = self.channel_ids

            for detail in line.detail_ids:
                try:
                    if not math.isnan(detail.logger_value):
                        if channel.modbus == 'adam':
                            function_name = 'process_modbus_adam'
                        elif channel.modbus == 'other':
                            function_name = 'process_modbus_other'
                        else:
                            function_name = line.point_id.function_name_display

                        if function_name:
                            params = {
                                'channel': channel,
                                'detail': detail
                            }
                            value_date, value_channel, value_channel_formatted = getattr(self, function_name)(params)
                        else:
                            value_date = detail.logger_date
                            value_channel = detail.logger_value
                            value_channel_formatted = round(detail.logger_value, 3)

                        # if value_date and value_channel:
                        value_vals = {
                            'logger_id': self.id,
                            'channel_id': channel.id,
                            'dates': value_date,
                            'channel_value': round(value_channel, 3),
                            'channel_value_formatted': value_channel_formatted,
                            'value_type': 'trending'
                        }

                        logger_value = self.env['onpoint.logger.value'].sudo().create(value_vals)
                        self.env.cr.commit()

                        row_value = (0, 0, value_vals)
                        value_ids.append(row_value)
                except Exception as e:
                    raise ValidationError(e)
                    # continue

        return value_ids, channels

    def read_trending_file(self, df, points, value_ids, channels):
        totalizer = False
        columns = []

        for key in df.keys():
            if key == 'Date & Time':
                new_key = key
            else:
                new_key = key
            columns.append(new_key)

        previous_row = pd.DataFrame(columns=columns)

        for index, row in df.iterrows():
            # if index > 0:
            for key in df.keys():
                if row[key] != '':
                    key_point = key[0:4]
                    point_id = points.filtered(lambda p: p.code_source_alt == key_point)

                    # If exist in Points Map
                    if point_id:
                        value_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                        value_channel = float(row[key])
                        channel = channels.filtered(lambda c: c.point_id.id == point_id.id)

                        if not math.isnan(value_channel):
                            # If channel / points hasn't been created
                            if not channel:
                                channel = self.env['onpoint.logger.channel'].sudo().create({
                                    'logger_id': self.id,
                                    'point_id': point_id.id,
                                    'display_on_chart': False
                                })
                                channels = self.channel_ids

                            if channel.modbus == 'adam':
                                function_name = 'process_modbus_adam'
                            elif channel.modbus == 'other':
                                function_name = 'process_modbus_other'
                            else:
                                function_name = point_id.function_name

                            if function_name:
                                if key == 'AI01 ()':
                                    key_target = key
                                else:
                                    key_target = point_id.code_alt

                                params = {
                                    'key': key,
                                    'key_target': key_target,
                                    'channel': channel,
                                    'current_row': row,
                                    'previous_row': previous_row,
                                }
                                value_date, value_channel = getattr(self, function_name)(params)

                            if value_date and value_channel:
                                if channel.value_type_id.need_totalizer:
                                    if totalizer:
                                        totalizer += value_channel
                                    else:
                                        totalizer = channel.last_totalizer + value_channel

                                    value_vals = {
                                        'channel_id': channel.id,
                                        'dates': value_date,
                                        'channel_value': value_channel,
                                        'totalizer': totalizer,
                                        'value_type': 'trending'
                                    }

                                else:
                                    value_vals = {
                                        'channel_id': channel.id,
                                        'dates': value_date,
                                        'channel_value': value_channel,
                                        'value_type': 'trending'
                                    }

                                row_value = (0, 0, value_vals)
                                value_ids.append(row_value)

            previous_row = row

        return value_ids, channels

    def read_trending_file2(self, csv_file, points, value_ids, channels):
        previous_row = False
        totalizer = False
        value_vals = False
        for row in csv_file:
            for key in row:
                if key is not None and key != '':
                    if row[key] != '':
                        key_point = key[0:4]
                        point_id = points.filtered(lambda p: p.code_source_alt == key_point)

                        # If exist in Points Map
                        if point_id:
                            value_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                            value_channel = float(row[key])
                            channel = channels.filtered(lambda c: c.point_id.id == point_id.id)

                            # If channel / points hasn't been created
                            if not channel:
                                channel = self.env['onpoint.logger.channel'].sudo().create({
                                    'logger_id': self.id,
                                    'point_id': point_id.id,
                                })
                                channels = self.channel_ids

                            if channel.modbus == 'adam':
                                function_name = 'process_modbus_adam'
                            else:
                                function_name = point_id.function_name

                            if function_name:
                                params = {
                                    'key': key,
                                    'key_target': point_id.code_alt,
                                    'channel': channel,
                                    'current_row': row,
                                    'previous_row': previous_row,
                                }
                                value_date, value_channel = getattr(self, function_name)(params)

                            if value_date:
                                if point_id.need_totalizer:
                                    if totalizer:
                                        totalizer += value_channel
                                    else:
                                        totalizer = channel.last_totalizer + value_channel

                                    value_vals = {
                                        'channel_id': channel.id,
                                        'dates': value_date,
                                        'channel_value': value_channel,
                                        'totalizer': totalizer,
                                        'value_type': 'trending'
                                    }

                                else:
                                    value_vals = {
                                        'channel_id': channel.id,
                                        'dates': value_date,
                                        'channel_value': value_channel,
                                        'value_type': 'trending'
                                    }

                                row_value = (0, 0, value_vals)
                                value_ids.append(row_value)

                previous_row = row
        return value_ids, channels

    def set_main_alarm(self, logger_id, start_date, end_date):
        main_alarms = super(OnpointLogger, self).set_main_alarm(logger_id, start_date, end_date)

        state_battery = main_alarms['state_battery']
        state_external = main_alarms['state_external']
        state_signal = main_alarms['state_signal']
        state_submerged = main_alarms['state_submerged']
        state_temperature = main_alarms['state_temperature']

        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        channels = logger.channel_ids.search([('logger_id', '=', logger_id), ('point_id.alarm_type', '!=', False)])

        for channel in channels:

            last_value = channel.value_ids.search([('channel_id', '=', channel.id), ('dates', '<=', end_date)],
                                                  order='dates desc',
                                                  limit=1)

            alarm_count = channel.value_ids.search_count([('channel_id', '=', channel.id),
                                                          ('dates', '>=', start_date),
                                                          ('dates', '<=', end_date),
                                                          ('value_type', '=', 'alarm')])

            function_name_display = channel.point_id.function_name_display

            if last_value:
                value_type = last_value.value_type

                if function_name_display:
                    params = {
                        'value': last_value.channel_value,
                        'channel': channel
                    }
                    last_channel_value = getattr(self, function_name_display)(params)
                else:
                    last_channel_value = last_value.channel_value

                alarm_threshold = self.env['onpoint.alarm.threshold'].search(
                    [('alarm_type', '=', channel.point_id.alarm_type)])

                if channel.point_id.alarm_type == 'battery':
                    if value_type == 'trending':
                        state_battery['src'] = 'icon_battery_full.png'
                    else:
                        state_battery['src'] = 'icon_battery_empty.png'

                    state_battery['enable'] = True
                    state_battery['last_date'] = last_value.dates
                    state_battery['last_value'] = last_channel_value
                    state_battery['alarm_events'] = alarm_count

                    if alarm_threshold.normal_min <= last_channel_value <= alarm_threshold.normal_max:
                        state_battery['src'] = 'icon_battery_full.png'
                        state_battery['message'] = 'Battery in Full Capacity'
                    elif alarm_threshold.medium_min <= last_channel_value <= alarm_threshold.medium_max:
                        state_battery['src'] = 'icon_battery_half.png'
                        state_battery['message'] = 'Battery is in Half capacity'
                    elif last_channel_value <= alarm_threshold.danger_max:
                        state_battery['src'] = 'icon_battery_empty.png'
                        state_battery['message'] = 'Battery is Weak, Please replace the battery'
                    else:
                        state_battery['src'] = 'icon_battery_disable.png'

                if channel.point_id.alarm_type == 'external':

                    state_external['enable'] = True
                    state_external['last_date'] = last_value.dates
                    state_external['last_value'] = last_channel_value
                    state_external['alarm_events'] = alarm_count

                    if alarm_threshold.normal_min <= last_channel_value >= alarm_threshold.normal_max:
                        state_external['src'] = 'icon_external_power_empty.png'
                        state_external['message'] = 'External Power Weak Voltage'
                    elif alarm_threshold.medium_min <= last_channel_value >= alarm_threshold.medium_max:
                        state_external['src'] = 'icon_external_power_half.png'
                        state_external['message'] = 'External Power Half Voltage'
                    elif alarm_threshold.danger_min <= last_channel_value >= alarm_threshold.danger_max:
                        state_external['src'] = 'icon_external_power.png'
                        state_external['message'] = 'External Power Full Voltage'
                    else:
                        state_external['src'] = 'icon_external_power_disable.png'

                if channel.point_id.alarm_type == 'signal':
                    if value_type == 'trending':
                        state_signal['src'] = 'icon_signal_full.png'
                    else:
                        state_signal['src'] = 'icon_signal_empty.png'

                    state_signal['enable'] = True
                    state_signal['last_date'] = last_value.dates
                    state_signal['last_value'] = last_channel_value
                    state_signal['alarm_events'] = alarm_count

                    last_channel_value_float = float(last_channel_value[0:-4])

                    if alarm_threshold.signal_excellent_min >= last_channel_value_float >= alarm_threshold.signal_excellent_max:
                        state_signal['src'] = 'icon_signal_excellent.png'
                        state_signal['message'] = 'Signal is Excellent'
                    elif alarm_threshold.signal_good_min >= last_channel_value_float >= alarm_threshold.signal_good_max:
                        state_signal['src'] = 'icon_signal_good.png'
                        state_signal['message'] = 'Signal is Good'
                    elif alarm_threshold.signal_fair_min >= last_channel_value_float >= alarm_threshold.signal_fair_max:
                        state_signal['src'] = 'icon_signal_fair.png'
                        state_signal['message'] = 'Signal is Fair'
                    elif alarm_threshold.signal_poor_min >= last_channel_value_float >= alarm_threshold.signal_poor_max:
                        state_signal['src'] = 'icon_signal_poor.png'
                        state_signal['message'] = 'Signal is Poor. Please check!'
                    elif alarm_threshold.signal_nosignal_min >= last_channel_value_float > alarm_threshold.signal_nosignal_max:
                        state_signal['src'] = 'icon_signal_nosignal.png'
                        state_signal['message'] = 'Signal is Lost. Please check!'
                    else:
                        # state_signal['src'] = 'icon_signal_disable.png'
                        state_signal['src'] = 'icon_signal_nosignal.png'
                        state_signal['message'] = 'Signal Disable'

                if channel.point_id.alarm_type == 'submerged':
                    if last_value.channel_value == 0:
                        state_submerged['src'] = 'icon_over_water.png'
                    else:
                        state_submerged['src'] = 'icon_under_water.png'

                    state_submerged['enable'] = True
                    state_submerged['last_date'] = last_value.dates
                    state_submerged['last_value'] = last_channel_value
                    state_submerged['alarm_events'] = alarm_count

                if channel.point_id.alarm_type == 'temperature':
                    if value_type == 'trending':
                        state_temperature['src'] = 'icon_temperature_normal.png'
                    else:
                        state_temperature['src'] = 'icon_temperature_danger.png'

                    state_temperature['enable'] = True
                    state_temperature['last_date'] = last_value.dates
                    state_temperature['last_value'] = last_channel_value
                    state_temperature['alarm_events'] = alarm_count

                    if alarm_threshold.normal_min <= last_channel_value <= alarm_threshold.normal_max:
                        state_temperature['src'] = 'icon_temperature_normal.png'
                        state_temperature['message'] = 'Temperature is in Normal Level'
                    elif alarm_threshold.medium_min <= last_channel_value <= alarm_threshold.medium_max:
                        state_temperature['src'] = 'icon_temperature_warning.png'
                        state_temperature['message'] = 'Temperature above Normal Level'
                    elif alarm_threshold.danger_min <= last_channel_value <= alarm_threshold.danger_max:
                        state_temperature['src'] = 'icon_temperature_danger.png'
                        state_temperature['message'] = 'Temperature is in Danger Level. Please Check!'
                    else:
                        state_temperature['src'] = 'icon_temperature_disable.png'
                        state_temperature['message'] = 'Temperature Disable'

        data = {
            'state_battery': state_battery,
            'state_external': state_external,
            'state_signal': state_signal,
            'state_submerged': state_submerged,
            'state_temperature': state_temperature,
        }

        return data

    def read_ftp_pointorange_alarm(self):

        # points = self.env['onpoint.logger.point'].search([('owner', '=', 'pointorange')])
        channels = self.channel_ids

        ftp = self.set_ftp_connection()

        files = ftp.nlst()

        alarm_message = ''
        for file_name in files:
            value_ids = []
            value_alarms = []
            check_alarm_file = self.identifier + '_A_' in file_name

            if check_alarm_file:
                temp_file = io.StringIO()
                temp_filename = '/opt/odoo13/odoo-custom-addons/onpoint_pointorange/temps/temp.csv'

                with open(temp_filename, 'wb') as f:
                    ftp.retrbinary('RETR ' + file_name, f.write)

                df = pd.read_csv(temp_filename, engine='python')
                df = df.drop(df.columns[df.columns.str.contains('unnamed', case=False)], axis=1)

                for index, row in df.iterrows():
                    # if index > 0:
                    col_point = row['Point']
                    # point_id = points.filtered(lambda p: p.code_alt == col_point)
                    point_id = self.env['onpoint.logger.point'].search([('code', '=', col_point)])

                    if point_id:
                        channel = channels.filtered(lambda c: c.point_id.id == point_id.id)
                        value_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                        if channel.source_value_unit_id.name == 'm3/h':
                            current_source_value = row['Value'] / 3.6
                        elif channel.source_value_unit_id.name == 'm3/s' and channel.value_unit_id.name == 'l/s':
                            current_source_value = row['Value'] * 1000
                        else:
                            current_source_value = row['Value']

                        value_channel = float(current_source_value)

                        # if channel.modbus == 'adam':
                        #     function_name = 'process_modbus_adam'
                        # elif channel.modbus == 'other':
                        #     function_name = 'process_modbus_other'
                        # else:
                        #     function_name = point_id.function_name

                        # if function_name:
                        #     key_target = point_id.code_alt
                        #
                        #     params = {
                        #         'key': col_point,
                        #         'key_target': col_point,
                        #         'channel': channel,
                        #         'current_row': row
                        #     }
                        #     value_date, value_channel = getattr(self, function_name)(params)

                        if value_date:
                            value_vals = {
                                'channel_id': channel.id,
                                'dates': value_date,
                                'channel_value': value_channel,
                                'value_type': 'alarm'
                            }
                            row_value = (0, 0, value_vals)
                            value_ids.append(row_value)

                            value_alarm = {
                                'logger_id': self.id,
                                'channel_id': channel.id,
                                'alarm_date': value_date,
                                'alarm_value': value_channel
                            }

                            # row_alarm = (0, 0, value_alarm)
                            value_alarms.append(value_alarm)

                temp_file.close()
                ftp.rename(file_name, 'archives/' + file_name)

            if value_ids:
                logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

                logger.sudo().update({
                    'value_ids': value_ids
                })

                # alarm_message = self.env['onpoint.logger.alarm'].insert_alarm(value_alarms, alarm_message)

        ftp.quit()

    def read_alarm_file(self, csv_file, points, value_ids, channels):
        for row in csv_file:
            if row['Point'] != '':
                point_id = points.filtered(lambda p: p.code == row['Point'])

                if point_id:
                    channel = channels.filtered(lambda c: c.point_id.id == point_id.id)

                    # If channel / points hasn't been created
                    if not channel:
                        channel = self.env['onpoint.logger.channel'].sudo().create({
                            'logger_id': self.id,
                            'point_id': point_id.id,
                        })
                        channels = self.channel_ids

                    value_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                    value_vals = {
                        'channel_id': channel.id,
                        'dates': value_date,
                        'channel_value': float(row['Value']),
                        'value_type': 'alarm'
                    }
                    row_value = (0, 0, value_vals)
                    value_ids.append(row_value)

        return value_ids, channels

    @api.model
    def check_for_alarm(self, pos):
        points = self.env['onpoint.logger.point'].search([('owner', '=', 'pointorange')])
        return points

    def action_to_logger_alarm(self):
        action = self.env.ref('onpoint_pointorange.act_onpoint_logger_alarm')
        result = action.read()[0]

        alarm_ids = self.mapped('alarm_ids')

        if not alarm_ids or len(alarm_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (alarm_ids.ids)
        elif len(alarm_ids) == 1:
            res = self.env.ref('onpoint_pointorange.view_onpoint_logger_alarm_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = alarm_ids.id
        return result


class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    _inherit = ['onpoint.logger.channel', 'onpoint.pointorange']

    modbus = fields.Selection([
        ('unavailable', 'Unavailable'),
        ('other', 'Other'),
        ('adam', 'Serial'),
    ], default='unavailable')
    totalizer_point_id = fields.Many2one('onpoint.logger.point', string='Consumption', index=True)
    initial = fields.Float(string='Pulse', default=1)
    pulse = fields.Float(string='Pulse', default=1)
    conversion = fields.Float(string='Conversion', default=1)
    imin = fields.Float(string='IMIN', default=100)
    imax = fields.Float(string='IMAX', default=508)
    omin = fields.Float(string='OMIN', default=0)
    omax = fields.Float(string='OMAX', default=10)
    source_value_unit_id = fields.Many2one('onpoint.value.unit', string='Channel Source Unit', index=True)
    message = fields.Char(string='message')

    def _compute_last_value(self, logger_id, start_date, end_date):
        for record in self:
            last_value = record.value_ids.search([('channel_id', '=', record.id)], order='dates desc', limit=1)
            last_channel_value = round(last_value.channel_value, 3)

            # function_name_display = record.point_id.function_name_display
            # if function_name_display:
            #     params = {
            #         'value': last_value.channel_value,
            #         'channel': record
            #     }
            #     last_channel_value = getattr(self, function_name_display)(params)

            record.last_date = last_value.dates
            record.last_value = last_channel_value
            record.last_value_type = last_value.value_type

            main_alarms = self.pool.get('onpoint.logger').set_main_alarm(self, logger_id, start_date, end_date)

    def _compute_last_totalizer(self):
        for record in self:
            record.last_totalizer = 0
            if record.value_type_id.need_totalizer:
                if record.modbus != 'unavailable':
                    totalizer_point = self.env['onpoint.logger.channel'].search(
                        [('logger_id', '=', record.logger_id.id),
                         ('point_id', '=', record.totalizer_point_id.id)])
                    if totalizer_point:
                        record.last_totalizer = totalizer_point.last_value
                else:
                    last_totalizer = record.value_ids.search([('channel_id', '=', record.id)], order='dates desc',
                                                             limit=1)
                    if last_totalizer:
                        record.last_totalizer = last_totalizer.totalizer

    def check_initial_totalizer(self, previous_date, previous_totalizer, current_date):
        last_initial = self.env['onpoint.logger.initial'].search([('channel_id', '=', self.id),
                                                                  ('dates', '<', current_date)],
                                                                 order='dates desc',
                                                                 limit=1)
        totalizer = 0
        if last_initial:
            if previous_date:
                if last_initial.dates >= previous_date:
                    totalizer = last_initial.initial
                else:
                    totalizer = previous_totalizer
            else:
                totalizer = last_initial.initial

        return totalizer

    def calculate_totalizer(self):
        totalizer = 0

        values = self.env['onpoint.logger.value'].search([('channel_id', '=', self.id)],
                                                         order='dates asc')

        initial_ids = []
        totalizer = 0
        add_hours = self.logger_id.get_time_zone(self.logger_id.id)
        last_initial_id = 0
        last_initial_date = '1900-01-01 00:00:00'

        for value in values:
            replace_channel_value = False
            channel_value = value.channel_value
            # channel_dates = (value.dates + timedelta(hours=add_hours)).strftime('%Y-%m-%d %H:%M:%S')
            channel_dates = value.dates.strftime('%Y-%m-%d %H:%M:%S')
            if self.value_unit_id.name == 'l/s':
                channel_value = (value.channel_value * self.interval) / 1000

            initial = self.env['onpoint.logger.initial'].search([('channel_id', '=', self.id),
                                                                 ('id', 'not in', initial_ids),
                                                                 ('dates', '>', last_initial_date),
                                                                 ('dates', '<=', channel_dates)],
                                                                order='dates desc',
                                                                limit=1)
            if initial:
                initial_ids.append(initial.id)
                last_initial_id = initial.id
                last_initial_date = channel_dates
                totalizer = initial.initial
                replace_channel_value = True

                # if initial.dates == value.dates:
                #     replace_channel_value = True

            if not replace_channel_value:
                totalizer += channel_value

            value.sudo().write({
                'totalizer': totalizer
            })


    # def calculate_totalizer(self):
    #     totalizer = 0
    #
    #     last_initial = self.env['onpoint.logger.initial'].search([('channel_id', '=', self.id)], order='dates desc',
    #                                                              limit=1)
    #     last_row = self.env['onpoint.logger.value'].search([('channel_id', '=', self.id),
    #                                                         ('totalizer', '>', 0)],
    #                                                        order='dates desc',
    #                                                        limit=1)
    #
    #     initial_date = datetime.strptime('1970-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    #     initial_value = 0
    #     if last_initial:
    #         initial_date = last_initial.dates
    #         initial_value = last_initial.initial
    #
    #     previous_date = False
    #     if last_row:
    #         if initial_date > last_row.dates:
    #             totalizer = initial_value
    #         else:
    #             totalizer = last_row.totalizer
    #             previous_date = last_row.dates
    #     else:
    #         totalizer = initial_value
    #
    #     logger_values = self.env['onpoint.logger.value'].search([('channel_id', '=', self.id),
    #                                                              ('totalizer', '=', 0)],
    #                                                             order='dates asc')
    #
    #     for logger_value in logger_values:
    #         if previous_date:
    #             date_difference = logger_value.dates - previous_date
    #             interval = date_difference.total_seconds()
    #
    #             channel_value = logger_value.channel_value
    #             if self.value_unit_id.name == 'l/s':
    #                 channel_value = (logger_value.channel_value * interval) / 1000
    #
    #             totalizer = self.check_initial_totalizer(previous_date=previous_date,
    #                                                      previous_totalizer=totalizer,
    #                                                      current_date=logger_value.dates)
    #
    #             totalizer = totalizer + channel_value
    #         else:
    #             totalizer = self.check_initial_totalizer(previous_date=last_row.dates,
    #                                                      previous_totalizer=last_row.totalizer,
    #                                                      current_date=logger_value.dates)
    #
    #         previous_date = logger_value.dates
    #
    #         logger_value.sudo().update({
    #             'totalizer': totalizer
    #         })

    def action_calculate_totalizer(self):
        self.calculate_totalizer()

    def action_read_archives_pointorange(self):
        previous = datetime.now() - timedelta(days=1)
        previous_date_string = previous.strftime('%Y%m%d')
        previous_date = datetime.strptime(previous.strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        previous_file_name = self.logger_id.identifier + '_T_' + previous_date_string

        today = datetime.now()
        today_date_string = today.strftime('%Y%m%d')
        today_date = datetime.strptime(today.strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        today_file_name = self.logger_id.identifier + '_T_' + today_date_string

        logger_values = self.env['onpoint.logger.value'].search([('channel_id', '=', self.id),
                                                                 ('dates', '>=', previous_date)])
        logger_values.sudo().unlink()

        self.logger_id.read_ftp_archives_pointorange(previous_file_name)
        self.logger_id.read_ftp_archives_pointorange(today_file_name)


class OnpointLoggerValue(models.Model):
    _name = 'onpoint.logger.value'
    _inherit = ['onpoint.logger.value']

    channel_value_formatted = fields.Char(string='Formatted Value')
    alarm_sent = fields.Boolean(default=False)

    def reset_totalizer(self):
        self.update({
            'totalizer': 0
        })
        x = 1


class OnpointViewLoggerThreshold(models.Model):
    _name = 'onpoint.vw.logger.threshold'
    _auto = False

    logger_id = fields.Many2one('onpoint.logger', index=True, readonly=True)
    threshold_type = fields.Char(index=True, readonly=True)
    threshold = fields.Float(readonly=True)
    channel_id = fields.Many2one('onpoint.logger.channel', index=True, readonly=True)
    channel_value_id = fields.Many2one('onpoint.logger.value', index=True, readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
                create or replace view onpoint_vw_logger_threshold as (                 

                    select
                        row_number() over() as id,
                        x.logger_id,
                        x.threshold_type,
                        x.threshold,
                        x.channel_id,
                        (
                            select
                                olv.id
                            from
                                onpoint_logger_value olv
                            where
                                x.channel_id = olv.channel_id
                            order by olv.dates desc
                            limit 1 
                        ) as channel_value_id
                    from
                    (

                        select
                            'overrange' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.overrange_enabled ,
                            olt.overrange_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.overrange_enabled = true
                        union all
                        select
                            'hihi' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.hi_hi_enabled ,
                            olt.hi_hi_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.hi_hi_enabled = true
                        union all
                        select
                            'hi' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.hi_enabled ,
                            olt.hi_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.hi_enabled = true
                        union all
                        select
                            'underrange' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.underrange_enabled ,
                            olt.underrange_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.underrange_enabled = true 
                        union all
                        select
                            'lolo' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.lo_lo_enabled,
                            olt.lo_lo_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.lo_lo_enabled = true 
                        union all
                        select
                            'lo' as threshold_type,
                            ol.id as logger_id,
                            olc.id as channel_id,
                            olt.lo_enabled ,
                            olt.lo_threshold as threshold
                        from
                            onpoint_logger ol
                            inner join onpoint_logger_channel olc on ol.id = olc .logger_id
                            inner join onpoint_logger_threshold olt on olc.id = olt.id
                        where
                            ol.state = 'enabled' and olt.lo_enabled = true
                    ) x
                )
                """
        self.env.cr.execute(sql)

    def send_alarm(self):

        for record in self:
            logger = record.logger_id
            logger_channel = record.channel_id
            logger_value = record.channel_value_id
            channel_name = logger_channel.name if logger_channel.name else logger_channel.point_id.name

            if not logger_value.alarm_sent:
                message = ""
                if record.threshold_type == 'hi' and logger_value.channel_value >= record.threshold:
                    message = "ALARM - High Threshold\n"
                elif record.threshold_type == 'lo' and logger_value.channel_value <= record.threshold:
                    message = "ALARM - Lo Threshold\n"

                if message != "":
                    message = message + logger.name + "\n"
                    message = message + channel_name + " : " + str(
                        logger_value.channel_value) + ' ' + logger_channel.value_unit_name + "\n"
                    message = message + logger.convert_to_localtime(logger.id, logger_value.dates)

                    params = {
                        'logger_id': logger.id,
                        'message': message
                    }

                    record.send(params)

                    logger_value.update({
                        'alarm_sent': True
                    })

    def send(self, params):
        pics = self.env['onpoint.logger.message'].search([('logger_id', '=', params['logger_id']),
                                                          ('is_active', '=', True),
                                                          ('send_sms', '=', True)])

        for pic in pics:
            message_params = {
                'send_to': pic.mobile_phone,
                'message': params['message'],
                'send_sms': True,
                'send_wa': False
            }

            response_data_sms, response_data_wa = pic.send_message(message_params)

            if response_data_sms:
                cost = 0
                if response_data_sms['status'] == '1':
                    cost = response_data_sms['cost']

                outbox = {
                    'logger_message_id': pic.id,
                    'logger_id': pic.logger_id.id,
                    'message_type': 'summary',
                    'media': 'sms',
                    'message_id': response_data_sms['messageId'],
                    'send_to': pic.mobile_phone,
                    'message': params['message'],
                    'state': response_data_sms['status'],
                    'text_response': response_data_sms['text'],
                    'cost': cost
                }
                self.env['onpoint.logger.outbox'].create(outbox)


class OnpointLoggerAdditional(models.Model):
    _name = 'onpoint.logger.additional'

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    logger_channel_id = fields.Many2one('onpoint.logger.channel', required=True, index=True, domain="[('logger_id', '=', parent.id)]")
    message_on = fields.Char()
    message_off = fields.Char()

