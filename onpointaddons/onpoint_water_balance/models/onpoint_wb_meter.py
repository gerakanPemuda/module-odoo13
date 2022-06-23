from odoo import fields, models, api


class WaterBalanceMeterErrorBilledLines(models.Model):
    _name = 'onpoint.water.balance.meter.error.billed.lines'
    _description = 'Water Balance Meter Error Billed Lines'

    name = fields.Char()
    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    quantity = fields.Float()
    meter_under_registration = fields.Float()
    total = fields.Float(compute='_compute_total')
    error_margin = fields.Float()

    @api.depends('quantity', 'meter_under_registration')
    def _compute_total(self):
        total = self.quantity / (1 - self.meter_under_registration) - self.quantity
        self.total = total
