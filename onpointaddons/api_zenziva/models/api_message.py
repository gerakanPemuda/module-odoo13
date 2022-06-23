from odoo import api, fields, models
# import pycurl
from urllib.parse import urlencode


class ApiMessage(models.TransientModel):
    _name = 'api.message'

    send_to = fields.Char(string='Send To', default='+6288801620296', required=True)
    message = fields.Text(string='Message', required=True)

    def send_message(self):

        zenziva_userkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_userkey')
        zenziva_passkey = self.env['ir.config_parameter'].sudo().get_param('api.zenziva_passkey')

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
        #
        # curl.perform()
        # curl.close()

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

