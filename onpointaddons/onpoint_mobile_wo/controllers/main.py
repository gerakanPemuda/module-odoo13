# -*- coding: utf-8 -*-
#################################################################################
# Author      : ObengDevTeam
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
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.tools.misc import file_open

import werkzeug
import json

import logging

_logger = logging.getLogger(__name__)


class OnpointMobileMain(http.Controller):

    @http.route('/mobile/wo/index', type='http', auth='user', website=True)
    def home(self):
        employee = request.env['onpoint.mobile.wo'].get_employee()
        active_work_orders = request.env['onpoint.mobile.wo'].get_work_orders()
        complete_work_orders = request.env['onpoint.mobile.wo'].get_complete_work_orders()
        values = {
            'employee': employee,
            'work_orders': active_work_orders,
            'complete_work_orders': complete_work_orders,
        }
        return request.render('onpoint_mobile_wo.main_layout', values)

    @http.route('/mobile/wo/detail/<wo_id>', type='http', auth='user', website=True)
    def detail(self, wo_id=None, **post):
        work_order = request.env['onpoint.mobile.wo'].get_work_order(wo_id)
        values = {
            'work_order': work_order
        }
        return request.render('onpoint_mobile_wo.wo_detail_page', values)

    @http.route('/mobile/wo/response',
                type='json',
                auth='user',
                website=True,
                methods=['POST'],
                csrf=False)
    def response(self, **post):
        form_values = json.loads(request.httprequest.data)
        request.env['onpoint.mobile.wo'].set_response(form_values)

        data = {
            'results': 'done'
        }

        return data

    @http.route('/mobile/wo/picture/<wo_id>/<state_to>', type='http', auth='user', website=True)
    def picture(self, wo_id=None, state_to=None, **post):
        work_order = request.env['onpoint.mobile.wo'].get_work_order(wo_id)
        values = {
            'work_order': work_order,
            'state_to': state_to
        }
        return request.render('onpoint_mobile_wo.wo_picture_page', values)

    @http.route('/mobile/wo/picture/submit',
                type='json',
                auth='user',
                website=True,
                methods=['POST'],
                csrf=False)
    def report(self, **post):
        form_values = json.loads(request.httprequest.data)
        request.env['onpoint.mobile.wo'].submit_report(form_values)

        data = {
            'results': 'done'
        }

        return data
