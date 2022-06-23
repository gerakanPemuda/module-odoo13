from odoo import models, fields, api, tools
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointLoggerType(models.Model):
    _name = 'onpoint.logger.type'
    _inherit = ['image.mixin']

    name = fields.Char(required=True)
    is_threshold_hourly = fields.Boolean(string="Use Hourly Threshold", default=False)
    sequence = fields.Integer(default=0)


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _order = 'name asc'
    _inherit = ['image.mixin', 'mail.thread', 'onpoint.monitor']
    _description = 'Logger'

    name = fields.Char(required=True)
    brand_id = fields.Many2one('onpoint.logger.brand', required=True, index=True)
    brand_owner = fields.Selection('onpoint.logger.brand', related='brand_id.owner', index=True)
    convert_time = fields.Boolean('onpoint.logger.brand', related='brand_id.convert_time', index=True)
    identifier = fields.Char(string='Identifier', required=True)
    logger_type_id = fields.Many2one('onpoint.logger.type', required=True, index=True)
    logger_type_name = fields.Char('onpoint.logger.type', related='logger_type_id.name')
    is_threshold_hourly = fields.Boolean('onpoint.logger.type', related='logger_type_id.is_threshold_hourly')
    wtp_id = fields.Many2one('onpoint.wtp', string='WTP', index=True)
    zone_id = fields.Many2one('onpoint.zone', string='Zone', index=True)
    dma_id = fields.Many2one('onpoint.dma', string='DMA', index=True)
    department_id = fields.Many2one('hr.department', index=True)
    address = fields.Text(required=True)
    simcard = fields.Char(string="SIM Card")
    remarks = fields.Text()
    nosal = fields.Char()
    latitude = fields.Char()
    longitude = fields.Char()
    elevation = fields.Float()

    # threshold
    leakage = fields.Float()
    leakage_interval_minutes = fields.Integer(string="Interval (minutes)")
    leakage_interval_days = fields.Integer(string="Interval (days)")
    count_logger_value = fields.Integer(compute='_count_logger_value')
    is_logger = fields.Boolean()
    image = fields.Binary("Image", attachment=True, help="This field holds the image used for as favicon")
    last_data_date = fields.Datetime(string='Last Available Data', compute='_get_last_data_date', store=True)

    # profile
    meter_type_id = fields.Many2one('onpoint.meter.type', string='Meter Type')
    meter_brand_id = fields.Many2one('onpoint.meter.brand', string='Meter Brand')
    meter_size_id = fields.Many2one('onpoint.meter.size', string='Meter Size')
    pipe_material_id = fields.Many2one('onpoint.pipe.material', string='Pipe Material')
    pipe_size_id = fields.Many2one('onpoint.meter.size', string='Pipe Size')
    valve_control_id = fields.Many2one('onpoint.valve.control', string='Valve Control')

    # Dashboard
    is_on_dashboard = fields.Boolean(compute='_check_dashboard')
    is_still_active = fields.Boolean(string='Active', compute='_check_activity')
    show_all_channels = fields.Boolean(default=False)

    state = fields.Selection([
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled')
    ], default='enabled')

    auto_refresh = fields.Boolean(default=False)

    channel_ids = fields.One2many('onpoint.logger.channel', 'logger_id')
    threshold_hourly_ids = fields.One2many('onpoint.logger.threshold.hourly', 'logger_id')
    value_ids = fields.One2many('onpoint.logger.value', 'logger_id')

    def _count_logger_value(self):
        self.count_logger_value = self.env['onpoint.logger.value'].search_count([('logger_id', '=', self.id)])

    def _check_dashboard(self):
        check_dashboard = self.env['onpoint.monitor.dashboard'].search([('logger_id', '=', self.id),
                                                                        ('user_id', '=', self.env.uid)])
        if check_dashboard:
            self.is_on_dashboard = True
        else:
            self.is_on_dashboard = False

    def _check_activity(self):
        inactive_days = int(self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.inactive_days'))
        today = datetime.today()
        for record in self:
            add_hours = record.get_time_zone(record.id)
            today = datetime.today() + timedelta(hours=add_hours)
            if record.last_data_date:
                last_date = record.last_data_date + timedelta(hours=add_hours)
                diff = abs((today - last_date).days)
            else:
                diff = 9999
            if diff >= inactive_days:
                record.is_still_active = False
            else:
                record.is_still_active = True

    def action_to_logger_value(self):
        return {
            'name': 'Logger Value',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'onpoint.logger.value',
            'domain': [('logger_id', '=', self.id)],
            # 'context': {
            #     'group_by': 'channel_id'
            # }
        }

    def act_add_to_dashboard(self):
        dashboard = self.env['onpoint.monitor.dashboard'].sudo().create({
            'logger_id': self.id,
            'user_id': self.env.uid
        })
        return dashboard

    def act_remove_from_dashboard(self):
        dashboard = self.env['onpoint.monitor.dashboard'].sudo().search([('logger_id', '=', self.id),
                                                                         ('user_id', '=', self.env.uid)])
        dashboard.sudo().unlink()

    @api.model
    def act_view_data_channels(self, logger_id):
        return {
            'name': 'Logger Value',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'onpoint.logger.value',
            'domain': [('logger_id', '=', logger_id)],
        }

    def act_toggle_channels(self):
        self.write({
            'show_all_channels': not self.show_all_channels
        })

        for channel in self.channel_ids:
            show_channel = self.show_all_channels
            if channel.point_is_sensor or channel.display_on_chart:
                if channel.value_unit_id:
                    show_channel = True

            channel.sudo().update({
                'show_channel': show_channel
            })

    def act_view_logger_value(self):
        return {
            'name': 'Logger Value',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'onpoint.logger.value',
            'domain': [('logger_id', '=', self.id)],
            # 'context': {
            #     'group_by': 'channel_id'
            # }
        }

    @api.depends('value_ids.dates')
    def _get_last_data_date(self):
        for record in self:
            add_hours = self.get_time_zone_inverse(record.id)
            logger_values = self.env['onpoint.logger.value'].search([('logger_id', '=', record.id)],
                                                                    order='dates desc',
                                                                    limit=1)
            if logger_values.dates:
                # logger_last_date = datetime.strptime(logger_values.dates, ("%Y-%m-%d %H:%M:%S"))
                record.last_data_date = (logger_values.dates - timedelta(hours=add_hours)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                record.last_data_date = ''

    @api.onchange('is_threshold_hourly')
    def set_threshould_hourly(self):
        hour = 0
        thresholds = []
        if self.is_threshold_hourly:
            for x in range(24):
                thresholds.append({
                    'logger_id': self.id,
                    'hours': '{:02d}'.format(x),
                    'min_value': 0,
                    'max_value': 0
                })

            self.update({'threshold_hourly_ids': thresholds})
        else:
            self.update({'threshold_hourly_ids': thresholds})

    @api.model
    def get_data(self, logger_id, range_date, option, period, option_hour='00', with_alarm=True):
        view_id = self.env.ref('onpoint_monitor.view_onpoint_logger_value_tree').id

        # uid = request.session.uid
        add_hours = self.get_time_zone(logger_id)
        range_dates = range_date.split(' - ')
        if not option:
            option = '3d'

        start_hour = int(option_hour)
        if start_hour == 0:
            end_hour = 23
        else:
            end_hour = start_hour - 1

        start_hours = f'{start_hour:02}'
        end_hours = f'{end_hour:02}'

        start_date = (datetime.strptime(range_dates[0] + ' ' +  start_hours + ':00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(range_dates[1] + ' ' +  end_hours + ':59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        logger_data = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)
        loggers = self.env['onpoint.vw.logger'].sudo().search(
            [('logger_id', '=', logger_id)])

        # Channels
        y_axis, value_unit_ids = self._set_y_axis(logger_data, start_date, end_date)
        series, totalizers, events, is_totalizer = self._set_series(loggers, value_unit_ids, start_date, end_date)

        totalizers = []
        is_totalizer = False

        logger = {
            'id': logger_data.id,
            'name': logger_data.name,
            'option': option,
            'option_hour': option_hour,
            'period_start': start_date,
            'period_end': end_date,
            'yAxis': y_axis,
            'series': series,
            'events': events,
            'is_totalizer': is_totalizer,
            'totalizers': totalizers,
            'auto_refresh': logger_data.auto_refresh
        }

        # Channels
        # channels = self._set_chart_channels(logger_id, start_date, end_date)
        # logger.update(channels)

        # Main Alarms
        if with_alarm:
            main_alarms = self.set_main_alarm(logger_id, start_date, end_date)
            logger.update(main_alarms)
        return logger

    @api.model
    def get_flow_channels(self, logger_id):
        channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id)])

        flow_channels = []
        for channel in channels:
            if channel.value_type_id.need_totalizer and channel.show_consumption:
                flow_channels.append({
                    'channel_id': channel.id,
                    'channel_name': channel.name
                })

        return flow_channels

    @api.model
    def get_data_alarm(self, logger_id, range_date, alarm_type, option_hour='00'):
        alarms = {
            'power': {
                'title': 'Power',
                'title_axis': 'Power (V)',
                'alarm_type': ('battery', 'external'),
                'unit_name': 'V',
            },
            'signal': {
                'title': 'Signal',
                'title_axis': 'Signal (dBm)',
                'alarm_type': ('signal',),
                'unit_name': 'dBm',
            },
            'temperature': {
                'title': 'Temperature',
                'title_axis': 'Temperature (C)',
                'alarm_type': ('temperature',),
                'unit_name': 'C',
            },
        }

        series = []

        add_hours = self.get_time_zone(logger_id)
        range_dates = range_date.split(' - ')

        start_hour = int(option_hour)
        if start_hour == 0:
            end_hour = 23
        else:
            end_hour = start_hour - 1

        start_hours = f'{start_hour:02}'
        end_hours = f'{end_hour:02}'

        start_date = (datetime.strptime(range_dates[0] + ' ' +  start_hours + ':00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(range_dates[1] + ' ' +  end_hours + ':59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        point = self.env['onpoint.logger.point'].search([('alarm_type', 'in', alarms[alarm_type]['alarm_type'])])
        unit_name = alarms[alarm_type]['unit_name']

        channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id),
                                                              ('point_id', 'in', point.ids)])

        chart_type = ''
        color = ''
        for channel in channels:
            data = self.env['onpoint.logger.value'].get_data(channel.id, start_date, end_date)

            channel_values = []
            for value in data['values']:
                # Value
                channel_value = value.channel_value

                value_dates = value.dates + timedelta(hours=add_hours)
                unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                data_val = [unixtime, round(channel_value, 3)]
                channel_values.append(data_val)

            # Series
            if chart_type == '':
                chart_type = 'area'
                color = '#aeb6bf'
            else:
                chart_type = 'column'
                color = '#4B9AFF'

            series_data = self._set_series_data(channel.point_id.alarm_type.capitalize(),
                                                chart_type,
                                                0,
                                                color,
                                                channel_values,
                                                unit_name)
            series.append(series_data)

        result = {
            'title': alarms[alarm_type]['title'],
            'title_axis': alarms[alarm_type]['title_axis'],
            'series': series
        }

        return result

    def sort_by_value(self, e):
        return e[1]

    def exec_query_consumption(self, channel_id, start_date, end_date, interval='hour'):
        interval = '1 ' + interval
        sql = """
                select olv.id 
                FROM generate_series
                        ( %s, %s, %s::interval) dd
                left join onpoint_logger_value olv on dd = olv.dates
                where olv.channel_id = %s
                order by olv.dates
              """

        self._cr.execute(sql, (start_date, end_date, interval, channel_id ))
        data = self._cr.fetchall()

        result = []
        for row in data:
            result.append(row[0])

        return result


    @api.model
    def get_data_consumption(self, logger_id, channel_id, range_date, option_hour='00', interval='default'):
        series = []

        add_hours = self.get_time_zone(logger_id)
        range_dates = range_date.split(' - ')

        start_hour = int(option_hour)
        if start_hour == 0:
            end_hour = 23
        else:
            end_hour = start_hour - 1

        start_hours = f'{start_hour:02}'
        end_hours = f'{end_hour:02}'

        start_date = (datetime.strptime(range_dates[0]  + ' ' +  start_hours + ':00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(range_dates[1]  + ' ' +  end_hours + ':59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        y_axis = []
        y_axis_data = {
            'title': {
                'text': 'Consumption'
            },
            'opposite': False,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
        }
        y_axis.append(y_axis_data)

        y_axis_data = {
            'title': {
                'text': 'Meter Index'
            },
            'opposite': True,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
        }
        y_axis.append(y_axis_data)

        channel_data = self.env['onpoint.logger.channel'].search([('id', '=', channel_id)])
        has_totalizer_point_id = False
        if 'totalizer_point_id' in channel_data._fields:
            has_totalizer_point_id = True
            if channel_data.totalizer_point_id:
                channel_totalizer = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id),
                                                                               ('point_id', '=', channel_data.totalizer_point_id.id)])
            else:
                channel_totalizer = False

        if interval != 'default':
            value_ids = self.exec_query_consumption(channel_id, start_date, end_date, interval)
            data = self.env['onpoint.logger.value'].search([('id', 'in', value_ids)])
        else:
            data = self.env['onpoint.logger.value'].search([('channel_id', '=', channel_id),
                                                            ('dates', '>=', start_date),
                                                            ('dates', '<=', end_date)])

        min_value = False
        min_date = False
        max_value = False
        max_date = False
        last_value = False
        last_date = False
        last_totalizer = 0
        tabular_data = []

        channel_values = []
        totalizer_values = []
        prev_totalizer = -9999
        totalizer_value = 0
        index = 0
        for value in data:
            # Value
            # channel_value = value.channel_value
            if not channel_totalizer:
                totalizer_value = value.totalizer
            if index == 0:
                channel_value = 0
            else:
                channel_value = totalizer_value - prev_totalizer

            # prev_totalizer = totalizer_value

            if has_totalizer_point_id:
                if channel_totalizer:
                    totalizer_value = self.env['onpoint.logger.value'].search([('channel_id', '=', channel_totalizer.id),
                                                                               ('dates', '=', value.dates)],
                                                                              limit=1).channel_value

            value_dates = value.dates + timedelta(hours=add_hours)
            unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

            if channel_value < 0:
                channel_value = 0
            if index > 0:
                channel_value = totalizer_value - prev_totalizer
            channel_value = round(channel_value, 3)
            totalizer_value = round(totalizer_value, 3)
            prev_totalizer = totalizer_value

            index += 1
            data_val = [unixtime, channel_value]
            totalizer_val = [unixtime, totalizer_value]
            channel_values.append(data_val)
            tabular_data_val = [value_dates, channel_value, totalizer_value]
            tabular_data.append(tabular_data_val)

            if not min_value or channel_value < min_value:
                if channel_value > 0:
                    min_value = channel_value
                    min_date = value_dates

            if not max_value or channel_value > max_value:
                max_value = channel_value
                max_date = value_dates

            last_value = channel_value
            last_date = value_dates

            totalizer_values.append(totalizer_val)
            last_totalizer = totalizer_value

        # Series
        chart_type = 'column'
        color = '#4B9AFF'

        series_data = self._set_series_data('Consumption',
                                            chart_type,
                                            0,
                                            color,
                                            channel_values,
                                            'm3')
        series.append(series_data)

        chart_type = 'line'
        color = '#c2a46d'

        series_data = self._set_series_data('Meter Index',
                                            chart_type,
                                            1,
                                            color,
                                            totalizer_values,
                                            'm3')
        series.append(series_data)


        result = {
            'title': 'Consumption',
            'title_axis': 'X Axis',
            'yAxis': y_axis,
            'series': series,
            'tabular_data': tabular_data,
            'min_value': min_value,
            'min_date': min_date,
            'max_value': max_value,
            'max_date': max_date,
            'last_value': last_value,
            'last_date': last_date,
            'last_totalizer': last_totalizer,
            'interval': interval
        }
        return result

    def _set_y_axis(self, logger_data, start_date, end_date):

        logger_value_unit = self.env['onpoint.vw.logger'].sudo().read_group(
            [('logger_id', '=', logger_data.id), ('value_unit_id', '!=', False)],
            ['value_unit_id'],
            ['value_unit_id'],
            orderby='value_unit_id')

        value_unit_ids = []
        mapped_data = dict([(data['value_unit_id'], data['value_unit_id_count']) for data in logger_value_unit])
        if mapped_data:
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

    def _set_series(self, loggers, value_unit_ids, start_date, end_date):
        series = []
        totalizers = []
        events = []
        is_totalizer = False

        idx = 0
        for value_unit_id in value_unit_ids:
            for logger in loggers:
                add_hours = self.get_time_zone(logger.logger_id.id)

                if logger.value_unit_id.id == value_unit_id:
                    values = self.env['onpoint.logger.value'].search([('channel_id', '=', logger.channel_id.id),
                                                                      ('dates', '>=', start_date),
                                                                      ('dates', '<=', end_date)])

                    channel_name = ''
                    if logger.channel_id.value_type_name:
                        channel_name = logger.channel_id.value_type_name

                    if logger.channel_id.point_id.name:
                        channel_name += ' - ' + logger.channel_id.point_id.name

                    data_totalizer = {
                        'channel_name': channel_name,
                    }

                    if logger.point_id.need_totalizer:
                        is_totalizer = True
                        initial_date, initial_value = self.get_initial(logger.channel_id.id, end_date)
                        data_totalizer.update({
                            'initial_date': initial_date,
                            'initial_value': initial_value,
                        })

                    last_totalizer = 0
                    alarm_events = 0

                    data = []
                    min_date = False
                    min_value = 9999
                    max_date = False
                    max_value = 0
                    avg_value = 0
                    total_value = 0
                    total_data = 0
                    last_date = False
                    last_value = 0
                    for value in values:
                        # Value
                        channel_value = value.channel_value
                        value_dates = value.dates + timedelta(hours=add_hours)
                        unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                        # Events
                        if value.value_type == 'alarm':
                            alarm_events = alarm_events + 1

                        data_val = [unixtime, round(channel_value, 3)]
                        data.append(data_val)

                        last_date = value.dates + timedelta(hours=add_hours)
                        last_value = round(channel_value, 3)
                        total_value += last_value
                        total_data += 1

                        if last_value < min_value:
                            min_date = last_date
                            min_value = last_value

                        if last_value > max_value:
                            max_date = last_date
                            max_value = last_value

                        last_totalizer = round(value.totalizer, 3)

                    if total_data > 0:
                        avg_value = round(total_value / total_data, 3)
                    else:
                        avg_value = 0

                    data_totalizer.update({
                        'last_totalizer': last_totalizer,
                        'last_date': last_date
                    })

                    if logger.point_id.need_totalizer:
                        totalizers.append(data_totalizer)

                    # Series
                    if logger.channel_id.display_on_chart:
                        series_data = self._set_series_data(
                            logger.channel_id.name if logger.channel_id.name else logger.channel_id.value_type_name,
                            'spline',
                            idx,
                            logger.channel_id.color,
                            data,
                            logger.channel_id.value_unit_id.name)
                        series.append(series_data)

                    # Event and Information
                    threshold_event = "0 event"

                    if min_value == 9999:
                        min_value = '-'

                    if not min_date:
                        min_date = ''

                    if not max_date:
                        max_date = ''
                        max_value = '-'

                    if not last_date:
                        last_date = ''
                        last_value = '-'

                    data_event = {
                        'channel_id': logger.channel_id.id,
                        'color': logger.channel_id.color,
                        'name': logger.channel_id.name if logger.channel_id.name != False else logger.channel_id.value_type_id.name,
                        'unit_name': logger.channel_id.value_unit_id.name,
                        'threshold_event': threshold_event,
                        'last_date': last_date,
                        'last_value': last_value,
                        'min_date': min_date,
                        'min_value': min_value,
                        'max_date': max_date,
                        'max_value': max_value,
                        'avg_value': avg_value,
                        'alarm_events': alarm_events,
                        'need_totalizer': logger.channel_id.value_type_id.need_totalizer,
                        'show_consumption': logger.channel_id.show_consumption,
                        'last_totalizer': last_totalizer
                    }
                    events.append(data_event)

            idx = idx + 1
        return series, totalizers, events, is_totalizer

    def _set_chart_channels(self, logger_id, start_date, end_date):
        yAxis = []
        series = []
        yAxis_count = 0
        opposite = False
        add_hours = self.get_time_zone(logger_id)

        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        channels = logger.channel_ids.search([('logger_id', '=', logger_id),
                                              ('point_is_sensor', '=', True)])

        totalizers = []
        events = []
        value_units = []
        is_totalizer = False

        for channel in channels:

            last_date = ''
            last_value = 0

            if channel.display_on_chart:

                if not channel.value_unit_id.name in value_units:
                    value_units.append(channel.value_unit_id.name)
                    linkedTo = -1
                else:
                    value_units.append('0')
                    linkedTo = value_units.index(channel.value_unit_id.name)

                yaxis_data = self._set_yaxis(channel, opposite)

                # other_index = value_units.index(channel.value_unit_id.name)
                # if other_index != yAxis_count:
                if linkedTo > -1:
                    yaxis_data.update({
                        'linkedTo': linkedTo,
                    })

                yAxis.append(yaxis_data)

                if opposite:
                    opposite = False
                else:
                    opposite = True

            channel_values = []

            values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel.id),
                                                              ('dates', '>=', start_date),
                                                              ('dates', '<=', end_date)])

            channel_name = ''
            if channel.value_type_name:
                channel_name = channel.value_type_name

            if channel.point_id.name:
                channel_name += ' - ' + channel.point_id.name

            data_totalizer = {
                'channel_name': channel_name,
            }

            if channel.point_id.need_totalizer:
                is_totalizer = True
                initial_date, initial_value = self.get_initial(channel.id, end_date)
                data_totalizer.update({
                    'initial_date': initial_date,
                    'initial_value': initial_value,
                })

            last_totalizer = 0
            alarm_events = 0
            for value in values:

                # Value
                channel_value = value.channel_value

                # value_date = datetime.strptime(value.dates, '%Y-%m-%d %H:%M:%S')
                value_dates = value.dates + timedelta(hours=add_hours)
                unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                # Events
                if value.value_type == 'alarm':
                    alarm_events = alarm_events + 1

                data_val = [unixtime, round(channel_value, 3)]
                channel_values.append(data_val)

                last_date = value.dates + timedelta(hours=add_hours)
                last_value = round(channel_value, 3)
                last_totalizer = round(value.totalizer, 3)

            data_totalizer.update({
                'last_totalizer': last_totalizer,
                'last_date': last_date
            })

            if channel.point_id.need_totalizer:
                totalizers.append(data_totalizer)

            # Series
            if channel.display_on_chart:
                series_data = self._set_series(channel.name if channel.name != False else channel.value_type_id.name,
                                               yAxis_count,
                                               channel.color,
                                               channel_values,
                                               channel.value_unit_id.name)
                series.append(series_data)

                yAxis_count = yAxis_count + 1

            # Event and Information
            threshold_event = "0 event"

            data_event = {
                'channel_id': channel.id,
                'name': channel.name if channel.name != False else channel.value_type_id.name,
                'unit_name': channel.value_unit_id.name,
                'threshold_event': threshold_event,
                'last_date': last_date,
                'last_value': last_value,
                'alarm_events': alarm_events
            }
            events.append(data_event)

        # totalizers = {
        #     'initial_date': initial_date,
        #     'initial_value': initial_value,
        #     'totalizer': round(totalizer, 3)
        # }

        data = {
            'yAxis': yAxis,
            'series': series,
            'events': events,
            'is_totalizer': is_totalizer,
            'totalizers': totalizers
        }

        return data

    def set_main_alarm(self, logger_id, start_date, end_date):

        state_battery = {
            'enable': False,
            'src': 'icon_battery_disable.png',
            'last_date': 'N/A',
            'last_value': 'N/A',
            'alarm_events': 0
        }

        state_signal = {
            'enable': False,
            'src': 'icon_signal_disable.png',
            'last_date': 'N/A',
            'last_value': 'N/A',
            'alarm_events': 0
        }

        state_submerged = {
            'enable': False,
            'src': 'icon_submersion_disable.png',
            'last_date': 'N/A',
            'last_value': 'N/A',
            'alarm_events': 0
        }

        state_temperature = {
            'enable': False,
            'src': 'icon_temperature_disable.png',
            'last_date': 'N/A',
            'last_value': 'N/A',
            'alarm_events': 0
        }

        data = {
            'state_battery': state_battery,
            'state_signal': state_signal,
            'state_submerged': state_submerged,
            'state_temperature': state_temperature,
        }

        return data

    def _set_yaxis(self, channel, opposite):

        plotBands = []

        yAxis_data = {
            'title': {
                'text': channel.name if channel.name != False else channel.value_type_id.name
            },
            'opposite': opposite,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
            'plotBands': plotBands,
            'minPadding': 1
        }

        return yAxis_data

    def _set_series_data(self, value_type_name, chart_type, yAxis_count, color, data, value_unit_name):

        if value_unit_name:
            valueSuffix = value_unit_name
        else:
            valueSuffix = ''

        series_data = {
            'name': value_type_name,
            'type': chart_type,
            'yAxis': yAxis_count,
            'color': color,
            'zIndex': '1',
            'data': data,
            'tooltip': {
                'valueSuffix': ' ' + valueSuffix
            }
        }

        return series_data

    def get_initial(self, channel_id, start_date):
        initial_date = False
        initial_value = False
        initial = self.env['onpoint.logger.initial'].search([('channel_id', '=', channel_id),
                                                             ('dates', '<=', start_date)],
                                                            order='dates desc',
                                                            limit=1)

        if initial:
            initial_date, initial_value = initial.dates, initial.initial

        return initial_date, initial_value

    @api.model
    def get_map_data(self, logger_type=0, marker_type='logger_type', keyword=''):

        company = self.env.user.company_id

        if logger_type == 0:
            loggers = self.env['onpoint.logger'].sudo().search([('name', 'ilike', keyword), ('latitude', '!=', False), ('longitude', '!=', False)])
        else:
            loggers = self.env['onpoint.logger'].sudo().search([('name', 'ilike', keyword),
                                                                ('logger_type_id', '=', logger_type),
                                                                ('latitude', '!=', False),
                                                                ('longitude', '!=', False)])

        markers = []

        for logger in loggers:

            channel_info = "<table width='200vw'>"
            for channel in logger.channel_ids:
                if channel.display_on_chart:
                    channel_info += "<tr>"
                    channel_info += "<td width='50%'>" + channel.name if channel.name else channel.value_type_id.name if channel.value_type_id.name else "" + "</td>"
                    channel_info += "<td width='50%'>: " + channel.last_value + " " + channel.value_unit_name if channel.value_unit_name else "" + "</td>"
                    channel_info += "</tr>"

            channel_info += "</table>"

            if marker_type == 'logger_type':
                icon = logger.logger_type_id.image_128
            else:
                icon = logger.brand_id.image_128

            marker = {
                'id': logger.id,
                'name': logger.name,
                'brand_owner': logger.brand_owner,
                'logger_type_id': logger.logger_type_id.id,
                'logger_type_name': logger.logger_type_id.name,
                'icon': icon,
                'address': logger.address,
                'channel_info': channel_info,
                'position': {
                    'lat': logger.latitude,
                    'lng': logger.longitude
                },
            }

            markers.append(marker)

        data = {
            'company_logo': company.logo,
            'markers': markers

        }

        return data

    @api.model
    def get_realtime_data(self, logger_id):

        yAxis = []
        series = []
        events = []
        yAxis_count = 0
        opposite = False

        logger_data = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)

        channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id)])

        channel_params = {}
        value_units = []

        idx = 0
        for channel in channels:

            last_date = ''
            last_value = 0

            value_units.append(channel.value_unit_id.name)

            channel_params[idx] = {
                'value_type_name': channel.value_type_id.name,
                'color': channel.color,
                'value_unit_name': channel.value_unit_id.name
            }

            yAxis_data = self._set_yaxis(channel, opposite)

            other_index = value_units.index(channel.value_unit_id.name)
            if other_index != idx:
                yAxis_data.update({
                    'linkedTo': other_index
                })

            yAxis.append(yAxis_data)

            if opposite:
                opposite = False
            else:
                opposite = True

            idx = idx + 1

        _logger.debug('Value Units  %s ', value_units)

        ftp = FTP('www.wtccloud.net')
        self.login = ftp.login('loggersD3', 'loggersD3')
        data = []
        ftp.cwd('logd3')

        folder_name = str(logger_data.identifier).zfill(8)

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

                start_date = int(lines[1])
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
                    realtime_values = str(lines[idx_now]).split(',')

                    channel_values = []
                    value_date = start_date * 1000

                    last_date = ''
                    last_value = 0
                    min_value = 10

                    for realtime_value in realtime_values:
                        data_val = [value_date, float(realtime_value)]
                        if float(realtime_value) < min_value:
                            min_value = float(realtime_value)
                        channel_values.append(data_val)

                        last_date = value_date
                        last_value = float(realtime_value)

                        value_date = value_date + interval

                    series_data = self._set_series(channel_params[idx]['value_type_name'], yAxis_count,
                                                   channel_params[idx]['color'], channel_values,
                                                   channel_params[idx]['value_unit_name'])
                    series.append(series_data)

                    data_event = {
                        'name': channel_params[idx]['value_type_name'],
                        'unit_name': channel_params[idx]['value_unit_name'],
                        'last_date': last_date,
                        'last_value': last_value,
                    }
                    events.append(data_event)

                    idx_now = idx_now + 1
                    idx = idx + 1

        ftp.quit

        # yAxis[0].update({
        #     'min': min_value
        # })
        # yAxis[1].update({
        #     'min': min_value
        # })

        data = {
            'id': logger_data.id,
            'name': logger_data.name,
            'yAxis': yAxis,
            'series': series,
            'events': events
        }

        return data

    def act_enable_logger(self):
        self.update({
            'state': 'enabled'
        })

    def act_disable_logger(self):
        self.update({
            'state': 'disabled'
        })

    @api.model
    def act_print(self, logger_id):
        action = self.env.ref('onpoint_monitor.act_onpoint_logger')
        result = action.read()[0]

        res = self.env.ref('onpoint_monitor.view_onpoint_logger_form', False)
        form_view = [(res and res.id or False, 'form')]
        result['views'] = form_view
        result['res_id'] = logger_id

        return result

    @api.model
    def act_toggle_auto_refresh(self, logger_id):
        logger_data = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)
        logger_data.auto_refresh = not logger_data.auto_refresh
        return logger_data.auto_refresh


class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    # _rec_name = 'point_id'
    _inherits = {
        'onpoint.logger.threshold': 'threshold_id'
    }

    # @api.model
    # def _compute_show_channel(self):
    #     show_channel = False
    #     if self.point_is_sensor:
    #         if self.value_unit_id:
    #             show_channel = True
    #     else:
    #         show_channel = False
    #     return show_channel
    #

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    name = fields.Char()
    brand_owner = fields.Char()
    is_enabled = fields.Boolean(default=True)
    value_type_id = fields.Many2one('onpoint.value.type', string='Channel Type', index=True)
    value_type_name = fields.Char('onpoint.value.type', related='value_type_id.name', store=True)
    value_unit_id = fields.Many2one('onpoint.value.unit', string='Channel Unit', index=True)
    value_unit_name = fields.Char('onpoint.value.unit', related='value_unit_id.name')
    color = fields.Char(string='Channel Color Code', default="#4B9AFF")

    point_id = fields.Many2one('onpoint.logger.point',
                               string='Points',
                               required=True,
                               index=True,
                               domain="[('owner', '=', brand_owner)]")
    point_is_sensor = fields.Boolean('onpoint.logger.point', related='point_id.is_sensor')
    interval_minutes = fields.Integer(string='Interval', default=0)
    interval = fields.Integer(compute='_compute_interval')

    display_on_chart = fields.Boolean(default=True)
    show_channel = fields.Boolean(default=True)

    last_date = fields.Datetime(string='Last Date', compute='_compute_last_value', store=True)
    last_value = fields.Char(string='Last Value', compute='_compute_last_value', store=True)
    last_value_type = fields.Selection([
        ('trending', 'Trending'),
        ('alarm', 'Alarm')
    ], compute='_compute_last_value', store=True)

    show_consumption = fields.Boolean(default=False)

    last_initial = fields.Float(string='Last Initial', compute='_compute_last_initial')
    last_totalizer = fields.Float(string='Last Totalizer', compute='_compute_last_totalizer', default=0)

    value_ids = fields.One2many('onpoint.logger.value', 'channel_id')
    initial_ids = fields.One2many('onpoint.logger.initial', 'channel_id')

    @api.depends('name', 'point_id')
    def name_get(self):
        result = []
        for record in self:
            if record.name:
                result.append((record.id, record.name))
            else:
                result.append((record.id, record.point_id.name))
        return result

    def view_channel_values(self):
        view_id = self.env.ref('onpoint_monitor.view_channel_values_form').id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': view_id,
            'res_model': 'onpoint.logger.channel',
        }

    def _compute_interval(self):
        for record in self:
            record.interval = record.interval_minutes * 60

    @api.depends('value_ids.dates', 'value_ids.channel_value')
    def _compute_last_value(self):
        for record in self:
            last_value = record.value_ids.search([('channel_id', '=', record.id)], order='dates desc', limit=1)
            record.last_date = last_value.dates
            record.last_value = str(round(last_value.channel_value, 3))
            record.last_value_type = last_value.value_type

    def _compute_last_initial(self):
        for record in self:
            record.last_initial = 0
            if record.display_on_chart:
                last_initial = record.initial_ids.search([('channel_id', '=', record.id)], order='dates desc', limit=1)
                if last_initial:
                    record.last_inital = last_initial.initial

    def _compute_last_totalizer(self):
        for record in self:
            if record.value_type_name == 'Flow':
                last_totalizer = record.value_ids.search([('channel_id', '=', record.id)], order='dates desc', limit=1)
                if last_totalizer:
                    record.last_totalizer = last_totalizer.totalizer
                else:
                    last_initial = record.initial_ids.search([('channel_id', '=', record.id)], order='dates desc',
                                                             limit=1)
                    if last_initial:
                        record.last_totalizer = last_initial.initial
                    else:
                        record.last_totalizer = 0

    @api.onchange('value_type_id')
    def domain_value_unit_id(self):
        return {'domain': {'value_unit_id': [('value_type_id', '=', self.value_type_id.id)]}}

    # @api.onchange('point_id')
    # def domain_point_id(self):
    #     if self.logger_id.brand_id:
    #         brand_owner = self.logger_id.brand_owner
    #     else:
    #         brand_owner = ''
    #
    #     return {'domain': {'point_id': [('owner', '=', brand_owner)]}}


class OnpointLoggerThresholdHourly(models.Model):
    _name = 'onpoint.logger.threshold.hourly'

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    hours = fields.Selection([
        ('00', '00:00'), ('01', '01:00'), ('02', '02:00'), ('03', '03:00'), ('04', '04:00'),
        ('05', '05:00'), ('06', '06:00'), ('07', '07:00'), ('08', '08:00'), ('09', '09:00'),
        ('10', '10:00'), ('11', '11:00'), ('12', '12:00'), ('13', '13:00'), ('14', '14:00'),
        ('15', '15:00'), ('16', '16:00'), ('17', '17:00'), ('18', '18:00'), ('19', '19:00'),
        ('20', '20:00'), ('21', '21:00'), ('22', '22:00'), ('23', '23:00')], default='00', required=True,
    )
    min_value = fields.Float(required=True, default='0')
    max_value = fields.Float(required=True, default='0')


class OnpointLoggerInitial(models.Model):
    _name = 'onpoint.logger.initial'
    _order = 'dates desc'

    channel_id = fields.Many2one('onpoint.logger.channel',
                                 string='Channel',
                                 required=True,
                                 index=True,
                                 ondelete='cascade')
    dates = fields.Datetime(required=True)
    initial = fields.Float(required=True, default=0)


class OnpointLoggerValue(models.Model):
    _name = 'onpoint.logger.value'
    _order = 'dates asc'

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    channel_id = fields.Many2one('onpoint.logger.channel',
                                 string='Channel',
                                 required=True,
                                 index=True,
                                 ondelete='cascade')
    point_is_sensor = fields.Boolean('onpoint.logger.channel', related='channel_id.point_is_sensor')
    value_type = fields.Selection([
        ('trending', 'Trending'),
        ('alarm', 'Alarm')
    ], default='trending', index=True)
    dates = fields.Datetime(required=True, index=True)
    channel_value = fields.Float(required=True, digits=(12, 3))
    totalizer = fields.Float(string='Totatlizer', digits=(12, 3), default=0)

    @api.model
    def create(self, vals):
        try:
            data_exist_id = self.search([('logger_id', '=', vals['logger_id']),
                                         ('channel_id', '=', vals['channel_id']),
                                         ('value_type', '=', vals['value_type']),
                                         ('dates', '=', vals['dates'])])

            res = data_exist_id
            if not math.isnan(vals['channel_value']):
                if not data_exist_id:
                    res = super(OnpointLoggerValue, self).create(vals)

            return res
        except Exception as e:
            x = 1
            return False
            # continue

    def get_value_by_date(self, channel_id, dates):
        logger = self.env['onpoint.logger.value'].search([('channel_id', '=', channel_id),
                                                          ('dates', '<=', dates)],
                                                         limit=1,
                                                         order='dates desc')
        return logger.dates, logger.channel_value

    def get_data(self,
                 channel_id,
                 start_date,
                 end_date):
        values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel_id),
                                                          ('dates', '>=', start_date),
                                                          ('dates', '<=', end_date)])

        min_value = False
        min_date = False
        max_value = False
        max_date = False
        last_value = False
        last_date = False
        if values:
            last_idx = len(values) - 1
            values_sorted = values.sorted(key=lambda r: r.channel_value)
            min_value = values_sorted[0].channel_value
            min_date = values_sorted[0].dates
            max_value = values_sorted[last_idx].channel_value
            max_date = values_sorted[last_idx].dates
            values_sorted_by_date = values.sorted(key=lambda r: r.dates, reverse=True)
            last_value = values_sorted_by_date[0].channel_value
            last_date = values_sorted_by_date[0].dates

        result = {
            'values': values,
            'min_value': min_value,
            'min_date': min_date,
            'max_value': max_value,
            'max_date': max_date,
            'last_value': last_value,
            'last_date': last_date
        }

        return result


class OnpointViewLogger(models.Model):
    _name = 'onpoint.vw.logger'
    _auto = False

    logger_id = fields.Many2one('onpoint.logger', index=True, readonly=True)
    channel_id = fields.Many2one('onpoint.logger.channel', index=True, readonly=True)
    point_id = fields.Many2one('onpoint.logger.point', index=True, readonly=True)
    value_unit_id = fields.Many2one('onpoint.value.unit', index=True, readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
                create or replace view onpoint_vw_logger as (                 
                    select 
                        row_number()over() as id,
                        x.logger_id,
                        x.channel_id,
                        x.point_id,
                        x.value_unit_id
                    from 
                    ( 
                        select
                            ol.id as logger_id,
                            olc2.id as channel_id,
                            olc2.display_on_chart,
                            olp.id as point_id,
                            olc2.value_unit_id
                        from
                            onpoint_logger ol
                        inner join onpoint_logger_channel olc2 on ol.id = olc2.logger_id and olc2.display_on_chart = true
                        inner join onpoint_logger_point olp on olp.id = olc2.point_id
                      ) x
                    )
                """
        self.env.cr.execute(sql)
