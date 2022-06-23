from odoo import models, fields, api
# from easymodbus.modbusClient import ModbusClient
from pyModbusTCP.client import ModbusClient
import time
import logging
import math
_logger = logging.getLogger(__name__)


class OnpointModbusComm(models.TransientModel):
    _name = 'onpoint.modbus.comm'

    name = fields.Char(required=True, string='Server Host', default='192.168.1.1')
    port = fields.Char(required=True, string='Port', default='1100')
    unit_id = fields.Integer(required=True, default=1)
    address = fields.Integer(required=True, default=1)
    qty = fields.Integer(required=True, default=1)
    imin = fields.Integer(required=True, default=0)
    imax = fields.Integer(required=True, default=65535)
    omin = fields.Integer(required=True, default=0)
    omax = fields.Integer(required=True, default=10)

    data_write = fields.Float(default=0)

    raw_data = fields.Float(default=0)
    scaled_data = fields.Float(default=0)

    result_text = fields.Text(string='Message')

    value_ids = fields.One2many('onpoint.modbus.comm.line', 'modbus_comm_id')

    def truncate_float(self, n, places):
        return int(n * (10 ** places)) / 10 ** places

    def get_data(self):

        message = 'Initialize Connection...'
        self.update({
            'result_text': message
        })

        time.sleep(2)

        # SERVER_HOST = '192.168.1.1'
        # SERVER_PORT = 1100

        mmIm = ModbusClient(self.name, self.port, unit_id=self.unit_id, debug=True)

        current_source_value = 0
        result_channel_value = 0
        message = ''

        if not mmIm.is_open():
            if not mmIm.open():
                _logger.debug("Unable to connect")
                message += "Unable to connect"

        if mmIm.is_open():
            _logger.debug("Connected...")
            message += "\nConnected..."

            # Kepala 0 --> read_coil
            # Kepala 1 --> read_input
            # Kepala 3 --> read_input_registers
            # Kepala 4 --> read_holding

            address = self.address - 1
            data = mmIm.read_input_registers(address, self.qty)
            if data:
                _logger.debug("Ada Data : %s", data)

                current_source_value = data[0]

                message += "\nData Available..."
                message += "\n\nRaw Data... --> " + str(current_source_value)

                if current_source_value < self.imin:
                    result_channel_value = self.omin
                elif current_source_value > self.imax:
                    result_channel_value = self.omax
                else:
                    result_channel_value = self.omin + current_source_value * (self.omax - self.omin) / (self.imax + self.imin)

                result_channel_value = self.truncate_float(result_channel_value, 1)
                message += "\nScaled Data Float... --> " + str(result_channel_value)

            else:
                _logger.debug("No Data : ")
                message += "\nData Not Available..."

        mmIm.close()

        self.update({
            'raw_data': current_source_value,
            'scaled_data': result_channel_value,
            'result_text': message
        })

    def write_data(self):

        message = 'Initialize Connection...'
        self.update({
            'result_text': message
        })

        time.sleep(2)

        # SERVER_HOST = '192.168.1.1'
        # SERVER_PORT = 1100

        mmIm = ModbusClient(self.name, self.port, unit_id=self.unit_id, debug=True)

        current_source_value = 0
        result_channel_value = 0
        message = ''

        if not mmIm.is_open():
            if not mmIm.open():
                _logger.debug("Unable to connect")
                message += "Unable to connect"

        if mmIm.is_open():
            _logger.debug("Connected...")
            message += "\nConnected..."

            # Kepala 0 --> read_coil
            # Kepala 1 --> read_input
            # Kepala 3 --> read_input_registers
            # Kepala 4 --> read_holding

            address = self.address - 1
            write_imin = self.omin
            write_imax = self.omax
            write_omin = 0
            write_omax = 65535

            value_to_write = round(write_omin + self.data_write * (write_omax - write_omin) / (write_imax - write_imin))

            writing = mmIm.write_single_register(address, value_to_write)

            if writing:
                message += "\nWrite Data Success..."
                message += "\nValue to Write...." + str(value_to_write)
            else:
                _logger.debug("No Data : ")
                message += "\nWrite Data Failed..."

        mmIm.close()

        self.update({
            'result_text': message
        })


class OnpointModbusCommLine(models.TransientModel):
    _name = 'onpoint.modbus.comm.line'

    modbus_comm_id = fields.Many2one('onpoint.modbus.comm', required=True, string='Modbus', ondelete='cascade', index=True)
    comm_date = fields.Datetime(string='Date')
    comm_value_str = fields.Char(string='Last Value')

