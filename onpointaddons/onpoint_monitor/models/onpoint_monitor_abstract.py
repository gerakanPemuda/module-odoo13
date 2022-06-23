from odoo import models, fields, api, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging

_logger = logging.getLogger(__name__)


class OnpointMonitor(models.AbstractModel):
    _name = 'onpoint.monitor'
    _description = 'Onpoint Monitor Abstract Model'

    def get_time_zone(self, logger_id):
        logger = self.env['onpoint.logger'].browse(logger_id)
        convert_time = logger.convert_time
        if convert_time:
            time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        else:
            time_zone = 0
        return int(time_zone)

    def get_time_zone_inverse(self, logger_id):
        logger = self.env['onpoint.logger'].browse(logger_id)
        convert_time = logger.convert_time
        if not convert_time:
            time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        else:
            time_zone = 0
        return int(time_zone)

    def comparison_convert_to_localtime(self, logger_id, utctime):
        # add_hours = self.get_time_zone(logger_id)
        add_hours = 0

        localtime = (utctime + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S")
        return localtime

    def convert_to_localtime(self, logger_id, utctime):
        add_hours = self.get_time_zone(logger_id)

        localtime = (utctime + timedelta(hours=add_hours)).strftime("%d/%m/%Y %H:%M:%S")
        return localtime
