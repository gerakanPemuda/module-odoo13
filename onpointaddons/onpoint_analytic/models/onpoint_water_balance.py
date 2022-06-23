from odoo import models, fields, api
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta


class OnpointWaterBalance(models.Model):
    _name = 'onpoint.water.balance'

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
    start_date = fields.Date(compute='set_period_date')
    end_date = fields.Date(compute='set_period_date')
    line_ids = fields.One2many('onpoint.water.balance.line', 'water_balance_id')

    def set_period_date(self):
        self.start_date = self.years + '-' + self.months + '-01'
        self.end_date = (datetime.strptime(self.years + '-' + self.months + '-01', "%Y-%m-%d") + relativedelta(months=1) - relativedelta(days=1)).strftime("%Y-%m-%d")

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

    def get_time_zone(self, logger_id):
        logger = self.env['onpoint.logger'].browse(logger_id)
        convert_time = logger.convert_time
        if convert_time:
            time_zone = self.env['ir.config_parameter'].sudo().get_param('onpoint_monitor.time_zone')
        else:
            time_zone = 7
        return int(time_zone)


    def act_get_dmas(self):
        value_type = self.env['onpoint.value.type'].search([('name', '=', 'Flow')])
        if self.months:
            data = []

            dmas = self.env['onpoint.dma'].search([])
            for dma in dmas:
                consumption = 0
                # for logger in dma.logger_ids:
                #     add_hours = self.get_time_zone(logger.id)
                #     start_date_time = (datetime.strptime(self.start_date.strftime('%Y-%m-%d') + ' 00:00:00', "%Y-%m-%d %H:%M:%S") - timedelta(hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
                #     end_date_time = (datetime.strptime(self.end_date.strftime('%Y-%m-%d') + ' 23:59:59', "%Y-%m-%d %H:%M:%S") - timedelta(hours=add_hours)).strftime("%Y-%m-%d %H:%M:%S")
                #
                #     logger_channels = logger.channel_ids.search([('logger_id', '=', logger.id),
                #                                                  ('value_type_id', '=', value_type.id)])
                #     for logger_channel in logger_channels:
                #         logger_values = logger_channel.value_ids.search([('channel_id', '=', logger_channel.id),
                #                                                          ('dates', '>', start_date_time),
                #                                                          ('dates', '<=', end_date_time)])
                #         consumption += sum(logger_value.channel_value for logger_value in logger_values)
                #
                # consumption = (consumption * 300) / 1000
                #
                vals = {
                    'dma_id': dma.id,
                    'inlet': consumption
                }
                row = (0, 0, vals)
                data.append(row)

            self.line_ids = [(6, 0, [])]

            self.write({
                'line_ids': data
            })


class OnpointWaterBalanceLine(models.Model):
    _name = 'onpoint.water.balance.line'

    water_balance_id = fields.Many2one('onpoint.water.balance', required=True, string='Water Balance', ondelete='cascade', index=True)
    dma_id = fields.Many2one('onpoint.dma', string='DMA', required=True, index=True)
    diameter = fields.Float(string='Diameter', default=0)
    inlet = fields.Float(string='Q Inlet', default=0)
    outlet = fields.Float(string='Billing', default=0, compute='_compute_nrw', store=True)
    customer = fields.Float(string='Customer', default=0, compute='_compute_nrw', store=True)
    nrw_meter = fields.Float(string='NRW Meter', default=0, compute='_compute_nrw', store=True)
    nrw_percentage = fields.Float(default=0)
    mnf = fields.Integer(default=0)
    dma_boundary_verification = fields.Boolean(default=False)
    pipe_rehab = fields.Boolean(default=False)
    dma_meter_verification = fields.Boolean(default=False)
    alc = fields.Boolean(default=False)

    @api.depends('dma_id')
    def _compute_nrw(self):
        for record in self:
            dma_billing = self.env['onpoint.dma.billing'].search([('months', '=', record.water_balance_id.months),
                                                                  ('years', '=', record.water_balance_id.years)])
            dma_billing_line = dma_billing.line_ids.search([('dma_id', '=', record.dma_id.id)])
    
            # record.outlet = dma_billing_line.consumption
            # record.customer = dma_billing_line.customer_count
            # record.nrw_meter = record.inlet - record.outlet
            # record.nrw_percentage = (record.nrw_meter / record.inlet) * 100

            record.outlet = 0
            record.customer = 0
            record.nrw_meter = 0
            record.nrw_percentage = 0
