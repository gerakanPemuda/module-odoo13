# -*- coding: utf-8 -*-
from odoo import api, http, tools, _
from odoo.http import request, Response
import json
import werkzeug


class OnpointProduction(http.Controller):

    @http.route('/location/<location_id>', type='http', auth='user', website=True)
    def show_location(self, location_id=0):
        location_data, loggers = request.env['onpoint.scada.location'].get_data(location_id)
        action_logger_chart_id = request.env.ref('onpoint_monitor.act_view_logger_chart').id
        menu_monitor_id = request.env.ref('onpoint_monitor.menu_onpoint_root').id
        values = {
            'location_data': location_data,
            'loggers': loggers,
            'action_logger_chart_id': action_logger_chart_id,
            'menu_monitor_id': menu_monitor_id
        }

        return request.render('onpoint_scada.location_layout', values)

    @http.route('/unit/<unit_id>', type='http', auth='user', website=True)
    def show_unit(self, unit_id=0):
        unit_action_id = request.env.ref('onpoint_scada.act_view_unit_chart').id
        # return werkzeug.utils.redirect('/web&#35;action=' + str(unit_action_id) + '&#38;active_id=' + str(unit_id) + '&#38;cids=1&#38;menu_id=140')

        unit, loggers = request.env['onpoint.scada.unit'].get_data(unit_id)
        action_logger_chart_id = request.env.ref('onpoint_monitor.act_view_logger_chart').id
        menu_monitor_id = request.env.ref('onpoint_monitor.menu_onpoint_root').id

        values = {
            'unit': unit,
            'unit_action_id': unit_action_id,
            'loggers': loggers,
            'action_logger_chart_id': action_logger_chart_id,
            'menu_monitor_id': menu_monitor_id
        }
        return request.render('onpoint_scada.unit_layout', values)

    @http.route('/unit/get_data_detail', type='http', auth='user', methods=["POST"], csrf=False, website=True)
    def get_data_unit(self, **data):
        y_axis, series, stats = request.env['onpoint.scada.unit'].get_data_detail(data['unit_id'],
                                                                                  data['rangeDate'],
                                                                                  data['select_hour'],
                                                                                  data['interval'])

        headers = {'Content-Type': 'application/json'}
        body = {'results':
            {
                'code': 200,
                'message': 'OK',
                'y_axis': y_axis,
                'series': series,
                'stats': stats
            }
        }

        return Response(json.dumps(body), headers=headers)

    @http.route('/unit/toggle_auto_refresh', type='http', auth='user', methods=["POST"], csrf=False, website=True)
    def toggle_auto_refresh(self, **data):
        auto_refresh = request.env['onpoint.scada.unit'].toggle_auto_refresh(int(data['unit_id']))
        return True

    @http.route('/unit/print', type='http', auth='user', methods=["POST"], csrf=False, website=True)
    def print(self, **data):
        x = data['unit_id']
        y = data['img_chart']
        z = 1
        w = request.env['onpoint.scada.unit'].generate_pdf_report()
        return True
