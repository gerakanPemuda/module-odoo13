from odoo import models, fields, api
from datetime import datetime, timedelta
import time
import logging
_logger = logging.getLogger(__name__)


class OnpointMobileWo(models.Model):
    _name = 'onpoint.mobile.wo'

    def get_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return employee

    def get_work_orders(self):
        employee = self.get_employee()
        work_orders = self.env['onpoint.work.order'].search([('state', 'not in', ('draft', 'complete')),
                                                             ('wo_type_pic_id', '=', employee.id)])
        return work_orders

    def get_complete_work_orders(self):
        employee = self.get_employee()
        work_orders = self.env['onpoint.work.order'].search([('state', '=', 'complete'),
                                                             ('wo_type_pic_id', '=', employee.id)])
        return work_orders

    def get_work_order(self, wo_id):
        work_order = self.env['onpoint.work.order'].search([('id', '=', wo_id)])
        return work_order

    def set_response(self, form_values):
        work_order = self.env['onpoint.work.order'].search([('id', '=', form_values['wo_id'])])
        if form_values['response'] == 'accept':
            work_order.act_accept()

        return work_order

    def submit_report(self, form_values):
        work_order = self.env['onpoint.work.order'].search([('id', '=', form_values['wo_id'])])
        work_order_line = self.env['onpoint.work.order.line'].create({
            'wo_id': work_order.id,
            'state_from': work_order.state,
            'state_to': form_values['state_to'],
            'image_1920': form_values['image'],
            'remark': form_values['remark'],
        })

        if work_order.state != form_values['state_to']:
            work_order.write({
                'state': form_values['state_to']
            })

        return work_order_line

