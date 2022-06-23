from odoo import api, http, tools, _
from odoo.http import request
from datetime import datetime, timezone, timedelta
from odoo.addons.http_routing.models.ir_http import unslug
import math
import werkzeug
import json
import requests
from odoo.exceptions import ValidationError
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import logging

class OnpointliteApiMain(http.Controller):

    # @http.route('/auth/', type='json', auth='none', methods=["POST"], csrf=False)
    # def authenticate(self, *args, **post):
    #     try:
    #         login = post["login"]
    #     except KeyError:
    #         raise exceptions.AccessDenied(message='`login` is required.')

    #     try:
    #         password = post["password"]
    #     except KeyError:
    #         raise exceptions.AccessDenied(message='`password` is required.')

    #     try:
    #         db = post["db"]
    #     except KeyError:
    #         raise exceptions.AccessDenied(message='`db` is required.')

    #     url_root = request.httprequest.url_root
    #     AUTH_URL = f"{url_root}web/session/authenticate/"

    #     headers = {'Content-type': 'application/json'}

    #     data = {
    #         "jsonrpc": "2.0",
    #         "params": {
    #             "login": login,
    #             "password": password,
    #             "db": db
    #         }
    #     }

    #     res = requests.post(
    #         AUTH_URL,
    #         data=json.dumps(data),
    #         headers=headers
    #     )

    #     try:
    #         session_id = res.cookies["session_id"]
    #         user = json.loads(res.text)
    #         user["result"]["session_id"] = session_id
    #     except Exception:
    #         return "Invalid credentials."
    #     return user["result"]

    @http.route(['/api/get_loggers'], type='json', auth='user', website=True)
    def get_loggers(self, **post):
        loggers = request.env['onpointlite.api.abstract'].get_loggers(post["param_search"])
        # loggers = request.env['onpoint.logger'].get_all_loggers()

        data = {
            'status': 200,
            'response': loggers,
            'message': 'Success'
        }
        return data

    @http.route('/api/generate_logger_report', type='json', auth='user', website=True)
    def generate_logger_report(self, **post):
        # form_values = json.loads(request.httprequest.data)
        report = request.env['onpointlite.api.abstract'].generate_logger_report(post["datas"])
        # data = {
        #     'report_id': report.id
        # }

        data = {
            'status': 200,
            'response': report.id,
            'message': 'Success'
        }

        return data

    @http.route(['/api/get_logger_chart'], type='json', auth='user', website=True)
    def get_logger_chart(self, **post):
        logger = request.env['onpointlite.api.abstract'].get_logger_chart(post["logger_id"])
        
        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_logger_detail'], type='json', auth='user', website=True)
    def get_logger_detail(self, **post):
        logger = request.env['onpointlite.api.abstract'].get_logger_detail(post["logger_id"])
        # loggers = request.env['onpoint.logger'].get_all_loggers()

        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_logger_channel_consumption'], type='json', auth='user', website=True)
    def get_logger_channel_consumption(self, **post):
        logger = request.env['onpointlite.api.abstract'].get_logger_channel_consumption(post["logger_id"], post["channel_id"])
        # logger = request.env['onpoint.logger'].get_consumption_logger(post["logger_id"], post["channel_id"])
        # values = {
        #     'logger_id': logger_id,
        #     'channel_id': channel_id,
        #     'logger': logger,
        # }
        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_logger_channel_consumption_chart'], type='json', auth='user', website=True)
    def get_logger_channel_consumption_chart(self, **post):
        # form_values = json.loads(request.httprequest.data)
        # logger = request.env['onpoint.logger'].get_consumption_logger(form_values['logger_id'], form_values['channel_id'], form_values['interval'])
        # values = {
        #     'logger': logger,
        # }
        # return values
        logger = request.env['onpointlite.api.abstract'].get_logger_channel_consumption(post["logger_id"], post["channel_id"], post["interval"])
        data = {
            'status': 200,
            'response': logger,
            'message': 'Success'
        }
        return data

    @http.route(['/api/create_loggers'], type='json', auth='user', website=True)
    def create_loggers(self, **post):
        loggers = request.env['onpointlite.api.abstract'].create_loggers(post["param_datas"])

        data = {
            'status': 200,
            'response': loggers,
            'message': 'Success'
        }
        return data

    @http.route(['/api/update_loggers'], type='json', auth='user', website=True)
    def update_loggers(self, **post):
        loggers = request.env['onpointlite.api.abstract'].update_loggers(post["param_datas"])

        data = {
            'status': 200,
            'response': loggers,
            'message': 'Success'
        }
        return data

    @http.route(['/api/get_logger_types'], type='json', auth='user', website=True)
    def get_logger_types(self, **post):
        loggers = request.env['onpointlite.api.abstract'].get_logger_types(post["param_search"])

        data = {
            'status': 200,
            'response': loggers,
            'message': 'Success'
        }
        return data

    # # @http.route('/wtclite/logger/disable', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    # @http.route('/wtclite/logger/disable', type='json', auth='user', website=True)
    # def logger_disable(self, **post):
    #     form_values = json.loads(request.httprequest.data)
    #     logger = request.env['onpoint.logger'].disable_logger(form_values)
    #     data = {
    #         'results': 'done',
    #     }
    #     return data

    # def connect_destination_db(self, url, db, username, password):
    #     common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    #     uid = common.authenticate(db, username, password, {})

    #     return uid

        # common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        # uid = common.authenticate(db, username, password, {})

        # info = xmlrpc.client.ServerProxy('https://demo.odoo.com/start').start()
        # url, db, username, password = info['host'], info['database'], info['user'], info['password']

    # @http.route('/onpointlite/mobile/list', type='http', auth='user', website=True)
    # def home(self):
    #     loggers = request.env['onpoint.logger'].get_loggers_by_state('enabled')
    #     values = {
    #         'loggers': loggers,
    #     }
    #     return request.render('onpoint_wtclite.main_layout', values)

    # @http.route('/mobile/server/get_loggers', type='http', auth='user')
    # @http.route('/onpointlite/mobile/get_loggers', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    # @http.route('/mobile/server/get_loggers', type='json', auth='user', methods=['POST'])
    # def get_loggers(self, **post):
    #     url = "https://onpointpdam.wtccloud.net/mobile/client/get_loggers"
    #     # payload = "{'start_time' : '2020/03/01 00:00:00', 'stop_time' : '2020/03/30 23:59:59', 'lstNoPOL' : ['L 8292 UF']}"
        
    #     # url = "https://vtsapi.easygo-gps.co.id/api/report/lastposition"
    #     headers = {
    #         # 'Content-Type': 'application/json',
    #         'X-Openerp': post["session_id"]
    #         }
    #     body = "{'param_search' : [%s]}"%(post["param_search"])
        

    #     response = requests.post(url, headers=headers, data=body)



    #     # url = 'https://onpointpdam.wtccloud.net'
    #     # db = 'onpointpdam'
    #     # username = 'admin'
    #     # password = 'onpoint#123'

    #     # connect_destination_db = request.connect_destination_db(url, db, username, password)

    #     # models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    #     # count_logger = models.execute_kw(db, uid, password, 'onpoint.logger', 'search_count', [[['state', '=', 'enabled']]])

    #     # values = {
    #     #     'logger': logger,
    #     # }
    #     return response

    @http.route('/demo_html', type="http") #Work Pefrect when I call this URL
    def some_html(self):
        return "<h1>This is a test</h1>"

    @http.route('/demo_json', type="json") #Not working when I call this URL
    def some_json(self):
        x = {"sample_dictionary": "This is a sample JSON dictionary"}
        # return json.dumps(x)
        return False

# class OnpointMimicDiagram(http.Controller):

#     # @http.route('/mimic/diagram/<mimic_id>', type='http', auth='user', website=True)
#     # def show_mimic_diagram(self, mimic_id=0):
#     #     mimic = request.env['onpoint.mimic'].get_template(mimic_id)
#     #     template_name = 'onpoint_mimic.' + mimic.template_name
#     #     return request.render(template_name)

#     @http.route('/mimic/diagram/<mimic_id>', type='http', auth='user', website=True)
#     def show_mimic_diagram(self, mimic_id=0):
#         template = request.env['onpoint.mimic'].get_template(mimic_id)

#         return request.render('onpoint_mimic.main_layout1', template)

#     # @http.route('/mimic/chart/<mimic_id>', type='http', auth='user', website=True)
#     # def show_chart(self, mimic_id=0):
#     #     data = request.env['onpoint.mimic'].get_chart(mimic_id)
#     #
#     #     value = {
#     #         'data': data,
#     #     }
#     #
#     #     return request.render('onpoint_mimic.chart_layout', value)

    # @http.route('/test', type='json', auth='user')
    # def test(self):
    #     # url = "https://vtsapi.easygo-gps.co.id/api/report/historydata"
    #     # payload = "{'start_time' : '2020/03/01 00:00:00', 'stop_time' : '2020/03/30 23:59:59', 'lstNoPOL' : ['L 8292 UF']}"
        
    #     # url = "https://vtsapi.easygo-gps.co.id/api/report/lastposition"
    #     # payload = "{'data'  : ['L 8292 UF']}"
    #     # headers = {
    #     #     'Content-Type': 'application/json',
    #     #     'token': '2159D8D070484E4B9E58D71C53E997EE'
    #     #     }

    #     # response = requests.request("POST", url, headers=headers, data = payload)

    #     value = {
    #         'logger': 'tes',
    #         # 'channel': channel,
    #         # 'action_id': action_id.id,
    #         # 'menu_id': menu_id.id,
    #         # 'series_data': series_data
    #     }
        # return json.dumps(value)

#     @http.route('/mimic/get_data/', type='json', auth='user', csrf=False)
#     def get_data(self, **post):
#         logger_id = post.get('logger_id')

#         data = {'value': '109'}
#         return data


