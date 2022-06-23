from odoo import models, fields, api
# from easymodbus.modbusClient import ModbusClient
from pyModbusTCP.client import ModbusClient
from datetime import datetime, timedelta
import time
import logging
import subprocess

_logger = logging.getLogger(__name__)


class OnpointMmim(models.Model):
    _name = 'onpoint.mmim'

    name = fields.Char(required=True, string='Name')
    host = fields.Char(required=True, string='Server Host', default='192.168.1.1')
    port = fields.Char(required=True, string='Port', default='1100')
    unit_id = fields.Integer(required=True, default=1)

    line_ids = fields.One2many('onpoint.mmim.line', 'mmim_id')
    detail_ids = fields.One2many('onpoint.mmim.detail', 'mmim_id')


def truncate_float(n, places):
    return int(n * (10 ** places)) / 10 ** places


class OnpointMmimLine(models.Model):
    _name = 'onpoint.mmim.line'

    mmim_id = fields.Many2one('onpoint.mmim', required=True, string='Modbus', ondelete='cascade', index=True)
    line_type = fields.Selection([
        ('analog', 'Analog I/O'),
        ('digital', 'Digital I/O')
    ], string='I/O Type', default='analog')
    logger_id = fields.Many2one('onpoint.logger', string='Logger', index=True)
    logger_channel_id = fields.Many2one('onpoint.logger.channel', string='Logger Channel', index=True)
    name = fields.Char(string='Name', required=True)
    address = fields.Integer(required=True, default=1)
    qty = fields.Integer(default=1)
    using_scalling = fields.Boolean()
    divider = fields.Integer(default=100)
    imin = fields.Integer(default=0)
    imax = fields.Integer(default=65535)
    omin = fields.Integer(default=0)
    omax = fields.Integer(default=10)

    data_write = fields.Float(default=0)
    data_read = fields.Float(default=0)

    raw_data = fields.Float(default=0)
    scaled_data = fields.Float(default=0)

    last_value = fields.Float(default=0, compute='get_last_value', store=True)

    coil_state = fields.Boolean(default=False)

    result_text = fields.Text(string='Message')

    detail_ids = fields.One2many('onpoint.mmim.detail', 'mmim_line_id')
    value_ids = fields.One2many('onpoint.mmim.value', 'mmim_line_id')

    @api.onchange('logger_id')
    def domain_logger_channel_id(self):
        logger_id = self.logger_id.id
        return {'domain': {'logger_channel_id': [('logger_id', '=', self.logger_id.id)]}}

    @api.depends('value_ids')
    def get_last_value(self):
        for record in self:
            last_data = record.value_ids.search([('mmim_line_id', '=', record.id)],
                                               order='create_date desc',
                                               limit=1)
            if last_data:
                record.last_value = last_data.mmim_value
            else:
                record.last_value = False

    def ping(self, check_ip):
        try:
            subprocess.check_output(["ping", "-c", "1", check_ip])
            return True
        except subprocess.CalledProcessError:
            return False

    def write_data(self):
        message = 'Initialize Connection...'
        self.update({
            'result_text': message
        })

        mmim = ModbusClient(self.mmim_id.host, self.mmim_id.port, unit_id=self.mmim_id.unit_id, debug=True)

        current_source_value = 0
        result_channel_value = 0
        message = ''

        if not mmim.is_open():
            if not mmim.open():
                _logger.debug("Unable to connect")
                message += "Unable to connect"

        if mmim.is_open():
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

            writing = mmim.write_single_register(address, value_to_write)

            if writing:
                message += "\nWrite Data Success..."
                message += "\nValue to Write...." + str(value_to_write)
                _logger.debug("Write Data Success : %s", str(value_to_write))
            else:
                _logger.debug("No Data : ")
                message += "\nWrite Data Failed..."

        mmim.close()

        self.update({
            'result_text': message
        })

    def read_mmim_value(self):
        is_connected = self.ping(self.mmim_id.host)
        result_channel_value = 0
        result_coil_state = False
        message = ''

        if is_connected:
            mmim = ModbusClient(self.mmim_id.host, self.mmim_id.port, unit_id=self.mmim_id.unit_id, debug=True)

            current_source_value = 0
            result_channel_value_str = ""

            if not mmim.is_open():
                if not mmim.open():
                    message += "Unable to connect"
                    result_channel_value_str = "Unable to connect"

            if mmim.is_open():
                message += "Connected..."

                address = self.address - 1
                if self.line_type == 'analog':
                    data = mmim.read_input_registers(address, self.qty)
                    if data:
                        current_source_value = data[0]

                        message += "\nData: " + str(current_source_value)

                        if not self.using_scalling:
                            if self.divider > 0:
                                result_channel_value = current_source_value / self.divider
                            else:
                                result_channel_value = 0
                        else:
                            if current_source_value < self.imin:
                                result_channel_value = self.omin
                            elif current_source_value > self.imax:
                                result_channel_value = self.omax
                            else:
                                # result_channel_value = self.omin + current_source_value * (self.omax - self.omin) / (self.imax - self.imin)
                                result_channel_value = self.omin + current_source_value * (self.omax - self.omin) / (
                                            self.imax + self.imin)

                        result_channel_value = truncate_float(result_channel_value, 3)
                        result_channel_value_str = str(result_channel_value)
                        message += " --> " + str(result_channel_value)
                    else:
                        message += "Data Not Available: "
                        message += " " + mmim.last_error_txt()
                        # message += "\n" + mmim.last_except_txt()
                else:
                    data = mmim.read_coils(address, self.qty)
                    if data:
                        result_coil_state = data[0]
                    else:
                        message += "Data Not Available: "
                        message += " " + mmim.last_error_txt()
                        # message += "\n" + mmim.last_except_txt()
            mmim.close()
        else:
            message += 'Ping failed...\n'

        return result_channel_value, result_coil_state, message

    def read_data(self):

        result_channel_value, result_coil_state, message = self.read_mmim_value()

        try:
            self.env['onpoint.mmim.value'].sudo().create({
                'mmim_line_id': self.id,
                'mmim_value': result_channel_value,
                'coil_state': result_coil_state,
                'remarks': message
            })
        except Exception as e:
            x = 1
            pass

        # value_ids = []
        # value_vals = {
        #     'mmim_id': self.id,
        #     'comm_date': datetime.now(),
        #     'comm_value_str': result_channel_value_str
        # }
        #
        # row_value = (0, 0, value_vals)
        # value_ids.append(row_value)
        #
        # mmim_data.sudo().update({
        #     'line_ids': value_ids
        # })

    def clear_message(self):
        self.sudo().write({
            'result_text': ''
        })

    def write_coil(self):
        message = 'Initialize Connection...'
        self.update({
            'result_text': message
        })

        time.sleep(2)

        # SERVER_HOST = '192.168.1.1'
        # SERVER_PORT = 1100

        mmIm = ModbusClient(self.mmim_id.host, self.mmim_id.port, unit_id=self.mmim_id.unit_id, debug=True)

        current_source_value = 0
        result_channel_value = 0
        message = ''
        new_coil_state = False

        if not mmIm.is_open():
            if not mmIm.open():
                _logger.debug("Unable to connect")
                message += "Unable to connect"

        if mmIm.is_open():
            _logger.debug("Connected...")
            message += "\nConnected..."

            address = self.address - 1

            if self.coil_state:
                new_coil_state = False
            else:
                new_coil_state = True

            mmIm.write_single_coil(address, new_coil_state)

        mmIm.close()

        self.update({
            'coil_state': new_coil_state,
            'result_text': message
        })

    def act_goto_mmim_value(self):
        action = self.env.ref('onpoint_modbus.act_onpoint_mmim_value')
        result = action.read()[0]

        value_ids = self.mapped('value_ids')

        result['domain'] = "[('id','in',%s)]" % (value_ids.ids)

        return result


class OnpointMmimDetail(models.Model):
    _name = 'onpoint.mmim.detail'

    mmim_id = fields.Many2one('onpoint.mmim', required=True, string='Modbus', ondelete='cascade', index=True)
    mmim_line_id = fields.Many2one('onpoint.mmim.line', required=True, string='Modbus', ondelete='cascade', index=True)
    comm_date = fields.Datetime(string='Date')
    comm_value_str = fields.Char(string='Last Value')


class OnpointMmimValue(models.Model):
    _name = 'onpoint.mmim.value'
    _order = 'create_date desc'

    mmim_line_id = fields.Many2one('onpoint.mmim.line', required=True, string='Modbus', ondelete='cascade', index=True)
    mmim_value = fields.Float(default=0)
    coil_state = fields.Boolean(default=False)
    remarks = fields.Text()
