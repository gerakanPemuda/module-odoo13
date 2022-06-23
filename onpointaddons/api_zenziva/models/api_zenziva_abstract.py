from odoo import models, fields, api, _
# import pycurl
from urllib.parse import urlencode
from io import BytesIO
import json

import logging

_logger = logging.getLogger(__name__)


class ApiZenzivaAbstract(models.AbstractModel):
    _name = 'api.zenziva.abstract'
    _description = 'Zenziva Driver'

    def send_message(self, params):
        zenziva_userkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_userkey')
        zenziva_passkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_passkey')

        send_to = params['send_to']
        message = params['message']

        post_data = {
            'userkey': zenziva_userkey,
            'passkey': zenziva_passkey,
            'to': send_to,
            'message': message
        }
        postfields = urlencode(post_data)

        response_data_sms = False
        response_data_wa = False

        if params['send_sms']:
            response = BytesIO()
            # curl = pycurl.Curl()
            # url = 'https://console.zenziva.net/reguler/api/sendsms/'
            #
            # curl.setopt(curl.URL, url)
            #
            # curl.setopt(curl.POSTFIELDS, postfields)
            # curl.setopt(curl.WRITEDATA, response)
            #
            # curl.perform()
            #
            # response_data_sms = json.loads(response.getvalue())
            #
            # curl.close()

        if params['send_wa']:
            response_wa = BytesIO()
            # curl_wa = pycurl.Curl()
            # url_wa = 'https://console.zenziva.net/wareguler/api/sendWA/'
            #
            # curl_wa.setopt(curl_wa.URL, url_wa)
            #
            # curl_wa.setopt(curl_wa.POSTFIELDS, postfields)
            # curl_wa.setopt(curl_wa.WRITEDATA, response_wa)
            #
            # curl_wa.perform()
            #
            # response_data_wa = json.loads(response_wa.getvalue())
            #
            # curl_wa.close()

        return response_data_sms, response_data_wa
