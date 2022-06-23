from odoo import models, fields, api
from datetime import datetime, timezone, timedelta


class OnpointMonitorDashboard(models.Model):
    _name = 'onpoint.monitor.dashboard'

    logger_id = fields.Many2one('onpoint.logger', required=True, index=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', index=True)

    @api.model
    def get_data(self):

        company = self.env.user.company_id

        loggers = self.get_dashboard_loggers()
        activities = self.get_dashboard_activities()
        active_loggers, total_loggers = self.count_loggers()

        datas = [{
            'company': company.name,
            'loggers': loggers,
            'activities': activities,
            'active_loggers': active_loggers,
            'total_loggers': total_loggers
        }]
        return datas

    def count_loggers(self):
        loggers = self.env['onpoint.logger'].search([('state', '=', 'enabled')])
        active_loggers = 0
        total_loggers = 0
        for logger in loggers:
            if logger.is_still_active:
                active_loggers += 1
            total_loggers += 1

        return active_loggers, total_loggers

    def get_dashboard_loggers(self):

        today = datetime.today()
        loggers = self.env['onpoint.monitor.dashboard'].sudo().search([('user_id', '=', self.env.uid)])

        results = []
        for logger in loggers:
            add_hours = logger.logger_id.get_time_zone(logger.logger_id.id)

            data_channels = []
            channels = logger.logger_id.channel_ids
            for channel in channels:
                if channel.display_on_chart:
                    data_channel = {
                        'id': channel.id,
                        'name': channel.value_type_name,
                        'color': channel.color,
                        'last_date': channel.last_date,
                        'last_value': channel.last_value,
                        'value_unit_name': channel.value_unit_id.name,
                    }
                    data_channels.append(data_channel)

            # Main Alarms
            alarms = self.env['onpoint.logger'].set_main_alarm(logger.logger_id.id, today, today)

            if logger.logger_id.last_data_date:
                last_data_date = logger.logger_id.last_data_date + timedelta(hours=add_hours)
            else:
                last_data_date = False
            data = {
                'id': logger.logger_id.id,
                'name': logger.logger_id.name,
                'logger_type_name' : logger.logger_id.logger_type_name,
                'channels': data_channels,
                'last_data_date': last_data_date.strftime('%d-%m-%Y %H:%M') if last_data_date else '',
                'alarms': alarms
            }
            results.append(data)

        return results

    def get_dashboard_activities(self):
        inactive_days = (int(self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.inactive_days'))  + 1) * -1
        today = datetime.today()
        minimum_date = today + timedelta(days=inactive_days)

        total = 0
        active = 0
        total = self.env['onpoint.logger'].search_count([('state', '=', 'enabled')])
        active = self.env['onpoint.logger'].search_count([('last_data_date', '>', minimum_date)])

        result = [{
            'total': total,
            'active': active,
            'inactive': 0
        }]

        return result
