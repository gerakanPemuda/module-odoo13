from odoo import api, fields, models


class OnpointLogger(models.Model):
    _inherit = 'onpoint.logger'

    telegram_group_id = fields.Many2one('onpoint.telegram.group')
    telegram_alarm_group_id = fields.Many2one('onpoint.telegram.group', string='Telegram Alarm Group')
    telegram_send_alarm = fields.Boolean(default=False, string='Alarm')
    telegram_send_info = fields.Boolean(default=False, string='Summary')
    telegram_info_interval = fields.Selection([
        ('1h', 'Every Hour'),
        ('2h', 'Every Two Hours'),
        ('3h', 'Every Three Hours'),
        ('6h', 'Every Six Hours'),
        ('12h', 'Every Tweleve Hours'),
        ('1d', 'Every Day'),
    ], default='1h', string='Interval')
    telegram_next_send = fields.Datetime(string='Next Schedule', required=True, default=fields.Datetime.now())

