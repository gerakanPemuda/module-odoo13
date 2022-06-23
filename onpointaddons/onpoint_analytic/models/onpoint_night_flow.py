from odoo import models, fields, api
from datetime import datetime, timedelta


class OnpointNightFlow(models.TransientModel):
    _name = 'onpoint.night.flow'

    name = fields.Char(string='Name')
    title = fields.Char(string='Title')
    sub_title = fields.Char(string='Sub Title')
    source_selection = fields.Selection([
        ('logger', 'Logger'),
        ('comparison', 'Chart Comparison')
    ], default='logger', required=True)
    logger_id = fields.Many2one('onpoint.logger', string='Logger')
    logger_compare_id = fields.Many2one('onpoint.logger.compare', string='Logger Comparison')
    channel_id = fields.Many2one('onpoint.logger.channel',
                                 string='Flow Channel',
                                 required=True)
    first_period_start = fields.Date(string='Start')
    first_period_end = fields.Date(string='End')
    second_period_start = fields.Date(string='Start')
    second_period_end = fields.Date(string='End')

    @api.onchange('logger_id', 'logger_compare_id')
    def domain_logger_channel(self):
        data = []
        if self.source_selection == 'logger':
            if self.logger_id:
                for channel in self.logger_id.channel_ids:
                    if channel.value_type_name == 'Flow' and channel.display_on_chart:
                        data.append(channel.id)
        else:
            if self.logger_compare_id:
                for line in self.logger_compare_id.line_ids:
                    if line.logger_id:
                        for channel in line.logger_id.channel_ids:
                            if channel.value_type_name == 'Flow' and channel.display_on_chart:
                                data.append(channel.id)

        return {'domain': {'channel_id': [('id', 'in', data)]}}

    def act_view_chart(self):
        range_date = '01/12/2020 - 31/12/2020'
        option = ''
        period = ''
        # logger_data = self.logger_id.get_data(self.logger_id.id, range_date, option, period)

        if self.source_selection == 'logger':
            name = self.logger_id.name
        else:
            name = self.logger_compare_id.name

        self.write({
            'name': name
        })

        action_context = {'night_flow_id': self.id,
                          'name': self.name,
                          'source_selection': self.source_selection,
                          'logger_id': self.logger_id.id,
                          'logger_compare_id': self.logger_compare_id.id,
                          'channel_id': self.channel_id.id,
                          }
        return {
            'type': 'ir.actions.client',
            'tag': 'onpoint_analytic_night_flow',
            'context': action_context,
        }

    @api.model
    def get_data(self, params):
        x = 1
        result = {
            'logger_id': 1,
        }

        return result

    def get_night_flow_area(self, night_flow, start_date, end_date, range_times):

        loggers = []
        night_flow_loggers = []

        if night_flow.source_selection == 'logger':
            loggers.append(night_flow.logger_id)
        else:
            for line in night_flow.logger_compare_id.line_ids:
                loggers.append(line.logger_id)

        for logger in loggers:
            for channel in logger.channel_ids:
                if channel.display_on_chart:
                    min_value = 9999
                    min_date = False
                    max_value = -9999
                    max_date = False

                    data = self.env['onpoint.logger.value'].get_data(channel.id, start_date, end_date)

                    for range_time in range_times:
                        start_time = range_time['start']
                        end_time = range_time['end']
                        for value in data['values']:
                            if start_time <= value.dates <= end_time:
                                if value.channel_value <= min_value:
                                    min_value = value.channel_value
                                    min_date = value.dates

                                if value.channel_value >= max_value:
                                    max_value = value.channel_value
                                    max_date = value.dates

                    if not min_date:
                        min_value = '-'
                        min_date = ''

                    if not max_date:
                        max_value = '-'
                        max_date = ''

                    night_flow_loggers.append({
                        'logger_id': logger.id,
                        'logger_name': logger.name,
                        'channel_id': channel.id,
                        'channel_name': channel.name,
                        'unit_value_name': channel.value_unit_name,
                        'min_value': min_value,
                        'min_date': min_date,
                        'max_value': max_value,
                        'max_date': max_date
                    })

        return night_flow_loggers

    @api.model
    def get_chart_data(self,
                       night_flow_id,
                       range_date,
                       input_start_hour,
                       input_start_minute,
                       input_end_hour,
                       input_end_minute):

        night_flow = self.env['onpoint.night.flow'].search([('id', '=', night_flow_id)])

        add_hours = night_flow.channel_id.logger_id.get_time_zone(night_flow.channel_id.logger_id.id)

        logger_data = []
        if night_flow:

            range_dates = range_date.split(' - ')

            start_date = (datetime.strptime(range_dates[0], "%d/%m/%Y"))
            end_date = (datetime.strptime(range_dates[1], "%d/%m/%Y"))
            delta = timedelta(days=1)

            plot_lines = []
            min_line = []
            max_line = []
            current_date = start_date
            range_times = []
            while current_date <= end_date:
                start_string = current_date.strftime("%Y-%m-%d " + input_start_hour + ":" + input_start_minute + ":00")
                start_time = datetime.strptime(start_string, "%Y-%m-%d %H:%M:%S")
                start_unixtime = (start_time - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000
                end_string = current_date.strftime("%Y-%m-%d " + input_end_hour + ":" + input_end_minute + ":00")
                end_time = datetime.strptime(end_string, "%Y-%m-%d %H:%M:%S")
                end_unixtime = (end_time - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                range_times.append({
                    'start': start_time - timedelta(hours=add_hours),
                    'end': end_time - timedelta(hours=add_hours)
                })

                plot_lines.append({
                    'color': '#FF0000',
                    'width': 2,
                    'value': start_unixtime
                })
                plot_lines.append({
                    'color': '#FF0000',
                    'width': 2,
                    'value': end_unixtime
                })
                # min_data = [start_unixtime, 0.94]
                # min_line.append(min_data)
                # min_data = [end_unixtime, 0.944]
                # min_line.append(min_data)
                #
                # max_data = [start_unixtime, 1.689]
                # max_line.append(max_data)
                # max_data = [end_unixtime, 1.689]
                # max_line.append(max_data)

                current_date += delta

            option = ""
            period = ""
            plot_line_data = {
                'plot_lines': plot_lines
            }

            if night_flow.source_selection == 'logger':
                logger_data = self.logger_id.get_data(night_flow.logger_id.id, range_date, option, period)
            else:
                logger_data = self.logger_compare_id.get_data(night_flow.logger_compare_id.id, range_date)
            logger_data.update(plot_line_data)

            # max_series_data = {
            #     'name': 'Max',
            #     'type': 'line',
            #     'color': 'orange',
            #     'zIndex': '1',
            #     'yAxis': 1,
            #     'data': max_line,
            # }
            #
            # min_series_data = {
            #     'name': 'Min',
            #     'type': 'line',
            #     'color': 'green',
            #     'zIndex': '1',
            #     'yAxis': 1,
            #     'data': min_line,
            # }
            #
            # logger_data['series'].append(max_series_data)
            # logger_data['series'].append(min_series_data)

            night_flow_loggers = self.get_night_flow_area(night_flow, start_date, end_date, range_times)

            band_min_value = 0
            band_min_date = 0
            band_max_value = 0
            band_max_date = 0

            for night_flow_logger in night_flow_loggers:
                if night_flow.channel_id.id == night_flow_logger['channel_id']:
                    band_min_value = night_flow_logger['min_value']
                    band_max_value = night_flow_logger['max_value']

            for yaxis in logger_data['yAxis']:
                unit_name = yaxis['title']['text']
                if unit_name == 'l/s':
                    plot_band = {
                        'from': band_min_value,
                        'to': band_max_value,
                        'borderColor': 'blue',
                        'borderWidth': 1,
                        'color': 'rgba(68, 170, 213, 0.1)',
                        'zIndex': 3
                    }
                    plot_bands = {
                        'plotBands': plot_band
                    }
                    yaxis.update(plot_bands)

            logger_data.update({
                'night_flow_loggers': night_flow_loggers
            })

            return logger_data
