from odoo import models, fields, tools, api, _
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
    _inherit = ['onpoint.logger']

    def get_all_loggers(self):
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled')])

        data = []
        for logger in loggers:
            add_hours = self.get_time_zone(logger.id)
            channels = []
            for channel in logger.channel_ids:
                val_channels = {
                    'id': channel.id,
                    'name': channel.name if channel.name else channel.point_id.name,
                    'value_type_name': channel.value_type_name if channel.value_type_name else '',
                    'value_unit_name': channel.value_unit_name if channel.value_unit_name else '',
                    'last_date': channel.last_date + timedelta(hours=add_hours),
                    'last_value': channel.last_value
                }
                channels.append(val_channels)

            vals = {
                'id': logger.id,
                'name': logger.name,
                'address': logger.address,
                'channels': channels
            }
            data.append(vals)

        return data

    def get_info_logger(self, logger_id):
        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        add_hours = self.get_time_zone(logger.id)

        data = []
        if logger:
            channels = []
            for channel in logger.channel_ids:
                val_channels = {
                    'id': channel.id,
                    'name': channel.name if channel.name else channel.point_id.name,
                    'value_type_name': channel.value_type_name if channel.value_type_name else '',
                    'value_unit_name': channel.value_unit_name if channel.value_unit_name else '',
                    'last_date': channel.last_date + timedelta(hours=add_hours),
                    'last_value': channel.last_value
                }
                channels.append(val_channels)

            vals = {
                'id': logger.id,
                'name': logger.name,
                'address': logger.address,
                'channels': channels
            }
            data.append(vals)

        return data

    def get_value_logger(self, logger_id, start_date, end_date):

        # add_hours = self.get_time_zone(logger_id)
        # add_hours = 7
        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        add_hours = self.get_time_zone(logger.id)

        start = (datetime.strptime(start_date, "%d-%m-%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end = (datetime.strptime(end_date, "%d-%m-%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        data = []
        if logger:
            channels = []
            for channel in logger.channel_ids:
                logger_values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel.id),
                                                                         ('dates', '>=', start),
                                                                         ('dates', '<=', end)])
                values = []
                for logger_value in logger_values:
                    val_values = {
                        'channel_value_date': logger_value.dates + timedelta(hours=add_hours),
                        'channel_value': logger_value.channel_value
                    }
                    values.append(val_values)

                val_channels = {
                    'id': channel.id,
                    'name': channel.name if channel.name else channel.point_id.name,
                    'value_type_name': channel.value_type_name if channel.value_type_name else '',
                    'value_unit_name': channel.value_unit_name if channel.value_unit_name else '',
                    'last_date': channel.last_date + timedelta(hours=add_hours),
                    'last_value': channel.last_value,
                    'channel_values': values
                }
                channels.append(val_channels)

            vals = {
                'id': logger.id,
                'name': logger.name,
                'address': logger.address,
                'channels': channels
            }
            data.append(vals)

        return data
