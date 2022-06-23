from odoo import models, fields, api
from datetime import datetime
from time import mktime

import logging
_logger = logging.getLogger(__name__)


class OnpointComparison(models.Model):
    _name = 'onpoint.comparison'
    
    name = fields.Char(required=True)
    line_ids = fields.One2many('onpoint.comparison.line', 'comparison_id')
    channel_ids = fields.One2many('onpoint.comparison.channel', 'comparison_id')

    @api.model
    def get_data(self, comparison_id, range_date, option, period):

        range_dates = range_date.split(' - ')

        start_date = datetime.strptime(range_dates[0], ("%d/%m/%Y")).strftime("%Y-%m-%d")
        end_date = datetime.strptime(range_dates[1], ("%d/%m/%Y")).strftime("%Y-%m-%d")

        comparison = self.env['onpoint.comparison'].sudo().search_read([('id', '=', comparison_id)], limit=1)

        _logger.debug("Comparison : %s", comparison)

        yAxis_data = self._get_comparison_channel(comparison_id, start_date, end_date, option, period)
        comparison[0].update(yAxis_data)

        series = self._set_chart_parameters(comparison_id, start_date, end_date, option, period)
            
        _logger.debug("Debug message x : %s", series)

        comparison[0].update(series)

        return comparison


    def _get_comparison_channel(self, comparison_id, start_date, end_date, option, period):

        txt_query = """
            SELECT x.value_type_id, x.value_type_name, x.value_unit_id, x.value_unit_name
            FROM (
                select a.id as comparison_id, c.value_type_id, d."name" as value_type_name, c.value_unit_id, e."name" as value_unit_name  
                from 
                    onpoint_comparison a,
                    onpoint_comparison_line b,
                    onpoint_logger_channel c,
                    onpoint_value_type d,
                    onpoint_value_unit e 
                where a.id = b.comparison_id and c.logger_id = b.logger_id and d.id = c.value_type_id and e.id = c.value_unit_id
            ) x
            WHERE x.comparison_id = %s
            group by x.value_type_id, x.value_type_name, x.value_unit_id, x.value_unit_name
        """

        self._cr.execute(txt_query, (comparison_id, ))
        comparison_channels = self._cr.fetchall()

        data = []
        y_axis = 0
        yAxis = []
        opposite = False

        for value_type_id, value_type_name, value_unit_id, value_unit_name in comparison_channels:

            vals = {
                'comparison_id': comparison_id,
                'value_type_id': value_type_id,
                'value_unit_id': value_unit_id,
                'y_axis': y_axis 
            }

            yAxis_data = self._set_yAxis(value_type_name, opposite)
            yAxis.append(yAxis_data)

            row = (0, 0, vals)
            data.append(row)

            y_axis = y_axis + 1

            if opposite:
                opposite = False
            else:
                opposite = True


        unlink_comparison_channel = self.env['onpoint.comparison.channel'].sudo().search([('comparison_id', '=', comparison_id)]).unlink()

        comparison = self.env['onpoint.comparison'].search([('id', '=', comparison_id)])
        comparison.write({'channel_ids': data})        

        data = {
            'yAxis': yAxis,
        }

        return data

    def _set_chart_parameters(self, comparison_id, start_date, end_date, option, period):

        yAxis_count = 0
        opposite = False
        
        yAxis = []
        series = []

        # Logger Values
        selected_option = option
        selected_period = 'all'

        if (option == 'all'):
            selected_period = 'all'
        else:
            selected_period = period


        comparison_line_ids = self.env['onpoint.comparison.line'].search([('comparison_id', '=', comparison_id)])

        for line in comparison_line_ids:
            
            logger_id = line.logger_id.id

            txt_query = """
                SELECT 
            """

            txt_from_where = """
                from onpoint_logger_value
                where
                    logger_id = %s
                    AND dates BETWEEN %s AND %s
            """

            if selected_period == 'all':
                txt_date = """
                    extract(epoch from dates) * 1000 as dates, 
                """

                txt_group_by = " ORDER BY dates"
            else:
                txt_date = """
                    extract(epoch from date_trunc('""" + selected_period + """', dates)) * 1000 as dates, 
                """

                txt_group_by = """
                    GROUP BY date_trunc('""" + selected_period + """', dates)
                    ORDER BY date_trunc('""" + selected_period + """', dates)            
                """


            if selected_option == 'all':
                txt_option = """
                    ch1_value,
                    ch2_value,
                    ch3_value,
                    ch4_value
                """
            elif option == 'avg':
                txt_option = """
                    ROUND(cast(AVG(ch1_value) as numeric), 2) as ch1_value,
                    ROUND(cast(AVG(ch2_value) as numeric), 2) as ch2_value,
                    ROUND(cast(AVG(ch3_value) as numeric), 2) as ch3_value,
                    ROUND(cast(AVG(ch4_value) as numeric), 2) as ch4_value
                """
            else:
                txt_option = """
                    ROUND(cast(SUM(ch1_value) as numeric), 2)  as ch1_value,
                    ROUND(cast(SUM(ch2_value) as numeric), 2) as ch2_value,
                    ROUND(cast(SUM(ch3_value) as numeric), 2) as ch3_value,
                    ROUND(cast(SUM(ch4_value) as numeric), 2) as ch4_value
                """

            txt_query = txt_query + ' ' + txt_date + ' ' + txt_option + ' ' + txt_from_where + ' ' + txt_group_by

            self._cr.execute(txt_query, (logger_id, start_date, end_date))
            logger_values = self._cr.fetchall()

            ch1_data = []
            ch2_data = []
            ch3_data = []
            ch4_data = []

            for dates, ch1_value, ch2_value, ch3_value, ch4_value in logger_values:
                
                ch1_val = [dates, ch1_value]
                ch1_data.append(ch1_val)

                ch2_val = [dates, ch2_value]
                ch2_data.append(ch2_val)

                ch3_val = [dates, ch3_value]
                ch3_data.append(ch3_val)

                ch4_val = [dates, ch4_value]
                ch4_data.append(ch4_val)

            # Chart Settings
            
            logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])

            if logger.ch1_active:

                comparison_channel = self.env['onpoint.comparison.channel'].search([('value_type_id', '=', logger.ch1_value_type_id.id)])
                series_name = logger.name + ' (' + logger.ch1_value_type_id.name + ')'
                series_data = self._set_series(series_name, comparison_channel.y_axis, logger.ch1_color, ch1_data, logger.ch1_value_unit_id.name)
                series.append(series_data)

            if logger.ch2_active:

                comparison_channel = self.env['onpoint.comparison.channel'].search([('value_type_id', '=', logger.ch2_value_type_id.id)])
                series_name = logger.name + ' (' + logger.ch2_value_type_id.name + ')'
                series_data = self._set_series(series_name, comparison_channel.y_axis, logger.ch2_color, ch2_data, logger.ch2_value_unit_id.name)
                series.append(series_data)

            if logger.ch3_active:

                comparison_channel = self.env['onpoint.comparison.channel'].search([('value_type_id', '=', logger.ch3_value_type_id.id)])
                series_name = logger.name + ' (' + logger.ch3_value_type_id.name + ')'
                series_data = self._set_series(series_name, comparison_channel.y_axis, logger.ch3_color, ch3_data, logger.ch3_value_unit_id.name)
                series.append(series_data)


            if logger.ch4_active:

                comparison_channel = self.env['onpoint.comparison.channel'].search([('value_type_id', '=', logger.ch4_value_type_id.id)])
                series_name = logger.name + ' (' + logger.ch4_value_type_id.name + ')'
                series_data = self._set_series(series_name, comparison_channel.y_axis, logger.ch4_color, ch4_data, logger.ch4_value_unit_id.name)
                series.append(series_data)


        if selected_period == 'all':
            selected_period = 'hour'

        data = {
            'series': series,
            'selected_option'  : selected_option,
            'selected_period'  : selected_period
        }

        return data

    def _set_yAxis(self, title, opposite):

        yAxis_data = {
            'title': {
                'text': title
            },
            'opposite': opposite
        }

        return yAxis_data

    def _set_series(self, value_type_name, yAxis, color, data, value_unit_name):

        if value_unit_name:
            valueSuffix = value_unit_name
        else:
            valueSuffix = ''

        series_data = {
            'name': value_type_name,
            'type': 'spline',
            'yAxis': yAxis,
            'data': data,
            'tooltip': {
                'valueSuffix': ' ' + valueSuffix
            }
        }

        return series_data




class OnpointComparisonLine(models.Model):
    _name = 'onpoint.comparison.line'
    
    comparison_id = fields.Many2one('onpoint.comparison', index=True, ondelete='cascade' )
    logger_id = fields.Many2one('onpoint.logger', required=True, index=True, ondelete='cascade' )
    logger_dma_name = fields.Char('onpoint.logger', related='logger_id.dma_id.name')


class OnpointComparisonChannel(models.Model):
    _name = 'onpoint.comparison.channel'
    
    comparison_id = fields.Many2one('onpoint.comparison', index=True, ondelete='cascade' )
    value_type_id = fields.Many2one('onpoint.value.type', string='Channel Type')    
    value_unit_id = fields.Many2one('onpoint.value.unit', string='Channel Unit')
    y_axis = fields.Integer()

