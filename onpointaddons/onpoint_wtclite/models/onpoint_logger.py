from odoo import models, fields, api, tools
from datetime import datetime, timezone, timedelta
import xlsxwriter
import base64
from io import StringIO, BytesIO
from odoo.exceptions import ValidationError
import logging
import math

_logger = logging.getLogger(__name__)


class OnpointLoggerType(models.Model):
    _name = 'onpoint.logger.type'
    _inherit = 'onpoint.logger.type'

    def get_all(self):
        logger_types = self.search([])
        return logger_types


class OnpointLogger(models.Model):
    _name = 'onpoint.logger'
    _inherit = 'onpoint.logger'

    def set_logger(self, form_values):
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

        logger = self.env['onpoint.logger'].create({
            'name': form_values['name'],
            'identifier': form_values['identifier'],
            'brand_id': brand.id,
            'logger_type_id': form_values['logger_type_id'],
            'address': form_values['address'],
            'channel_ids': channel_ids
        })
        return logger

    def disable_logger(self, form_values):
        logger = self.env['onpoint.logger'].search([('id', '=', form_values['logger_id'])], limit=1)
        logger.sudo().write({
            'state': 'disabled',
        })
        return logger

    def get_loggers_by_state(self, state):
        logger_datas = self.env['onpoint.logger'].search([('state', '=', state)],
                                                         order='is_still_active desc')
        loggers = []
        for logger in logger_datas:
            add_hours = self.get_time_zone(logger.id)
            channels = []
            for channel in logger.channel_ids:
                if channel.display_on_chart:
                    channel_val = {
                        'name': channel.name,
                        'last_value': channel.last_value,
                        'unit': channel.value_unit_id.name,
                        'color': channel.color
                    }
                    channels.append(channel_val)

            val = {
                'id': logger.id,
                'name': logger.name,
                'logger_type_name': logger.logger_type_id.name,
                'is_still_active': logger.is_still_active,
                'channels': channels,
                'last_data_date': (logger.last_data_date + timedelta(hours=add_hours)).strftime('%Y-%m-%d %H:%M:%S') if logger.last_data_date else ''
            }
            loggers.append(val)

        return loggers

    def get_detail_logger(self, logger_id):
        now = datetime.now()
        current_date = now.strftime('%d/%m/%Y')
        previous = now - timedelta(days=30)
        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '7d'

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

    def get_detail_logger_refresh(self, logger_id):
        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        logger.read_ftp_pointorange()

    def get_chart_logger(self, logger_id):
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

    def generate_mobile_report(self, form_values):
        if not 'report_period' in form_values:
            now = datetime.now() + timedelta(hours=7)
            current_date = now.strftime('%d/%m/%Y')
            previous = now - timedelta(days=2)
            previous_date = previous.strftime('%d/%m/%Y')
            report_period = previous_date + ' - ' + current_date
        else:
            report_period = form_values['report_period']

        logger_report = self.env['onpoint.logger.report'].create({
            'logger_id': int(form_values['logger_id']),
            'channel_id': int(form_values['channel_id']),
            'report_period': report_period,
            'image_url': form_values['image_url'],
            'power_image': form_values['state_battery'],
            'power_value': form_values['state_battery_value'],
            'signal_image': form_values['state_signal'],
            'signal_value': form_values['state_signal_value'],
            'temperature_image': form_values['state_temperature'],
            'temperature_value': form_values['state_signal_value'],
            'is_flow': form_values['is_flow'],
            'show_data': form_values['show_data'],
            'interval': form_values['interval'],
        })

        attachment = logger_report.generate_pdf_report(with_attachment=True)
        return attachment

    def get_consumption_logger(self, logger_id, channel_id, interval='default'):
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

    def get_consumption_report(self, logger_id, channel_id):
        now = datetime.now()
        current_date = now.strftime('%d/%m/%Y')
        previous = now - timedelta(days=30)
        previous_date = previous.strftime('%d/%m/%Y')
        range_date = previous_date + ' - ' + current_date
        option = '7d'

        consumption_datas = self.env['onpoint.logger'].get_data_consumption(logger_id=int(logger_id),
                                                                            channel_id=int(channel_id),
                                                                            range_date=range_date,
                                                                            option_hour='00')
        flow_data = []
        idx = 0
        for value in consumption_datas['tabular_data']:
            if idx > 0:
                flow_data.append({
                    'dates': value[0],
                    'channel_value': value[1],
                    'totalizer_value': value[2]
                })
            idx += 1

    def get_threshold_logger(self, logger_id, channel_id):
        can_write = self.env.user.has_group('onpoint_monitor.group_onpoint_monitor_admin')
        logger_channel = self.env['onpoint.logger.channel'].search([('id', '=', channel_id)])

        channel = {
            'logger_channel_id': logger_channel.id,
            'can_write': can_write,
            'logger_name': logger_channel.logger_id.name,
            'logger_identifier': logger_channel.logger_id.identifier,
            'overrange_enabled': logger_channel.overrange_enabled,
            'overrange_threshold': logger_channel.overrange_threshold,
            'hi_hi_enabled': logger_channel.hi_hi_enabled,
            'hi_hi_threshold': logger_channel.hi_hi_threshold,
            'hi_enabled': logger_channel.hi_enabled,
            'hi_threshold': logger_channel.hi_threshold,
            'lo_enabled': logger_channel.lo_enabled,
            'lo_threshold': logger_channel.lo_threshold,
            'lo_lo_enabled': logger_channel.lo_lo_enabled,
            'lo_lo_threshold': logger_channel.lo_lo_threshold,
            'underrange_enabled': logger_channel.underrange_enabled,
            'underrange_threshold': logger_channel.underrange_threshold,
        }
        return channel

    def set_threshold(self, form_values):
        logger_channel = self.env['onpoint.logger.channel'].search([('id', '=', form_values['logger_channel_id'])])

        logger_channel.write({
            'overrange_enabled': form_values['overrange_enabled'],
            'overrange_threshold': 0 if not form_values['overrange_enabled'] else form_values['overrange_threshold'],
            'hi_hi_enabled': form_values['hi_hi_enabled'],
            'hi_hi_threshold': 0 if not form_values['hi_hi_enabled'] else form_values['hi_hi_threshold'],
            'hi_enabled': form_values['hi_enabled'],
            'hi_threshold': 0 if not form_values['hi_enabled'] else form_values['hi_threshold'],
            'lo_enabled': form_values['lo_enabled'],
            'lo_threshold': 0 if not form_values['lo_enabled'] else form_values['lo_threshold'],
            'lo_lo_enabled': form_values['lo_lo_enabled'],
            'lo_lo_threshold': 0 if not form_values['lo_lo_enabled'] else form_values['lo_lo_threshold'],
            'underrange_enabled': form_values['underrange_enabled'],
            'underrange_threshold': 0 if not form_values['underrange_enabled'] else form_values['underrange_threshold'],
        })


class OnpointLoggerChannel(models.Model):
    _name = 'onpoint.logger.channel'
    _inherit = 'onpoint.logger.channel'

    def get_data(self, channel_id):
        channel = self.search([('id', '=', int(channel_id))])
        # result = {
        #     'id': channel.id,
        #     'name': channel.name,
        #     'brand_owner': channel.brand_owner,
        #     'point_id': channel.point_id.id,
        #     'point_name': channel.point_id.name,
        #     'value_type_name': channel.value_type_id.name,
        #     'value_unit_name': channel.value_unit_id.name,
        #     'interval': channel.interval_minutes,
        #     'pulse': channel.pulse
        # }
        return channel

    def set_channel(self, form_values):
        logger_channel = self.env['onpoint.logger.channel'].search([('id', '=', form_values['id'])])

        logger_channel.write({
            'interval_minutes': form_values['interval_minutes'],
            'pulse': form_values['pulse'],
        })

