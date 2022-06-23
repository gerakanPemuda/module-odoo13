from odoo import api, http, tools, _
from odoo.http import request, Response
from odoo.exceptions import ValidationError
import requests
from datetime import datetime, timezone, timedelta
from odoo.addons.http_routing.models.ir_http import unslug

import werkzeug
import json

import logging

_logger = logging.getLogger(__name__)


class OnpointScadaMain(http.Controller):

    @http.route('/home', type='http', auth='user', website=True)
    def home(self):
        config_action_id = request.env.ref('onpoint_modbus.act_onpoint_mmim').id
        mimic_image = 'GUNUNG-ULIN-GIF.gif'
        results = {
            'config_action_id': config_action_id,
            'mimic_image': mimic_image
        }

        return request.render('onpoint_scada_samarinda.home_layout', results)

    @http.route('/home/get_data', type='json', auth='user', methods=["POST"], csrf=False, website=True)
    def get_data(self, **data):
        form_values = json.loads(request.httprequest.data)
        data = request.env['onpoint.mmim.line'].get_last_data(2)

        results = {
            'val': data.last_value,
        }

        return results
