from odoo import models, fields, api, tools
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
import math


class OnpointLoggerCompare(models.Model):
    _name = 'onpoint.logger.compare'
    _inherit = 'onpoint.monitor'

    name = fields.Char(required=True)
    remarks = fields.Text()
    line_ids = fields.One2many('onpoint.logger.compare.line', 'logger_compare_id')

    def get_global_time_zone(self):
        time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        return int(time_zone)

    def get_time_zone_logger(self, logger_id):
        logger = self.env['onpoint.logger'].browse(logger_id)
        convert_time = logger.convert_time
        if convert_time:
            time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        else:
            time_zone = 0
        return int(time_zone)

    @api.model
    def get_data(self, logger_compare_id, range_date):

        add_hours = self.get_global_time_zone()
        range_dates = range_date.split(' - ')

        start_date = (datetime.strptime(range_dates[0] + ' 00:00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(range_dates[1] + ' 23:59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        logger_compare_data = self.env['onpoint.logger.compare'].sudo().search([('id', '=', logger_compare_id)],
                                                                               limit=1)
        logger_compares = self.env['onpoint.vw.logger.compare'].sudo().search(
            [('logger_compare_id', '=', logger_compare_id)])

        # Channels
        y_axis, value_unit_ids = self._set_y_axis(logger_compare_data, start_date, end_date)
        series, loggers = self._set_series(logger_compares, value_unit_ids, start_date, end_date)
        # series = self._set_series()
        # channels = self._set_chart_channels(logger_compare_data.id, start_date, end_date)
        # logger.update(channels)

        totalizers = []
        events = []
        is_totalizer = False

        logger = {
            'id': logger_compare_data.id,
            'name': logger_compare_data.name,
            'period_start': start_date,
            'period_end': end_date,
            'yAxis': y_axis,
            'series': series,
            'events': events,
            'is_totalizer': is_totalizer,
            'totalizers': totalizers,
            'loggers': loggers
        }

        return logger

    def _set_y_axis(self, logger_compare_data, start_date, end_date):

        logger_value_unit = self.env['onpoint.vw.logger.compare'].sudo().read_group(
            [('logger_compare_id', '=', logger_compare_data.id)],
            ['value_unit_id'],
            ['value_unit_id'],
            orderby='value_unit_id')

        value_unit_ids = []
        mapped_data = dict([(data['value_unit_id'], data['value_unit_id_count']) for data in logger_value_unit])
        for key, value in mapped_data:
            value_unit_ids.append(key)

        opposite = False
        y_axis = []
        for value_unit_id in value_unit_ids:
            value_unit = self.env['onpoint.value.unit'].browse(value_unit_id)
            y_axis_data = {
                'title': {
                    'text': value_unit.name
                },
                'opposite': opposite,
                'minorGridLineWidth': 0,
                'gridLineWidth': 0,
            }
            y_axis.append(y_axis_data)

            if opposite:
                opposite = False
            else:
                opposite = True

        return y_axis, value_unit_ids

    def _set_series(self, logger_compares, value_unit_ids, start_date, end_date):
        series = []
        loggers = []

        idx = 0
        for value_unit_id in value_unit_ids:
            for logger_compare in logger_compares:
                add_hours = self.get_time_zone_logger(logger_compare.logger_id.id)

                if logger_compare.value_unit_id.id == value_unit_id:
                    values = self.env['onpoint.logger.value'].search([('channel_id', '=', logger_compare.channel_id.id),
                                                                      ('dates', '>=', start_date),
                                                                      ('dates', '<=', end_date)])

                    data = []
                    last_date = ''
                    last_value = 0
                    min_date = ''
                    min_value = 9999
                    max_date = ''
                    max_value = 0
                    for value in values:
                        # Value
                        channel_value = value.channel_value
                        value_dates = value.dates + timedelta(hours=add_hours)
                        unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                        data_val = [unixtime, round(channel_value, 3)]
                        data.append(data_val)

                        last_date = value.dates + timedelta(hours=add_hours)
                        last_value = round(channel_value, 3)

                        if last_value < min_value:
                            min_date = last_date
                            min_value = last_value

                        if last_value > max_value:
                            max_date = last_date
                            max_value = last_value

                    # Series
                    series_data = self._set_series_data(
                        logger_compare.logger_id.name + ' [' + logger_compare.channel_id.name + ']',
                        idx,
                        data,
                        logger_compare.channel_id.value_unit_id.name)
                    series.append(series_data)

                    if min_date != '':
                        min_date = self.comparison_convert_to_localtime(logger_compare.logger_id.id, min_date)

                    if max_date != '':
                        max_date = self.comparison_convert_to_localtime(logger_compare.logger_id.id, max_date)

                    if last_date != '':
                        last_date = self.comparison_convert_to_localtime(logger_compare.logger_id.id, last_date)

                    # Logger Information
                    logger_data = {
                        'logger_id': logger_compare.logger_id.id,
                        'logger_name': logger_compare.logger_id.name,
                        'channel_name': logger_compare.channel_id.name,
                        'last_date': last_date,
                        'last_value': last_value,
                        'min_date': min_date,
                        'min_value': min_value if min_value != 9999 else 0,
                        'max_date': max_date,
                        'max_value': max_value,
                        'unit_value_name': logger_compare.channel_id.value_unit_id.name
                    }
                    loggers.append(logger_data)

            idx = idx + 1
        return series, loggers

    #
    # def _set_chart_channels(self, logger_compare_id, start_date, end_date):
    #     yAxis = []
    #     series = []
    #     yAxis_count = 0
    #     opposite = False
    #     add_hours = self.get_time_zone()
    #
    #     logger_ids = []
    #     loggers = self.env['onpoint.logger.compare.line'].search([('logger_compare_id', '=', logger_compare_id)])
    #     for logger in loggers:
    #         logger_ids.append(logger.logger_id.id)
    #
    #     points = self.env['onpoint.logger.channel'].read_group([('logger_id', 'in', logger_ids),
    #                                                             ('point_is_sensor', '=', True)],
    #                                                            ['point_id'],
    #                                                            ['point_id'],
    #                                                            orderby='point_id')
    #
    #     point_ids = []
    #     mapped_data = dict([(data['point_id'], data['point_id_count']) for data in points])
    #     for key, value in mapped_data:
    #         point_ids.append(key)
    #
    #     totalizers = []
    #     events = []
    #     value_units = []
    #     is_totalizer = False
    #
    #     for point_id in point_ids:
    #         yaxis_data = self._set_yaxis(point_id, opposite)
    #         yAxis.append(yaxis_data)
    #
    #         if opposite:
    #             opposite = False
    #         else:
    #             opposite = True
    #
    #         for logger_id in logger_ids:
    #             logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
    #             channel = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id),
    #                                                                  ('point_id', '=', point_id)])
    #             channel_values = []
    #             values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel.id),
    #                                                               ('dates', '>=', start_date),
    #                                                               ('dates', '<=', end_date)])
    #
    #             for value in values:
    #                 # Value
    #                 channel_value = value.channel_value
    #                 value_dates = value.dates + timedelta(hours=add_hours)
    #                 unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000
    #
    #                 data_val = [unixtime, round(channel_value, 3)]
    #                 channel_values.append(data_val)
    #
    #                 last_date = value.dates + timedelta(hours=add_hours)
    #                 last_value = round(channel_value, 3)
    #
    #             # Series
    #             if channel.value_type_id.name:
    #                 series_data = self._set_series(logger.name + ' [' + channel.value_type_id.name + ']',
    #                                                yAxis_count,
    #                                                channel.color,
    #                                                channel_values,
    #                                                channel.value_unit_id.name)
    #                 series.append(series_data)
    #
    #         yAxis_count = yAxis_count + 1
    #
    #     data = {
    #         'yAxis': yAxis,
    #         'series': series,
    #         'events': events,
    #         'is_totalizer': is_totalizer,
    #         'totalizers': totalizers
    #     }
    #
    #     return data
    #
    # def _set_yaxis(self, channel, opposite):
    #     yAxis_data = {
    #         'title': {
    #             'text': 'X'
    #         },
    #         'opposite': opposite,
    #         'minorGridLineWidth': 0,
    #         'gridLineWidth': 0,
    #     }
    #
    #     return yAxis_data
    #
    def _set_series_data(self, value_type_name, yAxis_count, data, value_unit_name):

        if value_unit_name:
            valueSuffix = value_unit_name
        else:
            valueSuffix = ''

        series_data = {
            'name': value_type_name,
            'type': 'spline',
            'yAxis': yAxis_count,
            'zIndex': '1',
            'data': data,
            'tooltip': {
                'valueSuffix': ' ' + valueSuffix
            }
        }

        return series_data


class OnpointLoggerCompareLine(models.Model):
    _name = 'onpoint.logger.compare.line'

    logger_compare_id = fields.Many2one('onpoint.logger.compare', index=True, ondelete='cascade')
    logger_id = fields.Many2one('onpoint.logger', required=True, index=True, ondelete='cascade')


class OnpointViewLoggerCompare(models.Model):
    _name = 'onpoint.vw.logger.compare'
    _auto = False

    logger_compare_id = fields.Many2one('onpoint.logger.compare', readonly=True, index=True)
    logger_id = fields.Many2one('onpoint.logger', index=True, readonly=True)
    channel_id = fields.Many2one('onpoint.logger.channel', index=True, readonly=True)
    point_id = fields.Many2one('onpoint.logger.point', index=True, readonly=True)
    value_unit_id = fields.Many2one('onpoint.value.unit', index=True, readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
                create or replace view onpoint_vw_logger_compare as (                 
                    select 
                        row_number()over() as id,
                        x.logger_compare_id,
                        x.logger_id,
                        x.channel_id,
                        x.point_id,
                        x.value_unit_id
                    from 
                    ( 
                        select
                            olc.id as logger_compare_id,
                            ol.id as logger_id,
                            olc2.id as channel_id,
                            olp.id as point_id,
                            olc2.value_unit_id
                        from
                            onpoint_logger_compare olc
                        inner join onpoint_logger_compare_line olcl on olc.id = olcl.logger_compare_id
                        inner join onpoint_logger ol on ol.id = olcl.logger_id
                        inner join onpoint_logger_channel olc2 on ol.id = olc2.logger_id and olc2.display_on_chart = true
                        inner join onpoint_logger_point olp on olp.id = olc2.point_id
                      ) x
                    )
                """
        self.env.cr.execute(sql)
