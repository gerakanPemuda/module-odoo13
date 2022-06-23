from odoo import api, http, tools, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from odoo.addons.http_routing.models.ir_http import unslug
import math
import werkzeug
import json
from odoo.exceptions import ValidationError
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import logging
import requests

_logger = logging.getLogger(__name__)

class OnpointliteBaseMain(http.Controller):

    def destination_authenticate(self, url, db, login, password):
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params": {
                "db": db,
                "login": login,
                "password": password,
            }
        }

        res = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
        )

        session_id = res.cookies["session_id"]
        
        return session_id

    @http.route(['/mobile/index'], type='http', auth='user', website=True)
    def dashboard(self):
        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])
        
        url_root_prefix = company.website
        url_root_suffix = '/api/get_loggers'
        url = url_root_prefix + url_root_suffix
        
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "param_search": "[('state', '=', 'enabled')]"
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }


        get_loggers = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
            cookies=cookies,
        )

        loggers = get_loggers.json()

        values = {
            'loggers': loggers['result']['response'],
        }
        return request.render('onpointlite_base.main_layout', values)

    @http.route(['/mobile/logger/form'], type='http', auth='user', website=True)
    def logger_form(self):
        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_types'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "param_search": "[]"
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }


        get_logger_types = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
            cookies=cookies,
        )

        logger_types = get_logger_types.json()

        values = {
            'logger_types': logger_types['result']['response'],
        }
        return request.render('onpointlite_base.logger_form_page', values)

    @http.route(['/mobile/logger/create'], type='json', auth='user', website=True)
    def logger_create(self, **post):
        form_values = json.loads(request.httprequest.data)

        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/create_loggers'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params": {"param_datas": "[{'name': '%s', 'identifier': '%s', 'logger_type_id': %s, 'address': '%s', 'latitude': %s, 'longitude': %s}]"%(str(form_values.get('name')), str(form_values.get('identifier')), str(form_values.get('logger_type_id')), str(form_values.get('address')), str(form_values.get('latitude')), str(form_values.get('longitude')),)}
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_create_logger = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        create_logger = connect_create_logger.json()

        return create_logger['result']

    @http.route(['/mobile/logger/disable'], type='json', auth='user', website=True)
    def logger_disable(self, **post):
        form_values = json.loads(request.httprequest.data)

        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/update_loggers'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{"param_datas": "[{'logger_id': %s, 'data_update': {'state': 'disabled'} }]"%(str(form_values.get('logger_id')))}
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_update_logger = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        update_logger = connect_update_logger.json()

        return update_logger['result']

    @http.route(['/mobile/logger/chart'], type='json', auth='user', website=True)
    def logger_chart(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger_id = form_values.get('logger_id')

        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_chart'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "logger_id": int(logger_id),
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_logger_chart = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        create_logger_chart = connect_logger_chart.json()

        return create_logger_chart['result']

    @http.route(['/mobile/logger/report'], type='json', auth='user', website=True)
    def logger_report(self, **post):
        form_values = json.loads(request.httprequest.data)

        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/generate_logger_report'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "datas": form_values,
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_logger_report = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        create_logger_report = connect_logger_report.json()

        return create_logger_report['result']

    @http.route(['/mobile/logger/detail/<logger_id>'], type='http', auth='user', website=True)
    def logger_detail(self, logger_id):
        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_detail'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "logger_id": int(logger_id),
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }


        get_logger_detail = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
            cookies=cookies,
        )

        logger_detail = get_logger_detail.json()

        values = {
            'logger_profile': logger_detail['result']['response']['logger_profile'],
            'logger_channels': logger_detail['result']['response']['logger_channels'],
            'logger_chart': logger_detail['result']['response']['logger_chart'],
        }
        return request.render('onpointlite_base.logger_detail_page', values)

    @http.route(['/mobile/logger/channel/consumption/<logger_id>/<channel_id>'], type='http', auth='user', website=True)
    def logger_channel_consumption(self, logger_id, channel_id):
        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_channel_consumption'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "logger_id": int(logger_id),
                "channel_id": int(channel_id),
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_logger_channel_consumption = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        logger_channel_consumption = connect_logger_channel_consumption.json()

        values = {
            'logger_id': logger_id,
            'channel_id': channel_id,
            'logger_channel_consumption': logger_channel_consumption['result']['response'],
            # 'logger_channels': logger_detail['result']['response']['logger_channels'],
            # 'logger_chart': logger_detail['result']['response']['logger_chart'],
        }
        return request.render('onpointlite_base.logger_channel_consumption_page', values)

    @http.route(['/mobile/logger/channel/consumption/chart'], type='json', auth='user', website=True)
    def logger_channel_consumption_chart(self, **post):
        form_values = json.loads(request.httprequest.data)
        logger_id = form_values.get('logger_id')
        channel_id = form_values.get('channel_id')
        interval = form_values.get('interval')

        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_channel_consumption_chart'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "logger_id": int(logger_id),
                "channel_id": int(channel_id),
                "interval": interval,
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }

        connect_logger_channel_consumption_chart = requests.post(
            url,
            json=data,
            headers=headers,
            cookies=cookies,
        )

        create_logger_channel_consumption_chart = connect_logger_channel_consumption_chart.json()

        return create_logger_channel_consumption_chart['result']

    @http.route(['/mobile/logger/channel/form/<channel_id>'], type='http', auth='user', website=True)
    def logger_channel_form(self):
        user = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        company = request.env['res.company'].sudo().search([('id', '=', user.company_id.id)])

        url_root_prefix = company.website
        url_root_suffix = '/api/get_logger_types'
        url = url_root_prefix + url_root_suffix
        db = (url.split(".")[0]).split("//")[1]
        login = company.api_login
        password = company.api_password

        destination_authenticate = self.destination_authenticate(company.website + '/web/session/authenticate', db, login, password)
        
        headers = {'Content-type': 'application/json'}

        data = {
            "jsonrpc": "2.0",
            "params":{
                "param_search": "[]"
            }
        }

        cookies = {
            "login": login,
            "password": password,
            "session_id" : destination_authenticate,
        }


        get_logger_types = requests.post(
            url,
            data=json.dumps(data),
            headers=headers,
            cookies=cookies,
        )

        logger_types = get_logger_types.json()

        values = {
            'logger_types': logger_types['result']['response'],
        }
        return request.render('onpointlite_base.logger_form_page', values)

    @http.route(['/mobile/logout'], type='http', auth='user', website=True)
    def mobile_logout(self):
        request.session.logout(keep_db=True)
        data = {
            'success': True
        }
        return json.dumps(data)

    # @http.route(['/mobile/testing'], type='json', auth='user', website=True)
    # def testing(self, **post):
    #     form_values = json.loads(request.httprequest.data)

    #     login = 'mobile_api@email.com'
    #     password = 'onpoint#123'

    #     destination_authenticate = self.destination_authenticate('https://onpointpdam.wtccloud.net/web/session/authenticate', 'onpointpdam', login, password)

    #     url = 'https://onpointpdam.wtccloud.net/api/create_loggers'
    #     data = {
    #         "jsonrpc": "2.0", 
    #         "params": {"param_datas": "[{'name': '%s', 'identifier': '%s', 'logger_type_id': %s, 'address': '%s', 'latitude': %s, 'longitude': %s}]"%(
    #             str(form_values.get('name')),
    #             str(form_values.get('identifier')),
    #             str(form_values.get('logger_type_id')),
    #             str(form_values.get('address')),
    #             str(form_values.get('latitude')),
    #             str(form_values.get('longitude')),
    #             )}
    #         }

    #     headers = {'Content-type': 'application/json'}
    #     cookies = {
    #         "login": login,
    #         "password": password,
    #         "session_id" : destination_authenticate,
    #     }

    #     connect_create_logger = requests.post(
    #         url,
    #         json=data,
    #         headers=headers,
    #         cookies=cookies,
    #     )

    #     create_logger = connect_create_logger.json()

    #     return create_logger['result']
