from odoo import fields, models, api


class WaterBalanceIntermittentLines(models.Model):
    _name = 'onpoint.water.balance.intermittent.lines'
    _description = 'Water Balance Intermittent Lines'

    name = fields.Char(string='Area')
    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    connection_number = fields.Integer(string='Approximate Number of Connections')
    supply_days_per_week = fields.Integer(string='Supply Time [days per week]')
    supply_hours_per_day = fields.Integer(string='Supply Time [hours per day]')
    supply_total = fields.Float(compute='_compute_supply_total', store=True)

    @api.depends('connection_number', 'supply_days_per_week', 'supply_hours_per_day')
    def _compute_supply_total(self):
        self.supply_total = float(self.connection_number) * float(self.supply_days_per_week) * float(self.supply_hours_per_day)