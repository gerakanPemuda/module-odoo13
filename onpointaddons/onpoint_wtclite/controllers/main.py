# -*- coding: utf-8 -*-
#################################################################################
# Author      : WTCDevTeam
# Copyright(c): 2020
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
from odoo import api, http, tools, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from odoo.addons.http_routing.models.ir_http import unslug

import werkzeug
import json

import logging

_logger = logging.getLogger(__name__)


class WTCLiteMain(http.Controller):

    @http.route('/wtclite/index', type='http', auth='user', website=True)
    def home(self):
        loggers = request.env['onpoint.logger'].get_loggers_by_state('enabled')
        values = {
            'loggers': loggers,
        }
        return request.render('onpoint_wtclite.main_layout', values)

    @http.route('/wtclite/logger/form', type='http', auth='user', website=True)
    def logger_form(self):
        logger_types = request.env['onpoint.logger.type'].get_all()
        values = {
            'logger_types': logger_types
        }
        return request.render('onpoint_wtclite.logger_form_page', values)

    @http.route('/wtclite/logger/create', type='json', auth='user', website=True, methods=['POST'],
                csrf=False)
    def logger_create(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger = request.env['onpoint.logger'].set_logger(form_values)

        data = {
            'results': 'done',
            'logger_id': logger.id
        }

        return data

    @http.route('/wtclite/logger/disable', type='json', auth='user', website=True, methods=['POST'],
                csrf=False)
    def logger_disable(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger = request.env['onpoint.logger'].disable_logger(form_values)
        data = {
            'results': 'done',
        }
        return data

    @http.route('/wtclite/logger/detail/<logger_id>', type='http', auth='user', website=True)
    def logger_detail(self, logger_id):
        logger = request.env['onpoint.logger'].get_detail_logger(logger_id)
        values = {
            'logger': logger,
        }
        return request.render('onpoint_wtclite.logger_detail_page', values)

    @http.route('/wtclite/logger/refresh', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def logger_detail_refresh(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger = request.env['onpoint.logger'].get_detail_logger_refresh(form_values['logger_id'])
        values = {
            'logger': logger,
        }
        return request.render('onpoint_wtclite.logger_detail_page', values)

    @http.route('/wtclite/logger/channel/form/<channel_id>', type='http', auth='user', website=True)
    def logger_channel_form(self, channel_id):
        channel = request.env['onpoint.logger.channel'].get_data(channel_id)
        points = request.env['onpoint.logger.point'].get_all(channel['brand_owner'])

        values = {
            'channel_id': channel_id,
            'channel': channel,
            'points': points
        }
        return request.render('onpoint_wtclite.logger_channel_form_page', values)

    # @http.route('/wtclite/logger/channel/form/get_data', type='json', auth='user', website=True, methods=['POST'],
    #             csrf=False)
    # def logger_channel_get_data(self, **post):
    #     form_values = json.loads(request.httprequest.data)
    #     channel = request.env['onpoint.logger.channel'].get_data(form_values['channel_id'])
    #
    #     data = {
    #         'results': 'done',
    #         'channel': channel,
    #     }
    #     return data

    @http.route('/wtclite/logger/channel/update', type='json', auth='user', website=True, methods=['POST'],
                csrf=False)
    def logger_channel_update(self, **post):
        form_values = json.loads(request.httprequest.data)
        channel = request.env['onpoint.logger.channel'].set_channel(form_values)

        data = {
            'results': 'done',
        }

        return data

    @http.route('/wtclite/logger/chart', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def logger_chart(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger = request.env['onpoint.logger'].get_chart_logger(form_values['logger_id'])
        values = {
            'logger': logger,
        }
        return values

    @http.route('/wtclite/logger/report', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def logger_report(self, **post):
        form_values = json.loads(request.httprequest.data)
        report = request.env['onpoint.logger'].generate_mobile_report(form_values)
        data = {
            'report_id': report.id
        }

        return data

    @http.route('/wtclite/logger/consumption/<logger_id>/<channel_id>', type='http', auth='user', website=True)
    def logger_consumption(self, logger_id, channel_id):
        logger = request.env['onpoint.logger'].get_consumption_logger(logger_id, channel_id)
        values = {
            'logger_id': logger_id,
            'channel_id': channel_id,
            'logger': logger,
        }
        return request.render('onpoint_wtclite.logger_consumption_page', values)

    @http.route('/wtclite/logger/consumption/report/<logger_id>/<channel_id>', type='http', auth='user', website=True)
    def logger_consumption_report(self, logger_id, channel_id):
        # logger = request.env['report.onpoint_wtclite.consumption_report'].generate_xlsx_report(logger_id, channel_id)
        x = 1
        y = 1
        return True

    @http.route('/wtclite/logger/consumption/chart', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def logger_consumption_chart(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger = request.env['onpoint.logger'].get_consumption_logger(form_values['logger_id'],
                                                                      form_values['channel_id'],
                                                                      form_values['interval'])
        values = {
            'logger': logger,
        }
        return values

    @http.route('/wtclite/logger/threshold/<logger_id>/<channel_id>', type='http', auth='user', website=True)
    def logger_threshold(self, logger_id, channel_id):
        logger = request.env['onpoint.logger'].get_threshold_logger(logger_id, channel_id)
        values = {
            'logger': logger,
        }
        return request.render('onpoint_wtclite.logger_threshold_page', values)

    @http.route('/wtclite/logger/threshold/update', type='json', auth='user', website=True, methods=['POST'],
                csrf=False)
    def logger_threshold_update(self, **post):
        form_values = json.loads(request.httprequest.data)
        request.env['onpoint.logger'].set_threshold(form_values)

        data = {
            'results': 'done'
        }

        return data

    @http.route('/wtclite/logout', type='http', auth='user', website=True)
    def mobile_logout(self):
        request.session.logout(keep_db=True)
        data = {
            'success': True
        }
        return json.dumps(data)
