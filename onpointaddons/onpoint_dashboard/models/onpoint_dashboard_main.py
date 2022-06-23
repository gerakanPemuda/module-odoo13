from odoo import models, fields, api, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging

_logger = logging.getLogger(__name__)
PRODUCT_TYPE = ['all', 'car', 'bike', 'general']
EMERGENCY_TYPE = ['flat', 'gas', 'tow', 'battery']

# testing


class OnpointDashboardMain(models.AbstractModel):
    _name = 'onpoint.dashboard.main'
    _description = 'Onpoint Main Dashboard Functions'

    @api.model
    def get_data(self, logger_type=0, marker_type='logger_type', keyword=''):

        loggers = self.env['onpoint.logger'].get_map_data(int(logger_type), marker_type, keyword)
        onpoint_logger_types = self.env['onpoint.logger.type'].search([], order='sequence')

        logger_types = []
        for onpoint_logger_type in onpoint_logger_types:
            data = {
                'id': onpoint_logger_type.id,
                'name': onpoint_logger_type.name,
                'icon': onpoint_logger_type.image_128
            }
            logger_types.append(data)

        result = {
            'loggers': loggers,
            'logger_types': logger_types
        }
        return result

