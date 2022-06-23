from odoo import models, fields, api
from datetime import datetime, timedelta


class OnpointCpRecap(models.Model):
    _name = 'onpoint.cp.recap'

    def _default_year(self):
        return str(datetime.today().year)

    months = fields.Selection([
        ('01', 'January'),
        ('02', 'February'),
        ('03', 'March'),
        ('04', 'April'),
        ('05', 'May'),
        ('06', 'June'),
        ('07', 'July'),
        ('08', 'August'),
        ('09', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], default='01', required=True)
    years = fields.Char(default=_default_year, required=True)
    line_ids = fields.One2many('onpoint.cp.recap.line', 'cp_recap_id')

    def act_get_critical_points(self):
        if self.months:
            data = []

            loggers = self.env['onpoint.logger'].search([])
            for logger in loggers:
                vals = {
                    'logger_id': logger.id,
                }
                row = (0, 0, vals)
                data.append(row)

            self.line_ids = [(6, 0, [])]

            self.write({
                'line_ids': data
            })


class OnpointCpRecapLine(models.Model):
    _name = 'onpoint.cp.recap.line'

    cp_recap_id = fields.Many2one('onpoint.cp.recap', required=True, string='CP Recap', ondelete='cascade', index=True)
    logger_id = fields.Many2one('onpoint.logger', string='Logger', index=True)
    pressure_0 = fields.Float(string='Pressure\n@ 00:00', default=0)
    pressure_6 = fields.Float(string='Pressure @ 06:00', default=0)
    pressure_12 = fields.Float(string='Pressure @ 12:00', default=0)
    pressure_18 = fields.Float(string='Pressure @ 18:00', default=0)
    threshold_max = fields.Float(default=0)
    threshold_min = fields.Float(default=0)
    alarm_freq_max = fields.Integer(default=0)
    alarm_freq_min = fields.Integer(default=0)

