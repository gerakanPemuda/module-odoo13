from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import logging
_logger = logging.getLogger(__name__)


class OnpointSchedulerTelegram(models.Model):
    _name = 'onpoint.scheduler.telegram'
    _inherit = 'api.telegram.abstract'

    @api.model
    def send_info(self):
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled'),
                                                     ('telegram_send_info', '=', True),
                                                     ('telegram_next_send', '<=', datetime.now())])

        for logger in loggers:
            if logger.telegram_group_id.chat_id:
                message = '<b>' + logger.name + '</b>'

                channels = logger.channel_ids.search([('logger_id', '=', logger.id),
                                                      ('point_id.alarm_type', '!=', False)])

                alarm = "("
                for channel in channels:
                    unit_name = ""
                    channel_value = channel.last_value
                    if channel.point_id.alarm_type in ('battery', 'external'):
                        channel_value = channel_value + " V"
                    elif channel.point_id.alarm_type == 'signal':
                        channel_value = channel_value + " dBm"
                    elif channel.point_id.alarm_type == 'temperature':
                        channel_value = channel_value + " C"
                    elif channel.point_id.alarm_type == 'submerged':
                        channel_value = "Unsub"
                    else:
                        channel_value = ""

                    if channel_value != "":
                        if alarm != "(":
                            alarm = alarm + ", "

                        alarm = alarm + channel_value + " " + unit_name

                alarm = alarm + ")"

                channels = logger.channel_ids.search([('logger_id', '=', logger.id),
                                                      ('display_on_chart', '=', True)])

                last_values = ""
                last_date = ""
                for channel in channels:
                    consumption = ''
                    channel_name = channel.name if channel.name else channel.point_id.name
                    channel_unit = channel.value_unit_name if channel.value_unit_name else ""
                    channel_last_value = channel.last_value + " " + channel_unit
                    if channel.modbus != 'unavailable':
                        totalizer_channel = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger.id),
                                                                                       ('point_id', '=', channel.totalizer_point_id.id)])
                        if totalizer_channel:
                            consumption = 'Consumption : ' + totalizer_channel.last_value + ' m3'

                    if channel.last_date:
                        last_values = last_values + "\n"
                        last_values = last_values + channel_name + " : " + channel_last_value
                        if consumption != '':
                            last_values = last_values + '\n' + consumption
                        last_date = logger.convert_to_localtime(logger.id, channel.last_date)

                if last_values != "":
                    if logger.is_still_active:
                        if alarm != "()":
                            message += "\n" + alarm
                        message += "\n" + last_values + "\n" + last_date
                    else:
                        message += "\n\n" + 'Logger is <b>INACTIVE</b> since <u>' + last_date + '</u>'

                params = {
                    'chat_id': logger.telegram_group_id.chat_id,
                    'message': message
                }

                result = self.send_message(params)

                interval_type = logger.telegram_info_interval[-1]
                interval_qty = int(logger.telegram_info_interval[0:-1])

                if interval_type == 'h':
                    next_send = logger.telegram_next_send + timedelta(hours=interval_qty)
                elif interval_type == 'd':
                    next_send = logger.telegram_next_send + timedelta(days=interval_qty)

                logger.update({
                    'telegram_next_send': next_send
                })

    @api.model
    def read_data_alarm(self):
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled'),
                                                     ('brand_owner', '=', 'pointorange')])

        for logger in loggers:
            logger.read_ftp_pointorange_alarm()

        logger_thresholds = self.env['onpoint.vw.logger.threshold'].search([])

        for record in logger_thresholds:
            logger = record.logger_id
            logger_channel = record.channel_id
            logger_value = record.channel_value_id
            channel_name = logger_channel.name if logger_channel.name else logger_channel.point_id.name

            if logger.telegram_alarm_group_id:
                telegram_group = logger.telegram_alarm_group_id.chat_id
            else:
                telegram_group = logger.telegram_group_id.chat_id

            if not logger_value.alarm_sent:
                message = ""
                if record.threshold_type == 'overrange' and logger_value.channel_value >= record.threshold:
                    message = "<b>ALARM - Overrange Threshold</b>\n\n"
                elif record.threshold_type == 'hihi' and logger_value.channel_value >= record.threshold:
                    message = "<b>ALARM - High High Threshold</b>\n\n"
                elif record.threshold_type == 'hi' and logger_value.channel_value >= record.threshold:
                    message = "<b>ALARM - High Threshold</b>\n\n"
                elif record.threshold_type == 'lo' and logger_value.channel_value <= record.threshold:
                    message = "<b>ALARM - Lo Threshold</b>\n\n"
                elif record.threshold_type == 'lolo' and logger_value.channel_value <= record.threshold:
                    message = "<b>ALARM - Low Low Threshold</b>\n\n"
                elif record.threshold_type == 'underrange' and logger_value.channel_value <= record.threshold:
                    message = "<b>ALARM - Underrange Threshold</b>\n\n"
                elif record.threshold_type == 'additional':
                    if logger_value.value_type == 'alarm':
                        additional = self.env['onpoint.logger.additional'].search([('logger_id', '=', logger.id),
                                                                                   ('logger_channel_id', '=', logger_channel.id)])
                        if logger_value.channel_value == 0:
                            message = "<b>ALARM - " + additional.message_off + "</b>\n\n"
                        else:
                            message = "<b>ALARM - " + additional.message_on + "</b>\n\n"

                if message != "":
                    message = message + '<b>' + logger.name + "</b>\n\n"
                    if record.threshold_type != 'additional':
                        message = message + channel_name + " : " + str(logger_value.channel_value) + ' ' + logger_channel.value_unit_name + "\n"
                    message = message + logger.convert_to_localtime(logger.id, logger_value.dates)

                    params = {
                        'chat_id': telegram_group,
                        'message': message
                    }

                    logger_value.update({
                        'alarm_sent': True
                    })

                    result = self.send_message(params)


