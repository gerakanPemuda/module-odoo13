from odoo import fields, models, api


class WaterBalancePressureLines(models.Model):
    _name = 'onpoint.water.balance.pressure.lines'
    _description = 'Water Balance Pressure'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char()
    connection_number = fields.Integer()
    daily_average_pressure = fields.Float()
