from odoo import models, fields, api, _
from datetime import datetime, timezone, timedelta
from ftplib import FTP
import csv
import pandas as pd
import chardet
import math
import io
import logging

_logger = logging.getLogger(__name__)


class OnpointLoggerAlarm(models.Model):
    _name = 'onpoint.logger.alarm'
    _rec_name = 'channel_id'
    _inherit = ['onpoint.pointorange']

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    channel_id = fields.Many2one('onpoint.logger.channel',
                                 string='Channel',
                                 required=True,
                                 index=True,
                                 ondelete='cascade')
    is_active = fields.Boolean(string='Active', compute='_get_last_active', store=True)
    line_ids = fields.One2many('onpoint.logger.alarm.line', 'logger_alarm_id')

    @api.depends('line_ids')
    def _get_last_active(self):
        for record in self:
            last_row = record.line_ids.search([], order='alarm_date desc', limit=1)
            if last_row:
                record.is_active = last_row.is_active
            else:
                record.is_active = False

    def insert_alarm(self, vals, alarm_message):
        for value in vals:
            logger = self.env['onpoint.logger'].search([('id', '=', value['logger_id'])])
            channel = self.env['onpoint.logger.channel'].search([('id', '=', value['channel_id'])])

            logger_alarm = self.env['onpoint.logger.alarm'].search([('logger_id', '=', value['logger_id']),
                                                                    ('channel_id', '=', value['channel_id'])])

            if not logger_alarm:
                logger_alarm.create({
                    'logger_id': value['logger_id'],
                    'channel_id': value['channel_id'],
                    'line_ids': [(0, 0, {
                        'alarm_date': value['alarm_date'],
                        'alarm_value': value['alarm_value'],
                        'is_active': True
                    })]
                })
                alarm_message += ' Logger ' + logger.name + '\n' \
                                 + channel.name + '\n' \
                                 + value['alarm_date'] + ' - ' + value['alarm_value']
            else:
                line_id = logger_alarm.line_ids.search([('alarm_date', '=', value['alarm_date']),
                                                        ('alarm_value', '=', value['alarm_value'])])
                if not line_id:
                    logger_alarm.line_ids.create({
                        'logger_alarm_id': logger_alarm.id,
                        'alarm_date': value['alarm_date'],
                        'alarm_value': value['alarm_value'],
                        'is_active': not logger_alarm.is_active
                    })

                    alarm_message += ' Logger ' + logger.name + '\n' \
                                     + channel.name + '\n' \
                                     + ' - ' + str(value['alarm_value'])

        return alarm_message


class OnpointLoggerAlarmLine(models.Model):
    _name = 'onpoint.logger.alarm.line'
    _order = 'alarm_date desc'

    logger_alarm_id = fields.Many2one('onpoint.logger.alarm', required=True, ondelete='cascade', index=True)
    alarm_date = fields.Datetime(required=True, index=True)
    alarm_value = fields.Float(required=True, digits=(12, 3))
    is_active = fields.Boolean(string='Active', default=True)
