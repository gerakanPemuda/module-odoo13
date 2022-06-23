from odoo import api, fields, models
# import pycurl
from urllib.parse import urlencode
from io import BytesIO
import json


class ZenzivaOutbox(models.Model):
    _name = 'zenziva.outbox'
    _description = 'Zenziva Outbox'
    _rec_name = 'message_id'
    _order = 'create_date desc'

    message_id = fields.Integer(string='Message ID')
    send_to = fields.Char(string='Send To', required=True)
    message = fields.Text(string='Message', required=True)
    text_response = fields.Char(string='Text Response')
    cost = fields.Integer(string='Cost')
    state = fields.Selection([
        ('-1', 'Draft'),
        ('0', 'Failed'),
        ('1', 'Success')
    ], default='-1', string="Status")

    def send_sms(self):

        zenziva_userkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_userkey')
        zenziva_passkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_passkey')

        response = BytesIO()
        # curl = pycurl.Curl()
        # url = 'https://console.zenziva.net/reguler/api/sendsms/';
        #
        # curl.setopt(curl.URL, url)

        post_data = {
            'userkey': zenziva_userkey,
            'passkey': zenziva_passkey,
            'to': self.send_to,
            'message': self.message
        }
        postfields = urlencode(post_data)

        # curl.setopt(curl.POSTFIELDS, postfields)
        # curl.setopt(curl.WRITEDATA, response)
        #
        # curl.perform()

        response_data = json.loads(response.getvalue())

        # curl.close()

        cost = 0
        if response_data['status'] == '1':
            cost = response_data['cost']

        self.update({
            'message_id': response_data['messageId'],
            'state': response_data['status'],
            'text_response': response_data['text'],
            'cost': cost
        })

    def send_whatsapp(self):

        zenziva_userkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_userkey')
        zenziva_passkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_passkey')

        # curl = pycurl.Curl()
        # url = 'https://console.zenziva.net/wareguler/api/sendWA/';
        #
        # curl.setopt(curl.URL, url)

        post_data = {
            'userkey': zenziva_userkey,
            'passkey': zenziva_passkey,
            'to': self.send_to,
            'message': self.message
        }
        postfields = urlencode(post_data)

        # curl.setopt(curl.POSTFIELDS, postfields)
        #
        # curl.perform()
        # curl.close()

