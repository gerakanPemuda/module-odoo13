from odoo import models, fields, api
# from easymodbus.modbusClient import ModbusClient
import logging
_logger = logging.getLogger(__name__)


class OnpointStyleSheet(models.Model):
    _name = 'onpoint.style.sheet'

    name = fields.Char(required=True, string='Name')
