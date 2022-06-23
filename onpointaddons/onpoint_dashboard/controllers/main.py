# -*- coding: utf-8 -*-
#################################################################################
# Author      : OnpointDevTeam
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
import werkzeug.utils
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.tools.misc import file_open

import werkzeug
import json

import logging
_logger = logging.getLogger(__name__)


class OnpointDashboardMain(http.Controller):

    @http.route('/dashboard/main', type='http', auth='user', website=True)
    def main_page(self):
        config = http.request.env['ir.config_parameter'].sudo()
        google_maps_api_key = config.get_param('google_maps_view_api_key', default='')

        # map_data = request.env['onpoint.logger'].get_map_data()

        values = {
            # 'map_data': map_data,
            'google_maps_api_key': google_maps_api_key
        }
        return request.render('onpoint_dashboard.main_layout', values)

    @http.route('/dashboard/goto_monitor', type='http', auth='user', website=True)
    def goto_monitor(self):
        action_id = http.request.env.ref('onpoint_monitor.act_onpoint_logger').id
        return werkzeug.utils.redirect('/web#action=%s&model=onpoint.logger&view_type=kanban' % (action_id))

    @http.route('/dashboard/goto_mimic', type='http', auth='user', website=True)
    def goto_mimic(self):
        action_id = http.request.env.ref('onpoint_mimic.act_onpoint_mimic').id
        return werkzeug.utils.redirect('/web#action=%s&model=onpoint.mimic&view_type=kanban' % (action_id))
