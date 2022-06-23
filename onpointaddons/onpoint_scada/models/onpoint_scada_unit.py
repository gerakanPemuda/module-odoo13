from odoo import models, fields, api, tools
from odoo.http import request
from datetime import datetime, timezone, timedelta
from odoo.osv import expression
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointScadaSensorType(models.Model):
    _name = 'onpoint.scada.sensor.type'

    name = fields.Char(required=True)
    uom = fields.Char(required=True)


class OnpointScadaLocation(models.Model):
    _name = 'onpoint.scada.location'
    _inherit = ['image.mixin']

    name = fields.Char(required=True)
    unit_ids = fields.One2many('onpoint.scada.unit', 'location_id')

    def get_data(self, location_id):
        location_data = self.env['onpoint.scada.location'].search([('id', '=', location_id)])
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled')])

        return location_data, loggers

    def act_view_location(self):
        url_location = '/location/' + str(self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url_location
        }


class OnpointScadaUnit(models.Model):
    _name = 'onpoint.scada.unit'
    _order = 'sequence'

    name = fields.Char()
    location_id = fields.Many2one('onpoint.scada.location', required=True, string='Location', ondelete='cascade',
                                  index=True)
    sequence = fields.Integer(default=1, required=True)
    state = fields.Selection([
        ('enabled', 'Enabled'),
        ('disabled', 'Disabled')
    ], default='enabled')
    auto_refresh = fields.Boolean(default=False)
    line_ids = fields.One2many('onpoint.scada.unit.line', 'unit_id')

    @api.onchange('location_id', 'sensor_type_id')
    def generate_name(self):
        for record in self:
            if record.sensor_type_id and record.location_id:
                record.name = record.sensor_type_id.name + ' - ' + record.location_id.name
            else:
                record.name = '-'

    def get_data(self, unit_id):
        unit = self.env['onpoint.scada.unit'].search([('id', '=', unit_id)])
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled')])
        return unit, loggers

    @api.model
    def get_unit_data(self, unit_id, range_date, period='1d', option_hour='00', interval='900'):
        unit = self.env['onpoint.scada.unit'].search([('id', '=', unit_id)])
        other_units = []
        for other_unit in unit.location_id.unit_ids:
            other_units.append({
                'unit_id': other_unit.id,
                'unit_name': other_unit.name
            })

        y_axis, series, stats = self.get_data_detail(unit_id, range_date, option_hour, interval)
        x = 1
        data = {
            'location_id': unit.location_id.id,
            'location_name': unit.location_id.name,
            'unit': unit,
            'unit_id': unit.id,
            'unit_name': unit.name,
            'other_units': other_units,
            'period': period,
            'interval': interval,
            'option_hour': option_hour,
            'yAxis': y_axis,
            'series': series,
            'stats': stats
        }
        return data

    def get_data_detail(self, unit_id, range_date, option_hour, interval):
        add_hours = 0
        subtract_hours = 6
        range_dates = range_date.split(' - ')

        start_hour = int(option_hour)
        if start_hour == 0:
            end_hour = 23
        else:
            end_hour = start_hour - 1

        start_hours = f'{start_hour:02}'
        end_hours = f'{end_hour:02}'

        start_date = (datetime.strptime(range_dates[0] + ' ' + start_hours + ':00:00', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
        end_date = (datetime.strptime(range_dates[1] + ' ' + end_hours + ':59:59', "%d/%m/%Y %H:%M:%S") - timedelta(
            hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")

        unit = self.env['onpoint.scada.unit'].search([('id', '=', unit_id)])

        opposite = False
        y_axis = []
        series = []
        stats = []

        idx = 0
        for line in unit.line_ids:
            detail_data = []
            min_date = False
            min_value = 9999
            max_date = False
            max_value = 0
            avg_value = 0
            total_value = 0
            total_data = 0
            last_date = False
            last_value = 0

            if not line.is_parameter:
                sql = """select x.unit_line_id, x.sensor_value, x.sensor_dates, (extract('epoch' from sensor_dates)) as sensor_timestamp
                         from (
                             select unit_line_id, avg(sensor_value) as sensor_value,
                             to_timestamp(floor((extract('epoch' from sensor_date) / %s)) * %s)::timestamp as sensor_dates
                             from onpoint_scada_unit_detail osud
                             group by unit_line_id, sensor_dates) x
                         where x.unit_line_id = %s and x.sensor_dates >= %s and x.sensor_dates <= %s
                         order by x.unit_line_id, x.sensor_dates"""
                # sql = """select x.unit_line_id, x.sensor_value, x.sensor_dates, (extract('epoch' from sensor_dates)) as sensor_timestamp
                #          from (
                #              select unit_line_id, sensor_value,
                #              to_timestamp(floor((extract('epoch' from sensor_date) / %s)) * %s)::timestamp as sensor_dates
                #              from onpoint_scada_unit_detail osud
                #              where unit_line_id = %s and sensor_date >= %s and sensor_date <= %s
                #          ) x
                #          group by x.unit_line_id, x.sensor_value, x.sensor_dates
                #          order by x.unit_line_id, x.sensor_dates"""
                self.env.cr.execute(sql, (interval, interval, line.id, start_date, end_date))
                details = self._cr.fetchall()

                for detail in details:
                    # Value
                    # sensor_value = detail.sensor_value
                    # sensor_date = detail.sensor_date

                    sensor_value = detail[1]
                    sensor_date = detail[2]
                    sensor_timestamp = detail[3]
                    sensor_date = sensor_date - timedelta(hours=subtract_hours)
                    unixtime = (sensor_date - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()

                    data_val = [round(unixtime) * 1000, round(sensor_value, 2)]
                    detail_data.append(data_val)

                    last_value = sensor_value
                    last_date = sensor_date

                    total_value += last_value
                    total_data += 1

                    if last_value < min_value:
                        min_date = sensor_date
                        min_value = last_value

                    if last_value > max_value:
                        max_date = last_date
                        max_value = last_value

                if total_data > 0:
                    avg_value = round(total_value / total_data, 3)
                else:
                    avg_value = 0

                stat_value = {
                    'unit_line_id': line.id,
                    'name': line.sensor_type_id.name,
                    'sensor_type_uom': line.sensor_type_id.uom,
                    'last_date': last_date.strftime('%d-%m-%Y %H:%M:%S') if last_date else '',
                    'last_value': round(last_value, 2),
                    'min_date': min_date.strftime('%d-%m-%Y %H:%M:%S') if min_date else '',
                    'min_value': round(min_value, 2) if min_value != 9999 else 0,
                    'max_date': max_date.strftime('%d-%m-%Y %H:%M:%S') if max_date else '',
                    'max_value': round(max_value, 2),
                    'avg_value': round(avg_value, 2),
                }
                stats.append(stat_value)

                series_data = {
                    'name': line.sensor_type_id.name,
                    'uom': line.sensor_type_id.uom,
                    'type': 'spline',
                    'yAxis': idx,
                    'data': detail_data,
                }
                series.append(series_data)
                idx += 1

                y_axis_data = {
                    'title': {
                        'text': line.sensor_type_id.name
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
            else:
                sensor_paramaters = self.env['onpoint.scada.sensor.parameter'].search([('unit_line_id', '=', line.id),
                                                                                       ('create_date', '>=', start_date),
                                                                                       ('create_date', '<=', end_date)])
                data_counter = 0
                sensor_date = False
                for detail in sensor_paramaters:
                    if data_counter == 0:
                        if datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S') < detail.create_date:
                            previous_data = self.env['onpoint.scada.sensor.parameter'].search([('unit_line_id', '=', line.id),
                                                                                               ('create_date', '<', start_date)],
                                                                                              order='create_date desc',
                                                                                              limit=1)
                            if previous_data:
                                sensor_value = previous_data.parameter_value
                                sensor_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                            else:
                                sensor_value = 0
                                sensor_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')

                            sensor_date = sensor_date - timedelta(hours=subtract_hours)
                            unixtime = (sensor_date - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()

                            data_val = [round(unixtime) * 1000, round(sensor_value, 2)]
                            detail_data.append(data_val)

                    sensor_value = detail.parameter_value
                    sensor_date = detail.create_date
                    last_value = sensor_value
                    last_date = sensor_date

                    sensor_date = sensor_date - timedelta(hours=subtract_hours)
                    unixtime = (sensor_date - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()

                    data_val = [round(unixtime) * 1000, round(sensor_value, 2)]
                    detail_data.append(data_val)

                    data_counter += 1

                if last_date:
                    if last_date < datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S'):
                        unixtime = (datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S') - datetime(1970, 1, 1, 0, 0, 0)).total_seconds()

                        data_val = [round(unixtime) * 1000, round(last_value, 2)]
                        detail_data.append(data_val)

                series_data = {
                    'name': line.sensor_type_id.name,
                    'type': 'line',
                    'step': True,
                    'yAxis': idx,
                    'data': detail_data
                }
                series.append(series_data)
                idx += 1

                y_axis_data = {
                    'title': {
                        'text': line.sensor_type_id.name
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

        return y_axis, series, stats

    def toggle_auto_refresh(self, unit_id):
        unit = self.env['onpoint.scada.unit'].search([('id', '=', unit_id)])
        if unit:
            if unit.auto_refresh:
                auto_refresh = not unit.auto_refresh
            else:
                auto_refresh = True

            unit.write({
                'auto_refresh': auto_refresh
            })

    def generate_pdf_report(self):
        x = 1
        data = {
            'x': 'a'
        }
        return self.env.ref('onpoint_scada.act_onpoint_scada_unit_report').report_action(self, data=data)


class OnpointScadaLine(models.Model):
    _name = 'onpoint.scada.unit.line'
    _rec_name = 'sensor_type_id'

    unit_id = fields.Many2one('onpoint.scada.unit',
                              required=True,
                              string='Sensor',
                              ondelete='cascade',
                              index=True)
    unit_name = fields.Char(related='unit_id.name')
    category = fields.Selection([
        ('flow', 'Flow'),
        ('pressure', 'Pressure'),
        ('quality', 'Quality')
    ], default='flow')
    sensor_type_id = fields.Many2one('onpoint.scada.sensor.type',
                                     required=True,
                                     string='Sensor Type',
                                     ondelete='cascade', index=True)
    sensor_type_name = fields.Char(related='sensor_type_id.name')
    is_parameter = fields.Boolean(string='Is Parameter', default=False)
    parameter_id = fields.Many2one('onpoint.scada.parameter', string='Parameter', index=True)

    sensor_type_uom = fields.Char(related='sensor_type_id.uom', string='Unit of Measurement')
    sensor_last_value = fields.Float(compute='compute_last_value')

    overrange_enabled = fields.Boolean(default=False)
    overrange_threshold = fields.Float(string='Overrange', default='0')

    hi_hi_enabled = fields.Boolean(default=False)
    hi_hi_threshold = fields.Float(string='Hi Hi', default='0')

    hi_enabled = fields.Boolean(default=False)
    hi_threshold = fields.Float(string='Hi', default='0')

    lo_enabled = fields.Boolean(default=False)
    lo_threshold = fields.Float(string='Lo', default='0')

    lo_lo_enabled = fields.Boolean(default=False)
    lo_lo_threshold = fields.Float(string='Lo Lo', default='0')

    underrange_enabled = fields.Boolean(default=False)
    underrange_threshold = fields.Float(string='Underrange', default='0')

    detail_ids = fields.One2many('onpoint.scada.unit.detail', 'unit_line_id')
    alarm_ids = fields.One2many('onpoint.scada.alarm', 'unit_line_id')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('unit_name', '=ilike', name + '%'), ('sensor_type_name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        data = self.search(domain + args, limit=limit)
        return data.name_get()

    @api.depends('unit_id', 'sensor_type_id')
    def name_get(self):
        result = []
        for record in self:
            name = record.unit_name + ' - ' + record.sensor_type_name

            result.append((record.id, name))
        return result

    def compute_last_value(self):
        for record in self:
            last_value = record.detail_ids.search([('unit_line_id', '=', record.id)], order='sensor_date desc', limit=1)
            record.sensor_last_value = last_value.sensor_value


class OnpointScadaDetail(models.Model):
    _name = 'onpoint.scada.unit.detail'

    unit_line_id = fields.Many2one('onpoint.scada.unit.line', required=True, string='Sensor', ondelete='cascade',
                                   index=True)
    sensor_date = fields.Datetime(default=fields.Datetime.now(), required=True, string='Date', index=True)
    sensor_value = fields.Float(default=0, required=True, string='Value')


class OnpointScadaAlarm(models.Model):
    _name = 'onpoint.scada.alarm'

    unit_line_id = fields.Many2one('onpoint.scada.unit.line', required=True, string='Sensor', ondelete='cascade',
                                   index=True)
    alarm = fields.Char(required=True, string='Alarm')
    alarm_value = fields.Float(default=0, required=True, string='Value')
    is_sent = fields.Boolean(default=False)
