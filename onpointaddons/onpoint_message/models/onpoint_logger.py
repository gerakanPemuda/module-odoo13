from odoo import api, fields, models


class OnpointLogger(models.Model):
    _inherit = 'onpoint.logger'

    message_setup_ids = fields.One2many('onpoint.logger.message', 'logger_id')
    outbox_ids = fields.One2many('onpoint.logger.outbox', 'logger_id')

    def act_view_notification_log(self):
        return {
            'name': 'Notification Logs',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'onpoint.logger.outbox',
            'domain': [('logger_id', '=', self.id)],
            # 'context': {
            #     'group_by': 'channel_id'
            # }
        }


class OnpointLoggerMessage(models.Model):
    _name = 'onpoint.logger.message'
    _inherit = 'api.zenziva.abstract'

    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    mobile_phone = fields.Char(string="Mobile Phone", required=True)
    send_alarm = fields.Boolean(default=False, string='Alarm')
    send_info = fields.Boolean(default=False, string='Summary')
    info_interval = fields.Selection([
        ('1h', 'Every Hour'),
        ('2h', 'Every Two Hours'),
        ('3h', 'Every Three Hours'),
        ('6h', 'Every Six Hours'),
        ('12h', 'Every Tweleve Hours'),
        ('1d', 'Every Day'),
    ], default='1h', string='Interval')
    is_active = fields.Boolean(default=True, string='Active')
    next_send = fields.Datetime(string='Next Schedule', required=True, default=fields.Datetime.now())
    send_sms = fields.Boolean(string='Send SMS', default=True)
    send_wa = fields.Boolean(string='Send WA', default=False)

    outbox_ids = fields.One2many('onpoint.logger.outbox', 'logger_message_id')

    @api.onchange('employee_id')
    def _get_mobile_phone(self):
        if self.employee_id:
            self.mobile_phone = self.employee_id.mobile_phone
        else:
            self.mobile_phone = False


class OnpointLoggerOutbox(models.Model):
    _name = 'onpoint.logger.outbox'
    _inherit = 'zenziva.outbox'

    logger_message_id = fields.Many2one('onpoint.logger.message', required=True, string='Logger Message', ondelete='cascade', index=True)
    logger_id = fields.Many2one('onpoint.logger', required=True, string='Logger', ondelete='cascade', index=True)
    message_type = fields.Selection([
        ('alarm', 'Alarm'),
        ('summary', 'Summary')
    ], string='Type', required=True)
    media = fields.Selection([
        ('sms', 'SMS'),
        ('wa', 'Whatsapp')
    ], default='sms', string='Media', required=True)

