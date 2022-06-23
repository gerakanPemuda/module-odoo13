# -*- coding: utf-8 -*-
#################################################################################
# Author      : OnpointDevTeam
# Copyright(c): 2021
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
import requests

from odoo.http import request
from odoo import http, _, exceptions
from datetime import date, datetime

import json

import logging
_logger = logging.getLogger(__name__)


class OnpointApi(http.Controller):

    @http.route('/auth/', type='json', auth='none', methods=["POST"], csrf=False)
    def authenticate(self, *args, **post):
        try:
            login = post["login"]
        except KeyError:
            raise exceptions.AccessDenied(message='`login` is required.')

        try:
            password = post["password"]
        except KeyError:
            raise exceptions.AccessDenied(message='`password` is required.')

        try:
            db = post["db"]
        except KeyError:
            raise exceptions.AccessDenied(message='`db` is required.')

        url_root = request.httprequest.url_root
        AUTH_URL = f"{url_root}web/session/authenticate/"

        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params": {
                "login": login,
                "password": password,
                "db": db
            }
        }

        res = requests.post(
            AUTH_URL,
            data=json.dumps(data),
            headers=headers
        )

        try:
            session_id = res.cookies["session_id"]
            user = json.loads(res.text)
            user["result"]["session_id"] = session_id
        except Exception:
            return "Invalid credentials."
        return user["result"]

    @http.route(['/api/get_all_loggers/'], type='json', auth='user', website=True)
    def get_all_loggers(self):
        loggers = request.env['onpoint.logger'].get_all_loggers()

        data = {
            'status': 200,
            'response': loggers,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_info_logger/<logger_id>'], type='json', auth='user', website=True)
    def get_info_logger(self, logger_id):
        logger = request.env['onpoint.logger'].get_info_logger(logger_id)

        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_value_logger_json/<logger_id>/<start_date>/<end_date>'], type='json', auth='user', website=True)
    def get_value_logger_json(self, logger_id, start_date, end_date):
        logger = request.env['onpoint.logger'].get_value_logger(logger_id, start_date, end_date)

        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_value_logger/<logger_id>/<start_date>/<end_date>'],
                type='http',
                auth='user',
                methods=["GET"],
                csrf=False,
                website=True)
    def get_value_logger(self, logger_id, start_date, end_date):
        logger = request.env['onpoint.logger'].get_value_logger(logger_id, start_date, end_date)

        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return json.dumps(data, default=self.json_serial)

    def json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))
