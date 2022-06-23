from odoo import fields, models, api


class WaterBalanceNetworkDistributionLines(models.Model):
    _name = 'onpoint.water.balance.network.distribution.lines'
    _description = 'Water Balance Network Distribution Lines'

    water_balance_id = fields.Many2one('onpoint.water.balance', ondelete='cascade', index=True)
    name = fields.Char(string='Description')
    length = fields.Float()
