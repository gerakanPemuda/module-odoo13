from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

class OnpointliteApiAbstract(models.AbstractModel):
    _name = 'onpointlite.api.abstract'

    # def connect_destination_db(self, url, db, username, password):
    #     common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    #     uid = common.authenticate(db, username, password, {})

    #     return uid

    def get_time_zone(self, logger_id):
        logger = self.env['onpoint.logger'].sudo().browse(logger_id)
        convert_time = logger.convert_time
        if convert_time:
            time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        else:
            time_zone = 0
        return int(time_zone)

    # def get_logger_profile(self, logger_id):

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

    def get_loggers(self, param_search):
        loggers = self.env['onpoint.logger'].search(eval(param_search), order='name asc')
        logger_datas = []
        for logger in loggers:
            add_hours = self.get_time_zone(logger.id)
            
            logger_channels = []
            for logger_channel in logger.channel_ids:
                if logger_channel.display_on_chart:
                    logger_channel_val = {
                        'name': logger_channel.name,
                        'last_value': logger_channel.last_value,
                        'unit': logger_channel.value_unit_id.name,
                        'color': logger_channel.color
                    }
                    logger_channels.append(logger_channel_val)

            logger_val = {
                'id': logger.id,
                'name': logger.name,
                'logger_type_name': logger.logger_type_id.name,
                'is_still_active': logger.is_still_active,
                'logger_channels': logger_channels,
                'last_data_date': (logger.last_data_date + timedelta(hours=add_hours)).strftime('%Y-%m-%d %H:%M:%S') if logger.last_data_date else ''
            }
            logger_datas.append(logger_val)

        return logger_datas

    def get_logger_profilexxxx(self, logger_id, range_date, option, period, option_hour='00', with_alarm=True):
        # view_id = self.env.ref('onpoint_monitor.view_onpoint_logger_value_tree').id

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
        channels = self._set_chart_channels(logger_id, start_date, end_date)
        logger.update(channels)

        # Main Alarms
        if with_alarm:
            main_alarms = self.set_main_alarm(logger_id, start_date, end_date)
            logger.update(main_alarms)
        return logger

    def _set_series(self, loggers, value_unit_ids, start_date, end_date):
        # series = []
        # totalizers = []
        events = []
        # is_totalizer = False

        # idx = 0
        for value_unit_id in value_unit_ids:
            for logger in loggers:
                add_hours = self.get_time_zone(logger.logger_id.id)

                if logger.value_unit_id.id == value_unit_id:
                    logger_values = self.env['onpoint.logger.value'].search([('channel_id', '=', logger.channel_id.id), ('dates', '>=', start_date), ('dates', '<=', end_date)])

                    # channel_name = ''
                    # if logger.channel_id.value_type_name:
                    #     channel_name = logger.channel_id.value_type_name

                    # if logger.channel_id.point_id.name:
                    #     channel_name += ' - ' + logger.channel_id.point_id.name

                    # data_totalizer = {
                    #     'channel_name': channel_name,
                    # }

                    # if logger.point_id.need_totalizer:
                    #     is_totalizer = True
                    #     initial_date, initial_value = self.get_initial(logger.channel_id.id, end_date)
                    #     data_totalizer.update({
                    #         'initial_date': initial_date,
                    #         'initial_value': initial_value,
                    #     })

                    last_totalizer = 0
                    # alarm_events = 0

                    # data = []
                    # min_date = False
                    min_value = 9999
                    # max_date = False
                    # max_value = 0
                    # avg_value = 0
                    # total_value = 0
                    # total_data = 0
                    last_date = False
                    last_value = 0
                    for logger_value in logger_values:
                    #     # Value
                    #     channel_value = value.channel_value
                    #     value_dates = value.dates + timedelta(hours=add_hours)
                    #     unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                    #     # Events
                    #     if value.value_type == 'alarm':
                    #         alarm_events = alarm_events + 1

                    #     data_val = [unixtime, round(channel_value, 3)]
                    #     data.append(data_val)

                        last_date = logger_value.dates + timedelta(hours=add_hours)
                        last_value = round(channel_value, 3)
                        # total_value += last_value
                        # total_data += 1

                        if last_value < min_value:
                            min_date = last_date
                            min_value = last_value

                        if last_value > max_value:
                            max_date = last_date
                            max_value = last_value

                        last_totalizer = round(logger_value.totalizer, 3)

                    # if total_data > 0:
                    #     avg_value = round(total_value / total_data, 3)
                    # else:
                    #     avg_value = 0

                    # data_totalizer.update({
                    #     'last_totalizer': last_totalizer,
                    #     'last_date': last_date
                    # })

                    # if logger.point_id.need_totalizer:
                    #     totalizers.append(data_totalizer)

                    # # Series
                    # if logger.channel_id.display_on_chart:
                    #     series_data = self._set_series_data(
                    #         logger.channel_id.name if logger.channel_id.name else logger.channel_id.value_type_name,
                    #         'spline',
                    #         idx,
                    #         logger.channel_id.color,
                    #         data,
                    #         logger.channel_id.value_unit_id.name)
                    #     series.append(series_data)

                    # # Event and Information
                    # threshold_event = "0 event"

                    # if min_value == 9999:
                    #     min_value = '-'

                    # if not min_date:
                    #     min_date = ''

                    # if not max_date:
                    #     max_date = ''
                    #     max_value = '-'

                    if not last_date:
                        last_date = ''
                        last_value = '-'

                    data_event = {
                        -'channel_id': logger.channel_id.id,
                        'color': logger.channel_id.color,
                        -'name': logger.channel_id.name if logger.channel_id.name != False else logger.channel_id.value_type_id.name,
                        -'unit_name': logger.channel_id.value_unit_id.name,
                        'threshold_event': threshold_event,
                        -'last_date': last_date,
                        -'last_value': last_value,
                        'min_date': min_date,
                        'min_value': min_value,
                        'max_date': max_date,
                        'max_value': max_value,
                        'avg_value': avg_value,
                        'alarm_events': alarm_events,
                        -'need_totalizer': logger.channel_id.value_type_id.need_totalizer,
                        -'show_consumption': logger.channel_id.show_consumption,
                        -'last_totalizer': last_totalizer
                    }
                    events.append(data_event)

            idx = idx + 1
        return series, totalizers, events, is_totalizer

    def get_logger_profile(self, logger_id):
        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        val = {
            'id': logger.id,
            'name': logger.name,
            'identifier': logger.identifier,
            'logger_type_name': logger.logger_type_name,
            'department_name': logger.department_id.name,
            'wtp_name': logger.wtp_id.name,
            'zone_name': logger.zone_id.name,
            'dma_name': logger.dma_id.name,
            'simcard': logger.simcard,
            'address': logger.address,
            'latitude': logger.latitude,
            'longitude': logger.longitude,
            'meter_type_name': logger.meter_type_id.name,
            'meter_brand_name': logger.meter_brand_id.name,
            'meter_size_name': logger.meter_size_id.name,
            'pipe_material_name': logger.pipe_material_id.name,
            'pipe_size_name': logger.pipe_size_id.name,
            'valve_control_name': logger.valve_control_id.name
        }
        return val

    def get_logger_channels(self, logger_id):
        add_hours = self.get_time_zone(logger_id)

        logger_channels = self.env['onpoint.logger.channel'].search([('logger_id', '=', logger_id)])
        logger_channels_datas = []
        for logger_channel in logger_channels:
            if logger_channel.display_on_chart:
                logger_channel_val = {
                    'id': logger_channel.id,
                    'name': logger_channel.name if logger_channel.name != False else logger_channel.value_type_id.name,
                    'color': logger_channel.color,
                    'unit_name': logger_channel.value_unit_id.name,
                    'last_date': (logger_channel.last_date + timedelta(hours=add_hours)).strftime('%Y-%m-%d %H:%M:%S') if logger_channel.last_date else '',
                    'last_value': logger_channel.last_value,
                    'need_totalizer': logger_channel.value_type_id.need_totalizer,
                    'show_consumption': logger_channel.show_consumption,
                    'last_totalizer': logger_channel.last_totalizer,
                    }

                logger_channels_datas.append(logger_channel_val)

        return logger_channels_datas

    def get_logger_chart(self, logger_id):
        now = datetime.now() + timedelta(hours=7)
        current_date = now.strftime('%d/%m/%Y')
        previous = now - timedelta(days=2)
        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '2d'

        try:
            logger = self.env['onpoint.logger'].get_data(logger_id=int(logger_id),
                                                         range_date=range_date,
                                                         option=option,
                                                         period='',
                                                         with_alarm=True)
        except Exception as e:
            x = 1

        logger_profile = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        profile = {
            'logger_identifier': logger_profile.identifier,
            'logger_type_name': logger_profile.logger_type_name,
            'logger_department_name': logger_profile.department_id.name,
            'logger_wtp_name': logger_profile.wtp_id.name,
            'logger_zone_name': logger_profile.zone_id.name,
            'logger_dma_name': logger_profile.dma_id.name,
            'logger_simcard': logger_profile.simcard,
            'logger_address': logger_profile.address,
            'logger_latitude': logger_profile.latitude,
            'logger_longitude': logger_profile.longitude,
            'logger_meter_type_name': logger_profile.meter_type_id.name,
            'logger_meter_brand_name': logger_profile.meter_brand_id.name,
            'logger_meter_size_name': logger_profile.meter_size_id.name,
            'logger_pipe_material_name': logger_profile.pipe_material_id.name,
            'logger_pipe_size_name': logger_profile.pipe_size_id.name,
            'logger_valve_control_name': logger_profile.valve_control_id.name

        }
        logger.update(profile)
        return logger

    def get_logger_channels_old(self, logger_id, range_date, option, option_hour='00'):
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

        # series = []
        # totalizers = []
        logger_channels = []
        # is_totalizer = False

        # idx = 0
        logger = self.env['onpoint.logger'].sudo().search([('id', '=', logger_id)], limit=1)
        logger_value_unit = self.env['onpoint.vw.logger'].sudo().read_group([('logger_id', '=', logger.id), ('value_unit_id', '!=', False)], ['value_unit_id'], ['value_unit_id'], orderby='value_unit_id')

        value_unit_ids = []
        mapped_data = dict([(data['value_unit_id'], data['value_unit_id_count']) for data in logger_value_unit])
        if mapped_data:
            for key, value in mapped_data:
                value_unit_ids.append(key)

        for value_unit_id in value_unit_ids:
            vw_loggers = self.env['onpoint.vw.logger'].sudo().search([('logger_id', '=', logger_id)])
            
            for vw_logger in vw_loggers:
                add_hours = self.get_time_zone(vw_logger.logger_id.id)

                if vw_logger.value_unit_id.id == value_unit_id:
                    logger_values = self.env['onpoint.logger.value'].search([('channel_id', '=', vw_logger.channel_id.id), ('dates', '>=', start_date), ('dates', '<=', end_date)])

                    # channel_name = ''
                    # if logger.channel_id.value_type_name:
                    #     channel_name = logger.channel_id.value_type_name

                    # if logger.channel_id.point_id.name:
                    #     channel_name += ' - ' + logger.channel_id.point_id.name

                    # data_totalizer = {
                    #     'channel_name': channel_name,
                    # }

                    # if logger.point_id.need_totalizer:
                    #     is_totalizer = True
                    #     initial_date, initial_value = self.get_initial(logger.channel_id.id, end_date)
                    #     data_totalizer.update({
                    #         'initial_date': initial_date,
                    #         'initial_value': initial_value,
                    #     })

                    last_totalizer = 0
                    # alarm_events = 0

                    # data = []
                    min_date = False
                    min_value = 9999
                    max_date = False
                    max_value = 0
                    avg_value = 0
                    total_value = 0
                    total_data = 0
                    last_date = False
                    last_value = 0
                    for logger_value in logger_values:
                    #     # Value
                        channel_value = value.channel_value
                    #     value_dates = value.dates + timedelta(hours=add_hours)
                    #     unixtime = (value_dates - datetime(1970, 1, 1, 0, 0, 0)).total_seconds() * 1000

                    #     # Events
                    #     if value.value_type == 'alarm':
                    #         alarm_events = alarm_events + 1

                    #     data_val = [unixtime, round(channel_value, 3)]
                    #     data.append(data_val)

                        last_date = logger_value.dates + timedelta(hours=add_hours)
                        last_value = round(channel_value, 3)
                        total_value += last_value
                        total_data += 1

                        if last_value < min_value:
                            min_date = last_date
                            min_value = last_value

                        if last_value > max_value:
                            max_date = last_date
                            max_value = last_value

                        last_totalizer = round(logger_value.totalizer, 3)

                    if total_data > 0:
                        avg_value = round(total_value / total_data, 3)
                    else:
                        avg_value = 0

                    # data_totalizer.update({
                    #     'last_totalizer': last_totalizer,
                    #     'last_date': last_date
                    # })

                    # if logger.point_id.need_totalizer:
                    #     totalizers.append(data_totalizer)

                    # # Series
                    # if logger.channel_id.display_on_chart:
                    #     series_data = self._set_series_data(
                    #         logger.channel_id.name if logger.channel_id.name else logger.channel_id.value_type_name,
                    #         'spline',
                    #         idx,
                    #         logger.channel_id.color,
                    #         data,
                    #         logger.channel_id.value_unit_id.name)
                    #     series.append(series_data)

                    # # Event and Information
                    # threshold_event = "0 event"

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

                    logger_channel_val = {
                        'id': vw_logger.channel_id.id,
                        'color': vw_logger.channel_id.color,
                        'name': vw_logger.channel_id.name if vw_logger.channel_id.name != False else vw_logger.channel_id.value_type_id.name,
                        'unit_name': vw_logger.channel_id.value_unit_id.name,
                        # 'threshold_event': threshold_event,
                        'last_date': last_date,
                        'last_value': last_value,
                        'min_date': min_date,
                        'min_value': min_value,
                        'max_date': max_date,
                        'max_value': max_value,
                        'avg_value': avg_value,
                        # 'alarm_events': alarm_events,
                        'need_totalizer': vw_logger.channel_id.value_type_id.need_totalizer,
                        'show_consumption': vw_logger.channel_id.show_consumption,
                        'last_totalizer': last_totalizer
                    }
                    logger_channels.append(logger_channel_val)

                # idx = idx + 1
        # return series, totalizers, events, is_totalizer
        return logger_channels

    def get_logger_channelsxxx(self, logger_id, range_date, option, period, option_hour='00', with_alarm=True):
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
        loggers = self.env['onpoint.vw.logger'].sudo().search([('logger_id', '=', logger_id)])

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

    def generate_logger_report(self, datas):
        if not 'report_period' in datas:
            now = datetime.now() + timedelta(hours=7)
            current_date = now.strftime('%d/%m/%Y')
            previous = now - timedelta(days=2)
            previous_date = previous.strftime('%d/%m/%Y')
            report_period = previous_date + ' - ' + current_date
        else:
            report_period = datas['report_period']

        logger_report = self.env['onpoint.logger.report'].create({
            'logger_id': int(datas['logger_id']),
            'channel_id': int(datas['channel_id']),
            'report_period': report_period,
            'image_url': datas['image_url'],
            'power_image': datas['state_battery'],
            'power_value': datas['state_battery_value'],
            'signal_image': datas['state_signal'],
            'signal_value': datas['state_signal_value'],
            'temperature_image': datas['state_temperature'],
            'temperature_value': datas['state_signal_value'],
            'is_flow': datas['is_flow'],
            'show_data': datas['show_data'],
            'interval': datas['interval'],
        })

        attachment = logger_report.generate_pdf_report(with_attachment=True)
        return attachment

    def get_logger_detail(self, logger_id):
        now = datetime.now()
        current_date = now.strftime('%d/%m/%Y')
        previous = now - timedelta(days=30)
        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '7d'

        # logger = {}

        logger_profile = self.get_logger_profile(logger_id)
        # logger.update(logger_profile)

        logger_channels = self.get_logger_channels(logger_id)
        
        logger_chart = self.get_logger_chart(logger_id)
        
        # logger_chart = self.get_logger_chart(logger_id, range_date, option)
        # logger.update({
            # 'logger_channels': logger_channels
            # })
        # logger.update(logger_profile)



        # try:
            # logger = self.env['onpoint.logger'].get_data(logger_id=int(logger_id), range_date=range_date, option=option, period='', with_alarm=True)
        # except Exception as e:
            # x = 1

        # logger_profile = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        # profile = {
        #     'logger_identifier': logger_profile.identifier,
        #     'logger_type_name': logger_profile.logger_type_name,
        #     'logger_department_name': logger_profile.department_id.name,
        #     'logger_wtp_name': logger_profile.wtp_id.name,
        #     'logger_zone_name': logger_profile.zone_id.name,
        #     'logger_dma_name': logger_profile.dma_id.name,
        #     'logger_simcard': logger_profile.simcard,
        #     'logger_address': logger_profile.address,
        #     'logger_latitude': logger_profile.latitude,
        #     'logger_longitude': logger_profile.longitude,
        #     'logger_meter_type_name': logger_profile.meter_type_id.name,
        #     'logger_meter_brand_name': logger_profile.meter_brand_id.name,
        #     'logger_meter_size_name': logger_profile.meter_size_id.name,
        #     'logger_pipe_material_name': logger_profile.pipe_material_id.name,
        #     'logger_pipe_size_name': logger_profile.pipe_size_id.name,
        #     'logger_valve_control_name': logger_profile.valve_control_id.name

        # }
        # logger.update(profile)
        logger = {
            # 'logger_profile': logger,
            'logger_profile': logger_profile,
            'logger_channels': logger_channels,
            'logger_chart': logger_chart,
        }
        return logger

    def get_logger_channel_consumption(self, logger_id, channel_id, interval='default'):
        now = datetime.now()
        current_date = now.strftime('%d/%m/%Y')
        if interval != 'month':
            previous = now - timedelta(days=30)
        else:
            previous = now - timedelta(days=120)

        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '7d'

        logger = self.env['onpoint.logger'].get_data_consumption(logger_id=int(logger_id),
                                                                 channel_id=int(channel_id),
                                                                 range_date=range_date,
                                                                 option_hour='00',
                                                                 interval=interval)

        logger_profile = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        profile = {
            'logger_name': logger_profile.name,
            'logger_identifier': logger_profile.identifier,
            'logger_address': logger_profile.address,
            'report_period': range_date
        }
        logger.update(profile)
        return logger

    def create_loggers(self, param_datas):
        logger_ids = []
        for param_data in eval(param_datas):
            brand = self.env['onpoint.logger.brand'].search([('name', '=', 'Point Orange')], limit=1)
            point = self.env['onpoint.logger.point'].search([('code', '=', 'AI24')], limit=1)
            value_type = self.env['onpoint.value.type'].search([('name', '=', 'Flow')], limit=1)
            value_unit = self.env['onpoint.value.unit'].search([('name', '=', 'l/s'),
                                                                ('value_type_id', '=', value_type.id)], limit=1)
            channel_ids = []
            value_vals = {
                'name': 'Flow',
                'brand_owner': 'pointorange',
                'value_type_id': value_type.id,
                'value_unit_id': value_unit.id,
                'point_id': point.id,
                'interval_minutes': 15,
                'pulse': 100
            }
            row_value = (0, 0, value_vals)
            channel_ids.append(row_value)

            logger = self.env['onpoint.logger'].sudo().create({
                'name': param_data['name'],
                'identifier': param_data['identifier'],
                'brand_id': brand.id,
                'logger_type_id': param_data['logger_type_id'],
                'address': param_data['address'],
                'latitude': param_data['latitude'],
                'longitude': param_data['longitude'],
                'channel_ids': channel_ids
            })
            logger_ids.append(logger.id)

        return logger_ids

    def update_loggers(self, param_datas):
        loggers = []
        for param_data in eval(param_datas):
            logger = self.env['onpoint.logger'].search([('id', '=', param_data['logger_id'])], limit=1)
            logger.sudo().write(param_data['data_update'])

        return param_datas

    # def set_logger(self, form_values):
    #     brand = self.env['onpoint.logger.brand'].search([('name', '=', 'Point Orange')], limit=1)
    #     point = self.env['onpoint.logger.point'].search([('code', '=', 'AI24')], limit=1)
    #     value_type = self.env['onpoint.value.type'].search([('name', '=', 'Flow')], limit=1)
    #     value_unit = self.env['onpoint.value.unit'].search([('name', '=', 'l/s'),
    #                                                         ('value_type_id', '=', value_type.id)], limit=1)
    #     channel_ids = []
    #     value_vals = {
    #         'name': 'Flow',
    #         'brand_owner': 'pointorange',
    #         'value_type_id': value_type.id,
    #         'value_unit_id': value_unit.id,
    #         'point_id': point.id,
    #         'interval_minutes': 15,
    #         'pulse': 100
    #     }
    #     row_value = (0, 0, value_vals)
    #     channel_ids.append(row_value)

    #     logger = self.env['onpoint.logger'].create({
    #         'name': form_values['name'],
    #         'identifier': form_values['identifier'],
    #         'brand_id': brand.id,
    #         'logger_type_id': form_values['logger_type_id'],
    #         'address': form_values['address'],
    #         'channel_ids': channel_ids
    #     })
    #     return logger

    def get_logger_types(self, param_search):
        logger_type_datas = self.env['onpoint.logger.type'].search(eval(param_search))
        logger_types = []
        for logger_type in logger_type_datas:
            val = {
                'id': logger_type.id,
                'name': logger_type.name,
                'sequence': logger_type.sequence,
                'is_threshold_hourly': logger_type.is_threshold_hourly,
            }
            logger_types.append(val)
            
        return logger_types