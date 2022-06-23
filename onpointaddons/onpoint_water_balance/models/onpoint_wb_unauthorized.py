from odoo import fields, models, api


class WaterBalanceUnauthorizedConsumptionLines(models.Model):
    _name = 'onpoint.water.balance.unauthorized.consumption.lines'
    _description = 'Water Balance Unauthorized Consumption Line'

    name = fields.Char()
    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    period_duration = fields.Integer(related='water_balance_id.period_duration', readonly=True)
    error_margin = fields.Float(string='Error Margin')
    consumption = fields.Float(string='Consumption [m3/day]')
    total = fields.Float(string='Total [m3]', compute='_compute_total', store=True)

    @api.depends('error_margin', 'consumption', 'period_duration')
    def _compute_total(self):
        total = self.consumption * self.period_duration
        self.total = total
