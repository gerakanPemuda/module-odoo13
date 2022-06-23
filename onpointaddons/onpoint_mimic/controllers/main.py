# -*- coding: utf-8 -*-
from odoo import api, http, tools, _
from odoo.http import request
import json

class OnpointMimicDiagram(http.Controller):

    # @http.route('/mimic/diagram/<mimic_id>', type='http', auth='user', website=True)
    # def show_mimic_diagram(self, mimic_id=0):
    #     mimic = request.env['onpoint.mimic'].get_template(mimic_id)
    #     template_name = 'onpoint_mimic.' + mimic.template_name
    #     return request.render(template_name)

    @http.route('/mimic/diagram/<mimic_id>', type='http', auth='user', website=True)
    def show_mimic_diagram(self, mimic_id=0):
        template = request.env['onpoint.mimic'].get_template(mimic_id)

        return request.render('onpoint_mimic.main_layout1', template)

    # @http.route('/mimic/chart/<mimic_id>', type='http', auth='user', website=True)
    # def show_chart(self, mimic_id=0):
    #     data = request.env['onpoint.mimic'].get_chart(mimic_id)
    #
    #     value = {
    #         'data': data,
    #     }
    #
    #     return request.render('onpoint_mimic.chart_layout', value)

    @http.route('/mimic/chart/<logger_id>/<channel_id>', type='http', auth='user', website=True)
    def show_chart(self, logger_id, channel_id):
        data_logger, data_channel, data_value = request.env['onpoint.mimic'].get_chart(logger_id, channel_id)

        action_id = request.env['ir.actions.actions'].search([('name', '=', 'View Logger Chart')])
        menu_id = request.env['ir.ui.menu'].search([('name', '=', 'Monitor')])

        series_data = {
            'name': data_channel.name,
            'type': 'line',
            'yAxis': 0,
            'zIndex': '1',
            'data': data_value,
        }

        logger = {
            'id': data_logger.id,
            'name': data_logger.name
        }

        channel = {
            'name': data_channel.name,
            'value_unit': data_channel.value_unit_name
        }

        value = {
            'logger': logger,
            'channel': channel,
            'action_id': action_id.id,
            'menu_id': menu_id.id,
            'series_data': series_data
        }
        return json.dumps(value)

    @http.route('/mimic/get_data/', type='json', auth='user', csrf=False)
    def get_data(self, **post):
        logger_id = post.get('logger_id')

        data = {'value': '109'}
        return data


