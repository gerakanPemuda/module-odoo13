from odoo import models, fields, api, _
import requests
from urllib.parse import urlencode
from io import BytesIO
import json


class ApiTelegramAbstract(models.AbstractModel):
    _name = 'api.telegram.abstract'
    _description = 'Telegram Driver'

    def send_message(self, params):
        telegram_token = self.env['ir.config_parameter'].sudo().get_param('api_telegram.telegram_token')

        chat_id = params['chat_id']
        message = params['message']

        url_req = "https://api.telegram.org/bot" + telegram_token + "/sendMessage" + "?chat_id=" + chat_id + '&text=' + message + '&parse_mode=html'
        results = requests.get(url_req)
        print(results.json())
        response_data_telegram = results.json()

        return response_data_telegram
