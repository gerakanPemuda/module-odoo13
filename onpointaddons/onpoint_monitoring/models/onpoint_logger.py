from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ftplib import FTP
import csv
import io
# from random import randrange

# from pymodbus.client.sync import ModbusTcpClient
# from pymodbus.client.async import ModbusTcpClient as ModbusClient

import logging
_logger = logging.getLogger(__name__)


class OnpointLoggerBrand(models.Model):
    _name = 'onpoint.logger.brand'
    
    name = fields.Char(required=True)
    image = fields.Binary()


class OnpointLoggerType(models.Model):
    _name = 'onpoint.logger.type'
    
    name = fields.Char(required=True)
    is_threshold_hourly = fields.Boolean(string="Use Hourly Threshold", default=False)

class OnpointSebaSpec(models.Model):
    _name = 'onpoint.seba.spec'
    
    name = fields.Char(required=True)
    pos = fields.Integer()
    length = fields.Integer(default=1)
    function_name = fields.Char(required=True)
    table_name = fields.Char()
    field_name = fields.Char()


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _inherit = ['onpoint.seba']
    
    name = fields.Char(required=True)
    logger_image = fields.Binary()
    brand_id = fields.Many2one('onpoint.logger.brand', required=True, index=True )
    identifier = fields.Char(string='Identifier', required=True)
    logger_type_id = fields.Many2one('onpoint.logger.type', required=True, index=True )
    logger_type_name = fields.Char('onpoint.logger.type', related='logger_type_id.name')
    is_threshold_hourly = fields.Boolean('onpoint.logger.type', related='logger_type_id.is_threshold_hourly')
    zone_id = fields.Many2one('onpoint.zone', string='Zone', index=True)
    dma_id = fields.Many2one('onpoint.dma', string='DMA', index=True)
    department_id = fields.Many2one('hr.department', index=True )
    address = fields.Text(required=True)
    simcard = fields.Char()
    remarks = fields.Text()
    nosal = fields.Char()
    latitude = fields.Char()
    longitude = fields.Char()
    elevation = fields.Float()
    is_realtime = fields.Boolean(string='Realtime', default=False)

    # threshold
    leakage = fields.Float()
    leakage_interval_minutes = fields.Integer(string="Interval (minutes)")
    leakage_interval_days = fields.Integer(string="Interval (days)")
    count_logger_value = fields.Integer(compute='_count_logger_value')
    is_logger = fields.Boolean()
    image = fields.Binary("Image", attachment=True, help="This field holds the image used for as favicon")
    last_data_date = fields.Datetime(string='Last Available Data', compute='_get_last_data_date')

    channel_ids = fields.One2many('onpoint.logger.channel', 'logger_id')
    threshold_hourly_ids = fields.One2many('onpoint.logger.threshold.hourly', 'logger_id')
    value_ids = fields.One2many('onpoint.logger.value', 'logger_id')

    def _count_logger_value(self):
        self.count_logger_value = self.env['onpoint.logger.value'].search_count([('logger_id', '=', self.id)])

    def action_to_logger_value(self):
        return {
            'name': 'Logger Value',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'onpoint.logger.value',
            'domain': [('logger_id','=',self.id)],
            }


    @api.one
    def _get_last_data_date(self):

        logger_values = self.env['onpoint.logger.value'].search([('logger_id', '=', self.id)], order='dates desc', limit=1)
        if logger_values.dates != False:
            logger_last_date = datetime.strptime(logger_values.dates, ("%Y-%m-%d %H:%M:%S"))
            self.last_data_date = (logger_last_date - timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            self.last_data_date = ''


    def read_ftp(self):
        ftp = FTP('www.wtccloud.net')
        ftp.login('pointorange', 'pointorange')
        data = []
        ftp.cwd('files')
        
        files = ftp.nlst()
        value_ids = []

        for file_name in files:
            check_file_name = self.identifier + '_T_' in file_name
            if check_file_name:
                _logger.debug('file : %s', file_name)

                temp_file = io.BytesIO()

                ftp.retrbinary('RETR ' + file_name, temp_file.write)
                temp_file.seek(0)

                csv_file = csv.DictReader(io.TextIOWrapper(temp_file, newline=None), delimiter=',')

                for channel in self.channel_ids:
                    _logger.debug('Points : %s', channel.points)
                    
                    idx = 0
                    for row in csv_file:
                        if idx > 0:
                            for key in row: 
                                if channel.points in key :

                                    if row[key] != '':

                                        value_date = datetime.strptime(row['Date & Time'], '%Y/%m/%d %H:%M:%S')
                                        value_vals = {
                                            'channel_id' : channel.id,
                                            'dates' : value_date,
                                            'channel_value' : row[key]
                                        }

                                        row_value = (0, 0, value_vals)
                                        value_ids.append(row_value)

                                    # _logger.debug('datetime : %s - %s', row['Date & Time'], row[key])

                        idx = idx + 1
                    
                    temp_file.seek(0)
                    

                temp_file.close()

        logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

        logger.sudo().update({
            'value_ids' : value_ids
        })


        # --> dir list end


        ftp.quit


    def read_ftp_seba(self):

        ftp = FTP('www.wtccloud.net')
        ftp.login('loggersD3', 'loggersD3')
        data = []
        ftp.cwd('logd3')
        
        folder_name = str(self.identifier).zfill(8)

        ftp.cwd(folder_name)

        files = ftp.nlst()
        value_ids = []

        for file_name in files:
            check_file_name = 'measdata_' in file_name
            if check_file_name:
                _logger.debug('file : %s', file_name)

                temp_file = io.BytesIO()

                ftp.retrbinary('RETR ' + file_name, temp_file.write)
                temp_file.seek(0)

                stream_data = temp_file.read()

                _logger.debug('stream %s', stream_data)


                buffer = temp_file.getbuffer()

                data = self._process_block1(buffer)

                channel_values = self._process_block7(buffer, data)

                for channel in self.channel_ids:
                    # _logger.debug('Points : %s', channel.points)
                    
                    idx = 0
                    for channel_value in channel_values:
                        # _logger.debug('%s --> dates : %s = %s', channel.points, channel_value['dates'], channel_value[channel.points])

                        value_date = datetime.strptime(channel_value['dates'], '%Y-%m-%d %H:%M:%S')
                        value_vals = {
                            'channel_id' : channel.id,
                            'dates' : value_date,
                            'channel_value' : channel_value[channel.points]
                        }

                        row_value = (0, 0, value_vals)
                        value_ids.append(row_value)

                ftp.rename(file_name, 'archives/' + file_name)

        logger = self.env['onpoint.logger'].search([('id', '=', self.id)])

        logger.sudo().update({
            'value_ids' : value_ids
        })

        ftp.quit


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
    def get_data(self, logger_id, range_date, option, period):
        # uid = request.session.uid
        range_dates = range_date.split(' - ')

        start_date = datetime.strptime(range_dates[0], ("%d/%m/%Y")).strftime("%Y-%m-%d")
        end_date = datetime.strptime(range_dates[1], ("%d/%m/%Y")).strftime("%Y-%m-%d")

        logger_data = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)

        logger = {
            'id'    : logger_data.id,
            'name'  : logger_data.name
        }

        # Channels
        channels    = self._set_chart_channels(logger_id, start_date, end_date)
        logger.update(channels)


        # Channel Information
        # channel_information = self._get_channel_information(logger)
        # logger[0].update(channel_information)
        # End of Channel Information

        # chart_parameters = self._set_chart_parameters(logger_id, start_date, end_date, option, period)
        # logger[0].update(chart_parameters)

        return logger

    def _get_channel_information(self, logger_id):

        # channel_on_class = "logger-channel-status-on"
        # channel_on_icon = "fa fa-check"

        # channel_off_class = "logger-channel-status-off"
        # channel_off_icon = "fa fa-times"

        # channel_value = "NaN"
        # channel_value_type = "n/a"
        # channel_value_unit = ""


        # ch1_active_class = channel_off_class
        # ch1_active_icon = channel_off_icon
        # ch1_active_value = channel_value
        # ch1_active_value_type = channel_value_type
        # ch1_active_value_unit = channel_value_unit

        # ch2_active_class = channel_off_class
        # ch2_active_icon = channel_off_icon
        # ch2_active_value = channel_value
        # ch2_active_value_type = channel_value_type
        # ch2_active_value_unit = channel_value_unit

        # ch3_active_class = channel_off_class
        # ch3_active_icon = channel_off_icon
        # ch3_active_value = channel_value
        # ch3_active_value_type = channel_value_type
        # ch3_active_value_unit = channel_value_unit

        # ch4_active_class = channel_off_class
        # ch4_active_icon = channel_off_icon
        # ch4_active_value = channel_value
        # ch4_active_value_type = channel_value_type
        # ch4_active_value_unit = channel_value_unit

        # if logger[0]['ch1_active']:
        #     ch1_active_class = channel_on_class
        #     ch1_active_icon = channel_on_icon
        #     ch1_active_value = 0
        #     if logger[0]['ch1_value_type_id']:
        #         ch1_active_value_type = logger[0]['ch1_value_type_id'][1]
            
        #     if logger[0]['ch1_value_unit_id']:
        #         ch1_active_value_unit = logger[0]['ch1_value_unit_id'][1]

        # if logger[0]['ch2_active']:
        #     ch2_active_class = channel_on_class
        #     ch2_active_icon = channel_on_icon
        #     ch2_active_value = 0
        #     if logger[0]['ch2_value_type_id']:
        #         ch2_active_value_type = logger[0]['ch2_value_type_id'][1]
            
        #     if logger[0]['ch2_value_unit_id']:
        #         ch2_active_value_unit = logger[0]['ch2_value_unit_id'][1]

        # if logger[0]['ch3_active']:
        #     ch3_active_class = channel_on_class
        #     ch3_active_icon = channel_on_icon
        #     ch3_active_value = 0
        #     if logger[0]['ch3_value_type_id']:
        #         ch3_active_value_type = logger[0]['ch3_value_type_id'][1]
            
        #     if logger[0]['ch3_value_unit_id']:
        #         ch3_active_value_unit = logger[0]['ch3_value_unit_id'][1]

        # if logger[0]['ch4_active']:
        #     ch4_active_class = channel_on_class
        #     ch4_active_icon = channel_on_icon
        #     ch4_active_value = 0
        #     if logger[0]['ch4_value_type_id']:
        #         ch4_active_value_type = logger[0]['ch4_value_type_id'][1]
            
        #     if logger[0]['ch4_value_unit_id']:
        #         ch4_active_value_unit = logger[0]['ch4_value_unit_id'][1]


        # data = {
        #     'ch1_active_class' : ch1_active_class,
        #     'ch1_active_icon' : ch1_active_icon,
        #     'ch1_active_value' : ch1_active_value,
        #     'ch1_active_value_type' : ch1_active_value_type,
        #     'ch1_active_value_unit' : ch1_active_value_unit,

        #     'ch2_active_class' : ch2_active_class,
        #     'ch2_active_icon' : ch2_active_icon,
        #     'ch2_active_value' : ch2_active_value,
        #     'ch2_active_value_type' : ch2_active_value_type,
        #     'ch2_active_value_unit' : ch2_active_value_unit,

        #     'ch3_active_class' : ch3_active_class,
        #     'ch3_active_icon' : ch3_active_icon,
        #     'ch3_active_value' : ch3_active_value,
        #     'ch3_active_value_type' : ch3_active_value_type,
        #     'ch3_active_value_unit' : ch3_active_value_unit,

        #     'ch4_active_class' : ch4_active_class,
        #     'ch4_active_icon' : ch4_active_icon,
        #     'ch4_active_value' : ch4_active_value,
        #     'ch4_active_value_type' : ch4_active_value_type,
        #     'ch4_active_value_unit' : ch4_active_value_unit,

        # }

        # return data

        data = {}

        return data

    def _set_chart_channels(self, logger_id, start_date, end_date):
        yAxis = []
        series = []
        yAxis_count = 0
        opposite = False
        overrange_threshold = 99999
        hi_hi_threshold = 99999
        hi_threshold = 99999
        lo_threshold = -99999
        lo_lo_threshold = -99999
        underrange_threshold = -99999


        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])

        channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id)])

        events = []
        value_units = []
        for channel in channels:

            last_date = ''
            last_value = 0

            value_units.append(channel.value_unit_id.name)

            yAxis_data = self._set_yAxis(channel, opposite)

            other_index = value_units.index(channel.value_unit_id.name)
            if other_index != yAxis_count:
                yAxis_data.update({
                    'linkedTo': other_index
                }) 


            yAxis.append(yAxis_data)

            if opposite:
                opposite = False
            else:
                opposite = True

            overrange_event = 0
            hi_hi_event = 0
            hi_event = 0
            lo_event = 0
            lo_lo_event = 0
            underrange_event = 0

            if channel.overrange_enabled:
                overrange_threshold = channel.overrange_threshold
            else:
                overrange_threshold = 99999
            
            if channel.hi_hi_enabled:
                hi_hi_threshold = channel.hi_hi_threshold
            else:
                hi_hi_threshold = 99999

            if channel.hi_enabled:
                hi_threshold = channel.hi_threshold
            else:
                hi_threshold = 99999

            if channel.lo_enabled:
                lo_threshold = channel.lo_threshold
            else:
                lo_threshold = -99999

            if channel.lo_lo_enabled:
                lo_lo_threshold = channel.lo_lo_threshold
            else:
                lo_lo_threshold = -99999

            if channel.underrange_enabled:
                underrange_threshold = channel.underrange_threshold
            else:
                underrange_threshold = -99999

            channel_values = []
            prev_raw_value = None

            values = self.env['onpoint.logger.value'].search([('channel_id', '=', channel.id), ('dates', '>=', start_date), ('dates', '<=', end_date)])
            
            for value in values:

                # Value
                if channel.value_type_id.name == 'Flow' and self.brand_id.name == 'Point Orange':
                    channel_value = self._get_flow(prev_raw_value, channel.id, value.dates, value.channel_value)
                else:
                    channel_value = value.channel_value

                value_date = datetime.strptime(value.dates, '%Y-%m-%d %H:%M:%S')
                unixtime = (value_date - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                # Events
                if channel_value > overrange_threshold:
                    overrange_event = overrange_event + 1
                else:
                    if channel_value > hi_hi_threshold:
                        hi_hi_event = hi_hi_event + 1
                    else:
                        if channel_value > hi_threshold:
                            hi_event = hi_event + 1
                
                if channel_value < underrange_threshold:
                    underrange_event = underrange_event + 1
                else:
                    if channel_value < lo_lo_threshold:
                        lo_lo_event = lo_lo_event + 1
                    else:
                        if channel_value < lo_threshold:
                            lo_event = lo_event + 1

                # data_val = { 'x': unixtime, 'y': round(channel_value, 3), 'option': var_option}
                data_val = [unixtime, round(channel_value, 3)]
                # data_val = { 'x': unixtime, 'y': round(channel_value, 3), 'marker': {'symbol': 'url(https://www.highcharts.com/samples/graphics/sun.png)'}}
                channel_values.append(data_val)

                last_date = value_date
                last_value = round(channel_value, 3)


            # Series
            series_data = self._set_series(channel.value_type_id.name, yAxis_count, channel.color, channel_values, channel.value_unit_id.name)
            series.append(series_data)

            # Event and Information
            threshold_event = ""
            if overrange_event > 0:
                threshold_event = threshold_event + str(overrange_event) + " times over Overrange Threshold\n"
            
            if hi_hi_event > 0:
                threshold_event = threshold_event + str(hi_hi_event) + " times over Hi Hi Threshold\n"

            if hi_event > 0:
                threshold_event = threshold_event + str(hi_event) + " times over Hi Threshold\n"

            if lo_event > 0:
                threshold_event = threshold_event + str(lo_event) + " times below Lo Threshold\n"

            if lo_lo_event > 0:
                threshold_event = threshold_event + str(lo_lo_event) + " times below Lo Lo Threshold\n"

            if underrange_event > 0:
                threshold_event = threshold_event + str(underrange_event) + " times below Underrange Threshold\n"


            if threshold_event == "":
                threshold_event = "0 event"


            data_event = {
                'name': channel.value_type_id.name,
                'unit_name': channel.value_unit_id.name,
                'threshold_event' : threshold_event,
                'overrange_event' : overrange_event,
                'hi_hi_event': hi_hi_event,
                'hi_event': hi_event,
                'lo_event': lo_event,
                'lo_lo_event': lo_lo_event,
                'underrange_event' : underrange_event,
                'last_date': last_date,
                'last_value': last_value,
            }
            events.append(data_event)

            yAxis_count = yAxis_count + 1


        data = {
            'yAxis': yAxis,
            'series': series,
            'events': events
        }

        return data

    def _get_flow(self, prev_raw_value, channel_id, channel_date, channel_value):

        if prev_raw_value is None:

            prev_channel_value = self.env['onpoint.logger.value'].search([('channel_id', '=', channel_id), ('dates', '<', channel_date)], order='dates desc', limit=1)

            if not prev_channel_value.exists():
                prev_raw_value = channel_value
            else:
                prev_raw_value = prev_channel_value.channel_value

        
        raw_value = channel_value - prev_raw_value
        prev_raw_value = channel_value

        real_value = (raw_value * 10) / 300

        return real_value

    def _set_yAxis(self, channel, opposite):

        plotBands = []

        # channel_threshold_max = 9999

        # if channel.overrange_enabled:

        #     plotBand = self._set_plotBand(channel.overrange_threshold, channel_threshold_max, '#000022', 'Overrange')
        #     plotBands.append(plotBand)
        #     channel_threshold_max = channel.overrange_threshold
        
        # if channel.hi_hi_enabled:

        #     plotBand = self._set_plotBand(channel.hi_hi_threshold, channel_threshold_max, '#d2db25', 'Hi Hi')
        #     plotBands.append(plotBand)
        #     channel_threshold_max = channel.hi_hi_threshold

        # if channel.hi_enabled:

        #     plotBand = self._set_plotBand(channel.hi_threshold, channel_threshold_max, '#84b025', 'Hi')
        #     plotBands.append(plotBand)
        #     channel_threshold_max = channel.hi_threshold


        yAxis_data = {
            'title': {
                'text': channel.value_type_id.name
            },
            'opposite': opposite,
            'minorGridLineWidth': 0,
            'gridLineWidth': 0,
            'plotBands': plotBands
        }

        return yAxis_data

    def _set_plotBand(self, channel_threshold_from, channel_threshold_to, color, title):

        plotBand = {
            'from' : channel_threshold_from,
            'to' : channel_threshold_to,
            'color': '#000000',
            'label': {
                'text': title,
                'style': '#606060'
            }
        }

        return plotBand

    def _set_series(self, value_type_name, yAxis_count, color, data, value_unit_name):

        if value_unit_name:
            valueSuffix = value_unit_name
        else:
            valueSuffix = ''

        series_data = {
            'name': value_type_name,
            'type': 'spline',
            'yAxis': yAxis_count,
            'color': color,
            'zIndex': '1',
            'data': data,
            'tooltip': {
                'valueSuffix': ' ' + valueSuffix
            }
        }

        return series_data

    def _set_threshold_hourly(self, value_type_name, yAxis_count, color, data, value_unit_name):

        if value_unit_name:
            valueSuffix = value_unit_name
        else:
            valueSuffix = ''

        series_data = {
            'name': 'Hourly Threshold',
            'type': 'arearange',
            'lineWidth': '1',
            'linkedTo': ':previous',
            'color': color,
            'fillOpacity': '0.2',
            'zIndex': '0',
            'data': data,
            'marker': {
                'enabled': 0
            }
        }

        return series_data


    def _set_threshold_area(self, logger_id):

        thresholds = self.env['onpoint.logger.threshold.hourly'].search([('logger_id', '=', logger_id)])


    @api.model
    def get_map_data(self):

        loggers = self.env['onpoint.logger'].sudo().search([])

        markers = []

        for logger in loggers:

            marker = {
                'id': logger.id,
                'name': logger.name,
                'logger_type_name': logger.logger_type_id.name,
                'address': logger.address,
                'position': {
                    'lat': logger.latitude,
                    'lng': logger.longitude
                },
            }

            markers.append(marker)

        data = {
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
              'value_type_name' : channel.value_type_id.name,
              'color': channel.color,
              'value_unit_name': channel.value_unit_id.name
            }

            yAxis_data = self._set_yAxis(channel, opposite)

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
        ftp.login('loggersD3', 'loggersD3')
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


                    for realtime_value in realtime_values:
                        data_val = [value_date, float(realtime_value)]
                        channel_values.append(data_val)

                        last_date = value_date
                        last_value = float(realtime_value)

                        value_date = value_date + interval


                    series_data = self._set_series(channel_params[idx]['value_type_name'], yAxis_count, channel_params[idx]['color'], channel_values, channel_params[idx]['value_unit_name'])
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

        data = {
            'id': logger_data.id,
            'name': logger_data.name,
            'yAxis': yAxis,
            'series': series,
            'events': events
        }

        return data





    # def get_modbus_data(self):
    #     client = ModbusTcpClient('127.0.0.1')
    #     # rq = client.write_coil(1, True)
    #     # rr = client.read_coils(1,1)        

    #     response = client.read_holding_registers(0x00,4,unit=1)
    #     _logger.debug('Modbus : %s', response.registers)
    #     client.close()

class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    _rec_name = 'value_type_id'
    
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade')
    is_enabled = fields.Boolean(default=True)
    value_type_id = fields.Many2one('onpoint.value.type', string='Channel Type', required=True)    
    value_unit_id = fields.Many2one('onpoint.value.unit', string='Channel Unit', required=True)
    color = fields.Char(string='Channel Color Code', default="#4B9AFF")

    # Point Orange
    points = fields.Selection([
        ('ch1', 'Channel 1'),
        ('ch2', 'Channel 2'),
        ('ch3', 'Channel 3'),
        ('ch4', 'Channel 4')
    ], default='ch1', string="Points", required=True)
    interval = fields.Integer(string='Interval')

    # Threshold
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

    value_ids = fields.One2many('onpoint.logger.value', 'channel_id')


    @api.multi
    def view_channel_values(self):
        view_id = self.env.ref('onpoint_monitoring.view_channel_values_form').id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': view_id,
            'res_model': 'onpoint.logger.channel',
            }


class OnpointLoggerThresholdHourly(models.Model):
    _name = 'onpoint.logger.threshold.hourly'
    
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade')
    hours = fields.Selection([
            ('00','00:00'),('01','01:00'),('02','02:00'),('03','03:00'),('04','04:00'),
            ('05','05:00'),('06','06:00'),('07','07:00'),('08','08:00'),('09','09:00'),
            ('10','10:00'),('11','11:00'),('12','12:00'),('13','13:00'),('14','14:00'),
            ('15','15:00'),('16','16:00'),('17','17:00'),('18','18:00'),('19','19:00'),
            ('20','20:00'),('21','21:00'),('22','22:00'),('23','23:00')], default='00', required=True, 
        )
    min_value = fields.Float(required=True, default='0')
    max_value = fields.Float(required=True, default='0')

class OnpointLoggerValue(models.Model):
    _name = 'onpoint.logger.value'
    _order = 'dates asc'
    
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade')
    channel_id = fields.Many2one('onpoint.logger.channel', string='Channel', required=True, index=True, ondelete='cascade')
    dates = fields.Datetime(required=True)
    channel_value = fields.Float(required=True, digits=(12,3))