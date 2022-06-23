from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import logging
_logger = logging.getLogger(__name__)


class OnpointSchedulerMessage(models.Model):
    _name = 'onpoint.scheduler.message'

    @api.model
    def send_messages(self):
        pics = self.env['onpoint.logger.message'].search([('is_active', '=', True),
                                                          ('send_info', '=', True),
                                                          ('next_send', '<=', datetime.now())])
        for pic in pics:
            logger = pic.logger_id
            message = logger.name

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

            if alarm != "()":
                message = message + "\n" + alarm

            channels = logger.channel_ids.search([('logger_id', '=', logger.id),
                                                  ('display_on_chart', '=', True)])

            last_values = ""
            last_date = ""
            for channel in channels:
                channel_name = channel.name if channel.name else channel.point_id.name
                channel_unit = channel.value_unit_name if channel.value_unit_name else ""
                channel_last_value = channel.last_value + " " + channel_unit
                last_values = last_values + "\n"
                last_values = last_values + channel_name + " : " + channel_last_value
                last_date = logger.convert_to_localtime(logger.id, channel.last_date)

            if last_values != "":
                message = message + "\n" + last_values + "\n" + last_date

            params = {
                'send_to': pic.mobile_phone,
                'message': message,
                'send_sms': pic.send_sms,
                'send_wa': pic.send_wa
            }

            response_data_sms, response_data_wa = pic.send_message(params)

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
                    'message': message,
                    'state': response_data_sms['status'],
                    'text_response': response_data_sms['text'],
                    'cost': cost
                }
                self.env['onpoint.logger.outbox'].create(outbox)

            if response_data_wa:
                cost = 0
                if response_data_wa['status'] == '1':
                    cost = response_data_wa['cost']

                outbox = {
                    'logger_message_id': pic.id,
                    'logger_id': pic.logger_id.id,
                    'message_type': 'summary',
                    'media': 'wa',
                    'message_id': response_data_wa['messageId'],
                    'send_to': pic.mobile_phone,
                    'message': message,
                    'state': response_data_wa['status'],
                    'text_response': response_data_wa['text'],
                    'cost': cost
                }
                self.env['onpoint.logger.outbox'].create(outbox)

            interval_type = pic.info_interval[-1]
            interval_qty = int(pic.info_interval[0:-1])

            if interval_type == 'h':
                next_send = pic.next_send + timedelta(hours=interval_qty)
            elif interval_type == 'd':
                next_send = pic.next_send + timedelta(days=interval_qty)

            pic.update({
                'next_send': next_send
            })
