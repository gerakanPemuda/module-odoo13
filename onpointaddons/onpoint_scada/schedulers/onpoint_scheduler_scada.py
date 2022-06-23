from odoo import models, fields, api
from datetime import datetime, timezone, timedelta


class OnpointSchedulerScada(models.Model):
    _name = 'onpoint.scheduler.scada'
    _inherit = 'api.telegram.abstract'

    @api.model
    def send_alarm(self):
        alarms = self.env['onpoint.scada.alarm'].search([('is_sent', '=', False)])
        telegram_group = self.env['onpoint.telegram.group'].search([], limit=1)
        add_hours = 0

        for alarm in alarms:
            message = '<b>' + alarm.unit_line_id.unit_name + ' - Alarm</b>' + "\n"
            message += alarm.alarm + "\n"
            message += alarm.unit_line_id.sensor_type_name + ": " + str(
                alarm.alarm_value) + " " + alarm.unit_line_id.sensor_type_uom + "\n"
            alarm_date = (alarm.create_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S")
            message += alarm_date

            params = {
                'chat_id': telegram_group.chat_id,
                'message': message
            }

            result = self.send_message(params)

            if alarm.alarm.lower() == 'normal':
                alarm.write({
                    'is_sent': True
                })

    def get_scada_data(self, unit_line_id):
        unit_lines = self.env['onpoint.scada.unit.detail'].search([('unit_line_id', '=', unit_line_id)],
                                                                  order='sensor_date desc',
                                                                  limit=1)
        last_date = False
        last_value = False
        uom = False
        if unit_lines:
            last_date = unit_lines.sensor_date
            last_value = unit_lines.sensor_value
            uom = unit_lines.unit_line_id.sensor_type_id.uom
        return last_date, last_value, uom

    @api.model
    def send_notification(self):
        telegram_group = self.env['onpoint.telegram.group'].search([], limit=1)
        add_hours = 0

        # Flow
        flow_in8_last_date, flow_in8_last_value, flow_in8_uom = self.get_scada_data(1)
        flow_out12_last_date, flow_out12_last_value, flow_out12_uom = self.get_scada_data(8)
        flow_out8_last_date, flow_out8_last_value, flow_out8_uom = self.get_scada_data(12)
        flow_out6_last_date, flow_out6_last_value, flow_out6_uom = self.get_scada_data(14)

        # Pressure
        pressure_out12_last_date, pressure_out12_last_value, pressure_out12_uom = self.get_scada_data(10)
        pressure_out8_last_date, pressure_out8_last_value, pressure_out8_uom = self.get_scada_data(13)
        pressure_out6_last_date, pressure_out6_last_value, pressure_out6_uom = self.get_scada_data(15)

        # Quality
        quality_turbidity_last_date, quality_turbidity_last_value, quality_turbidity_uom = self.get_scada_data(2)
        quality_ph_last_date, quality_ph_last_value, quality_ph_uom = self.get_scada_data(3)
        quality_scm_last_date, quality_scm_last_value, quality_scm_uom = self.get_scada_data(4)
        quality_dosing_last_date, quality_dosing_last_value, quality_dosing_uom = self.get_scada_data(6)
        quality_level_last_date, quality_level_last_value, quality_level_uom = self.get_scada_data(7)

        message = "<b>Gunung Ulin</b>\n"
        message += "\n"
        message += "<b>Flow</b>\n"
        message += "\n"
        if flow_in8_last_date:
            message += "Air Baku: " + str(flow_in8_last_value) + " " + flow_in8_uom + "\n"
            message += (flow_in8_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Air Baku: -" + "\n"
            message += "\n"

        if flow_out12_last_date:
            message += "Outlet 12'': " + str(flow_out12_last_value) + " " + flow_out12_uom + "\n"
            message += (flow_out12_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 12'': -" + "\n"
            message += "\n"

        if flow_out8_last_date:
            message += "Outlet 8'': " + str(flow_out8_last_value) + " " + flow_out8_uom + "\n"
            message += (flow_out8_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 8'': -" + "\n"
            message += "\n"

        if flow_out6_last_date:
            message += "Outlet 6'': " + str(flow_out6_last_value) + " " + flow_out6_uom + "\n"
            message += (flow_out6_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 6'': -" + "\n"
            message += "\n"

        message += "\n"
        message += "<b>Pressure</b>\n"
        message += "\n"

        if pressure_out12_last_date:
            message += "Outlet 12'': " + str(pressure_out12_last_value) + " " + pressure_out12_uom + "\n"
            message += (pressure_out12_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 12'': -" + "\n"
            message += "\n"

        if pressure_out8_last_date:
            message += "Outlet 8'': " + str(pressure_out8_last_value) + " " + pressure_out8_uom + "\n"
            message += (pressure_out8_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 8'': -" + "\n"
            message += "\n"

        if pressure_out6_last_date:
            message += "Outlet 6'': " + str(pressure_out6_last_value) + " " + pressure_out6_uom + "\n"
            message += (pressure_out6_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Outlet 6'': -" + "\n"
            message += "\n"

        message += "\n"
        message += "<b>Level</b>\n"
        message += "\n"

        if quality_level_last_date:
            message += "Reservoir: " + str(quality_level_last_value) + " " + quality_level_uom + "\n"
            message += (quality_level_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Reservoir: -" + "\n"
            message += "\n"

        message += "\n"
        message += "<b>Quality</b>\n"
        message += "\n"

        if quality_turbidity_last_date:
            message += "Turbidity: " + str(quality_turbidity_last_value) + " " + quality_turbidity_uom + "\n"
            message += (quality_turbidity_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Turbidity: -" + "\n"
            message += "\n"

        if quality_ph_last_date:
            message += "PH: " + str(quality_ph_last_value) + " " + quality_ph_uom + "\n"
            message += (quality_ph_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "PH: -" + "\n"
            message += "\n"

        if quality_scm_last_date:
            message += "SCM: " + str(quality_scm_last_value) + " " + quality_scm_uom + "\n"
            message += (quality_scm_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "SCM: -" + "\n"
            message += "\n"

        if quality_dosing_last_date:
            message += "Dosing: " + str(quality_dosing_last_value) + " " + quality_dosing_uom + "\n"
            message += (quality_dosing_last_date + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S") + "\n"
            message += "\n"
        else:
            message += "Dosing: -" + "\n"
            message += "\n"

        params = {
            'chat_id': telegram_group.chat_id,
            'message': message
        }

        result = self.send_message(params)

    def get_rely_data(self, channel_name, logger_id, channel_id):
        logger = self.env['onpoint.logger'].search([('id', '=', logger_id)])
        channel = self.env['onpoint.logger.channel'].search([('id', '=', channel_id)])

        last_values = False
        last_date = False
        channel_unit = channel.value_unit_name if channel.value_unit_name else ""
        channel_last_value = channel.last_value + " " + channel_unit
        if channel.last_date:
            last_date = logger.convert_to_localtime(logger.id, channel.last_date)

        message = "-"
        if last_values != "":
            if logger.is_still_active:
                message = channel_name + ': ' + channel_last_value + '\n' + last_date
            else:
                message = channel_name + ': ' + '<b>INACTIVE</b> since <u>' + last_date + '</u>'

        return message

    @api.model
    def send_notification_relly(self):
        telegram_group = self.env['onpoint.telegram.group'].search([], limit=1)

        message = '<b>Gunung Relly</b>'
        message += '\n'
        message += '\n'
        message += '<b>Flow</b>'
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Inlet 8"', 2, 12)
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Outlet 8"', 1, 1)
        message += '\n'
        message += '\n'
        message += '<b>Pressure</b>'
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Outlet 8"', 1, 9)
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Inlet PRV Mandin', 3, 24)
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Outlet PRV Mandin', 3, 25)
        message += '\n'
        message += '\n'
        message += '<b>Level</b>'
        message += '\n'
        message += '\n'
        message += self.get_rely_data('Reservoir', 2, 21)

        loggers = self.env['onpoint.logger'].search([('id', 'in', (1, 2, 3)),
                                                     ('state', '=', 'enabled')])

        message_state = ''
        for logger in loggers:
            if logger.is_still_active:
                message_state += '\n'
                message_state += logger.name
                message_state += '\n'

                channels = logger.channel_ids.search([('logger_id', '=', logger.id),
                                                      ('point_id.alarm_type', '!=', False)])

                states = ""
                for channel in channels:
                    unit_name = ""
                    channel_value = channel.last_value
                    if channel.point_id.alarm_type in ('battery', 'external'):
                        channel_value = channel_value + " V"
                    elif channel.point_id.alarm_type == 'signal':
                        channel_value = channel_value + " dBm"
                    elif channel.point_id.alarm_type == 'temperature':
                        channel_value = channel_value + " C"
                    elif channel.point_id.alarm_type == 'submerged':
                        channel_value = "Unsub"
                    else:
                        channel_value = ""

                    if channel_value != "":
                        if states != "":
                            states = states + ", "

                        states = states + channel_value + " " + unit_name

                if states != '':
                    message_state += states
                    message_state += '\n'

        if message_state != '':
            message += '\n'
            message += '\n'
            message += '<b>Logger Status</b>'
            message += '\n'
            message += message_state

        params = {
            'chat_id': telegram_group.chat_id,
            'message': message
        }

        result = self.send_message(params)

