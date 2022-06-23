from odoo import fields, models, api


class WaterBalanceUnbilledMeterLines(models.Model):
    _name = 'onpoint.water.balance.unbilled.meter.lines'
    _description = 'Water Balance Unbilled Meter Lines'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char()
    quantity = fields.Float()


class WaterBalanceUnbilledUnmeterLines(models.Model):
    _name = 'onpoint.water.balance.unbilled.unmeter.lines'
    _description = 'Water Balance Unbilled Unmeter Lines'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char()
    quantity = fields.Float()
    error_margin = fields.Float()
