from odoo import models, fields, api
from odoo.http import request
from datetime import datetime, timezone, timedelta
from time import mktime
from ast import literal_eval

import logging
_logger = logging.getLogger(__name__)


class OnpointSebaFTP(models.Model):
    _name = 'onpoint.seba.ftp'
    
    name = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)

class OnpointSeba(models.AbstractModel):
    _name = 'onpoint.seba'
    _description = 'Seba Driver'


    def _get_spec(self):
        specs = self.env['onpoint.seba.spec'].search_read([('name', 'like', 'block1_')])
        return specs

    def _read_data(self, buffer, idx, number_of_bytes):

        data_bit = 0

        if number_of_bytes == 1:
            data_bit = buffer[idx]
        elif number_of_bytes == 2:
            data_bit = (buffer[idx] << 8) + (buffer[idx+1])
        elif number_of_bytes == 3:
            data_bit = (buffer[idx] << 16) + (buffer[idx+1] << 8) + (buffer[idx+2])
            # _logger.debug('data bit %s - buffer idx --> %s buffer idx + 1 --> %s buffer idx + 2 --> %s', data_bit, buffer[idx], buffer[idx+1], buffer[idx+2])
        elif number_of_bytes == 4:
            data_bit = (buffer[idx] << 24) + (buffer[idx+1] << 16) + (buffer[idx+2] << 8) + (buffer[idx+3])
        else:
            data_bit = ''
            for x in range(0, number_of_bytes):
                if buffer[idx + x] != 0:
                    data_bit = data_bit + str(buffer[idx + x])

        return data_bit

    def _isbitset(self, byte, pos):

        if pos == 0:
            new_pos = 1
        else:
            new_pos = 2 ** pos
        
        if byte & new_pos == new_pos:
            return 1
        else:
            return 0


    def _process_bit_channel_flag(self, channel, flag_bytes):

        data = {}

        data['block1_ch'+ str(channel) +'_bit_chan_switch']          = self._isbitset(flag_bytes,0)
        data['block1_ch'+ str(channel) +'_bit_type_volt_5v']         = self._isbitset(flag_bytes,1)
        data['block1_ch'+ str(channel) +'_bit_type_pulse']           = self._isbitset(flag_bytes,2)
        data['block1_ch'+ str(channel) +'_bit_type_curr_pas']        = self._isbitset(flag_bytes,3)
        data['block1_ch'+ str(channel) +'_bit_type_curr_act']        = self._isbitset(flag_bytes,4)
        data['block1_ch'+ str(channel) +'_bit_type_frequency']       = self._isbitset(flag_bytes,5)
        data['block1_ch'+ str(channel) +'_bit_type_pwm']             = self._isbitset(flag_bytes,6)
        data['block1_ch'+ str(channel) +'_bit_type_ratiom']          = self._isbitset(flag_bytes,7)
        data['block1_ch'+ str(channel) +'_bit_type_signslave']       = self._isbitset(flag_bytes,8)
        data['block1_ch'+ str(channel) +'_bit_type_press_shock']     = self._isbitset(flag_bytes,9)
        data['block1_ch'+ str(channel) +'_bit_alarm_active']         = self._isbitset(flag_bytes,10)
        data['block1_ch'+ str(channel) +'_bit_alarm_maxlevel']       = self._isbitset(flag_bytes,11)
        data['block1_ch'+ str(channel) +'_bit_alarm_minlevel']       = self._isbitset(flag_bytes,12)
        data['block1_ch'+ str(channel) +'_bit_alarm_output1']        = self._isbitset(flag_bytes,13)
        data['block1_ch'+ str(channel) +'_bit_alarm_output2']        = self._isbitset(flag_bytes,14)
        data['block1_ch'+ str(channel) +'_bit_alarm_email']          = self._isbitset(flag_bytes,15)
        data['block1_ch'+ str(channel) +'_bit_alarm_sms']            = self._isbitset(flag_bytes,16)
        data['block1_ch'+ str(channel) +'_bit_alarm_edge']           = self._isbitset(flag_bytes,17)
        data['block1_ch'+ str(channel) +'_bit_alarm_wnd_min']        = self._isbitset(flag_bytes,18)
        data['block1_ch'+ str(channel) +'_bit_alarm_wnd_max']        = self._isbitset(flag_bytes,19)
        data['block1_ch'+ str(channel) +'_bit_alarm_wnd_low_flow']   = self._isbitset(flag_bytes,20)
        data['block1_ch'+ str(channel) +'_bit_press_shock_sampling'] = self._isbitset(flag_bytes,21)
        data['block1_ch'+ str(channel) +'_bit_reserved']             = self._isbitset(flag_bytes,22)
        
        return data

    def _parse_units(self, unit_id, unit_id_user, flag):

        units 		= {}
        units[0] 	= ''
        units[1] 	= '\B0C'
        units[2] 	= 'V'
        units[3] 	= 'mV'
        units[4] 	= 'l/s'
        units[5] 	= 'psi'
        units[6] 	= 'US gal.'
        units[7] 	= 'Imp. gal.'
        units[8] 	= 'mPa'
        units[9] 	= 'kg'
        units[10]	= 'm3/h'
        units[11] 	= 'lux'
        units[12] 	= 'mA'
        units[13] 	= 'bar'
        units[14] 	= 'V'
        units[15] 	= 'Hz'
        units[16] 	= '%'
        units[17] 	= 'm'

        unit_id		=  unit_id & 0x1F
        
        if unit_id == 18 :
            result	= unit_id_user
        else:
            result	= units[unit_id]

        if flag == 257:
            result = '<->'

        return result

    def _check_correction_value(self, val):
        if (val > 32767):
            val	= val - 65536
        
        return val
    
    def _corrData(self, flags, minR, maxR, minInput, maxInput, corrStart, corrEnd, val):

        Volt_5V_mode 	= 1
        Curr_Pas_mode 	= 4
        Curr_Act_mode 	= 8
        Ratiom_mode 	= 32
        
        result			= val

        if result < 0:
            result = 0

        if result > 65535:
            result = 65535

        if result < minInput:
            result = minR
        elif result >= maxInput:
            result = maxR
        else:
            result = (result - minInput) / ( maxInput - minInput)
            result = result * (maxR - minR)
            result = result + minR
        
        result	= round(result,3)
        
        return result
    
    def _flowData(self, interval, unit_id, maxReal, val):

        # _logger.debug('Interval %s - Unit ID %s - MaxReal %s - Val %s', interval, unit_id, maxReal, val)

        if ((unit_id & 0x80) == 0x80):
            result = ((val * maxReal) / interval)
        elif ((unit_id & 0x40) == 0x40): 
            result= (( val * maxReal ) / interval)*60
        elif ((unit_id & 0x20) == 0x20):
            result= (( val * maxReal ) / interval)*3600

        result	= round(result,3)

        return result

    def _bin2float(self, bin):
        bin2 = str(bin).replace('b', '').zfill(32)

        # _logger.debug('bin %s', bin)

        sign = bin2[0:1]
        exponent = bin2[1:9]
        mantissa = bin2[9:32]

        # _logger.debug('sign %s - exponent : %s - mantissa : %s', sign, exponent, mantissa)

        sign = 1 ** int(sign)
        exponent = int(exponent, 2)
        mantissa = int(mantissa, 2)

        # _logger.debug('sign %s - exponent : %s - mantissa : %s', sign, exponent, mantissa)

        if exponent != 0:
            exponent = 2 ** (exponent - 127)
            mantissa = 1 + (mantissa / (2 ** 23))
        else:
            exponent = 2 ** -126
            mantissa = mantissa / (2 ** 23)

        # _logger.debug('sign %s - exponent : %s - mantissa : %s', sign, exponent, mantissa)

        result 	= sign * exponent * mantissa

        # _logger.debug('result %s', result)

        return result

    def _process_treshold(self, data, channel, val):

        if data['block1_ch' + str(channel) + '_set_unit_id'] < 32:
            result             = self._corrData(data['block1_ch' + str(channel) + '_set_flags'],
                                                    data['block1_ch' + str(channel) + '_set_min_real'],
                                                    data['block1_ch' + str(channel) + '_set_max_real'],
                                                    data['block1_ch' + str(channel) + '_set_min_input'],
                                                    data['block1_ch' + str(channel) + '_set_max_input'],
                                                    data['block1_ch' + str(channel) + '_set_corr_start_volt'],
                                                    data['block1_ch' + str(channel) + '_set_corr_end_volt'],
                                                    val)
        else:
            result             = self._flowData(data['block1_interval'],
                                                    data['block1_ch' + str(channel) + '_set_unit_id'],
                                                    data['block1_ch' + str(channel) + '_set_max_real'],
                                                    val)

        return result

    def _process_block1(self, buffer=None):

        specs = self._get_spec()

        # _logger.debug('specs %s', specs)

        data = {}
        for spec in specs:
            data[spec['name']] = self._read_data(buffer, spec['pos'], spec['length'])
            # _logger.debug('name %s - Value : %s', spec['name'], data[spec['name']])

        
        data['block1_start_time'] = datetime.utcfromtimestamp(data['block1_start_time']).strftime('%Y-%m-%d %H:%M:%S')
        data['block1_current_logger_time'] = datetime.utcfromtimestamp(data['block1_current_logger_time']).strftime('%Y-%m-%d %H:%M:%S')

        cfg_bit_ch1 = self._process_bit_channel_flag(1, data['block1_ch1_set_flags'])
        cfg_bit_ch2 = self._process_bit_channel_flag(2, data['block1_ch2_set_flags'])
        cfg_bit_ch3 = self._process_bit_channel_flag(3, data['block1_ch3_set_flags'])
        cfg_bit_ch4 = self._process_bit_channel_flag(4, data['block1_ch4_set_flags'])

        data['block1_ch1_set_water_counter']   = round(self._bin2float(str(bin(data['block1_ch1_set_water_counter'])).zfill(32)),3)
        data['block1_ch2_set_water_counter']   = round(self._bin2float(str(bin(data['block1_ch2_set_water_counter'])).zfill(32)),3)
        data['block1_ch3_set_water_counter']   = round(self._bin2float(str(bin(data['block1_ch3_set_water_counter'])).zfill(32)),3)
        data['block1_ch4_set_water_counter']   = round(self._bin2float(str(bin(data['block1_ch4_set_water_counter'])).zfill(32)),3)

        data['block1_ch1_set_min_real']   = self._bin2float(str(bin(data['block1_ch1_set_min_real'])).zfill(32))
        data['block1_ch2_set_min_real']   = self._bin2float(str(bin(data['block1_ch2_set_min_real'])).zfill(32))
        data['block1_ch3_set_min_real']   = self._bin2float(str(bin(data['block1_ch3_set_min_real'])).zfill(32))
        data['block1_ch4_set_min_real']   = self._bin2float(str(bin(data['block1_ch4_set_min_real'])).zfill(32))


        data['block1_ch1_set_max_real']   = self._bin2float(str(bin(data['block1_ch1_set_max_real']).zfill(32)))
        data['block1_ch2_set_max_real']   = self._bin2float(str(bin(data['block1_ch2_set_max_real']).zfill(32)))
        data['block1_ch3_set_max_real']   = self._bin2float(str(bin(data['block1_ch3_set_max_real']).zfill(32)))
        data['block1_ch4_set_max_real']   = self._bin2float(str(bin(data['block1_ch4_set_max_real']).zfill(32)))


        data['block1_ch1_set_unit_text']       = self._parse_units(data['block1_ch1_set_unit_id'], data['block1_ch1_set_user_text'], data['block1_ch1_set_flags'])
        data['block1_ch2_set_unit_text']       = self._parse_units(data['block1_ch2_set_unit_id'], data['block1_ch2_set_user_text'], data['block1_ch2_set_flags'])
        data['block1_ch3_set_unit_text']       = self._parse_units(data['block1_ch3_set_unit_id'], data['block1_ch3_set_user_text'], data['block1_ch3_set_flags'])
        data['block1_ch4_set_unit_text']       = self._parse_units(data['block1_ch4_set_unit_id'], data['block1_ch4_set_user_text'], data['block1_ch4_set_flags'])

        data['block1_ch1_set_corr_start_volt'] = self._check_correction_value(data['block1_ch1_set_corr_start_volt'])
        data['block1_ch2_set_corr_start_volt'] = self._check_correction_value(data['block1_ch2_set_corr_start_volt'])
        data['block1_ch3_set_corr_start_volt'] = self._check_correction_value(data['block1_ch3_set_corr_start_volt'])
        data['block1_ch4_set_corr_start_volt'] = self._check_correction_value(data['block1_ch4_set_corr_start_volt'])
        
        data['block1_ch1_set_corr_end_volt']   = self._check_correction_value(data['block1_ch1_set_corr_end_volt'])
        data['block1_ch2_set_corr_end_volt']   = self._check_correction_value(data['block1_ch2_set_corr_end_volt'])
        data['block1_ch3_set_corr_end_volt']   = self._check_correction_value(data['block1_ch3_set_corr_end_volt'])
        data['block1_ch4_set_corr_end_volt']   = self._check_correction_value(data['block1_ch4_set_corr_end_volt'])
        
        data['block1_ch1_set_corr_start_current'] = self._check_correction_value(data['block1_ch1_set_corr_start_current'])
        data['block1_ch2_set_corr_start_current'] = self._check_correction_value(data['block1_ch2_set_corr_start_current'])
        data['block1_ch3_set_corr_start_current'] = self._check_correction_value(data['block1_ch3_set_corr_start_current'])
        data['block1_ch4_set_corr_start_current'] = self._check_correction_value(data['block1_ch4_set_corr_start_current'])
        
        data['block1_ch1_set_corr_end_current']   = self._check_correction_value(data['block1_ch1_set_corr_end_current'])
        data['block1_ch2_set_corr_end_current']   = self._check_correction_value(data['block1_ch2_set_corr_end_current'])
        data['block1_ch3_set_corr_end_current']   = self._check_correction_value(data['block1_ch3_set_corr_end_current'])
        data['block1_ch4_set_corr_end_current']   = self._check_correction_value(data['block1_ch4_set_corr_end_current'])

        data.update(cfg_bit_ch1)
        data.update(cfg_bit_ch2)
        data.update(cfg_bit_ch3)
        data.update(cfg_bit_ch4)

        # _logger.debug('data %s', data)

        return data

    def _process_block7(self, buffer, data):

        pos	= 1476
        page = 0
        count_pages = 0
        end_of_page = False

        active_channels = {}
        idx = 0
        for channel in range(1,5):
            if data['block1_ch' + str(channel) + '_bit_chan_switch'] == 1:
                active_channels[idx] = channel
                idx = idx + 1

        channel_values = []

        while end_of_page == False:

            data_length          = self._read_data(buffer, pos, 1)
            pos = pos + 1

            data_code = self._read_data(buffer, pos, 1)
            pos = pos + 1

            data_status_register = self._read_data(buffer, pos, 1)
            pos = pos + 1

            data_logger_id = self._read_data(buffer, pos, 3)
            pos    = pos + 3

            data_count_pages = self._read_data(buffer, pos, 2)
            pos    = pos + 2

            if count_pages == 0:
                count_pages = data_count_pages

            data_start_time = datetime.utcfromtimestamp(self._read_data(buffer, pos, 4)).strftime('%Y-%m-%d %H:%M:%S')
            pos    = pos + 4

            data_data_flash = self._read_data(buffer, pos, 1)
            pos = pos + 1

            data_count_data      = self._read_data(buffer, pos, 1)
            pos = pos + 1


            no = 0
            channel_idx = 0
            ch1		= 0
            ch2		= 0
            ch3		= 0
            ch4		= 0

            data_time = data_start_time

            while no <= data_count_data:

                # _logger.debug('Channel : %s / %s Pos : %s', channel_idx, len(active_channels), pos)

                if channel_idx >= len(active_channels):

                    channel_data = {
                        'dates' : data_time,
                        'ch1' : ch1,
                        'ch2' : ch2,
                        'ch3' : ch3,
                        'ch4' : ch4
                    }

                    channel_values.append(channel_data)
     
                    channel_idx = 0
                    next_date = datetime.strptime(data_time, ("%Y-%m-%d %H:%M:%S"))
                    data_time = (next_date + timedelta(seconds=data['block1_interval'])).strftime('%Y-%m-%d %H:%M:%S')
                    

                if no != data_count_data:
                    logger_value       = self._read_data(buffer, pos, 2)

                    logger_measurement = self._process_treshold(data, active_channels[channel_idx], logger_value)

                    # _logger.debug('--> %s Pos - %s Logger Value %s Logger Meas: %s', active_channels[channel_idx], pos, logger_value, logger_measurement)

                    pos                = pos + 2


                    if active_channels[channel_idx] == 1:
                        ch1 = logger_measurement
                    elif active_channels[channel_idx] == 2:
                        ch2 = logger_measurement
                    elif active_channels[channel_idx] == 3:
                        ch3 = logger_measurement
                    else:
                        ch4 = logger_measurement                        

                    channel_idx = channel_idx + 1

                no = no + 1


            if data_count_pages > 0:
                page = page + 1
            else:
                end_of_page = True

        # _logger.debug('Channel Values %s ', channel_values)

        return channel_values