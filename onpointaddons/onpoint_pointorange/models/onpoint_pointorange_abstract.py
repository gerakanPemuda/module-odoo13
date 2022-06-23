from odoo import models, fields, api, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging

_logger = logging.getLogger(__name__)


class OnpointPointorange(models.AbstractModel):
    _name = 'onpoint.pointorange'
    _description = 'Point Orange Driver'

    def process_counter(self, params):
        result_channel_value = False
        result_date_value = False

        channel = params['channel']
        detail = params['detail']

        interval = detail.logger_date_diff
        if interval == 0:
            interval = channel.interval

        result_channel_value = self.process_flow(detail.logger_value_diff,
                                                 channel.pulse,
                                                 interval,
                                                 channel.conversion)
        result_date_value = detail.logger_date

        return result_date_value, result_channel_value, result_channel_value

    def process_trend_delta(self, params):
        result_channel_value = False
        result_date_value = False

        channel = params['channel']
        detail = params['detail']

        interval = detail.logger_date_diff
        if interval == 0:
            interval = channel.interval

        result_channel_value = self.process_flow(detail.logger_value,
                                                 channel.pulse,
                                                 interval,
                                                 channel.conversion)
        if channel.value_unit_id.name == 'm3/h':
            result_channel_value = result_channel_value * 3.6

        result_date_value = detail.logger_date

        return result_date_value, result_channel_value, result_channel_value


    def process_modbus_adam(self, params):
        channel = params['channel']
        detail = params['detail']

        result_channel_value = 0
        if channel.imin >= channel.imax:
            result_channel_value = detail.logger_value
        elif detail.logger_value < channel.imin:
            result_channel_value = channel.omin
        elif detail.logger_value > channel.imax:
            result_channel_value = channel.omax
        else:
            input_value = detail.logger_value - channel.imin
            result_channel_value = channel.omin + input_value * (channel.omax - channel.omin) / (channel.imax - channel.imin)

        result_date_value = detail.logger_date

        return result_date_value, result_channel_value, result_channel_value

    def process_modbus_other(self, params):
        channel = params['channel']
        detail = params['detail']

        if channel.source_value_unit_id.name == 'm3/h':
            current_source_value = detail.logger_value / 3.6
        elif channel.source_value_unit_id.name == 'm3/s' and channel.value_unit_id.name == 'l/s':
            current_source_value = detail.logger_value * 1000
        else:
            current_source_value = detail.logger_value

        result_date_value = detail.logger_date
        result_channel_value = current_source_value

        return result_date_value, result_channel_value, result_channel_value

    def process_counter_old(self, params):
        result_channel_value = False
        result_date_value = False

        key = params['key']
        key_target = params['key_target']
        channel = params['channel']

        # Current Row
        current_row = params['current_row']
        current_date = datetime.strptime(current_row['Date & Time'], '%Y/%m/%d %H:%M:%S')
        current_source_value = float(current_row[key])

        # Previous Row/Data
        previous_row = params['previous_row']
        if not previous_row.empty:
            previous_date = datetime.strptime(previous_row['Date & Time'], '%Y/%m/%d %H:%M:%S')
            previous_target_value = float(previous_row[key_target])
            diff_time = current_date - previous_date
            time_delta = diff_time.total_seconds()

            if current_source_value != previous_target_value:
                if channel.value_type_name:
                    if channel.value_type_name in 'Flow':
                        result_channel_value = self.process_flow(current_source_value, channel.pulse, time_delta,
                                                                 channel.conversion)
                        result_date_value = previous_date
        else:
            previous_datas = self.env['onpoint.logger.value'].search([('logger_id', '=', channel.logger_id.id),
                                                                      ('channel_id', '=', channel.id)],
                                                                     order='dates desc',
                                                                     limit=1)

            if previous_datas:
                previous_date = previous_datas.dates
                diff_time = current_date - previous_date
                time_delta = channel.interval

                if channel.value_type_name in 'Flow':
                    result_channel_value = self.process_flow(current_source_value, channel.pulse, time_delta,
                                                             channel.conversion)
                    result_date_value = previous_date + timedelta(seconds=channel.interval)
            else:
                result_date_value = current_date
                result_channel_value = 0

        return result_date_value, result_channel_value

    def process_modbus_adam_old(self, params):
        key = params['key']
        channel = params['channel']

        # Current Row
        current_row = params['current_row']
        current_date = datetime.strptime(current_row['Date & Time'], '%Y/%m/%d %H:%M:%S')
        current_source_value = float(current_row[key])

        # if current_source_value < channel.imin:
        #     result_channel_value = channel.omin
        # elif current_source_value > channel.imax:
        #     result_channel_value = channel.omax
        # else:
        result_channel_value = channel.omin + current_source_value * (channel.omax - channel.omin) / (
                channel.imax - channel.imin)

        result_date_value = current_date

        return result_date_value, result_channel_value

    def process_modbus_other_old(self, params):
        key = params['key']
        channel = params['channel']

        # Current Row
        current_row = params['current_row']
        current_date = datetime.strptime(current_row['Date & Time'], '%Y/%m/%d %H:%M:%S')
        current_source_value = float(current_row[key])

        if channel.source_value_unit_id.name == 'm3/h':
            current_source_value = current_source_value / 3.6

        result_date_value = current_date
        result_channel_value = current_source_value

        return result_date_value, result_channel_value

    def process_flow(self, value, pulse, interval, conversion):
        if interval > 0:
            result = ((value * pulse) / interval) * conversion
            return round(result, 3)
        else:
            return 0

    def modem_signal_strength(self, params):
        if 'value' in params:
            raw_value = params['value']
            result = str(raw_value) + ' dBm'

            return result
        else:
            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date
            offset = -113
            multiplier = 2

            result = 'Not known or not detectable'
            value = raw_value

            if raw_value != 99:
                scaled_value = (raw_value * multiplier) + offset
                value = scaled_value
                result = str(scaled_value) + ' dBm'

            return result_date_value, value, result

    def modem_signal_quality(self, params):
        if 'value' in params:
            raw_value = params['value']

            list_of_values = {
                0: 'less than 0.2%',
                1: '0.2% to 0.4%',
                2: '0.4% to 0.8%',
                3: '0.8% to 1.6%',
                4: '1.6% to 3.2%',
                5: '3.2% to 6.4%',
                6: '6.4% to 12.8%',
                7: 'More than 12.8%',
                99: 'Not known or not detectable'
            }

            result = list_of_values[raw_value]

            return result
        else:

            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date

            list_of_values = {
                0: 'less than 0.2%',
                1: '0.2% to 0.4%',
                2: '0.4% to 0.8%',
                3: '0.8% to 1.6%',
                4: '1.6% to 3.2%',
                5: '3.2% to 6.4%',
                6: '6.4% to 12.8%',
                7: 'More than 12.8%',
                99: 'Not known or not detectable'
            }

            result = list_of_values[raw_value]

        return result_date_value, raw_value, result

    def modem_fail_code(self, params):
        list_of_values = {
            0: 'OK',
            50: 'Couldn’t create modem driver',
            51: 'Couldn’t install modem driver',
            52: 'Invalid modem serial port',
            53: 'Incorrect modem connected',
            101: 'Can’t communicate with modem',
            102: 'Couldn’t register on network',
            103: 'Couldn’t attach to network',
            104: 'Activate PDP failure',
            105: 'Socket creation failed',
            106: 'Could not connect to IP',
            107: 'Start Bearer Timeout',
            108: 'Failed to read SIM card number',
            110: 'Network deregistration failed',
            111: 'Power Saving Mode not used (Modem powered off)',
            199: 'Socket closed by remote host',
            201: 'Connection closed by remote host',
            202: 'Could not connect to phone number (GSM)',
            203: 'Can’t communicate with modem power controller',
            301: 'Could not connect to FTP server',
            302: 'FTP data read ended',
            303: 'FTP Command failed',
            304: 'Bad FTP Command starting state',
            305: 'FTP failed to open local file',
            306: 'FTP failed to read from local file',
            307: 'FTP failed to write to local file',
            308: 'FTP data connection failed',
            309: 'FTP data connection timed out',
            310: 'FTP not supported on this Modem',
            311: 'FTPS PEM file not found',
            312: 'FTPS Error using PEM file',
            313: 'FTP failed to resolve hostname',
            401: 'FTP failed to get time from mobile network or NTP server',
        }

        if 'value' in params:
            raw_value = params['value']

            result = list_of_values[raw_value]

            return result
        else:
            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date

            result = list_of_values[raw_value]

        return result_date_value, raw_value, result

    def registration_code(self, params):
        list_of_values = {
            0: 'Not registered, modem is not currently searching a new operator to register to',
            1: 'Registered, home network',
            2: 'Not registered, but modem is currently searching a new operator to register to',
            3: 'Registration denied',
            4: 'Unknown',
            5: 'Registered, roaming',
        }

        if 'value' in params:
            raw_value = params['value']

            result = list_of_values[raw_value]

            return result
        else:
            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date

            result = list_of_values[raw_value]

            return result_date_value, raw_value, result


    def configuration_error_code(self, params):
        list_of_values = {
            0: 'Not configured. No new configuration found',
            2: 'Not configured. New configuration invalid',
            4: 'Configured. No new Configuration found',
            6: 'Configured. New configuration invalid',
            7: 'Configured. New configuration valid',
        }

        if 'value' in params:
            raw_value = params['value']
            result = list_of_values[raw_value]

            return result
        else:
            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date

            result = list_of_values[raw_value]

            return result_date_value, raw_value, result


    def submerged(self, params):
        list_of_values = {
            0: 'Unsubmerged',
            1: 'Submerged',
        }

        if 'value' in params:
            raw_value = params['value']

            result = list_of_values[raw_value]

            return result
        else:
            raw_value = params['detail'].logger_value
            result_date_value = params['detail'].logger_date

            result = list_of_values[raw_value]

            return result_date_value, raw_value, result
