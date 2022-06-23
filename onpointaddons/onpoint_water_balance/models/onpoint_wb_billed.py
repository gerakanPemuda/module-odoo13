from odoo import fields, models, api


class WaterBalanceBilledMeterLines(models.Model):
    _name = 'onpoint.water.balance.billed.meter.lines'
    _description = 'Water Balance Billed Meter Consumption Lines'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char()
    quantity = fields.Float()


class WaterBalanceBilledUnmeterLines(models.Model):
    _name = 'onpoint.water.balance.billed.unmeter.lines'
    _description = 'Water Balance Billed Unmeter Consumption Lines'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char()
    quantity = fields.Float()
